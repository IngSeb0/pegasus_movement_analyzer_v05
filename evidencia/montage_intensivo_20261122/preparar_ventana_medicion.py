from datetime import datetime
from pathlib import Path
import re


root = Path(__file__).resolve().parent
windows = []
for folder in sorted(root.glob("sesion*")):
    if not (folder / "inicio_utc.txt").exists():
        continue
    if not (folder / "cierre_utc.txt").exists():
        raise RuntimeError(f"Sesión anterior aún abierta: {folder.name}")
    start, stop = (datetime.fromisoformat((folder / f"{name}_utc.txt").read_text().strip()[:26])
                   for name in ("inicio", "cierre"))
    windows.append((stop - start).total_seconds())
budget = int(18000 - sum(windows))
if budget < 4800:
    raise RuntimeError("El presupuesto restante no permite piloto y cierre")
if not (root / "RESULTADOS" / "DISENO_CONGELADO.json").is_file():
    raise RuntimeError("Falta el cotejo de los planes")
script = (root / "control_planes2.ps1").read_text().replace("sesion06", "sesion07").replace("-s06-ssh", "-s07-ssh")
script = script.replace("foreach ($name in @('dme-master'))", 
                        "foreach ($name in @('dme-master','dme-worker1','dme-worker2','dme-worker3','dme-worker4'))")
script = script.replace(
    "@($state | Where-Object { $_.name -eq 'dme-master' -and $_.state -eq 'VM running' }).Count -eq 1",
    "@($state | Where-Object state -eq 'VM running').Count -eq 5",
)
script = re.sub(r"AddSeconds\(\d+\)", f"AddSeconds({budget})", script)
script = re.sub(r"RuntimeMaxSec=\d+", f"RuntimeMaxSec={budget}", script)
(root / "control_medicion.ps1").write_text(script)
print(f"Tiempo restante: {budget} s de Azure", flush=True)
