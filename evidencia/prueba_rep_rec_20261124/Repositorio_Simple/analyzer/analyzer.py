"""Analyzer (versión corta): bytes requeridos y volumen del contrato de transferencia de una corrida.

Uso:  python analyzer.py CARPETA_run0001 history.long [-v]

Lee la carpeta que dejó pegasus-plan (workflow.yml, .sub, .meta) y el historial de HTCondor.
-v: de dónde sale cada byte requerido. Si el historial muestra reintentos, jobs incompletos o
transferencias que no cuadran con el contrato, no calcula nada y dice por qué.
"""
import glob, json, os, re, sys
import yaml

run, history = sys.argv[1], sys.argv[2]
RUTA = {os.path.basename(f): f for f in glob.glob(os.path.join(run, "00", "*", "*"))}   # Pegasus reparte los jobs en 00/00, 00/01, ...
COORDINADOR = "dme-master"


def parar(titulo, problemas):
    if problemas:
        sys.exit(titulo + "\n  " + "\n  ".join(problemas))


def campo(bloque, nombre):
    m = re.search(rf"^{nombre} = (.*)$", bloque, re.M)
    return m.group(1).strip('"') if m else None


# 1. Tamaño de cada archivo (Pegasus lo anota en los .meta de cada job).
tamano = {}
for meta in [f for n, f in RUTA.items() if n.endswith(".meta")]:
    for archivo in json.load(open(meta)):
        tamano[archivo["_id"]] = int(archivo["_attributes"]["size"])

# 2. Quién produce y quién lee cada archivo (workflow.yml de Pegasus).
productor, lectores, finales = {}, {}, set()
for tarea in yaml.safe_load(open(os.path.join(run, "workflow.yml")))["jobs"]:
    for uso in tarea["uses"]:
        if uso["type"] == "output":
            productor[uso["lfn"]] = tarea["id"]
            if uso.get("stageOut"):
                finales.add(uso["lfn"])
        else:
            lectores.setdefault(uso["lfn"], []).append(tarea["id"])

# 3. Qué tareas van en cada job: una por job, salvo los jobs agrupados (merge_*.in).
tareas_del_job = {}
for sub in [f for n, f in RUTA.items() if n.endswith(".sub")]:
    job = os.path.basename(sub)[:-4]
    if job.startswith("campaign_task_"):
        tareas_del_job[job] = [job[len("campaign_task_"):]]
    elif job.startswith("merge_"):
        tareas_del_job[job] = re.findall(r"^#@ \d+ \S+ (\S+)", open(sub[:-4] + ".in").read(), re.M)

# 4. Historial de HTCondor: un bloque por cada intento de cada job.
intentos = {}
for bloque in open(history).read().split("\n\n"):
    nodo = campo(bloque, "DAGNodeName")
    if nodo in tareas_del_job:
        intentos.setdefault(nodo, []).append(bloque)

# Diagnóstico: cada job debe haber corrido una sola vez, terminado bien y decir dónde corrió.
maquina_de_tarea, problemas = {}, []
for job, tareas in tareas_del_job.items():
    registros = intentos.get(job, [])
    if len(registros) != 1:
        problemas.append(f"{job}: {len(registros)} registros en el historial (falta, o hubo reintentos)")
        continue
    host = campo(registros[0], "LastRemoteHost")
    if campo(registros[0], "NumJobStarts") != "1":
        problemas.append(f"{job}: se inició {campo(registros[0], 'NumJobStarts')} veces (reintento)")
    elif not host or campo(registros[0], "JobStatus") != "4" or campo(registros[0], "ExitCode") != "0":
        problemas.append(f"{job}: no terminó bien o el historial no dice dónde corrió")
    else:
        maquina_de_tarea.update({t: host.split("@")[-1] for t in tareas})
parar("EVIDENCIA INCOMPLETA O CON REINTENTOS: no se calcula DME.", problemas)

# 5. REQUERIDO: cada archivo, una vez por cada máquina que lo necesita y no lo tiene.
requerido = 0
for archivo, bytes_ in tamano.items():
    if archivo not in productor and archivo not in lectores:
        continue                           # no es científico (p. ej. el ejecutable)
    origen = maquina_de_tarea[productor[archivo]] if archivo in productor else COORDINADOR
    destinos = {maquina_de_tarea[t] for t in lectores.get(archivo, [])}
    if archivo in productor and destinos - {origen}:
        destinos.add(COORDINADOR)          # CondorIO: todo pasa por el coordinador
    if archivo in finales:
        destinos.add(COORDINADOR)          # los resultados finales vuelven al coordinador
    destinos.discard(origen)               # donde ya está, no hace falta enviarlo
    requerido += bytes_ * len(destinos)
    if "-v" in sys.argv:
        print(f"  {archivo}: {origen} -> {sorted(destinos)}")

# 6. CONTRATO: los archivos científicos que cada job debía recibir y devolver, según su .sub,
#    comprobado contra lo que HTCondor registró. El ejecutable y los scripts de Pegasus no son científicos.
cientificos = set(productor) | set(lectores)
contrato, problemas = 0, []
for job in tareas_del_job:
    sub = open(RUTA[job + ".sub"]).read()
    for sentido, extra in (("Input", 1), ("Output", 2)):    # HTCondor suma además: el ejecutable / stdout y stderr
        lista = campo(sub, f"transfer_{sentido.lower()}_files") or ""
        archivos = {os.path.basename(n.strip()) for n in lista.split(",") if n.strip()}   # sin repetidos (jobs agrupados)
        cientif = sum(tamano[n] for n in archivos & cientificos)
        contrato += cientif
        reg = re.search(rf"^Transfer{sentido}Stats = \[ CedarSizeBytesTotal = (\d+); CedarFilesCountTotal = (\d+)",
                        intentos[job][0], re.M)
        if not reg:
            problemas.append(f"{job}: HTCondor no registró la transferencia de {sentido.lower()}")
        elif int(reg[2]) != len(archivos) + extra or int(reg[1]) < cientif:
            problemas.append(f"{job} ({sentido.lower()}): HTCondor registró {reg[2]} archivos y {reg[1]} B; "
                             f"el contrato pide {len(archivos) + extra} archivos y al menos {cientif} B")
parar("TRANSFERENCIAS QUE NO CUADRAN CON EL CONTRATO: no se calcula DME.", problemas)

print(f"Requerido:           {requerido} B")
print(f"Contrato (.sub):     {contrato} B   (corroborado: un intento por job y mismo número de archivos)")
print(f"DME con el contrato: {requerido / contrato:.6f}")
