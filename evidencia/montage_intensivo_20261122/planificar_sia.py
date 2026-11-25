from collections import Counter
from fractions import Fraction
from pathlib import Path
import sys


root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "runtime"))
import run_study as runner


def account(condition, design):
    row = dict(id=condition + "-PLAN", condition=condition, block=1, phase="plan")
    _, _, evidence, _, _, _ = runner.prepare(row)
    review = runner.read(evidence / "PLAN_REVIEW.json")
    files = {f["file_id"]: f for f in design["files"]}
    placement = {t["task_id"]: t["assigned_worker"] for t in design["dag"]["tasks"]}
    required = 0
    for file in files.values():
        producer = file["producer_task"]
        origin = placement[producer] if producer else "master"
        destinations = {placement[task] for task in file["consumer_tasks"]} - {origin}
        if file["role"] == "final" or (producer and destinations):
            destinations.add("master")
        required += file["size_bytes"] * len(destinations)

    counts = Counter(
        (name, direction, job["worker"])
        for job in review["jobs"]
        for direction in ("input", "output")
        for name in job["scientific_files"][direction]
    )
    tasks = {task["task_id"]: task for task in design["dag"]["tasks"]}
    expected_counts = Counter()
    for group in design["groups"]:
        worker = "dme-worker" + tasks[group[0]]["assigned_worker"][1:]
        assert all(tasks[task]["assigned_worker"] == tasks[group[0]]["assigned_worker"] for task in group)
        outputs = {name for task in group for name in tasks[task]["output_files"]}
        inputs = {name for task in group for name in tasks[task]["input_files"]} - outputs
        expected_counts.update((name, "input", worker) for name in inputs)
        expected_counts.update((name, "output", worker) for name in outputs)
    if counts != expected_counts:
        runner.save(root / "PLAN_DISCREPANCIA.json", {
            "condition": condition,
            "native_only": [[*key, n] for key, n in sorted((counts - expected_counts).items())],
            "design_only": [[*key, n] for key, n in sorted((expected_counts - counts).items())],
        })
        raise RuntimeError(f"El plan nativo de {condition} difiere de la cuenta prevista")
    observed = sum(files[name]["size_bytes"] * count for (name, _, _), count in counts.items())
    assert observed == review["planned_scientific_bytes"]
    return dict(required=required, observed=observed, jobs=len(review["jobs"]),
                dme=str(Fraction(required, observed)), evidence=str(evidence)), counts


if __name__ == "__main__":
    designs = runner.read(root / "SPECS.json")
    accounts = {}
    counts = {}
    for condition, design in designs.items():
        accounts[condition], counts[condition] = account(condition, design)
    baseline = accounts["MG-BASE"]
    grouped = accounts["MG-FINAL"]
    assert baseline["required"] == grouped["required"]
    assert baseline["jobs"] == grouped["jobs"] + 1
    assert not (counts["MG-FINAL"] - counts["MG-BASE"])
    removed = counts["MG-BASE"] - counts["MG-FINAL"]
    delta = baseline["observed"] - grouped["observed"]
    assert delta > 0
    runner.save(root / "PLAN_ACCOUNTS.json", accounts)
    runner.save(root / "PREDICCIONES.json", {
        "variants": accounts, "delta_observed_bytes": delta,
        "removed": [[*key, n] for key, n in sorted(removed.items())],
    })
    names = ("SPECS.json", "ENTRADAS.json", "mosaico.hdr", "REFERENCE.json",
             "PLAN_ACCOUNTS.json", "PREDICCIONES.json")
    runner.save(root / "DISENO_CONGELADO.json", {name: runner.sha(root / name) for name in names})
    print(f"Planes cotejados, ahorro previsto de {delta} bytes", flush=True)
