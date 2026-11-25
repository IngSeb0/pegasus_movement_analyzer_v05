"""Recomendador de agrupaciones: qué jobs juntar para evitar el exceso que mide DME.

Uso:  python recomendar.py CARPETA_run0001 history.long [--ancho MB_POR_S]

Lee lo mismo que analyzer.py (plan de Pegasus e historial de HTCondor). Para cada máquina busca
jobs que reciben el mismo archivo o que se pasan un archivo entre sí, y los junta de a dos mientras
el ahorro sea positivo y la unión no cree un ciclo entre jobs. El ahorro de cada unión se calcula
como Pegasus arma un job agrupado: recibe la unión de las entradas menos lo que produce el grupo,
y devuelve todas las salidas que el plan declara. Supone que cada tarea sigue en la máquina donde
corrió y que cada máquina ejecuta un job a la vez; con esa ubicación, agrupar no quita paralelismo.
Con --ancho (MB/s medidos) da además un orden de magnitud del ahorro de transferencia.
"""
import glob, json, os, re, sys
import yaml

run, history = sys.argv[1], sys.argv[2]
ancho = float(sys.argv[sys.argv.index("--ancho") + 1]) if "--ancho" in sys.argv else None
RUTA = {os.path.basename(f): f for f in glob.glob(os.path.join(run, "00", "*", "*"))}
campo = lambda b, n: (m.group(1).strip('"') if (m := re.search(rf"^{n} = (.*)$", b, re.M)) else None)

tamano = {}
for meta in [f for n, f in RUTA.items() if n.endswith(".meta")]:
    for a in json.load(open(meta)):
        tamano[a["_id"]] = int(a["_attributes"]["size"])
cientificos = set()
for tarea in yaml.safe_load(open(os.path.join(run, "workflow.yml")))["jobs"]:
    cientificos |= {u["lfn"] for u in tarea["uses"]}

tareas_del_job = {}
for sub in [f for n, f in RUTA.items() if n.endswith(".sub")]:
    job = os.path.basename(sub)[:-4]
    if job.startswith("campaign_task_"):
        tareas_del_job[job] = [job[len("campaign_task_"):]]
    elif job.startswith("merge_"):
        tareas_del_job[job] = re.findall(r"^#@ \d+ \S+ (\S+)", open(sub[:-4] + ".in").read(), re.M)

maquina = {}
for bloque in open(history).read().split("\n\n"):
    nodo, host = campo(bloque, "DAGNodeName"), campo(bloque, "LastRemoteHost")
    if nodo in tareas_del_job and host:
        maquina[nodo] = host.split("@")[-1]
falta = set(tareas_del_job) - set(maquina)
if falta:
    sys.exit(f"El historial no dice dónde corrieron: {sorted(falta)}")

def lista(job, sentido):
    texto = campo(open(RUTA[job + ".sub"]).read(), f"transfer_{sentido}_files") or ""
    return {os.path.basename(n.strip()) for n in texto.split(",") if n.strip()} & cientificos
entra = {j: lista(j, "input") for j in tareas_del_job}
sale = {j: lista(j, "output") for j in tareas_del_job}

grupos = {j: {j} for j in tareas_del_job}            # nombre del grupo -> jobs
cache = {}
def contrato(n):                                      # entradas y salidas del grupo n, como un job agrupado
    if n not in cache:
        e = set().union(*(entra[j] for j in grupos[n])); s = set().union(*(sale[j] for j in grupos[n]))
        cache[n] = (e - s, s)
    return cache[n]
def bytes_contrato(e, s):
    return sum(tamano[f] for f in e) + sum(tamano[f] for f in s)
def ahorro_union(a, b):
    (ea, sa), (eb, sb) = contrato(a), contrato(b)
    s = sa | sb; e = (ea | eb) - s
    return bytes_contrato(ea, sa) + bytes_contrato(eb, sb) - bytes_contrato(e, s)
def sucesores(n):                                     # grupos que leen algo que n produce
    s = contrato(n)[1]
    return {o for o in grupos if o != n and s & contrato(o)[0]}
def crea_ciclo(a, b):                                 # ¿hay un camino a -> ... -> b que pasa por otro grupo?
    for x, y in ((a, b), (b, a)):
        pila, vistos = [o for o in sucesores(x) if o != y], set()
        while pila:
            n = pila.pop()
            if n == y:
                return True
            if n not in vistos:
                vistos.add(n); pila += [o for o in sucesores(n) if o not in (x,)]
    return False
def candidatos():                                     # pares de la misma máquina que comparten algún archivo
    por_archivo = {}
    for n in grupos:
        e, s = contrato(n)
        for f in e | s:
            por_archivo.setdefault((maquina[n], f), set()).add(n)
    pares = {(a, b) for g in por_archivo.values() for a in g for b in g if a < b}
    return sorted(((ahorro_union(a, b), a, b) for a, b in pares), reverse=True)

observado_antes = sum(bytes_contrato(*contrato(n)) for n in grupos)
pasos = []
while True:
    elegido = next(((x, a, b) for x, a, b in candidatos() if x > 0 and not crea_ciclo(a, b)), None)
    if not elegido:
        break
    ahorro, a, b = elegido
    tareas = lambda n: sorted(t for j in grupos[n] for t in tareas_del_job[j])
    pasos.append((ahorro, maquina[a], tareas(a), tareas(b)))
    grupos[a] |= grupos.pop(b); cache.pop(a, None); cache.pop(b, None)

observado_despues = sum(bytes_contrato(*contrato(n)) for n in grupos)
print(f"Observado actual:   {observado_antes} B")
corto = lambda t: ",".join(t) if len(t) <= 4 else f"{','.join(t[:3])},… ({len(t)} tareas)"
pasos.sort(key=lambda p: -p[0]); grandes = [p for p in pasos if p[0] >= 0.001 * observado_antes]          # uniones que evitan al menos el 0,1 %
for i, (ahorro, m, ta, tb) in enumerate(grandes, 1):
    print(f"  {i}. En {m}: juntar [{corto(ta)}] con [{corto(tb)}]  evita {ahorro} B")
if len(pasos) > len(grandes):
    resto = pasos[len(grandes):]
    print(f"  + {len(resto)} uniones pequeñas que evitan {sum(p[0] for p in resto)} B en total")
print(f"Observado previsto: {observado_despues} B   (evita {observado_antes - observado_despues} B, "
      f"{100 * (observado_antes - observado_despues) / observado_antes:.2f} %)")
if ancho:
    print(f"Orden de magnitud del ahorro de transferencia: {(observado_antes - observado_despues) / 1e6 / ancho:.1f} s")
print(f"Jobs: {len(tareas_del_job)} -> {len(grupos)}")
