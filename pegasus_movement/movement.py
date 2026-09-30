from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .diagnostics import (
    AnalysisStatus,
    Diagnostic,
    ReasonCode,
)
from .execution_model import is_pegasus_compute_submit
from .model import (
    DeclaredMovementRecord,
    EvidenceLevel,
    ExecutionModelProfile,
    FileClassification,
    FileRole,
    JobTransferManifest,
    ManifestFile,
    RequiredMovementRecord,
    RequiredReason,
    ScientificFile,
    TaskExecution,
    TransferDirection,
)
from .normalize import strip_classad_quotes
from .pegasus_source import ParsedSubmitFile


CONDORIO_ADAPTER_NAME = "CondorIOStandardAdapter"

_URI_RE = re.compile(
    r"^([A-Za-z][A-Za-z0-9+.-]*)://"
)


@dataclass(slots=True)
class RequiredMovementBuildResult:
    records: list[RequiredMovementRecord] = field(
        default_factory=list
    )
    total_bytes: int = 0
    diagnostics: list[Diagnostic] = field(
        default_factory=list
    )


@dataclass(slots=True)
class ManifestBuildResult:
    manifests: list[JobTransferManifest] = field(
        default_factory=list
    )
    diagnostics: list[Diagnostic] = field(
        default_factory=list
    )


@dataclass(slots=True)
class DeclaredMovementBuildResult:
    records: list[DeclaredMovementRecord] = field(
        default_factory=list
    )
    total_bytes: int = 0
    diagnostics: list[Diagnostic] = field(
        default_factory=list
    )


def _diagnostic(
    status: AnalysisStatus,
    reason: ReasonCode,
    message: str,
    *,
    context: dict | None = None,
) -> Diagnostic:
    return Diagnostic(
        status=status,
        reason_code=reason,
        message=message,
        context=context or {},
        provenance=[],
    )


def _task_index(
    tasks: Iterable[TaskExecution],
) -> dict[str, TaskExecution]:
    result: dict[str, TaskExecution] = {}

    for task in tasks:
        result[task.task_id] = task
        result[task.pegasus_node_id] = task

    return result


def calculate_required_movement(
    records: Iterable[RequiredMovementRecord],
) -> int:
    return sum(
        record.required_bytes
        for record in records
    )


def build_required_movements(
    scientific_files: Iterable[ScientificFile],
    task_executions: Iterable[TaskExecution],
) -> RequiredMovementBuildResult:
    """
    File-centric logical lower bound conditioned on observed placement.
    """

    tasks = _task_index(
        task_executions
    )

    records: list[
        RequiredMovementRecord
    ] = []

    diagnostics: list[Diagnostic] = []

    for scientific_file in sorted(
        scientific_files,
        key=lambda item: item.file_id,
    ):
        if scientific_file.size_bytes is None:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCOMPLETE_EVIDENCE,
                    ReasonCode.MISSING_FILE_SIZE,
                    (
                        "RequiredMovement needs an "
                        "authoritative scientific file size."
                    ),
                    context={
                        "file_id": scientific_file.file_id,
                    },
                )
            )
            continue

        origin: str | None = None

        if scientific_file.producer_task_id:
            producer = tasks.get(
                scientific_file.producer_task_id
            )

            if (
                producer is None
                or producer.worker_location_id
                is None
            ):
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCOMPLETE_EVIDENCE,
                        ReasonCode.MISSING_PLACEMENT,
                        (
                            "Producer placement is "
                            "required for RequiredMovement."
                        ),
                        context={
                            "file_id": (
                                scientific_file.file_id
                            ),
                            "producer_task_id": (
                                scientific_file
                                .producer_task_id
                            ),
                        },
                    )
                )
                continue

            origin = (
                producer.worker_location_id
            )

        elif (
            FileRole.EXTERNAL_INPUT
            in scientific_file.roles
        ):
            origin = (
                scientific_file
                .origin_location_id
            )

            if origin is None:
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCOMPLETE_EVIDENCE,
                        ReasonCode.MISSING_PLACEMENT,
                        (
                            "External input origin is "
                            "required for RequiredMovement."
                        ),
                        context={
                            "file_id": (
                                scientific_file.file_id
                            ),
                        },
                    )
                )
                continue

        else:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.SCOPE_MISMATCH,
                    (
                        "Scientific file has neither "
                        "an internal producer nor an "
                        "external input origin."
                    ),
                    context={
                        "file_id": scientific_file.file_id,
                    },
                )
            )
            continue

        destination_reasons: dict[
            str,
            RequiredReason,
        ] = {}

        consumer_reason = (
            RequiredReason.INPUT
            if (
                FileRole.EXTERNAL_INPUT
                in scientific_file.roles
            )
            else RequiredReason.CONSUMER
        )

        for consumer_task_id in (
            scientific_file.consumer_task_ids
        ):
            consumer = tasks.get(
                consumer_task_id
            )

            if (
                consumer is None
                or consumer.worker_location_id
                is None
            ):
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCOMPLETE_EVIDENCE,
                        ReasonCode.MISSING_PLACEMENT,
                        (
                            "Consumer placement is "
                            "required for RequiredMovement."
                        ),
                        context={
                            "file_id": (
                                scientific_file.file_id
                            ),
                            "consumer_task_id": (
                                consumer_task_id
                            ),
                        },
                    )
                )
                continue

            destination_reasons.setdefault(
                consumer.worker_location_id,
                consumer_reason,
            )

        for destination in (
            scientific_file
            .final_destination_ids
        ):
            destination_reasons.setdefault(
                destination,
                RequiredReason.FINAL_DESTINATION,
            )

        destination_reasons.pop(
            origin,
            None,
        )

        for destination in sorted(
            destination_reasons
        ):
            records.append(
                RequiredMovementRecord(
                    file_id=scientific_file.file_id,
                    from_location_id=origin,
                    to_location_id=destination,
                    size_bytes=(
                        scientific_file.size_bytes
                    ),
                    required_bytes=(
                        scientific_file.size_bytes
                    ),
                    reason=destination_reasons[
                        destination
                    ],
                )
            )

    return RequiredMovementBuildResult(
        records=records,
        total_bytes=(
            calculate_required_movement(
                records
            )
        ),
        diagnostics=diagnostics,
    )


