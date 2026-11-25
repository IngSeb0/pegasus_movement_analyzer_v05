"""Crea un flujo listo para pegasus-plan: workflow.yml, pegasus.properties, programas y archivo inicial.

    python3 crear_flujo.py especificaciones.json DISTRIBUTION-W2 carpeta_del_flujo

Corre en el coordinador (necesita Pegasus.api y gcc). Una especificación dice qué tareas hay y
qué archivos lee y escribe cada una. Si una tarea no trae "maquina", la ubicación la decide HTCondor.
Las de Montage (montage.py) traen además: "programa" (la tarea), "entradas" (las fotos) y "maquina"
por tarea. Los "groups" con más de una tarea (W2-AGR, MG-FINAL) los junta Pegasus en un solo job.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path
from Pegasus.api import (Arch, Directory, File, FileServer, Job, Operation, OS, ReplicaCatalog,
                         Site, SiteCatalog, Transformation, TransformationCatalog, Workflow)

archivo, condicion, carpeta = sys.argv[1], sys.argv[2], Path(sys.argv[3]).resolve()
espec = json.load(open(archivo))[condicion]
aqui, base = Path(__file__).parent, Path(archivo).resolve().parent
for d in ("bin", "inputs", "scratch", "outputs"):
    (carpeta / d).mkdir(parents=True, exist_ok=True)

# 1. Programa que correrán los workers. En los patrones sintéticos también va el kernel de cómputo
#    (FMA); no es un dato del flujo, así que no se declara como entrada: ejecutar_flujo.py lo añade a los .sub.
shutil.copy(base / espec["programa"] if "programa" in espec else aqui / "tarea.py", carpeta / "bin" / "tarea.py")
if "programa" not in espec:
    subprocess.run(["gcc", "-O2", "-mfma", "-static", str(aqui / "fma_kernel.c"),
                    "-o", str(carpeta / "bin" / "fma_kernel"), "-lm"], check=True)

# 2. Archivos iniciales: los de Montage ya existen (las fotos); los sintéticos se generan aquí,
#    en el coordinador, con su tamaño exacto.
tamano = {f["file_id"]: f["size_bytes"] for f in espec["files"]}
bloque = os.urandom(1 << 20)
for nombre in espec["dag"]["external_inputs"]:
    if "entradas" in espec:
        shutil.copy(base / espec["entradas"] / nombre, carpeta / "inputs" / nombre)
        continue
    restante = tamano[nombre]
    with open(carpeta / "inputs" / nombre, "wb") as f:
        while restante:
            f.write(bloque[:restante])
            restante -= min(restante, len(bloque))

# 3. Dónde viven las cosas: "local" es el coordinador; "condorpool" son los workers.
local = Site("local", arch=Arch.X86_64, os_type=OS.LINUX).add_directories(
    Directory(Directory.SHARED_SCRATCH, carpeta / "scratch", shared_file_system=False)
        .add_file_servers(FileServer((carpeta / "scratch").as_uri(), Operation.ALL)),
    Directory(Directory.LOCAL_STORAGE, carpeta / "outputs", shared_file_system=False)
        .add_file_servers(FileServer((carpeta / "outputs").as_uri(), Operation.ALL)))
workers = (Site("condorpool", arch=Arch.X86_64, os_type=OS.LINUX)
           .add_pegasus_profile(style="condor", auxillary_local=True)
           .add_condor_profile(universe="vanilla", request_cpus="1", request_memory="256"))

archivos = {n: File(n) for n in tamano}
replicas = ReplicaCatalog()
for nombre in espec["dag"]["external_inputs"]:
    replicas.add_replica("local", archivos[nombre], carpeta / "inputs" / nombre)
# "campaign_task" es el nombre que el Analyzer espera en los jobs.
programa = Transformation("campaign_task", site="local", pfn=carpeta / "bin" / "tarea.py",
                          is_stageable=True, arch=Arch.X86_64, os_type=OS.LINUX)

# 4. Un job por tarea, con sus archivos de entrada y salida.
flujo = Workflow(f"flujo-{condicion.lower()}", infer_dependencies=False)
flujo.add_site_catalog(SiteCatalog().add_sites(local, workers))
flujo.add_replica_catalog(replicas)
grupos = [g for g in espec.get("groups", []) if len(g) > 1]
catalogo = TransformationCatalog().add_transformations(programa)
if grupos:           # pegasus-cluster es el programa que ejecuta en un solo job las tareas de un grupo
    catalogo.add_transformations(Transformation("seqexec", namespace="pegasus", site="condorpool",
                                                pfn="/usr/bin/pegasus-cluster", is_stageable=False,
                                                arch=Arch.X86_64, os_type=OS.LINUX))
flujo.add_transformation_catalog(catalogo)
jobs = {}
for t in espec["dag"]["tasks"]:
    job = Job(programa, _id=t["task_id"])
    job.add_args("--task-id", t["task_id"], *(["--flops", str(t["flops"])] if "flops" in t else []))
    for n in t["input_files"]:
        job.add_args("--input", archivos[n], str(tamano[n]))
        job.add_inputs(archivos[n])
    for n in t["output_files"]:
        job.add_args("--output", archivos[n], str(tamano[n]))
        job.add_outputs(archivos[n], stage_out=n in espec["dag"]["final_outputs"], register_replica=False)
    job.add_condor_profile(requirements=f'TARGET.Machine == "{t["maquina"]}"' if "maquina" in t
                           else "TARGET.DMEStudyEligible == true", request_cpus="1", request_memory="256")
    flujo.add_jobs(job)
    jobs[t["task_id"]] = job
for e in {(e["producer_task"], e["consumer_task"]) for e in espec["dag"]["edges"]}:
    flujo.add_dependency(jobs[e[0]], children=[jobs[e[1]]])     # el hijo espera al padre
# Grupos: las tareas de un grupo llevan la misma etiqueta y Pegasus las junta en un job (pegasus-cluster).
for i, grupo in enumerate(grupos, 1):
    for tarea in grupo:
        jobs[tarea].add_pegasus_profiles(label=f"group_{i}")
flujo.write(str(carpeta / "workflow.yml"))

# 5. Configuración de Pegasus: CondorIO (los archivos viajan con HTCondor, pasando por el
#    coordinador), un site elegido por turnos y ningún reintento.
(carpeta / "pegasus.properties").write_text(
    "pegasus.data.configuration=condorio\npegasus.selector.site=RoundRobin\ndagman.retry=0\n")
print("Flujo creado en", carpeta)
