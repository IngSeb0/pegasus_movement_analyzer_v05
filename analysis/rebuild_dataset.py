"""Rebuild the normalized 113-workflow table from bundled processed inputs."""
from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source"
OUTPUT = ROOT / "data" / "derived"
MIB = 1024 * 1024
FIELDS = [
    "block", "case", "condition", "replica", "uuid", "required_bytes",
    "observed_bytes", "dme_exact", "dag_duration_s", "source_file",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def exact_bytes(mib: str | int | float) -> int:
    value = Decimal(str(mib)) * MIB
    if value != value.to_integral_value():
        raise ValueError(f"MiB value does not resolve to whole bytes: {mib}")
    return int(value)


def validate_ratio(row: dict) -> None:
    expected = Fraction(row["required_bytes"], row["observed_bytes"])
    if expected != Fraction(row["dme_exact"]):
        raise ValueError(f"DME mismatch in {row['case']}: {row['dme_exact']} != {expected}")


def main() -> None:
    eligible_index = read_json(SOURCE / "A" / "INDICE_EVIDENCIA_TESIS.json")
    eligible = {item["uuid"] for item in eligible_index["capsules"] if item["eligible"]}
    if len(eligible) != 72:
        raise ValueError(f"Expected 72 eligible main runs, found {len(eligible)}")

    rows: list[dict] = []
    with (SOURCE / "A" / "TIEMPOS_INDIVIDUALES.csv").open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            if item["uuid"] not in eligible:
                continue
            row = {
                "block": "A",
                "case": f"{item['condition']}-r{int(item['replica']):02d}",
                "condition": item["condition"],
                "replica": int(item["replica"]),
                "uuid": item["uuid"],
                "required_bytes": exact_bytes(item["required_mib"]),
                "observed_bytes": exact_bytes(item["observed_mib"]),
                "dme_exact": item["dme_exact"],
                "dag_duration_s": float(item["dag_duration_s"]),
                "source_file": "A/TIEMPOS_INDIVIDUALES.csv",
            }
            validate_ratio(row)
            rows.append(row)

    with (SOURCE / "BD" / "COMPLEMENTARIOS_INDIVIDUALES.csv").open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            row = {
                "block": item["block"],
                "case": item["study_case"],
                "condition": item["condition"],
                "replica": int(item["replica"]),
                "uuid": item["uuid"],
                "required_bytes": int(item["required_bytes"]),
                "observed_bytes": int(item["observed_bytes"]),
                "dme_exact": item["dme_exact"],
                "dag_duration_s": float(item["dag_duration_s"]),
                "source_file": "BD/COMPLEMENTARIOS_INDIVIDUALES.csv",
            }
            validate_ratio(row)
            rows.append(row)

    intensity = read_json(SOURCE / "E" / "RESULTADOS_INTENSIDAD.json")
    for item in intensity["runs"]:
        row = {
            "block": "E",
            "case": item["study_case"],
            "condition": item["condition"],
            "replica": int(item["replica"]),
            "uuid": "",
            "required_bytes": exact_bytes(item["required_mib"]),
            "observed_bytes": exact_bytes(item["observed_mib"]),
            "dme_exact": item["dme"],
            "dag_duration_s": float(item["dag_duration_s"]),
            "source_file": "E/RESULTADOS_INTENSIDAD.json",
        }
        validate_ratio(row)
        rows.append(row)

    for item in read_json(SOURCE / "FH" / "ACCEPTED_RESULTS_SESSION_FINAL_18.json"):
        row = {
            "block": item["block"],
            "case": item["study_case"],
            "condition": item["condition"],
            "replica": int(item["pair"]),
            "uuid": item["uuid"],
            "required_bytes": int(item["required_bytes"]),
            "observed_bytes": int(item["observed_bytes"]),
            "dme_exact": item["dme_exact"],
            "dag_duration_s": float(item["dag_duration_s"]),
            "source_file": "FH/ACCEPTED_RESULTS_SESSION_FINAL_18.json",
        }
        validate_ratio(row)
        rows.append(row)

    expected_counts = {
        "A": 72, "temporal": 9, "operational_cost": 6,
        "free_placement": 3, "E": 5, "COST_SCALE": 12,
        "REAL_APPLICATION": 4, "RECEIVER_OBSERVATION": 2,
    }
    counts = Counter(row["block"] for row in rows)
    if dict(counts) != expected_counts:
        raise ValueError(f"Unexpected cohort counts: {dict(counts)}")
    if len(rows) != 113:
        raise ValueError(f"Expected 113 workflows, found {len(rows)}")
    run_ids = [(row["block"], row["case"]) for row in rows]
    if len(run_ids) != len(set(run_ids)):
        raise ValueError("Duplicate block/case identifiers")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "workflows_113.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["block"], row["case"])))
    summary = {
        "unique_workflows": len(rows),
        "main_conditions": len({row["condition"] for row in rows if row["block"] == "A"}),
        "eligible_main_workflows": counts["A"],
        "workflows_by_block": dict(sorted(counts.items())),
        "notes": [
            "The 72 main rows are selected by eligible UUID from the preserved campaign index.",
            "The 113 rows comprise A-H; 21 local Analyzer profile invocations are not workflows.",
            "Durations are preserved measurements and may vary on other hardware; byte totals and DME are deterministic for these inputs.",
        ],
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} unique workflow rows to {OUTPUT.relative_to(ROOT)}")
    print(json.dumps(summary["workflows_by_block"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