def _clean_submit_value(
    submit: ParsedSubmitFile,
    key: str,
) -> str | None:
    raw = submit.value(key)

    if raw is None:
        return None

    value = strip_classad_quotes(raw)

    if value is None:
        return None

    value = value.strip()

    return value or None


def _split_condor_list(
    raw: str | None,
) -> list[str]:
    if raw is None:
        return []

    cleaned = strip_classad_quotes(raw)

    if cleaned is None:
        return []

    try:
        row = next(
            csv.reader(
                [cleaned],
                skipinitialspace=True,
            )
        )
    except csv.Error:
        return [
            part.strip()
            for part in cleaned.split(",")
            if part.strip()
        ]

    return [
        part.strip()
        for part in row
        if part.strip()
    ]


def _submit_bool(
    submit: ParsedSubmitFile,
    key: str,
) -> bool | None:
    value = _clean_submit_value(
        submit,
        key,
    )

    if value is None:
        return None

    lowered = value.lower()

    if lowered in {"true", "yes", "1"}:
        return True

    if lowered in {"false", "no", "0"}:
        return False

    return None


def _parse_output_remaps(
    raw: str | None,
) -> dict[str, str]:
    if raw is None:
        return {}

    cleaned = strip_classad_quotes(raw)

    if cleaned is None:
        return {}

    result: dict[str, str] = {}

    for item in cleaned.split(";"):
        if "=" not in item:
            continue

        source, destination = item.split(
            "=",
            1,
        )

        source = source.strip()
        destination = destination.strip()

        if source:
            result[source] = destination

    return result


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result


def _protocol(path: str) -> str:
    match = _URI_RE.match(path)

    if match:
        return match.group(1).lower()

    return "cedar"


def _filesystem_path(
    raw_path: str,
) -> Path | None:
    if "$(" in raw_path:
        return None

    parsed = urlparse(raw_path)

    if parsed.scheme == "file":
        return Path(parsed.path)

    if parsed.scheme:
        return None

    path = Path(raw_path)

    if path.is_absolute():
        return path

    return None


def _auxiliary_size(
    raw_path: str,
) -> int | None:
    path = _filesystem_path(
        raw_path
    )

    if (
        path is None
        or not path.exists()
        or not path.is_file()
    ):
        return None

    return path.stat().st_size


def _scientific_indexes(
    scientific_files: Iterable[ScientificFile],
):
    by_logical: dict[str, ScientificFile] = {}
    by_physical: dict[str, ScientificFile] = {}

    for scientific_file in scientific_files:
        by_logical[
            scientific_file.logical_name
        ] = scientific_file

        for physical_ref in (
            scientific_file.physical_refs
        ):
            by_physical[
                physical_ref
            ] = scientific_file

    return by_logical, by_physical


