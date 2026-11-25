"""Tiempos (versión corta): en qué se fue la duración de una corrida.

Uso:  python tiempos.py CARPETA_run0001 history.long

Parte la duración del flujo en 6 tramos que suman el total (cada segundo va a un solo tramo;
si dos coinciden gana el de arriba). Fuentes: jobstate.log (Pegasus/DAGMan) e history.long (HTCondor).
"""
import glob, json, os, re, sys

run, history = sys.argv[1], sys.argv[2]
AUXILIARES = ("create_dir", "stage_in", "stage_out", "cleanup", "register", "chmod")


def campo(bloque, nombre):
    m = re.search(rf"^{nombre} = (\S+)", bloque, re.M)
    return int(float(m[1])) if m else None


# 1. Eventos de cada job en jobstate.log: envío a la cola (SUBMIT) y fin del post-script.
envio, fin_post, inicio, fin = {}, {}, None, None
for linea in open(os.path.join(run, "jobstate.log")):
    p = linea.split()
    if p[1] == "INTERNAL":
        inicio = min(inicio or int(p[0]), int(p[0])) if "DAGMAN_STARTED" in linea else inicio
        fin = int(p[0]) if "DAGMAN_FINISHED" in linea else fin
    elif p[2] == "SUBMIT":
        envio.setdefault(p[1], int(p[0]))
    elif p[2] in ("POST_SCRIPT_SUCCESS", "POST_SCRIPT_FAILURE", "JOB_SUCCESS"):
        fin_post[p[1]] = int(p[0])

# 2. Eventos de transferencia de cada tarea en history.long (HTCondor los registra en segundos).
tramos = {k: [] for k in ("ejecucion", "transferencia", "auxiliares", "cola", "cierre", "dagman")}
for bloque in open(history).read().split("\n\n"):
    nodo = re.search(r'^DAGNodeName = "(\S+)"', bloque, re.M)
    if not nodo or nodo[1] not in envio or nodo[1].startswith(AUXILIARES):
        continue
    n = nodo[1]
    ent_i, ent_f, sal_i, sal_f = (campo(bloque, c) for c in
                                  ("TransferInStarted", "TransferInFinished", "TransferOutStarted", "TransferOutFinished"))
    tramos["cola"].append((envio[n], ent_i))            # esperando máquina
    tramos["transferencia"] += [(ent_i, ent_f), (sal_i, sal_f)]
    tramos["ejecucion"].append((ent_f, sal_i))          # de que termina de llegar la entrada a que empieza la salida
    tramos["cierre"].append((sal_f, fin_post[n]))       # post-script de Pegasus
for n in envio:                                          # jobs auxiliares de Pegasus: toda su vida
    if n.startswith(AUXILIARES):
        tramos["auxiliares"].append((envio[n], fin_post[n]))

# 3. Cada segundo de la corrida se asigna al primer tramo (en este orden) que lo cubre; si ninguno, DAGMan.
suma = dict.fromkeys(tramos, 0)
for t in range(inicio, fin):
    suma[next((k for k in tramos if k != "dagman" and any(a <= t < b for a, b in tramos[k]) ), "dagman")] += 1

total = fin - inicio
oficial = json.load(open(glob.glob(os.path.join(run, "*.dag.metrics"))[0]))
print(f"Duración del flujo (DAGMan): {oficial['end_time'] - oficial['start_time']:.1f} s   (suma de tramos: {total} s)")
for k, v in suma.items():
    print(f"  {k:<14}{v:>5} s  {100 * v / total:5.1f} %")
