from collections import defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path
from statistics import mean, stdev


results = Path(__file__).resolve().parent / "RESULTADOS"
native = results / "evidencia_nativa"
for name in ("PILOTO.json", "ANCHO_DE_BANDA.json", "COMPLETE.json", "LEDGER.json"):
    source = native / name
    if source.exists():
        (results / name).write_bytes(source.read_bytes())


def rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write(name, records):
    if records:
        with (results / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)


jobs, runs, volumes, files = [], [], [], []
for receipt in sorted(native.rglob("ACCEPTANCE.json")):
    record = json.loads(receipt.read_text())
    required, observed = record["required_bytes"], record["observed_bytes"]
    volumes.append({
        "corrida": record["id"], "condicion": record["condition"], "fase": record["phase"],
        "requerido_B": required, "observado_B": observed, "exceso_B": observed - required,
        "DME": record["dme"],
    })
    for final in record["final_files"]:
        files.append({
            "corrida": record["id"], "condicion": record["condition"],
            "fase": record["phase"], "archivo": final["file"], "bytes": final["bytes"],
            "sha256": final["sha256"],
        })
    if (receipt.parent / "corridas.csv").exists():
        runs.extend(dict(fase=record["phase"], bloque=record["block"], **row)
                    for row in rows(receipt.parent / "corridas.csv"))
        jobs.extend(rows(receipt.parent / "jobs.csv"))
write("jobs", jobs)
write("corridas", runs)
write("BYTES", volumes)
write("FITS_IGUALES", files)

main = defaultdict(list)
blocks = defaultdict(dict)
for run in runs:
    if run["fase"] == "main":
        main[run["condicion"]].append(run)
        blocks[run["bloque"]][run["condicion"]] = run
if runs:
    measures = ["duracion_dagman_s", *(key for key in runs[0] if key.startswith("tramo_"))]
    fit_counts = defaultdict(set)
    for row in files:
        if row["fase"] == "main":
            fit_counts[row["archivo"]].add((row["bytes"], row["sha256"]))
    summary = []
    for condition, observations in sorted(main.items()):
        for key in measures:
            values = [float(record[key]) for record in observations]
            summary.append({
                "condicion": condition, "medida": key, "n": len(values), "promedio_s": mean(values),
                "desviacion_s": stdev(values) if len(values) > 1 else "",
            })
    write("resumen", summary)
    write("diferencias_por_bloque", [
        {"bloque": block, "medida": key,
         "base_menos_final_s": float(values["MG-BASE"][key]) - float(values["MG-FINAL"][key])}
        for block, values in sorted(blocks.items()) if {"MG-BASE", "MG-FINAL"} <= values.keys()
        for key in measures
    ])
    if fit_counts:
        (results / "EQUIVALENCIA_FITS.json").write_text(json.dumps(
            {name: {"coinciden": len(signatures) == 1, "firmas": sorted(signatures)}
             for name, signatures in fit_counts.items()}, indent=2
        ))

windows = []
for folder in sorted(results.parent.glob("sesion*")):
    if not (folder / "cierre_utc.txt").exists():
        continue
    start, stop = (datetime.fromisoformat((folder / f"{label}_utc.txt").read_text().strip()[:26])
                   for label in ("inicio", "cierre"))
    states = json.loads((folder / "estado_final.json").read_text(encoding="utf-8-sig"))
    assert len(states) == 5 and all(vm["state"] == "VM deallocated" for vm in states)
    windows.append((folder.name, (stop - start).total_seconds()))
total = sum(elapsed for _, elapsed in windows)
tc = "Las verificaciones de tc están en TC.txt." if (results / "TC.txt").exists() else "No se aplicó tc."
if (results / "TC_ERRORES.json").exists():
    tc = "TC_ERRORES.json registra las comprobaciones de restauración pendientes."
listed = "".join(f"- {folder}, {elapsed:.3f} s\n" for folder, elapsed in windows)
(results / "VMS.md").write_text(
    f"# Cierre de Azure\n\n{listed}\n"
    f"Ventana acumulada de las sesiones cerradas {total:.3f} s de 18 000 s. "
    f"Todas las sesiones listadas cerraron con las cinco VMs desasignadas. {tc}\n",
    encoding="utf-8",
)