def _manifest_file(
    *,
    job_id: str,
    direction: TransferDirection,
    physical_path: str,
    by_logical: dict[str, ScientificFile],
    by_physical: dict[str, ScientificFile],
    remaps: dict[str, str],
) -> ManifestFile:
    scientific_file = (
        by_logical.get(physical_path)
        or by_physical.get(physical_path)
    )

    if scientific_file is not None:
        classification = (
            FileClassification.SCIENTIFIC
        )
        logical_file_id = (
            scientific_file.file_id
        )
        size_bytes = (
            scientific_file.size_bytes
        )
        size_provenance = list(
            scientific_file.size_provenance
        )

    else:
        classification = (
            FileClassification.AUXILIARY
        )
        logical_file_id = None
        size_bytes = _auxiliary_size(
            physical_path
        )
        size_provenance = []

    return ManifestFile(
        job_id=job_id,
        direction=direction,
        logical_file_id=logical_file_id,
        physical_path=physical_path,
        basename=Path(
            physical_path
        ).name,
        classification=classification,
        size_bytes=size_bytes,
        size_provenance=size_provenance,
        protocol=_protocol(
            physical_path
        ),
        remap_from=(
            physical_path
            if physical_path in remaps
            else None
        ),
        remap_to=remaps.get(
            physical_path
        ),
    )


def _task_for_submit(
    submit: ParsedSubmitFile,
    tasks: dict[str, TaskExecution],
) -> TaskExecution | None:
    dag_id = _clean_submit_value(
        submit,
        "+pegasus_wf_dag_job_id",
    )

    if dag_id is None:
        return None

    return tasks.get(dag_id)


def _manifest_complete(
    files: list[ManifestFile],
) -> bool:
    return all(
        item.size_bytes is not None
        for item in files
    )


