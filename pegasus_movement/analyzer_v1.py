from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .dataflow import build_scientific_dataflow
from .diagnostics import (
    AnalysisStatus,
    Diagnostic,
    ReasonCode,
)
from .execution_model import (
    build_execution_model_evidence_from_run,
    detect_execution_model,
)
from .htcondor_source import (
    ParsedHistoryFile,
    build_transfer_evidence,
    parse_history_file,
)
from .metrics import calculate_metrics
from .model import (
    Location,
    LocationType,
    RunExecution,
    TaskExecution,
)
from .movement import (
    build_condorio_manifests,
    build_declared_movements,
    build_required_movements,
)
from .normalize import (
    build_worker_locations,
    normalize_history_identities,
    strip_classad_quotes,
)
from .pegasus_source import (
    load_run_sources,
    parse_submit_files,
)
from .reconciliation import reconcile_movements


_BLOCKING = {
    AnalysisStatus.INCOMPLETE_EVIDENCE,
    AnalysisStatus.UNSUPPORTED,
    AnalysisStatus.INCONSISTENT,
    AnalysisStatus.FAILED_WORKFLOW,
    AnalysisStatus.ERROR,
}

_STATUS_RANK = {
    AnalysisStatus.VALID: 0,
    AnalysisStatus.NOT_APPLICABLE: 1,
    AnalysisStatus.INCOMPLETE_EVIDENCE: 2,
    AnalysisStatus.FAILED_WORKFLOW: 3,
    AnalysisStatus.UNSUPPORTED: 4,
    AnalysisStatus.INCONSISTENT: 5,
    AnalysisStatus.ERROR: 6,
}


def _diagnostic(
    status: AnalysisStatus,
    reason: ReasonCode,
    message: str,
    *,
    context: dict[str, Any] | None = None,
    provenance=None,
) -> Diagnostic:
    return Diagnostic(
        status=status,
        reason_code=reason,
        message=message,
        context=context or {},
        provenance=list(provenance or []),
    )


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(raw, dict):
        raise ValueError(
            f"{path} must contain a mapping"
        )

    return raw


def _run_metadata(
    run_path: Path,
    workflow_path: Path,
) -> tuple[
    str,
    str | None,
    str | None,
    dict[str, Any],
]:
    workflow = _read_yaml_mapping(
        workflow_path
    )

    workflow_name = workflow.get("name")

    if not isinstance(workflow_name, str):
        workflow_name = None

    metadata = workflow.get(
        "metadata",
        {},
    ) or {}

    if not isinstance(metadata, dict):
        metadata = {}

    pattern = metadata.get("pattern")

    if not isinstance(pattern, str):
        pattern = None

    run_id: str | None = None

    braindump = run_path / "braindump.yml"

    if braindump.exists():
        try:
            raw = _read_yaml_mapping(
                braindump
            )

            for key in (
                "root_wf_uuid",
                "pegasus_root_wf_uuid",
                "wf_uuid",
                "uuid",
            ):
                value = raw.get(key)

                if isinstance(
                    value,
                    str,
                ) and value:
                    run_id = value
                    break

        except Exception:
            pass

    if run_id is None:
        run_id = str(
            run_path.resolve()
        )

    return (
        run_id,
        workflow_name,
        pattern,
        dict(metadata),
    )


def _record_text(
    record,
    key: str,
) -> str | None:
    raw = record.value(key)

    if raw is None:
        return None

    value = strip_classad_quotes(
        raw.strip()
    )

    return value or None


def _record_int(
    record,
    key: str,
) -> int | None:
    raw = _record_text(
        record,
        key,
    )

    if raw is None:
        return None

    try:
        value = int(raw)
    except ValueError:
        return None

    if value < 0:
        return None

    return value


def _record_bool(
    record,
    key: str,
) -> bool | None:
    raw = _record_text(
        record,
        key,
    )

    if raw is None:
        return None

    lowered = raw.lower()

    if lowered in {
        "true",
        "1",
    }:
        return True

    if lowered in {
        "false",
        "0",
    }:
        return False

    return None


