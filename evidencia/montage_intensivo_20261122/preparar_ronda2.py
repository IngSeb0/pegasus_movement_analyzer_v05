from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import tarfile


root = Path(__file__).resolve().parent
first = root / "RESULTADOS"
out = root / "ronda2_50mbit"
out.mkdir(exist_ok=True)
pilot = json.loads((first / "PILOTO.json").read_text())
assert pilot["transferencia_s"] == 289 and pilot["otros_tramos_s"]["tramo_ejecucion_s"] == 394
assert pilot["intensivo_en_datos"] is False
assert sha256((root / "HIPOTESIS.md").read_bytes()).hexdigest() == (root / "HIPOTESIS.sha256").read_text().split()[0]
for name, digest in json.loads((first / "DISENO_CONGELADO.json").read_text()).items():
    assert sha256((first / name).read_bytes()).hexdigest() == digest, name

name = "ANEXO_RONDA2_50MBIT_20261122"
document = """# Enmienda posterior al piloto · 22 de noviembre de 2026

En el piloto a 100 Mbit/s, la transferencia ocupó 289 s y la ejecución 394 s. El protocolo original ordenaba detener la matriz si la transferencia no era el tramo mayor y no cambiar la red para forzar el criterio. La matriz se detuvo.

Luis, autor de la tesis, decidió repetir el piloto con un límite de 50 Mbit/s tras conocer ese resultado. El cambio se limita al ancho de banda. Se mantienen el mosaico, las 147 imágenes, el grafo, las ubicaciones, las variantes, el criterio de parada y las hipótesis M1–M5.

El régimen intensivo en datos de Montage se logra reduciendo el ancho de banda tras ver un primer piloto que no lo cumplía; los resultados de esta ronda son condicionales a ese régimen. El segundo piloto determinará si este régimen satisface el criterio.
"""
for folder in (out, first):
    path = folder / (name + ".md")
    if path.exists():
        assert path.read_text(encoding="utf-8") == document
    else:
        path.write_text(document, encoding="utf-8")
    path.with_suffix(".sha256").write_text(f"{sha256(path.read_bytes()).hexdigest()}  {path.name}\n")

prediction = json.loads((first / "PREDICCIONES.json").read_text())
prediction["tiempo"] = {"bandwidth_nominal_mbit_s": 50, "entrada_estimada_mbit_s": 47,
                        "delta_observado_s_estimado": prediction["delta_observed_bytes"] / (47e6 / 8),
                        "base_transferencia_estimada_s": 578, "base_ejecucion_estimada_s": 394}
(out / "PREDICCIONES.json").write_text(json.dumps(prediction, indent=2))

elapsed = 0.0
for directory in sorted(root.glob("sesion*")):
    if not (directory / "inicio_utc.txt").exists():
        continue
    start, stop = (datetime.fromisoformat((directory / f"{label}_utc.txt").read_text().strip()[:26])
                   for label in ("inicio", "cierre"))
    elapsed += (stop - start).total_seconds()
budget = int(18000 - elapsed)
assert budget > 4800
control = (root / "control_medicion.ps1").read_text()
control = control.replace("'sesion07'", "'ronda2_50mbit/sesion08'").replace("-s07-ssh", "-s08-ssh")
control = re.sub(r"AddSeconds\(\d+\)", f"AddSeconds({budget})", control)
control = re.sub(r"RuntimeMaxSec=\d+", f"RuntimeMaxSec={budget}", control)
(root / "control_ronda2.ps1").write_text(control)

supervisor = (root / "supervisar_sia.py").read_text()
supervisor = supervisor.replace('results = root / "RESULTADOS"', 'results = root / "ronda2_50mbit"\nfirst = root / "RESULTADOS"')
supervisor = supervisor.replace('session = root / "sesion07"', 'session = results / "sesion08"')
supervisor = supervisor.replace("/20261122/medicion", "/20261122/ronda2")
supervisor = supervisor.replace("20261122/medicion", "20261122/ronda2")
supervisor = supervisor.replace('results / "SPECS.json"', 'first / "SPECS.json"')
supervisor = supervisor.replace('results / "DISENO_CONGELADO.json"', 'first / "DISENO_CONGELADO.json"')
supervisor = supervisor.replace("scp(results / name,", "scp(first / name,")
supervisor = supervisor.replace('root / "preparacion_planes.tar.gz"', 'results / "payload.tar.gz"')
supervisor = supervisor.replace("tbf rate 100mbit", "tbf rate 50mbit").replace("montage-quitar-tc", "montage-r2-quitar-tc")
supervisor = supervisor.replace('run("montage-sia-banda", "banda", 1350)', 'run("montage-r2-banda", "banda", 1350)')
supervisor = supervisor.replace("montage-sia-medir", "montage-r2-medir").replace("control_medicion.ps1", "control_ronda2.ps1")
(root / "supervisar_ronda2.py").write_text(supervisor)

measurement = (root / "medir_sia.py").read_text()
measurement = measurement.replace(
    "    for block in range(1, 4):",
    """    from datetime import datetime, timezone
    deadline = datetime.fromisoformat(runner.session()["stopSubmissionsUtc"])
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
    expected = max(1080, runner.read(summary_path)["duracion_dagman_s"])
    blocks = 3 if remaining >= 6 * expected else 2
    if remaining < 4 * expected:
        raise RuntimeError("No queda presupuesto para dos bloques completos")
    runner.save(root / "MATRIZ_DECISION.json", {"bloques": blocks, "presupuesto_s": remaining,
                                               "estimacion_por_corrida_s": expected})
    for block in range(1, blocks + 1):""")
measurement = measurement.replace('{"accepted_main": 6}', '{"accepted_main": 2 * blocks}')
with tarfile.open(root / "preparacion_planes.tar.gz") as source:
    with tarfile.open(out / "payload.tar.gz", "w:gz") as package:
        for item in source:
            if item.name == "medir_sia.py":
                data = measurement.encode()
                item.size = len(data)
                package.addfile(item, BytesIO(data))
            else:
                package.addfile(item, source.extractfile(item))
print(f"Enmienda sellada. Presupuesto restante: {budget} s.")