def build_condorio_manifests(
    *,
    submits: Iterable[ParsedSubmitFile],
    task_executions: Iterable[TaskExecution],
    scientific_files: Iterable[ScientificFile],
    execution_model: ExecutionModelProfile,
    attempt_context_by_job_id: (
        dict[str, str | None] | None
    ) = None,
) -> ManifestBuildResult:
    """
    Build complete scientific+auxiliary manifest declarations.

    This stage does not claim that a transfer occurred.
    """

    diagnostics: list[Diagnostic] = []
    manifests: list[
        JobTransferManifest
    ] = []

    if (
        not execution_model.supported
        or execution_model.adapter_name
        != CONDORIO_ADAPTER_NAME
    ):
        diagnostics.append(
            _diagnostic(
                AnalysisStatus.UNSUPPORTED,
                ReasonCode.SCOPE_MISMATCH,
                (
                    "DeclaredMovement requires a "
                    "supported CondorIOStandardAdapter."
                ),
            )
        )

        return ManifestBuildResult(
            diagnostics=diagnostics
        )

    tasks = _task_index(
        task_executions
    )

    by_logical, by_physical = (
        _scientific_indexes(
            scientific_files
        )
    )

    attempts = (
        attempt_context_by_job_id
        or {}
    )

    for submit in submits:
        if not is_pegasus_compute_submit(
            submit
        ):
            continue

        task = _task_for_submit(
            submit,
            tasks,
        )

        if task is None or task.job_id is None:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCOMPLETE_EVIDENCE,
                    ReasonCode.AMBIGUOUS_JOB_IDENTITY,
                    (
                        "Compute submit cannot be mapped "
                        "to one executed scientific job."
                    ),
                    context={
                        "submit": str(submit.path),
                    },
                )
            )
            continue

        job_id = task.job_id

        # ----------------------------------------------------
        # INPUT MANIFEST
        # ----------------------------------------------------

        input_paths: list[str] = []

        if (
            _submit_bool(
                submit,
                "transfer_executable",
            )
            is True
        ):
            executable = _clean_submit_value(
                submit,
                "executable",
            )

            if executable:
                input_paths.append(
                    executable
                )

        input_paths.extend(
            _split_condor_list(
                submit.value(
                    "transfer_input_files"
                )
            )
        )

        standard_input = (
            _clean_submit_value(
                submit,
                "input",
            )
        )

        if (
            standard_input
            and standard_input
            not in {"/dev/null", "NUL"}
        ):
            input_paths.append(
                standard_input
            )

        input_paths = _dedupe(
            input_paths
        )

        input_files = [
            _manifest_file(
                job_id=job_id,
                direction=(
                    TransferDirection.INPUT
                ),
                physical_path=raw_path,
                by_logical=by_logical,
                by_physical=by_physical,
                remaps={},
            )
            for raw_path in input_paths
        ]

        manifests.append(
            JobTransferManifest(
                job_id=job_id,
                direction=TransferDirection.INPUT,
                attempt_context=attempts.get(
                    job_id
                ),
                files=input_files,
                expected_file_count=len(
                    input_files
                ),
                expected_total_bytes=(
                    sum(
                        item.size_bytes
                        for item in input_files
                        if item.size_bytes
                        is not None
                    )
                    if _manifest_complete(
                        input_files
                    )
                    else None
                ),
                scientific_file_count=sum(
                    1
                    for item in input_files
                    if item.classification
                    == FileClassification.SCIENTIFIC
                ),
                scientific_total_bytes=(
                    sum(
                        item.size_bytes
                        for item in input_files
                        if (
                            item.classification
                            == FileClassification.SCIENTIFIC
                            and item.size_bytes
                            is not None
                        )
                    )
                    if all(
                        item.size_bytes
                        is not None
                        for item in input_files
                        if item.classification
                        == FileClassification.SCIENTIFIC
                    )
                    else None
                ),
                complete=_manifest_complete(
                    input_files
                ),
            )
        )

        # ----------------------------------------------------
        # OUTPUT MANIFEST
        # ----------------------------------------------------

        output_raw = submit.value(
            "transfer_output_files"
        )

        output_paths = _split_condor_list(
            output_raw
        )

        output_semantics_complete = (
            output_raw is not None
        )

        remaps = _parse_output_remaps(
            submit.value(
                "transfer_output_remaps"
            )
        )

        stdout_path = _clean_submit_value(
            submit,
            "output",
        )
        stderr_path = _clean_submit_value(
            submit,
            "error",
        )

        if (
            stdout_path
            and stdout_path
            not in {"/dev/null", "NUL"}
            and _submit_bool(
                submit,
                "stream_output",
            )
            is not True
        ):
            output_paths.append(
                stdout_path
            )

        if (
            stderr_path
            and stderr_path
            not in {"/dev/null", "NUL"}
            and _submit_bool(
                submit,
                "stream_error",
            )
            is not True
        ):
            output_paths.append(
                stderr_path
            )

        output_paths = _dedupe(
            output_paths
        )

        output_files = [
            _manifest_file(
                job_id=job_id,
                direction=(
                    TransferDirection.OUTPUT
                ),
                physical_path=raw_path,
                by_logical=by_logical,
                by_physical=by_physical,
                remaps=remaps,
            )
            for raw_path in output_paths
        ]

        output_complete = (
            output_semantics_complete
            and _manifest_complete(
                output_files
            )
        )

        if not output_semantics_complete:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCOMPLETE_EVIDENCE,
                    ReasonCode.MANIFEST_INCOMPLETE,
                    (
                        "Implicit HTCondor output "
                        "semantics were not expanded "
                        "into an exact manifest."
                    ),
                    context={
                        "job_id": job_id,
                    },
                )
            )

        manifests.append(
            JobTransferManifest(
                job_id=job_id,
                direction=TransferDirection.OUTPUT,
                attempt_context=attempts.get(
                    job_id
                ),
                files=output_files,
                expected_file_count=len(
                    output_files
                ),
                expected_total_bytes=(
                    sum(
                        item.size_bytes
                        for item in output_files
                        if item.size_bytes
                        is not None
                    )
                    if output_complete
                    else None
                ),
                scientific_file_count=sum(
                    1
                    for item in output_files
                    if item.classification
                    == FileClassification.SCIENTIFIC
                ),
                scientific_total_bytes=(
                    sum(
                        item.size_bytes
                        for item in output_files
                        if (
                            item.classification
                            == FileClassification.SCIENTIFIC
                            and item.size_bytes
                            is not None
                        )
                    )
                    if all(
                        item.size_bytes
                        is not None
                        for item in output_files
                        if item.classification
                        == FileClassification.SCIENTIFIC
                    )
                    else None
                ),
                complete=output_complete,
            )
        )

    return ManifestBuildResult(
        manifests=manifests,
        diagnostics=diagnostics,
    )