def _scope_history(
    parsed: ParsedHistoryFile,
    run_id: str,
) -> ParsedHistoryFile:
    """
    Prefer explicit Pegasus root workflow UUID scoping.

    If the history snapshot does not carry that attribute,
    leave records intact and let task/job identity checks
    fail closed if the snapshot is ambiguous.
    """

    scoped = []
    saw_scope_attribute = False

    for record in parsed.records:
        raw = (
            record.value(
                "pegasus_root_wf_uuid"
            )
            or record.value(
                "PegasusRootWfUuid"
            )
        )

        if raw is None:
            continue

        saw_scope_attribute = True

        value = strip_classad_quotes(
            raw.strip()
        )

        if value == run_id:
            scoped.append(record)

    if not saw_scope_attribute:
        return parsed

    return ParsedHistoryFile(
        path=parsed.path,
        records=scoped,
        structural_errors=list(
            parsed.structural_errors
        ),
    )


def _task_executions(
    parsed_history: ParsedHistoryFile,
    *,
    scientific_task_ids: list[str],
) -> tuple[
    dict[str, TaskExecution],
    list[Diagnostic],
]:
    identities = (
        normalize_history_identities(
            parsed_history
        )
    )

    record_by_index = {
        record.record_index: record
        for record in parsed_history.records
    }

    tasks: dict[
        str,
        TaskExecution,
    ] = {}

    diagnostics: list[
        Diagnostic
    ] = []

    wanted = set(
        scientific_task_ids
    )

    by_task: dict[
        str,
        list,
    ] = {}

    for identity in identities:
        if (
            identity.task_id in wanted
            and identity.job_id is not None
        ):
            by_task.setdefault(
                identity.task_id,
                [],
            ).append(identity)

    for task_id in sorted(wanted):
        candidates = by_task.get(
            task_id,
            [],
        )

        job_ids = {
            item.job_id
            for item in candidates
            if item.job_id is not None
        }

        if len(job_ids) != 1:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.AMBIGUOUS_JOB_IDENTITY,
                    (
                        "Scientific task does not map "
                        "to exactly one HTCondor job."
                    ),
                    context={
                        "task_id": task_id,
                        "job_ids": sorted(
                            job_ids
                        ),
                    },
                )
            )
            continue

        job_id = next(
            iter(job_ids)
        )

        matching = [
            item
            for item in candidates
            if item.job_id == job_id
        ]

        identity = matching[-1]

        record = record_by_index.get(
            identity.record_index
        )

        if record is None:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCOMPLETE_EVIDENCE,
                    ReasonCode.HISTORY_MISSING,
                    (
                        "Normalized job identity has "
                        "no corresponding history record."
                    ),
                    context={
                        "task_id": task_id,
                        "job_id": job_id,
                    },
                )
            )
            continue

        job_status = _record_int(
            record,
            "JobStatus",
        )

        exit_code = _record_int(
            record,
            "ExitCode",
        )

        exit_by_signal = _record_bool(
            record,
            "ExitBySignal",
        )

        successful = None

        if (
            job_status is not None
            and exit_code is not None
        ):
            successful = (
                job_status == 4
                and exit_code == 0
                and exit_by_signal is not True
            )

        provenance = list(
            identity.provenance
        )

        for key in (
            "JobStatus",
            "ExitCode",
            "JobRunCount",
            "NumJobStarts",
            "LastRemoteHost",
            "RemoteHost",
        ):
            attr = record.get_last(key)

            if attr is not None:
                provenance.append(
                    attr.provenance
                )

        if identity.location_id is None:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCOMPLETE_EVIDENCE,
                    ReasonCode.MISSING_PLACEMENT,
                    (
                        "Scientific task has no "
                        "observed worker location."
                    ),
                    context={
                        "task_id": task_id,
                        "job_id": job_id,
                    },
                    provenance=provenance,
                )
            )

        tasks[task_id] = TaskExecution(
            task_id=task_id,
            pegasus_node_id=(
                identity.pegasus_node_id
                or task_id
            ),
            job_id=job_id,
            worker_location_id=(
                identity.location_id
            ),
            job_status=job_status,
            exit_code=exit_code,
            job_run_count=_record_int(
                record,
                "JobRunCount",
            ),
            num_job_starts=_record_int(
                record,
                "NumJobStarts",
            ),
            successful=successful,
            provenance=provenance,
        )

    return tasks, diagnostics


def _attempt_contexts(
    tasks: dict[
        str,
        TaskExecution,
    ],
) -> dict[str, str | None]:
    result: dict[
        str,
        str | None,
    ] = {}

    for task in tasks.values():
        if task.job_id is None:
            continue

        if (
            task.job_run_count == 1
            and task.num_job_starts == 1
        ):
            result[
                task.job_id
            ] = "attempt:1"
        else:
            result[
                task.job_id
            ] = None

    return result


