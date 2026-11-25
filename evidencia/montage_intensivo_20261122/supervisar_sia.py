"""Coteja el disco y ejecuta la medición con restauración de tc."""

from datetime import datetime, timedelta
from pathlib import Path
import json
import shlex
import subprocess
import tarfile
import time

import acceso


root = Path(__file__).resolve().parent
results = root / "RESULTADOS"
session = root / "sesion07"
acceso.SESSION = session
hosts = ["dme-master", *(f"dme-worker{i}" for i in range(1, 5))]
remote = "/mnt/montage_intensivo_20261122/medicion"
ssh, scp = acceso.ssh, acceso.scp


def setup_ssh():
    config = session / "ssh_config"
    text = config.read_text()
    key = next(line.split(None, 1)[1] for line in text.splitlines() if "IdentityFile" in line)
    for index, host in enumerate(hosts[1:], 1):
        text += (f"\nHost {host}\n  HostName 10.42.1.{index + 3}\n  User dmeadmin\n"
                 f"  IdentityFile {key}\n  ProxyJump dme-master\n  BatchMode yes\n"
                 "  ConnectTimeout 12\n  StrictHostKeyChecking accept-new\n")
    config.write_text(text, encoding="ascii")


def network(host, when, iface):
    state = ssh(host, f"tc -s qdisc show dev {iface}")
    with (results / "TC.txt").open("a", encoding="utf-8") as stream:
        stream.write(f"\n{host} {when} {iface}\n{state}")
    return state


def stage(deadline):
    sizes = json.loads((results / "SPECS.json").read_text())["MG-BASE"]["files"]
    entries = sum(f["size_bytes"] for f in sizes if f["role"] == "external")
    projected = sum(f["size_bytes"] for f in sizes if f["role"] == "intermediate")
    mosaics = sum(f["size_bytes"] for f in sizes if f["role"] == "final")
    minimum = max(3 * 2**30, 2 * (3 * (entries + projected) + 2 * mosaics))
    disks = {}
    for host in hosts:
        folder = "/mnt" if host == "dme-master" else '$(condor_config_val EXECUTE)'
        value = ssh(host, f'df -PB1 "{folder}"')
        disks[host] = {"available_bytes": int(value.splitlines()[1].split()[3]), "required_bytes": minimum}
    (results / "DISCO_PILOTO.json").write_text(json.dumps(disks, indent=2))
    if any(disk["available_bytes"] < minimum for disk in disks.values()):
        raise RuntimeError("Espacio insuficiente con el margen de disco sellado")
    ssh("dme-master", f"sudo -n install -d -o dmeadmin -g dmeadmin {remote}")
    scp(root / "preparacion_planes.tar.gz", f"dme-master:{remote}/")
    frozen = json.loads((results / "DISENO_CONGELADO.json").read_text())
    for name in (*frozen, "DISENO_CONGELADO.json"):
        scp(results / name, f"dme-master:{remote}/")
    ssh("dme-master", f"cd {remote} && tar -xzf preparacion_planes.tar.gz && "
        "cp ~/montage_intensivo_20261122/entradas_sia/*.fits montage_assets/ && "
        "cp mosaico.hdr montage_assets/template.hdr")
    settings = {
        "startedAtUtc": (session / "inicio_utc.txt").read_text().strip(),
        "deadlineUtc": (deadline - timedelta(minutes=25)).isoformat(),
        "stopSubmissionsUtc": (deadline - timedelta(minutes=35)).isoformat(),
        "maximumNewWorkflows": 7,
    }
    python = ("import hashlib,json; from pathlib import Path; "
              "paths=[*Path('runtime').rglob('*.py'),*Path('core').rglob('*.py'),"
              "*Path('montage_assets').iterdir(),Path('medir_sia.py')]; "
              "Path('HASHES.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() "
              "for p in paths})); "
              f"Path('SESSION_ACTIVE.json').write_text({json.dumps(settings)!r})")
    ssh("dme-master", f"cd {remote} && python3 -c {shlex.quote(python)}")


