"""Ejecuta un flujo creado con crear_flujo.py y guarda la evidencia para el Analyzer.

    python3 ejecutar_flujo.py carpeta_del_flujo

Corre en el coordinador (donde están Pegasus y HTCondor). Al terminar deja en la carpeta
history.long y submit/.../run0001, que es lo que lee analyzer/analyzer.py.
"""
import re, subprocess, sys, time
from pathlib import Path
import yaml

carpeta = Path(sys.argv[1]).resolve()


def correr(*comando):
    r = subprocess.run([str(c) for c in comando], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FALLÓ {comando[0]}:\n{r.stderr[-1500:]}")
    return r.stdout


# 1. PLAN: Pegasus convierte workflow.yml en archivos que HTCondor entiende
#    (un .dag con el orden y un .sub por job). Todavía no se ejecuta nada.
agrupa = ["--cluster", "label"] if "label: group_" in (carpeta / "workflow.yml").read_text() else []
correr("pegasus-plan", "--conf", carpeta / "pegasus.properties", "--dir", carpeta / "submit",
       "--sites", "condorpool", "--output-sites", "local", "--cleanup", "none", *agrupa,
       "--json", carpeta / "workflow.yml")
run = next((carpeta / "submit").rglob("braindump.yml")).parent          # .../run0001
uuid = yaml.safe_load((run / "braindump.yml").read_text())["root_wf_uuid"]

# 2. KERNEL (solo en los flujos sintéticos): el programa de cómputo no es un dato del flujo, así que
#    se añade directamente a la lista de archivos que HTCondor envía en cada job (transfer_input_files).
kernel = carpeta / "bin" / "fma_kernel"
for sub in run.rglob("*.sub") if kernel.exists() else []:
    texto = sub.read_text()
    if "+pegasus_job_class = 1" in texto:                                  # solo jobs de tareas
        sub.write_text(re.sub(r"(?m)^(transfer_input_files\s*=.*)$", rf"\1,{kernel}", texto))

# 3. RUN: entrega el .dag a DAGMan, que envía cada job a HTCondor en orden.
#    Responde al instante; el flujo sigue corriendo solo.
correr("pegasus-run", run)

# 4. ESPERAR: DAGMan escribe "EXITING WITH STATUS n" en su log cuando termina.
for _ in range(1350):                                                      # hasta 45 min
    logs = " ".join(p.read_text(errors="replace") for p in run.glob("*.dag.dagman.out"))
    salida = re.findall(r"EXITING WITH STATUS\s+(\d+)", logs)
    if salida:
        break
    time.sleep(2)
else:
    sys.exit("El flujo no terminó en 45 minutos")
if salida[-1] != "0":
    sys.exit(f"El flujo terminó con error (ver el .dagman.out en {run})")

# 5. HISTORIAL: HTCondor guarda en qué máquina corrió cada job y cuántos bytes movió.
(carpeta / "history.long").write_text(
    correr("condor_history", "-long", "-constraint", f'pegasus_root_wf_uuid == "{uuid}"'))

print(f"Listo. Para calcular DME:\n  python3 analyzer.py {run} {carpeta / 'history.long'}")