def calculate_declared_movement(
    records: Iterable[DeclaredMovementRecord],
) -> int:
    return sum(
        record.size_bytes
        for record in records
    )


def build_declared_movements(
    *,
    manifests: Iterable[JobTransferManifest],
    task_executions: Iterable[TaskExecution],
    execution_model: ExecutionModelProfile,
) -> DeclaredMovementBuildResult:
    """
    Convert scientific manifest entries into declared movements.

    Records start as unconfirmed. Reconciliation in I9 is the only
    stage allowed to upgrade evidence/confirmation.
    """

    diagnostics: list[Diagnostic] = []
    records: list[
        DeclaredMovementRecord
    ] = []

    if (
        not execution_model.supported
        or execution_model.adapter_name
        != CONDORIO_ADAPTER_NAME
        or not execution_model.submit_host
    ):
        diagnostics.append(
            _diagnostic(
                AnalysisStatus.UNSUPPORTED,
                ReasonCode.SCOPE_MISMATCH,
                (
                    "DeclaredMovement requires the "
                    "supported CondorIO execution model."
                ),
            )
        )

        return DeclaredMovementBuildResult(
            diagnostics=diagnostics
        )

    by_job = {
        task.job_id: task
        for task in task_executions
        if task.job_id is not None
    }

    ordinal = 0

    for manifest in manifests:
        task = by_job.get(
            manifest.job_id
        )

        if (
            task is None
            or task.worker_location_id
            is None
        ):
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCOMPLETE_EVIDENCE,
                    ReasonCode.MISSING_PLACEMENT,
                    (
                        "DeclaredMovement needs the "
                        "observed worker for each job."
                    ),
                    context={
                        "job_id": manifest.job_id,
                    },
                )
            )
            continue

        submit_host = (
            execution_model.submit_host
        )
        worker = (
            task.worker_location_id
        )

        if submit_host == worker:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.UNSUPPORTED,
                    ReasonCode.SCOPE_MISMATCH,
                    (
                        "v1 requires submit host and "
                        "scientific worker to be distinct."
                    ),
                    context={
                        "job_id": manifest.job_id,
                        "location_id": submit_host,
                    },
                )
            )
            continue

        if (
            manifest.direction
            == TransferDirection.INPUT
        ):
            source = submit_host
            destination = worker

        else:
            source = worker
            destination = submit_host

        for manifest_file in manifest.files:
            if (
                manifest_file.classification
                != FileClassification.SCIENTIFIC
            ):
                continue

            if (
                manifest_file.logical_file_id
                is None
            ):
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCONSISTENT,
                        ReasonCode.AMBIGUOUS_FILE_IDENTITY,
                        (
                            "Scientific manifest entry "
                            "has no logical file identity."
                        ),
                        context={
                            "job_id": manifest.job_id,
                            "path": (
                                manifest_file
                                .physical_path
                            ),
                        },
                    )
                )
                continue

            if manifest_file.size_bytes is None:
                diagnostics.append(
                    _diagnostic(
                        AnalysisStatus.INCOMPLETE_EVIDENCE,
                        ReasonCode.MISSING_FILE_SIZE,
                        (
                            "Declared scientific "
                            "movement has unknown size."
                        ),
                        context={
                            "job_id": manifest.job_id,
                            "file_id": (
                                manifest_file
                                .logical_file_id
                            ),
                        },
                    )
                )
                continue

            ordinal += 1

            records.append(
                DeclaredMovementRecord(
                    movement_id=(
                        f"{manifest.job_id}:"
                        f"{manifest.direction.value}:"
                        f"{ordinal}"
                    ),
                    job_id=manifest.job_id,
                    attempt_context=(
                        manifest.attempt_context
                    ),
                    file_id=(
                        manifest_file
                        .logical_file_id
                    ),
                    direction=(
                        manifest.direction
                    ),
                    from_location_id=source,
                    to_location_id=destination,
                    size_bytes=(
                        manifest_file.size_bytes
                    ),
                    verification_level=(
                        EvidenceLevel.INSUFFICIENT
                    ),
                    confirmed=False,
                    verification_reason=(
                        ReasonCode.MANIFEST_INCOMPLETE
                        if not manifest.complete
                        else None
                    ),
                )
            )

    return DeclaredMovementBuildResult(
        records=records,
        total_bytes=(
            calculate_declared_movement(
                records
            )
        ),
        diagnostics=diagnostics,
    )