def _blocking(
    diagnostics: list[Diagnostic],
) -> bool:
    return any(
        item.status in _BLOCKING
        for item in diagnostics
    )


def overall_status(
    run: RunExecution,
) -> AnalysisStatus:
    statuses = [
        item.status
        for item in run.diagnostics
    ]

    if run.metric_result is not None:
        statuses.append(
            run.metric_result.analysis_status
        )

    if not statuses:
        return (
            AnalysisStatus.INCOMPLETE_EVIDENCE
        )

    return max(
        statuses,
        key=lambda status: (
            _STATUS_RANK[status]
        ),
    )


def analyze_run_v1(
    run_path: str | Path,
    *,
    history_file: str | Path,
) -> RunExecution:
    run_path = Path(
        run_path
    ).expanduser().resolve()

    history_file = Path(
        history_file
    ).expanduser().resolve()

    workflow_path = (
        run_path / "workflow.yml"
    )

    if not workflow_path.is_file():
        raise FileNotFoundError(
            workflow_path
        )

    if not history_file.is_file():
        raise FileNotFoundError(
            history_file
        )

    (
        run_id,
        workflow_name,
        pattern_context,
        experiment_parameters,
    ) = _run_metadata(
        run_path,
        workflow_path,
    )

    sources = load_run_sources(
        run_path
    )

    submits = parse_submit_files(
        sources.submit_files
    )

    parsed_history = (
        parse_history_file(
            history_file
        )
    )

    parsed_history = _scope_history(
        parsed_history,
        run_id,
    )

    identities = (
        normalize_history_identities(
            parsed_history
        )
    )

    locations = (
        build_worker_locations(
            identities
        )
    )

    diagnostics: list[
        Diagnostic
    ] = []

    execution_evidence = (
        build_execution_model_evidence_from_run(
            run_path,
            history_path=history_file,
        )
    )

    execution_model = (
        detect_execution_model(
            execution_evidence
        )
    )

    if execution_model.submit_host:
        submit_host = (
            execution_model.submit_host
        )

        if submit_host in locations:
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.INCONSISTENT,
                    ReasonCode.SCOPE_MISMATCH,
                    (
                        "Submit host and scientific "
                        "worker resolve to the same "
                        "canonical location."
                    ),
                    context={
                        "location_id": (
                            submit_host
                        )
                    },
                )
            )
        else:
            locations[
                submit_host
            ] = Location(
                location_id=submit_host,
                location_type=(
                    LocationType.SUBMIT_HOST
                ),
                raw_values=[
                    submit_host
                ],
                provenance=list(
                    execution_model.provenance
                ),
            )

    if not execution_model.supported:
        for reason in (
            execution_model
            .unsupported_reasons
        ):
            diagnostics.append(
                _diagnostic(
                    AnalysisStatus.UNSUPPORTED,
                    reason,
                    (
                        "Execution model is outside "
                        "the supported v1 adapter."
                    ),
                    provenance=(
                        execution_model
                        .provenance
                    ),
                )
            )

        return RunExecution(
            run_id=run_id,
            run_path=str(run_path),
            workflow_name=workflow_name,
            pattern_context=pattern_context,
            experiment_parameters=(
                experiment_parameters
            ),
            tasks={},
            scientific_files={},
            locations=locations,
            execution_model=(
                execution_model
            ),
            manifests=[],
            evidence=[],
            verifications=[],
            required_movements=[],
            declared_movements=[],
            metric_result=None,
            diagnostics=diagnostics,
            provenance=list(
                execution_model.provenance
            ),
        )

    # In supported condorio v1, the Pegasus local/access
    # point corresponds to the confirmed submit host.
    site_location_map: dict[
        str,
        str,
    ] = {}

    final_destination = None

    if execution_model.submit_host:
        site_location_map[
            "local"
        ] = execution_model.submit_host

        final_destination = (
            execution_model.submit_host
        )

    dataflow = (
        build_scientific_dataflow(
            workflow_path,
            submits=submits,
            site_location_map=(
                site_location_map
            ),
            final_destination_location_id=(
                final_destination
            ),
            meta_paths=[
                *sources.meta_files,
                *sources.cache_meta_files,
            ],
        )
    )

    diagnostics.extend(
        dataflow.diagnostics
    )

    tasks, task_diagnostics = (
        _task_executions(
            parsed_history,
            scientific_task_ids=(
                dataflow.task_ids
            ),
        )
    )

    diagnostics.extend(
        task_diagnostics
    )

    if _blocking(diagnostics):
        return RunExecution(
            run_id=run_id,
            run_path=str(run_path),
            workflow_name=workflow_name,
            pattern_context=pattern_context,
            experiment_parameters=(
                experiment_parameters
            ),
            tasks=tasks,
            scientific_files=(
                dataflow.scientific_files
            ),
            locations=locations,
            execution_model=execution_model,
            manifests=[],
            evidence=[],
            verifications=[],
            required_movements=[],
            declared_movements=[],
            metric_result=None,
            diagnostics=diagnostics,
            provenance=list(
                execution_model.provenance
            ),
        )

    required = (
        build_required_movements(
            dataflow.scientific_files.values(),
            tasks.values(),
        )
    )

    diagnostics.extend(
        required.diagnostics
    )

    if _blocking(diagnostics):
        return RunExecution(
            run_id=run_id,
            run_path=str(run_path),
            workflow_name=workflow_name,
            pattern_context=pattern_context,
            experiment_parameters=(
                experiment_parameters
            ),
            tasks=tasks,
            scientific_files=(
                dataflow.scientific_files
            ),
            locations=locations,
            execution_model=execution_model,
            manifests=[],
            evidence=[],
            verifications=[],
            required_movements=(
                required.records
            ),
            declared_movements=[],
            metric_result=None,
            diagnostics=diagnostics,
            provenance=list(
                execution_model.provenance
            ),
        )

    manifest_result = (
        build_condorio_manifests(
            submits=submits,
            task_executions=(
                tasks.values()
            ),
            scientific_files=(
                dataflow
                .scientific_files
                .values()
            ),
            execution_model=(
                execution_model
            ),
            attempt_context_by_job_id=(
                _attempt_contexts(
                    tasks
                )
            ),
        )
    )

    diagnostics.extend(
        manifest_result.diagnostics
    )

    declared_result = (
        build_declared_movements(
            manifests=(
                manifest_result.manifests
            ),
            task_executions=(
                tasks.values()
            ),
            execution_model=(
                execution_model
            ),
        )
    )

    diagnostics.extend(
        declared_result.diagnostics
    )

    if _blocking(diagnostics):
        return RunExecution(
            run_id=run_id,
            run_path=str(run_path),
            workflow_name=workflow_name,
            pattern_context=pattern_context,
            experiment_parameters=(
                experiment_parameters
            ),
            tasks=tasks,
            scientific_files=(
                dataflow.scientific_files
            ),
            locations=locations,
            execution_model=execution_model,
            manifests=(
                manifest_result.manifests
            ),
            evidence=[],
            verifications=[],
            required_movements=(
                required.records
            ),
            declared_movements=(
                declared_result
                .records
            ),
            metric_result=None,
            diagnostics=diagnostics,
            provenance=list(
                execution_model.provenance
            ),
        )

    scientific_job_ids = {
        task.job_id
        for task in tasks.values()
        if task.job_id is not None
    }

    evidence = (
        build_transfer_evidence(
            parsed_history,
            scientific_job_ids=(
                scientific_job_ids
            ),
        )
    )

    reconciled = (
        reconcile_movements(
            manifests=(
                manifest_result.manifests
            ),
            evidence=evidence,
            declared_movements=(
                declared_result
                .records
            ),
        )
    )

    diagnostics.extend(
        reconciled.diagnostics
    )

    metric = calculate_metrics(
        required_movements=(
            required.records
        ),
        declared_movements=(
            reconciled
            .declared_movements
        ),
    )

    return RunExecution(
        run_id=run_id,
        run_path=str(run_path),
        workflow_name=workflow_name,
        pattern_context=pattern_context,
        experiment_parameters=(
            experiment_parameters
        ),
        tasks=tasks,
        scientific_files=(
            dataflow.scientific_files
        ),
        locations=locations,
        execution_model=execution_model,
        manifests=(
            manifest_result.manifests
        ),
        evidence=evidence,
        verifications=(
            reconciled.verifications
        ),
        required_movements=(
            required.records
        ),
        declared_movements=(
            reconciled.declared_movements
        ),
        metric_result=metric,
        diagnostics=diagnostics,
        provenance=list(
            execution_model.provenance
        ),
    )
