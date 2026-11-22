"""Recalculate the ten free-placement cases from compact extracted evidence.

This checks processed data, not the original administrative capsules.
"""
import csv
from fractions import Fraction
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/validation_free_20261107"


def main():
    rows = list(csv.DictReader((DATA / "RESULTADOS_VALIDACION_LIBRE.csv").open(encoding="utf-8-sig")))
    native = json.loads((DATA / "DESGLOSE_NATIVO.json").read_text(encoding="utf-8-sig"))
    by_case = {item["case"]: item for item in native}
    assert len(rows) == len(by_case) == 10
    assert len({row["uuid"] for row in rows}) == 10
    for row in rows:
        item = by_case[row["case"]]
        required = (2 + (row["T1_worker"] != row["T2_worker"]) +
                    (row["T2_worker"] != row["T3_worker"])) * 10 * 2**20
        observed = sum(delivery["bytes"] for delivery in item["deliveries"])
        assert required == sum(f["required_bytes"] for f in item["files"].values())
        assert required == int(row["required_mib"]) * 2**20
        assert observed == int(row["observed_mib"]) * 2**20
        assert Fraction(required, observed) == Fraction(row["dme_exact"])
        assert all(d["exact"] and d["residual"] == 0 for d in item["directions"])
    comparisons = [r for r in rows if r["phase"] == "COMPARISON"]
    assert len(comparisons) == 9
    summary = {}
    for condition in ("L01", "GL2", "GL3"):
        group = [r for r in comparisons if r["condition"] == condition]
        assert len(group) == 3
        summary[condition] = {"n": 3, "median_duration_s": median(float(r["duration_s"]) for r in group),
                              "observed_mib": [int(r["observed_mib"]) for r in group]}
    print(json.dumps({"cases": len(rows), "comparisons": 9, "pilot": 1,
                      "directions": sum(len(i["directions"]) for i in native),
                      "summary": summary, "scope": "compact processed evidence; not raw capsule audit"}, indent=2))


if __name__ == "__main__":
    main()
