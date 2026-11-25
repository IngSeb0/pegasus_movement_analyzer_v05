"""Limita, muestra o quita el ancho de banda entre el coordinador y los workers (así se logra el régimen
intensivo en datos: con la red lenta, mover los archivos tarda más que calcular).

    python red.py limitar 50      # 50 Mbit/s en cada nodo, solo hacia el otro extremo del flujo de datos
    python red.py ver             # estado de tc en los cinco nodos
    python red.py quitar          # deja la red como estaba (hacerlo siempre al terminar)

Usa tc (control de tráfico de Linux) por SSH. Cada nodo limita lo que ENVÍA: el coordinador hacia los workers
y cada worker hacia el coordinador. Solo se frena el tráfico hacia esos destinos; el resto (SSH) sigue libre.
"""
import os, subprocess, sys

# (nodo, un par al que enviar, red destino que se limita)
NODOS = [("dme-master", "10.42.1.5", "10.42.1.0/24")] + [(f"dme-worker{i}", "10.42.0.4", "10.42.0.4/32") for i in range(1, 5)]


SSH_CONFIG = os.environ.get("SSH_CONFIG")
SSH_OPTIONS = ["-F", SSH_CONFIG] if SSH_CONFIG else []


def ssh(nodo, orden):
    return subprocess.run(["ssh", *SSH_OPTIONS, nodo, orden], capture_output=True, text=True, check=True).stdout


accion, *args = sys.argv[1:] or ["?"]
for nodo, par, destino in NODOS:
    # la interfaz por la que sale el tráfico hacia ese par (p. ej. eth0)
    ruta = ssh(nodo, f"ip -o route get {par}").split()
    iface = ruta[ruta.index("dev") + 1]
    if accion == "limitar":
        if "tbf" in ssh(nodo, f"tc qdisc show dev {iface}") or "prio" in ssh(nodo, f"tc qdisc show dev {iface}"):
            sys.exit(f"{nodo} ya tiene un límite: primero «quitar»")
        # dos colas: la 1:2 tiene el tope (tbf); el filtro manda ahí solo lo dirigido a «destino»
        ssh(nodo, f"sudo tc qdisc add dev {iface} root handle 1: prio bands 2 priomap 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        ssh(nodo, f"sudo tc qdisc add dev {iface} parent 1:2 handle 20: tbf rate {args[0]}mbit burst 256kbit latency 400ms")
        ssh(nodo, f"sudo tc filter add dev {iface} parent 1: protocol ip prio 1 u32 match ip dst {destino} flowid 1:2")
    elif accion == "quitar":
        ssh(nodo, f"sudo tc qdisc del dev {iface} root || true")
    elif accion != "ver":
        sys.exit(__doc__)
    print(f"== {nodo} ({iface})\n" + ssh(nodo, f"tc qdisc show dev {iface}"))
