#!/usr/bin/env python3
"""Build a mechanical main-results table from observed RESULTS.json only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

MIB = 1 << 20
REQUIRED_EXPECTED_COUNTS = {
    "L01": 6, "GL2": 6, "GL3": 6,
    "AC1": 6, "AC2": 6, "AC4": 6,
    "D02": 6, "GD4": 6, "GL3_FINAL": 6,
    "MONTAGE_SEP": 3, "MONTAGE_GROUP": 3, "MONTAGE_GROUP_FINAL": 3,
}
SYNTHETIC = {name for name in REQUIRED_EXPECTED_COUNTS if not name.startswith("MONTAGE_")}
FAMILY_LABELS = {
    "L01": "Pipeline", "GL2": "Pipeline", "GL3": "Pipeline",
    "AC1": "Archivo compartido", "AC2": "Archivo compartido", "AC4": "Archivo compartido",
    "D02": "Particiones", "GD4": "Particiones",
    "GL3_FINAL": "Contrato de retorno",
    "MONTAGE_SEP": "Montage", "MONTAGE_GROUP": "Montage", "MONTAGE_GROUP_FINAL": "Montage",
}
BASE_COMPARISONS = [
    ("L01", "GL2"), ("L01", "GL3"),
    ("AC1", "AC2"), ("AC1", "AC4"),
    ("D02", "GD4"), ("GL3", "GL3_FINAL"),
    ("MONTAGE_SEP", "MONTAGE_GROUP"), ("MONTAGE_SEP", "MONTAGE_GROUP_FINAL"),
    ("MONTAGE_GROUP", "MONTAGE_GROUP_FINAL"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_int(value: Any, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} is not an integer")
    number = int(value)
    if number != value or number < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return number


def parse_result(row: Any, index: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return None, [f"RESULTS[{index}] is not an object"]
    parsed: dict[str, Any] = {k: row.get(k) for k in
                              ("id", "uuid", "phase", "condition", "family", "block")}
    if row.get("phase") not in ("pilot", "main"):
        errors.append("invalid phase")
    if not isinstance(row.get("condition"), str) or not row["condition"]:
        errors.append("missing condition")
    for field, minimum in (("required_bytes", 0), ("observed_bytes", 1), ("obligations", 0),
                           ("deliveries", 0), ("directions", 0)):
        try:
            parsed[field] = exact_int(row.get(field), field, minimum)
        except (ValueError, TypeError, OverflowError) as error:
            errors.append(str(error))
    try:
        dme = Fraction(str(row.get("dme")))
        if "required_bytes" in parsed and "observed_bytes" in parsed:
            actual = Fraction(parsed["required_bytes"], parsed["observed_bytes"])
            if dme != actual:
                errors.append(f"DME mismatch: observed {dme}, exact required/observed is {actual}")
        parsed["dme_exact"] = str(dme)
    except (ValueError, TypeError, ZeroDivisionError):
        errors.append("missing or invalid exact DME")
    try:
        duration = float(row.get("duration_s"))
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("duration_s is not finite and nonnegative")
        parsed["duration_s"] = duration
    except (ValueError, TypeError, OverflowError) as error:
        errors.append(str(error))
    parsed["all_exact"] = row.get("all_exact") if isinstance(row.get("all_exact"), bool) else None
    parsed["id"] = row.get("id")
    parsed["uuid"] = row.get("uuid")
    parsed["index"] = index
    parsed["errors"] = errors
    return parsed, errors


def tex_escape(text: str) -> str:
    table = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
             "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
             "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(table.get(ch, ch) for ch in text)


def fmt_values(values: set[int] | set[str], unit: bool = False) -> str:
    if not values:
        return r"\textemdash{}"
    shown = []
    for value in sorted(values, key=lambda x: Fraction(int(x), MIB) if unit else Fraction(str(x))):
        if unit:
            shown.append(str(Fraction(int(value), MIB)))
        else:
            shown.append(str(value))
    return ", ".join(tex_escape(x) for x in shown)


def load_expected(matrix_path: Path) -> tuple[dict[str, int], int, list[str]]:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        raise ValueError("MATRIX.json must contain rows[]")
    main = [row for row in rows if isinstance(row, dict) and row.get("phase") == "main"]
    counts = Counter(row.get("condition") for row in main)
    actual = {condition: counts.get(condition, 0) for condition in REQUIRED_EXPECTED_COUNTS}
    extra = sorted(str(k) for k, n in counts.items() if k not in REQUIRED_EXPECTED_COUNTS and n)
    issues = []
    if len(main) != 63:
        issues.append(f"matrix main row count is {len(main)}, expected design count 63")
    if actual != REQUIRED_EXPECTED_COUNTS:
        issues.append("matrix per-condition counts do not match six synthetic and three Montage repetitions")
    if extra:
        issues.append("matrix has unexpected main conditions: " + ", ".join(extra))
    return actual, len(main), issues


def summarize(results_path: Path, matrix_path: Path) -> dict[str, Any]:
    raw = json.loads(results_path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError("RESULTS.json must be a JSON array")
    expected, matrix_main_count, completeness_issues = load_expected(matrix_path)
    parsed, row_issues = [], []
    for index, row in enumerate(raw):
        clean, errors = parse_result(row, index)
        if clean is None:
            row_issues.append({"index": index, "errors": errors})
            continue
        parsed.append(clean)
        if errors:
            row_issues.append({"index": index, "id": clean.get("id"), "uuid": clean.get("uuid"), "errors": errors})
    all_ids = [r["id"] for r in parsed if isinstance(r.get("id"), str) and r["id"]]
    all_uuids = [r["uuid"] for r in parsed if isinstance(r.get("uuid"), str) and r["uuid"]]
    dup_ids = sorted(x for x, n in Counter(all_ids).items() if n > 1)
    dup_uuids = sorted(x for x, n in Counter(all_uuids).items() if n > 1)
    if dup_ids:
        completeness_issues.append("duplicate result ids")
    if dup_uuids:
        completeness_issues.append("duplicate UUIDs")

    pilots = [r for r in parsed if r.get("phase") == "pilot"]
    main_raw = [r for r in parsed if r.get("phase") == "main"]
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in main_raw:
        condition = r.get("condition")
        if condition in REQUIRED_EXPECTED_COUNTS:
            by_condition[condition].append(r)
        else:
            completeness_issues.append(f"unexpected main condition: {condition}")

    conditions = []
    for condition in REQUIRED_EXPECTED_COUNTS:
        records = by_condition.get(condition, [])
        valid = [r for r in records if not r["errors"]]
        observed_count = len(valid)
        expected_count = expected.get(condition, 0)
        if observed_count != expected_count:
            completeness_issues.append(f"{condition}: {observed_count} valid main records, expected {expected_count} from matrix")
        required_values = {r["required_bytes"] for r in valid if "required_bytes" in r}
        observed_values = {r["observed_bytes"] for r in valid if "observed_bytes" in r}
        dme_values = {r["dme_exact"] for r in valid if "dme_exact" in r}
        conditions.append({
            "condition": condition,
            "family_label": FAMILY_LABELS[condition],
            "n_real": observed_count,
            "n_records_in_results": len(records),
            "n_expected_from_matrix": expected_count,
            "required_bytes_values": sorted(required_values),
            "observed_bytes_values": sorted(observed_values),
            "dme_exact_values": sorted(dme_values, key=Fraction),
            "deliveries_total": sum(r["deliveries"] for r in valid if "deliveries" in r),
            "obligations_total": sum(r["obligations"] for r in valid if "obligations" in r),
            "directions_total": sum(r["directions"] for r in valid if "directions" in r),
            "duration_s_values": [r["duration_s"] for r in valid if "duration_s" in r],
            "all_exact_counts": dict(Counter("true" if r["all_exact"] is True else "false" if r["all_exact"] is False else "unknown" for r in valid)),
            "ids": [r["id"] for r in valid],
            "uuids": [r["uuid"] for r in valid],
        })
    valid_main = [r for r in main_raw if r.get("condition") in REQUIRED_EXPECTED_COUNTS and not r["errors"]]
    if len(valid_main) != 63:
        completeness_issues.append(f"valid main result count is {len(valid_main)}, expected 63")
    complete = not completeness_issues and len(valid_main) == 63 and all(
        item["n_real"] == item["n_expected_from_matrix"] for item in conditions
    )

    totals = {
        "main_valid_records": len(valid_main),
        "pilots_excluded_from_table": len(pilots),
        "sums_cover_all_expected_main": complete,
        "required_bytes": sum(r["required_bytes"] for r in valid_main) if valid_main else None,
        "observed_bytes": sum(r["observed_bytes"] for r in valid_main) if valid_main else None,
        "obligations": sum(r["obligations"] for r in valid_main) if valid_main else None,
        "deliveries": sum(r["deliveries"] for r in valid_main) if valid_main else None,
        "directions": sum(r["directions"] for r in valid_main) if valid_main else None,
        "all_exact_true_records": sum(r["all_exact"] is True for r in valid_main),
        "all_exact_false_records": sum(r["all_exact"] is False for r in valid_main),
        "all_exact_unknown_records": sum(r["all_exact"] is None for r in valid_main),
    }
    comparisons = []
    by_name = {item["condition"]: item for item in conditions}
    for base, variant in BASE_COMPARISONS:
        b, v = by_name[base], by_name[variant]
        b_total = sum(r["observed_bytes"] for r in valid_main if r["condition"] == base)
        v_total = sum(r["observed_bytes"] for r in valid_main if r["condition"] == variant)
        pct = ((b_total - v_total) * 100 / b_total) if b_total else None
        comparisons.append({
            "base_condition": base, "variant_condition": variant,
            "basis": "percentage change in sum of observed bytes; computed only when both conditions have valid real observations",
            "base_observed_bytes_total": b_total if b["n_real"] else None,
            "variant_observed_bytes_total": v_total if v["n_real"] else None,
            "observed_bytes_reduction_percent_vs_base": pct if b["n_real"] and v["n_real"] else None,
        })
    synthetic_expected = sum(expected.get(name, 0) for name in SYNTHETIC)
    montage_expected = sum(expected.get(name, 0) for name in REQUIRED_EXPECTED_COUNTS if name.startswith("MONTAGE_"))
    if valid_main:
        mechanical_text = (
            f"RESULTS contiene {len(pilots)} registros piloto excluidos y {len(valid_main)} registros principales válidos "
            f"de {matrix_main_count} filas principales esperadas según MATRIX. En los registros principales válidos, "
            f"las sumas observadas son M_req={totals['required_bytes']} bytes, M_obs={totals['observed_bytes']} bytes, "
            f"{totals['obligations']} obligaciones, {totals['deliveries']} entregas y {totals['directions']} direcciones. "
            f"Completitud: {'completa' if complete else 'incompleta'}; no se hacen afirmaciones inferenciales."
        )
    else:
        mechanical_text = (
            f"RESULTS contiene {len(pilots)} registros piloto excluidos y 0 registros principales válidos; "
            f"MATRIX define {matrix_main_count} filas principales ({synthetic_expected} sintéticas y {montage_expected} Montage). "
            "No hay métricas principales observadas que resumir; la entrega es incompleta."
        )
    return {
        "record_type": "mechanical_main_results_summary_from_observed_RESULTS_only",
        "results_path": str(results_path.resolve()), "results_sha256": sha(results_path),
        "matrix_path": str(matrix_path.resolve()), "matrix_sha256": sha(matrix_path),
        "pilot_records_observed_excluded": len(pilots),
        "main_records_observed_in_results": len(main_raw),
        "main_expected_count_from_matrix": matrix_main_count,
        "expected_synthetic_count_from_matrix": synthetic_expected,
        "expected_montage_count_from_matrix": montage_expected,
        "expected_count_source": "MATRIX.json rows where phase == main; expected per-condition counts shown separately",
        "observed_values_source": "RESULTS.json only; no predictions used to fill missing observations",
        "is_complete": complete,
        "completeness_status": "complete" if complete else "incomplete_or_invalid",
        "completeness_issues": sorted(set(completeness_issues)),
        "duplicate_ids": dup_ids, "duplicate_uuids": dup_uuids,
        "row_issues": row_issues,
        "conditions": conditions,
        "main_totals": totals,
        "mechanical_text": mechanical_text,
        "observed_bytes_reduction_vs_base": comparisons,
    }


def table_tex(report: dict[str, Any]) -> str:
    lines = [
        r"% Generated mechanically from observed RESULTS.json; incomplete samples are shown as such.",
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\begin{tabular}{llrrrrl}", r"\hline",
        r"Bloque & Configuraci\'{o}n & $n_{real}/n_{matriz}$ & $M_{req}$ (MiB) & $M_{obs}$ (MiB) & DME exacta & Entregas total \\",
        r"\hline",
    ]
    for item in report["conditions"]:
        ncell = f"{item['n_real']}/{item['n_expected_from_matrix']}"
        req = fmt_values(set(item["required_bytes_values"]), unit=True)
        obs = fmt_values(set(item["observed_bytes_values"]), unit=True)
        dme = fmt_values(set(item["dme_exact_values"]))
        deliveries = str(item["deliveries_total"]) if item["n_real"] else r"\textemdash{}"
        lines.append(f"{tex_escape(item['family_label'])} & {tex_escape(item['condition'])} & {ncell} & {req} & {obs} & {dme} & {deliveries} " + r"\\")
    lines.extend([
        r"\hline", r"\end{tabular}",
        r"\caption{Resultados principales observados. $n_{real}$ cuenta registros válidos en RESULTS; $n_{matriz}$ proviene de MATRIX. Los pilotos se excluyen. Los volúmenes y DME muestran los valores distintos observados por ejecución; las entregas son el total del grupo.}",
        r"\label{tab:agrupacion-dme-resultados}", r"\end{table}",
        "% Estado de completitud: " + ("completo" if report["is_complete"] else "INCOMPLETO"),
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="Downloaded RESULTS.json")
    parser.add_argument("--matrix", type=Path, help="Design MATRIX.json; default beside results, then ../payload/MATRIX.json")
    parser.add_argument("--tex-out", type=Path, help="LaTeX table path; default results_main.tex beside this script")
    parser.add_argument("--json-out", type=Path, help="Report path; default results_main.json beside this script")
    args = parser.parse_args(argv)
    here = Path(__file__).resolve().parent
    local_matrix = args.results.resolve().with_name("MATRIX.json")
    matrix = args.matrix.resolve() if args.matrix else (local_matrix if local_matrix.exists() else here.parent / "payload" / "MATRIX.json").resolve()
    tex_path = args.tex_out.resolve() if args.tex_out else here / "results_main.tex"
    json_path = args.json_out.resolve() if args.json_out else here / "results_main.json"
    try:
        results_path = args.results.resolve()
        report = summarize(results_path, matrix)
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(table_tex(report), encoding="utf-8")
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"is_complete": report["is_complete"], "main_observed": report["main_records_observed_in_results"],
                          "expected_from_matrix": report["main_expected_count_from_matrix"],
                          "pilots_excluded": report["pilot_records_observed_excluded"],
                          "tex": str(tex_path), "json": str(json_path), "issues": report["completeness_issues"]}, ensure_ascii=False))
        return 0 if report["is_complete"] else 2
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"table_tex failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