def run(unit, arguments, wait_limit):
    command = f"python3 -u medir_sia.py {arguments} > {unit}.log 2>&1; status=$?; echo $status > {unit}.exit"
    ssh("dme-master", f"sudo -n systemd-run --unit={unit} --uid=dmeadmin --working-directory={remote} "
        f"--property=RuntimeMaxSec={wait_limit} /bin/bash -c {shlex.quote(command)}")
    deadline = time.monotonic() + wait_limit
    while time.monotonic() < deadline:
        state = ssh("dme-master", f"cd {remote}; if test -f {unit}.exit; then cat {unit}.exit; "
                    f"else systemctl is-active {unit} || true; fi", 30).strip()
        if state == "0":
            return
        if state not in {"active", "activating"}:
            raise RuntimeError(ssh("dme-master", f"cd {remote}; tail -40 {unit}.log"))
        time.sleep(20)
    raise TimeoutError(f"Venció la ventana del proceso {unit}")


def export():
    source = root / "exportar_nativo.py"
    scp(source, f"dme-master:{remote}/")
    ssh("dme-master", f"cd {remote} && python3 exportar_nativo.py", 240)
    package = session / "evidencia.tar.gz"
    scp(f"dme-master:{remote}/evidencia.tar.gz", package)
    with tarfile.open(package) as archive:
        archive.extractall(results / "evidencia_nativa", filter="data")


def main():
    interfaces = {}
    staged = False
    deadline = datetime.fromisoformat((session / "limite_utc.txt").read_text().strip()[:26] + "+00:00")
    try:
        setup_ssh()
        stage(deadline)
        staged = True
        for host in hosts:
            central = host == hosts[0]
            peer = "10.42.1.5" if central else "10.42.0.4"
            destination = "10.42.1.0/24" if central else "10.42.0.4/32"
            route = ssh(host, f"ip -o route get {peer}").split()
            iface = route[route.index("dev") + 1]
            original = network(host, "antes", iface)
            queues = [line.split()[1] for line in original.splitlines() if line.startswith("qdisc ")]
            if not queues or set(queues) - {"noqueue", "mq", "fq_codel"}:
                raise RuntimeError(f"{host} tiene una disciplina de red previa: {original}")
            delay = max(1, int(deadline.timestamp() - time.time() - 20 * 60))
            ssh(host, f"sudo -n systemd-run --unit=montage-quitar-tc --on-active={delay}s "
                f"/usr/sbin/tc qdisc del dev {iface} root")
            interfaces[host] = iface
            ssh(host, f"sudo -n tc qdisc add dev {iface} root handle 1: prio bands 2 "
                "priomap 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
            ssh(host, f"sudo -n tc qdisc add dev {iface} parent 1:2 handle 20: "
                "tbf rate 100mbit burst 256kbit latency 400ms && "
                f"sudo -n tc filter add dev {iface} parent 1: protocol ip prio 1 u32 "
                f"match ip dst {destination} flowid 1:2")
            assert " tbf " in network(host, "durante", iface)
        run("montage-sia-banda", "banda", 1350)
        remaining = int(deadline.timestamp() - time.time() - 25 * 60)
        if remaining < 2700:
            raise RuntimeError("No queda el intervalo completo de 45 minutos para el piloto")
        run("montage-sia-medir", "", remaining)
    finally:
        errors = []
        for host, iface in interfaces.items():
            try:
                state = ssh(host, f"tc qdisc show dev {iface}")
                if "qdisc prio 1:" in state:
                    ssh(host, f"sudo -n tc qdisc del dev {iface} root")
                ssh(host, "sudo -n systemctl stop montage-quitar-tc.timer")
                assert " tbf " not in network(host, "después", iface)
            except Exception as exc:
                errors.append(f"{host}: {exc}")
        if errors:
            (results / "TC_ERRORES.json").write_text(json.dumps(errors, indent=2))
        try:
            if staged:
                export()
        finally:
            subprocess.run(["powershell", "-NoProfile", "-File", str(root / "control_medicion.ps1"),
                            "-Action", "close"], check=True, timeout=720)
        if errors:
            raise RuntimeError("No se confirmó la limpieza de tc en todos los nodos")


if __name__ == "__main__":
    main()
