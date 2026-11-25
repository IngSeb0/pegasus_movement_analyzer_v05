"""Configuración reversible de los workers para esta sesión FMA."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import shlex
from acceso import ssh, ROOT, SESSION

CONFIG = '/etc/condor/config.d/99-dme-intensivo-20261122.conf'


def ensure_aliases():
    config=SESSION/'ssh_config'
    text=config.read_text()
    if 'Host dme-worker1' not in text:
        key=(ROOT.parent/'azure_cloud_20261025/.local/id_ed25519_dme').as_posix()
        for i in range(1,5):
            text+=(f'\nHost dme-worker{i}\n  HostName 10.42.1.{i+3}\n  User dmeadmin\n'
                   f'  IdentityFile {key}\n  ProxyJump dme-master\n  BatchMode yes\n'
                   '  ConnectTimeout 15\n  StrictHostKeyChecking accept-new\n')
        config.write_text(text,encoding='ascii')
    if 'ServerAliveInterval' not in text:
        text+='\nHost *\n  ServerAliveInterval 15\n  ServerAliveCountMax 6\n'
        config.write_text(text,encoding='ascii')


def configure(i, count):
    host = f'dme-worker{i}'
    text = ('# Temporary intensivo 20261122\nNUM_CPUS = 1\nNUM_SLOTS = 1\n'
            'NUM_SLOTS_TYPE_1 = 1\nSLOT_TYPE_1 = cpus=1\nSLOT_TYPE_1_PARTITIONABLE = TRUE\n'
            f'DMEStudyEligible = {"TRUE" if i <= count else "FALSE"}\n'
            'DMEStudyName = "intensivo_20261122"\nSTARTD_ATTRS = $(STARTD_ATTRS), DMEStudyEligible, DMEStudyName\n')
    code = f"from pathlib import Path; import subprocess; p=Path({CONFIG!r}); assert not p.exists() or p.read_text().startswith('# Temporary intensivo 20261122'); p.write_text({text!r}); subprocess.run(['condor_reconfig'],check=True)"
    ssh(host, 'sudo python3 -c '+shlex.quote(code))
    return dict(worker=host, cpus=1, eligible=i<=count)


def pool(count):
    ensure_aliases()
    with ThreadPoolExecutor(max_workers=4) as executor:
        records = list(executor.map(lambda i: configure(i,count), range(1,5)))
    (SESSION/f'pool_W{count}.json').write_text(json.dumps(records,indent=2))


def restore():
    ensure_aliases()
    code = f"from pathlib import Path; import subprocess; p=Path({CONFIG!r}); assert not p.exists() or p.read_text().startswith('# Temporary intensivo 20261122'); p.unlink(missing_ok=True); subprocess.run(['condor_reconfig'],check=True)"
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda i: ssh(f'dme-worker{i}', 'sudo python3 -c '+shlex.quote(code)),range(1,5)))
    (SESSION/'pool_restaurado.json').write_text(json.dumps(dict(restaurado=True)))


if __name__ == '__main__':
    import sys
    pool(int(sys.argv[1]))
