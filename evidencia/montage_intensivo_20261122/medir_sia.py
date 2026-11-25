from pathlib import Path
import csv
import json
import sys


root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "runtime"))
import run_study as runner
import tabla_tiempos
from medir_banda import bandwidth


def register_times(case, evidence, row):
    audit = runner.read(evidence / "INDEPENDENT_AUDIT.json")
    assert all(item["exact"] and item["residual"] == 0 for item in audit["directions"])
    jobs, summary = tabla_tiempos.analyze(row["id"], row["condition"], str(case.parent.parent))
    scientific = [job for job in jobs if job["tipo"] == "tarea"]
    if not scientific or any(
        job[key] is None for job in scientific
        for key in ("transferencia_entrada_s", "transferencia_salida_s", "ejecucion_s")
    ):
        raise ValueError(f"Intervalos de jobs científicos incompletos en {row['id']}")
    archive = evidence / "TIEMPOS.json"
    archive.write_text(json.dumps(summary, indent=2))
    for name, records in (("jobs", jobs), ("corridas", [summary])):
        with (evidence / f"{name}.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)


def execute():
    for name, digest in runner.read(root / "DISENO_CONGELADO.json").items():
        assert runner.sha(root / name) == digest, name
    runner.archive = register_times
    conditions = ("MG-BASE", "MG-FINAL")
    pilot = {"id": "MG-BASE-PILOTO", "condition": conditions[0], "block": 0, "phase": "pilot"}
    runner.execute(pilot)
    summary_path = root / "cases" / pilot["id"] / "pilot" / pilot["condition"] / "TIEMPOS.json"
    tramos = {key: value for key, value in runner.read(summary_path).items() if key.startswith("tramo_")}
    transfer = tramos.pop("tramo_transferencia_s")
    admissible = transfer > max(tramos.values())
    runner.save(root / "PILOTO.json", {
        "transferencia_s": transfer, "otros_tramos_s": tramos, "intensivo_en_datos": admissible,
    })
    if not admissible:
        print("El tramo de transferencia del piloto no fue el mayor. Matriz detenida.", flush=True)
        return
    for block in range(1, 4):
        for condition in (conditions if block % 2 else conditions[::-1]):
            row = {"id": f"{condition}-B{block:02}", "condition": condition, "block": block, "phase": "main"}
            runner.execute(row)
    runner.save(root / "COMPLETE.json", {"accepted_main": 6})


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "banda":
        for direction in ("entrada", "salida"):
            bandwidth(direction)
        runner.save(root / "ANCHO_DE_BANDA.json", {
            direction: runner.read(root / f"banda-{direction}" / "BANDA.json")
            for direction in ("entrada", "salida")
        })
    else:
        execute()
