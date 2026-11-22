#!/usr/bin/env python3
"""Summarize accepted study results without filling from predictions.

Reads a JSON list of observed result records and writes JSON/CSV summaries.
Expected sample sizes are deliberately unspecified unless supplied by the data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any


def fraction(value: Any) -> Fraction:
    if isinstance(value, bool) or value is None:
        raise ValueError("DME missing or nonnumeric")
    return Fraction(str(value))


def integer(value: Any, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    number = int(value)
    if number != value or number < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return number


def finite_number(value: Any, field: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise ValueError(f"{field} must be finite and >= {minimum}")
    return number


def validate_row(row: Any, index: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return None, [f"row[{index}] is not an object"]
    phase = row.get("phase")
    condition = row.get("condition")
    if phase not in {"pilot", "main"}:
        errors.append("phase must be pilot or main")
    if not isinstance(condition, str) or not condition:
        errors.append("condition is missing")
    if not isinstance(row.get("id"), str) or not row["id"]:
        errors.append("id is missing")
    if not isinstance(row.get("uuid"), str) or not row["uuid"]:
        errors.append("uuid is missing")

    clean: dict[str, Any] = {
        "source_index": index,
        "id": row.get("id"),
        "uuid": row.get("uuid"),
        "phase": phase,
        "condition": condition,
        "family": row.get("family"),
        "block": row.get("block"),
        "validation_errors": errors,
    }
    try:
        required = integer(row.get("required_bytes"), "required_bytes")
        observed = integer(row.get("observed_bytes"), "observed_bytes", minimum=1)
        dme = fraction(row.get("dme"))
        if dme != Fraction(required, observed):
            raise ValueError(f"DME mismatch: {dme} != {required}/{observed}")
        clean.update(required_bytes=required, observed_bytes=observed, dme_exact=str(dme))
    except (ValueError, TypeError, ZeroDivisionError) as error:
        errors.append(str(error))
    try:
        clean["duration_s"] = finite_number(row.get("duration_s"), "duration_s")
    except (ValueError, TypeError) as error:
        errors.append(str(error))
    for field in ("obligations", "deliveries"):
        try:
            clean[field] = integer(row.get(field), field)
        except (ValueError, TypeError) as error:
            errors.append(str(error))
    if isinstance(row.get("all_exact"), bool):
        clean["all_exact"] = row["all_exact"]
    else:
        clean["all_exact"] = None
        errors.append("all_exact must be boolean")
    clean["validation_errors"] = errors
    return clean, errors


def number_range(values: list[float | int]) -> dict[str, float | int] | None:
    if not values:
        return None
    return {"min": min(values), "max": max(values)}


def summarize(rows: list[Any]) -> dict[str, Any]:
    parsed: list[dict[str, Any]] = []
    row_errors: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        clean, errors = validate_row(row, index)
        if clean is None:
            row_errors.append({"source_index": index, "errors": errors})
            continue
        parsed.append(clean)
        if errors:
            row_errors.append({"source_index": index, "id": clean.get("id"), "uuid": clean.get("uuid"), "errors": errors})

    ids = [r["id"] for r in parsed if r.get("id")]
    uuids = [r["uuid"] for r in parsed if r.get("uuid")]
    duplicate_ids = sorted(k for k, n in Counter(ids).items() if n > 1)
    duplicate_uuids = sorted(k for k, n in Counter(uuids).items() if n > 1)

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    ungrouped = []
    for row in parsed:
        if row.get("phase") in {"pilot", "main"} and isinstance(row.get("condition"), str) and row["condition"]:
            groups[(row["phase"], row["condition"])].append(row)
        else:
            ungrouped.append(row)

    summaries: list[dict[str, Any]] = []
    for (phase, condition), members in sorted(groups.items()):
        valid_metrics = [r for r in members if not any(
            e.startswith(("required_bytes", "observed_bytes", "DME", "duration_s"))
            for e in r["validation_errors"]
        ) and all(k in r for k in ("required_bytes", "observed_bytes", "dme_exact", "duration_s"))]
        durations = [r["duration_s"] for r in members if "duration_s" in r]
        obligations = [r["obligations"] for r in members if "obligations" in r]
        deliveries = [r["deliveries"] for r in members if "deliveries" in r]
        exact_counts = Counter("true" if r["all_exact"] is True else "false" if r["all_exact"] is False else "unknown" for r in members)
        summaries.append({
            "phase": phase,
            "condition": condition,
            "n_records": len(members),
            "n_valid_dme_duration": len(valid_metrics),
            "n_records_with_errors": sum(bool(r["validation_errors"]) for r in members),
            "expected_n": None,
            "sample_completeness": "not_assessed_no_expected_count_supplied",
            "required_bytes_values": sorted({r["required_bytes"] for r in valid_metrics}),
            "observed_bytes_values": sorted({r["observed_bytes"] for r in valid_metrics}),
            "dme_exact_values": sorted({r["dme_exact"] for r in valid_metrics}, key=Fraction),
            "duration_s_median": statistics.median(durations) if durations else None,
            "duration_s_range": number_range(durations),
            "obligations_n": len(obligations),
            "obligations_total": sum(obligations) if obligations else None,
            "obligations_range": number_range(obligations),
            "deliveries_n": len(deliveries),
            "deliveries_total": sum(deliveries) if deliveries else None,
            "deliveries_range": number_range(deliveries),
            "all_exact_counts": {key: exact_counts[key] for key in ("true", "false", "unknown")},
            "ids": [r["id"] for r in members],
            "uuids": [r["uuid"] for r in members],
            "blocks": [r.get("block") for r in members],
        })

    phase_counts = Counter(r.get("phase") for r in parsed)
    return {
        "record_type": "observed_results_summary_no_prediction_imputation",
        "input_records": len(rows),
        "parsed_object_records": len(parsed),
        "grouped_records": sum(len(v) for v in groups.values()),
        "ungrouped_records": len(ungrouped),
        "phase_record_counts": {k: phase_counts[k] for k in ("pilot", "main")},
        "unique_id_count": len(set(ids)),
        "unique_uuid_count": len(set(uuids)),
        "ids_unique": not duplicate_ids and len(ids) == len(parsed),
        "uuids_unique": not duplicate_uuids and len(uuids) == len(parsed),
        "duplicate_ids": duplicate_ids,
        "duplicate_uuids": duplicate_uuids,
        "sample_completeness": "not_assessed_no_expected_count_supplied",
        "groups": summaries,
        "ungrouped": ungrouped,
        "row_errors": row_errors,
    }


def write_csv(path: Path, groups: list[dict[str, Any]]) -> None:
    columns = [
        "phase", "condition", "n_records", "n_valid_dme_duration", "n_records_with_errors",
        "expected_n", "sample_completeness", "required_bytes_values", "observed_bytes_values",
        "dme_exact_values", "duration_s_median", "duration_s_min", "duration_s_max",
        "obligations_n", "obligations_total", "obligations_min", "obligations_max",
        "deliveries_n", "deliveries_total", "deliveries_min", "deliveries_max",
        "all_exact_true", "all_exact_false", "all_exact_unknown", "ids", "uuids", "blocks",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for group in groups:
            duration_range = group["duration_s_range"] or {}
            obligation_range = group["obligations_range"] or {}
            delivery_range = group["deliveries_range"] or {}
            exact = group["all_exact_counts"]
            writer.writerow({
                **{k: group.get(k) for k in columns if k in group},
                "required_bytes_values": ";".join(map(str, group["required_bytes_values"])),
                "observed_bytes_values": ";".join(map(str, group["observed_bytes_values"])),
                "dme_exact_values": ";".join(group["dme_exact_values"]),
                "duration_s_min": duration_range.get("min"), "duration_s_max": duration_range.get("max"),
                "obligations_min": obligation_range.get("min"), "obligations_max": obligation_range.get("max"),
                "deliveries_min": delivery_range.get("min"), "deliveries_max": delivery_range.get("max"),
                "all_exact_true": exact["true"], "all_exact_false": exact["false"], "all_exact_unknown": exact["unknown"],
                "ids": ";".join(str(x) for x in group["ids"]),
                "uuids": ";".join(str(x) for x in group["uuids"]),
                "blocks": ";".join("" if x is None else str(x) for x in group["blocks"]),
            })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="Downloaded RESULTS.json containing a JSON list")
    parser.add_argument("--json-out", type=Path, help="Summary JSON path (default: summary.json beside input)")
    parser.add_argument("--csv-out", type=Path, help="Grouped CSV path (default: summary.csv beside input)")
    args = parser.parse_args(argv)
    try:
        source = args.results.resolve()
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            raise ValueError("RESULTS.json must contain a JSON array")
        summary = summarize(data)
        json_out = (args.json_out or source.with_name("summary.json")).resolve()
        csv_out = (args.csv_out or source.with_name("summary.csv")).resolve()
        json_out.parent.mkdir(parents=True, exist_ok=True)
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_csv(csv_out, summary["groups"])
        print(json.dumps({"input_records": summary["input_records"], "groups": len(summary["groups"]),
                          "json": str(json_out), "csv": str(csv_out),
                          "ids_unique": summary["ids_unique"], "uuids_unique": summary["uuids_unique"],
                          "row_errors": len(summary["row_errors"])}, ensure_ascii=False))
        return 0 if not summary["row_errors"] and summary["ids_unique"] and summary["uuids_unique"] else 2
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"summarize failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
