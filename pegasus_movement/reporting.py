from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .diagnostics import AnalysisStatus


SCHEMA_VERSION = 1


def _jsonable(value: Any) -> Any:
    """
    Convert domain objects to deterministic JSON-compatible values.
    """

    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return {
            key: _jsonable(item)
            for key, item
            in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): _jsonable(item)
            for key, item
            in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, set):
        converted = [
            _jsonable(item)
            for item in value
        ]

        return sorted(
            converted,
            key=lambda item: str(item),
        )

    if isinstance(value, (list, tuple)):
        return [
            _jsonable(item)
            for item in value
        ]

    return value


def _objects(
    value: Any,
) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, dict):
        return list(value.values())

    return list(value)


def build_analysis_document(
    run_execution: Any,
    *,
    verifications: Iterable[Any] = (),
    diagnostics: Iterable[Any] = (),
    analyzer_version: str = "1.0.0-dev",
) -> dict[str, Any]:
    """
    Build the canonical analysis document without writing files.
    """

    metric_result = getattr(
        run_execution,
        "metric_result",
        None,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "analyzer_version": analyzer_version,
        "run": {
            "run_id": getattr(
                run_execution,
                "run_id",
                None,
            ),
            "run_path": getattr(
                run_execution,
                "run_path",
                None,
            ),
            "workflow_name": getattr(
                run_execution,
                "workflow_name",
                None,
            ),
            "pattern_context": getattr(
                run_execution,
                "pattern_context",
                None,
            ),
            "experiment_parameters": (
                getattr(
                    run_execution,
                    "experiment_parameters",
                    {},
                )
            ),
        },
        "execution_model": _jsonable(
            getattr(
                run_execution,
                "execution_model",
                None,
            )
        ),
        "sources": _jsonable(
            getattr(
                run_execution,
                "provenance",
                [],
            )
        ),
        "locations": _jsonable(
            _objects(
                getattr(
                    run_execution,
                    "locations",
                    {},
                )
            )
        ),
        "tasks": _jsonable(
            _objects(
                getattr(
                    run_execution,
                    "tasks",
                    {},
                )
            )
        ),
        "scientific_files": _jsonable(
            _objects(
                getattr(
                    run_execution,
                    "scientific_files",
                    {},
                )
            )
        ),
        "manifests": _jsonable(
            getattr(
                run_execution,
                "manifests",
                [],
            )
        ),
        "required_movements": _jsonable(
            getattr(
                run_execution,
                "required_movements",
                [],
            )
        ),
        "declared_movements": _jsonable(
            getattr(
                run_execution,
                "declared_movements",
                [],
            )
        ),
        "transfer_evidence": _jsonable(
            getattr(
                run_execution,
                "evidence",
                [],
            )
        ),
        "verifications": _jsonable(
            list(verifications)
        ),
        "metrics": _jsonable(
            metric_result
        ),
        "diagnostics": _jsonable(
            list(diagnostics)
        ),
    }


def _write_tsv(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def _join(values: Iterable[Any]) -> str:
    return ",".join(
        str(
            value.value
            if isinstance(value, Enum)
            else value
        )
        for value in values
    )


def write_tsv_reports(
    run_execution: Any,
    output_dir: Path,
    *,
    verifications: Iterable[Any] = (),
) -> list[Path]:
    created: list[Path] = []

    scientific_files = sorted(
        _objects(
            getattr(
                run_execution,
                "scientific_files",
                {},
            )
        ),
        key=lambda item: item.file_id,
    )

    path = output_dir / "scientific_files.tsv"

    _write_tsv(
        path,
        [
            "file_id",
            "roles",
            "size_bytes",
            "producer",
            "consumers",
            "origin",
            "final_destinations",
        ],
        (
            {
                "file_id": item.file_id,
                "roles": _join(
                    sorted(
                        item.roles,
                        key=lambda role: role.value,
                    )
                ),
                "size_bytes": item.size_bytes,
                "producer": (
                    item.producer_task_id
                    or ""
                ),
                "consumers": _join(
                    item.consumer_task_ids
                ),
                "origin": (
                    item.origin_location_id
                    or ""
                ),
                "final_destinations": _join(
                    item.final_destination_ids
                ),
            }
            for item in scientific_files
        ),
    )

    created.append(path)

    tasks = sorted(
        _objects(
            getattr(
                run_execution,
                "tasks",
                {},
            )
        ),
        key=lambda item: item.task_id,
    )

    path = output_dir / "task_placement.tsv"

    _write_tsv(
        path,
        [
            "task_id",
            "job_id",
            "worker",
            "status",
            "attempts",
        ],
        (
            {
                "task_id": item.task_id,
                "job_id": item.job_id or "",
                "worker": (
                    item.worker_location_id
                    or ""
                ),
                "status": (
                    item.job_status
                    if item.job_status
                    is not None
                    else ""
                ),
                "attempts": (
                    item.job_run_count
                    if item.job_run_count
                    is not None
                    else ""
                ),
            }
            for item in tasks
        ),
    )

    created.append(path)

    required = sorted(
        getattr(
            run_execution,
            "required_movements",
            [],
        ),
        key=lambda item: (
            item.file_id,
            item.to_location_id,
        ),
    )

    path = output_dir / "required_movement.tsv"

    _write_tsv(
        path,
        [
            "file_id",
            "source_location",
            "destination_location",
            "size_bytes",
            "required_bytes",
            "reason",
        ],
        (
            {
                "file_id": item.file_id,
                "source_location": (
                    item.from_location_id
                ),
                "destination_location": (
                    item.to_location_id
                ),
                "size_bytes": item.size_bytes,
                "required_bytes": (
                    item.required_bytes
                ),
                "reason": item.reason.value,
            }
            for item in required
        ),
    )

    created.append(path)

    declared = sorted(
        getattr(
            run_execution,
            "declared_movements",
            [],
        ),
        key=lambda item: item.movement_id,
    )

    path = output_dir / "declared_movement.tsv"

    _write_tsv(
        path,
        [
            "movement_id",
            "job_id",
            "attempt",
            "file_id",
            "direction",
            "source",
            "destination",
            "size_bytes",
            "confirmed",
            "evidence_level",
        ],
        (
            {
                "movement_id": (
                    item.movement_id
                ),
                "job_id": item.job_id,
                "attempt": (
                    item.attempt_context
                    or ""
                ),
                "file_id": item.file_id,
                "direction": (
                    item.direction.value
                ),
                "source": (
                    item.from_location_id
                ),
                "destination": (
                    item.to_location_id
                ),
                "size_bytes": item.size_bytes,
                "confirmed": (
                    str(item.confirmed).lower()
                ),
                "evidence_level": (
                    item.verification_level.value
                ),
            }
            for item in declared
        ),
    )

    created.append(path)

    verification_list = sorted(
        list(verifications),
        key=lambda item: (
            item.job_id,
            item.direction.value,
            item.attempt_context or "",
        ),
    )

    path = output_dir / "transfer_evidence.tsv"

    _write_tsv(
        path,
        [
            "job_id",
            "direction",
            "attempt",
            "expected_files",
            "observed_files",
            "expected_bytes",
            "observed_bytes",
            "level",
            "reason",
        ],
        (
            {
                "job_id": item.job_id,
                "direction": (
                    item.direction.value
                ),
                "attempt": (
                    item.attempt_context
                    or ""
                ),
                "expected_files": (
                    item.expected_file_count
                    if item.expected_file_count
                    is not None
                    else ""
                ),
                "observed_files": (
                    item.observed_file_count
                    if item.observed_file_count
                    is not None
                    else ""
                ),
                "expected_bytes": (
                    item.expected_total_bytes
                    if item.expected_total_bytes
                    is not None
                    else ""
                ),
                "observed_bytes": (
                    item.observed_total_bytes
                    if item.observed_total_bytes
                    is not None
                    else ""
                ),
                "level": item.level.value,
                "reason": (
                    item.reason_code.value
                    if item.reason_code
                    is not None
                    else ""
                ),
            }
            for item in verification_list
        ),
    )

    created.append(path)

    metric = getattr(
        run_execution,
        "metric_result",
        None,
    )

    path = output_dir / "summary.tsv"

    rows = []

    if metric is not None:
        rows.append(
            {
                "run_id": getattr(
                    run_execution,
                    "run_id",
                    "",
                ),
                "RequiredMovement": (
                    metric.required_movement_bytes
                ),
                "DeclaredMovement": (
                    metric.declared_movement_bytes
                ),
                "Coverage": metric.coverage,
                "ByteCoverage": (
                    metric.byte_coverage
                ),
                "ObservedMovement": (
                    metric.observed_movement_bytes
                ),
                "DME": metric.dme,
                "status": (
                    metric.analysis_status.value
                ),
            }
        )

    _write_tsv(
        path,
        [
            "run_id",
            "RequiredMovement",
            "DeclaredMovement",
            "Coverage",
            "ByteCoverage",
            "ObservedMovement",
            "DME",
            "status",
        ],
        rows,
    )

    created.append(path)

    return created


def write_human_report(
    run_execution: Any,
    output_dir: Path,
    *,
    diagnostics: Iterable[Any] = (),
) -> Path:
    metric = getattr(
        run_execution,
        "metric_result",
        None,
    )

    lines = [
        "DATA MOVEMENT ASSESSMENT",
        "========================",
        "",
        f"Run: {getattr(run_execution, 'run_id', '')}",
        (
            "Workflow: "
            f"{getattr(run_execution, 'workflow_name', '')}"
        ),
        "",
    ]

    if metric is not None:
        lines.extend(
            [
                (
                    "Analysis status: "
                    f"{metric.analysis_status.value}"
                ),
                (
                    "Metric status: "
                    f"{metric.metric_status.value}"
                ),
                (
                    "RequiredMovement: "
                    f"{metric.required_movement_bytes} B"
                ),
                (
                    "DeclaredMovement: "
                    f"{metric.declared_movement_bytes} B"
                ),
                (
                    "Coverage: "
                    f"{metric.coverage}"
                ),
                (
                    "ByteCoverage: "
                    f"{metric.byte_coverage}"
                ),
                (
                    "ObservedMovement: "
                    f"{metric.observed_movement_bytes}"
                ),
                f"DME: {metric.dme}",
                (
                    "ObservedMinusRequired: "
                    f"{metric.observed_minus_required_bytes}"
                ),
            ]
        )

    diagnostic_list = list(diagnostics)

    if diagnostic_list:
        lines.extend(
            [
                "",
                "Diagnostics",
                "-----------",
            ]
        )

        for diagnostic in diagnostic_list:
            lines.append(
                (
                    f"[{diagnostic.status.value}] "
                    f"{diagnostic.reason_code.value}: "
                    f"{diagnostic.message}"
                )
            )

    path = output_dir / "REPORT.txt"

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    return path


def exit_code_for_status(
    status: AnalysisStatus,
) -> int:
    if status in {
        AnalysisStatus.VALID,
        AnalysisStatus.NOT_APPLICABLE,
    }:
        return 0

    if status == AnalysisStatus.INCOMPLETE_EVIDENCE:
        return 2

    if status == AnalysisStatus.UNSUPPORTED:
        return 3

    if status in {
        AnalysisStatus.INCONSISTENT,
        AnalysisStatus.FAILED_WORKFLOW,
    }:
        return 4

    return 5


def write_reports(
    run_execution: Any,
    output_dir: str | Path,
    *,
    verifications: Iterable[Any] = (),
    diagnostics: Iterable[Any] = (),
    analyzer_version: str = "1.0.0-dev",
) -> list[Path]:
    output_dir = Path(
        output_dir
    ).expanduser().resolve()

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    verification_list = list(
        verifications
    )
    diagnostic_list = list(
        diagnostics
    )

    document = build_analysis_document(
        run_execution,
        verifications=verification_list,
        diagnostics=diagnostic_list,
        analyzer_version=analyzer_version,
    )

    json_path = (
        output_dir / "analysis.json"
    )

    json_path.write_text(
        json.dumps(
            document,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    created = [json_path]

    created.extend(
        write_tsv_reports(
            run_execution,
            output_dir,
            verifications=verification_list,
        )
    )

    created.append(
        write_human_report(
            run_execution,
            output_dir,
            diagnostics=diagnostic_list,
        )
    )

    return created
