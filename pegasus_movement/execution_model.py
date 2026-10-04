from __future__ import annotations

from dataclasses import dataclass, field
import re
import json
from pathlib import Path

from .diagnostics import ReasonCode
from .model import ExecutionModelProfile, ProvenanceRef
from .pegasus_source import ParsedSubmitFile, parse_submit_file


CONDORIO_ADAPTER_NAME = "CondorIOStandardAdapter"


@dataclass(slots=True)
class ExecutionModelEvidence:
    """
    Evidence already extracted from Pegasus/HTCondor sources.

    None means "not established by available evidence", never False.

    `plugin_methods_known` exists because an empty list can mean either:
      - confirmed no transfer plugins, or
      - plugin information was not available.
    """

    pegasus_version: str | None = None
    htcondor_version: str | None = None

    data_configuration: str | None = None
    universe: str | None = None

    submit_host: str | None = None

    should_transfer_files: str | None = None
    when_to_transfer_output: str | None = None

    bypass_enabled: bool | None = None

    plugin_methods: list[str] = field(default_factory=list)
    plugin_methods_known: bool = False

    clustered_jobs: bool | None = None
    shared_filesystem: bool | None = None

    provenance: list[ProvenanceRef] = field(default_factory=list)

    # Fields for which available sources disagree.
    conflicting_fields: list[str] = field(default_factory=list)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip().strip('"').strip()

    return cleaned or None


def _append_once(
    reasons: list[ReasonCode],
    reason: ReasonCode,
) -> None:
    if reason not in reasons:
        reasons.append(reason)


def detect_execution_model(
    evidence: ExecutionModelEvidence,
) -> ExecutionModelProfile:
    """
    Assess whether the supplied evidence proves support for the v1
    CondorIO execution model.

    The function is deliberately fail-closed:
      - missing critical evidence => unsupported;
      - conflicting/out-of-scope evidence => unsupported;
      - no defaults are invented.

    This function does not construct transfer manifests and does not
    calculate movement.
    """

    pegasus_version = _clean(evidence.pegasus_version)
    htcondor_version = _clean(evidence.htcondor_version)

    reasons: list[ReasonCode] = []

    if evidence.conflicting_fields:
        _append_once(
            reasons,
            ReasonCode.CONFLICTING_EXECUTION_MODEL_EVIDENCE,
        )

    data_configuration = _clean(
        evidence.data_configuration
    )
    universe = _clean(evidence.universe)

    submit_host = _clean(evidence.submit_host)

    if submit_host is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )

    should_transfer_files = _clean(
        evidence.should_transfer_files
    )
    when_to_transfer_output = _clean(
        evidence.when_to_transfer_output
    )

    plugin_methods = sorted({
        method.strip()
        for method in evidence.plugin_methods
        if method.strip()
    })

    # --------------------------------------------------------------
    # Version scope
    # --------------------------------------------------------------

    if pegasus_version is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif not pegasus_version.startswith("5."):
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_PEGASUS_VERSION,
        )

    # HTCondor version is preserved for reproducibility. The current
    # design does not yet define a generic version rejection rule here.
    if htcondor_version is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )

    # --------------------------------------------------------------
    # Pegasus data configuration
    # --------------------------------------------------------------

    if data_configuration is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif data_configuration.lower() != "condorio":
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_DATA_CONFIGURATION,
        )

    # --------------------------------------------------------------
    # HTCondor universe
    # --------------------------------------------------------------

    if universe is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif universe.lower() != "vanilla":
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_UNIVERSE,
        )

    # --------------------------------------------------------------
    # HTCondor-managed file transfer
    # --------------------------------------------------------------

    if should_transfer_files is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif should_transfer_files.upper() not in {
        "YES",
        "IF_NEEDED",
    }:
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_FILE_TRANSFER,
        )

    if when_to_transfer_output is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif when_to_transfer_output.upper() != "ON_EXIT":
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_WHEN_TO_TRANSFER_OUTPUT,
        )

    # --------------------------------------------------------------
    # sharedfs / bypass / plugins / clustering
    # --------------------------------------------------------------

    if evidence.shared_filesystem is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif evidence.shared_filesystem:
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_SHARED_FS,
        )

    if evidence.bypass_enabled is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif evidence.bypass_enabled:
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_BYPASS,
        )

    if not evidence.plugin_methods_known:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif plugin_methods:
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_TRANSFER_PLUGIN,
        )

    if evidence.clustered_jobs is None:
        _append_once(
            reasons,
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
        )
    elif evidence.clustered_jobs:
        _append_once(
            reasons,
            ReasonCode.UNSUPPORTED_CLUSTERED_JOB,
        )

    supported = not reasons

    return ExecutionModelProfile(
        pegasus_version=pegasus_version,
        htcondor_version=htcondor_version,
        data_configuration=data_configuration,
        universe=universe,
        submit_host=submit_host,
        should_transfer_files=should_transfer_files,
        when_to_transfer_output=when_to_transfer_output,
        bypass_enabled=evidence.bypass_enabled,
        plugin_methods=plugin_methods,
        clustered_jobs=evidence.clustered_jobs,
        shared_filesystem=evidence.shared_filesystem,
        adapter_name=(
            CONDORIO_ADAPTER_NAME
            if supported
            else None
        ),
        supported=supported,
        unsupported_reasons=reasons,
        provenance=list(evidence.provenance),
    )



# ---------------------------------------------------------------------------
# Evidence builder from Pegasus compute-job submit files
# ---------------------------------------------------------------------------

_URI_SCHEME_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9+.-]*)://"
)


PEGASUS_COMPUTE_JOB_CLASS = "1"


def is_pegasus_compute_submit(
    submit: ParsedSubmitFile,
) -> bool:
    """
    Identify a Pegasus compute job from generated ClassAds.

    We deliberately do not use filenames.

    For the supported Pegasus 5.x execution model:
      - pegasus_job_class == 1 identifies a compute job;
      - pegasus_wf_dax_job_id must identify a real workflow job;
      - literal null-like DAX ids are auxiliary/generated jobs.
    """

    job_class_attr = submit.get_last(
        "+pegasus_job_class"
    )
    dax_job_attr = submit.get_last(
        "+pegasus_wf_dax_job_id"
    )

    if job_class_attr is None or dax_job_attr is None:
        return False

    job_class = _clean(job_class_attr.raw_value)
    dax_job_id = _clean(dax_job_attr.raw_value)

    if job_class != PEGASUS_COMPUTE_JOB_CLASS:
        return False

    if dax_job_id is None:
        return False

    if dax_job_id.lower() in {
        "null",
        "none",
    }:
        return False

    return True


def _collect_submit_scalar(
    submits: list[ParsedSubmitFile],
    key: str,
) -> tuple[str | None, list[ProvenanceRef], bool]:
    """
    Return one value only when every selected submit provides an
    unambiguous and identical value.

    Returns:
        value
        provenance
        conflict
    """

    provenance: list[ProvenanceRef] = []
    run_values: set[str] = set()

    if not submits:
        return None, provenance, False

    for submit in submits:
        attrs = submit.get_all(key)

        if not attrs:
            # Evidence is incomplete across the selected compute jobs.
            return None, provenance, False

        local_values: set[str] = set()

        for attr in attrs:
            provenance.append(attr.provenance)

            value = _clean(attr.raw_value)

            if value is not None:
                local_values.add(value)

        if len(local_values) != 1:
            return None, provenance, True

        run_values.update(local_values)

    if len(run_values) != 1:
        return None, provenance, True

    return next(iter(run_values)), provenance, False


def _parse_positive_int(
    value: str | None,
) -> int | None:
    if value is None:
        return None

    cleaned = _clean(value)

    if cleaned is None or not cleaned.isdigit():
        return None

    parsed = int(cleaned)

    if parsed < 1:
        return None

    return parsed


def _merge_scalar_evidence(
    explicit_value: str | None,
    derived_value: str | None,
    field_name: str,
    conflicts: list[str],
) -> str | None:
    """
    Merge explicit evidence with submit-derived evidence.

    Explicit does not silently override contradictory generated
    evidence: disagreement is retained as a conflict.
    """

    explicit = _clean(explicit_value)
    derived = _clean(derived_value)

    if explicit is not None and derived is not None:
        if explicit.lower() != derived.lower():
            if field_name not in conflicts:
                conflicts.append(field_name)
            return None

    return explicit if explicit is not None else derived


def _submit_declared_protocols(
    submits: list[ParsedSubmitFile],
) -> tuple[list[str], list[ProvenanceRef]]:
    """
    Detect protocol/plugin signals visible in generated compute submits.

    This does not infer network traffic. It only preserves explicit
    transfer_plugins declarations and non-file URI schemes appearing
    in transfer-related submit attributes.
    """

    methods: set[str] = set()
    provenance: list[ProvenanceRef] = []

    for submit in submits:
        for attr in submit.get_all("transfer_plugins"):
            provenance.append(attr.provenance)

            value = _clean(attr.raw_value)

            if value:
                methods.add(value)

        for key in (
            "transfer_input_files",
            "transfer_output_files",
            "transfer_output_remaps",
        ):
            for attr in submit.get_all(key):
                provenance.append(attr.provenance)

                for scheme in _URI_SCHEME_RE.findall(
                    attr.raw_value
                ):
                    normalized = scheme.lower()

                    # file:// is not treated as an external protocol
                    # plugin signal here.
                    if normalized != "file":
                        methods.add(normalized)

    return sorted(methods), provenance


def build_execution_model_evidence_from_submits(
    submits: list[ParsedSubmitFile],
    *,
    explicit: ExecutionModelEvidence | None = None,
) -> ExecutionModelEvidence:
    """
    Build the submit-derived portion of execution-model evidence.

    Only Pegasus compute jobs are considered. Auxiliary jobs such as
    stage-in, cleanup, registration and DAGMan do not participate in
    the compute execution-model consensus.

    Fields not provable from submit files remain None.
    """

    base = explicit or ExecutionModelEvidence()

    compute_submits = [
        submit
        for submit in submits
        if is_pegasus_compute_submit(submit)
    ]

    conflicts = list(base.conflicting_fields)
    provenance = list(base.provenance)

    pegasus_version, prov, conflict = _collect_submit_scalar(
        compute_submits,
        "+pegasus_version",
    )
    provenance.extend(prov)

    if conflict and "pegasus_version" not in conflicts:
        conflicts.append("pegasus_version")

    universe, prov, conflict = _collect_submit_scalar(
        compute_submits,
        "universe",
    )
    provenance.extend(prov)

    if conflict and "universe" not in conflicts:
        conflicts.append("universe")

    should_transfer_files, prov, conflict = _collect_submit_scalar(
        compute_submits,
        "should_transfer_files",
    )
    provenance.extend(prov)

    if (
        conflict
        and "should_transfer_files" not in conflicts
    ):
        conflicts.append("should_transfer_files")

    when_to_transfer_output, prov, conflict = _collect_submit_scalar(
        compute_submits,
        "when_to_transfer_output",
    )
    provenance.extend(prov)

    if (
        conflict
        and "when_to_transfer_output" not in conflicts
    ):
        conflicts.append("when_to_transfer_output")

    cluster_size_raw, prov, cluster_conflict = (
        _collect_submit_scalar(
            compute_submits,
            "+pegasus_cluster_size",
        )
    )
    provenance.extend(prov)

    clustered_jobs: bool | None = None

    if cluster_conflict:
        if "clustered_jobs" not in conflicts:
            conflicts.append("clustered_jobs")
    else:
        cluster_size = _parse_positive_int(
            cluster_size_raw
        )

        if cluster_size is not None:
            clustered_jobs = cluster_size > 1

    protocol_methods, protocol_prov = (
        _submit_declared_protocols(compute_submits)
    )
    provenance.extend(protocol_prov)

    # Because every selected compute submit was inspected, the
    # submit-level protocol/plugin declaration state is known.
    plugin_methods_known = bool(compute_submits)

    merged_pegasus_version = _merge_scalar_evidence(
        base.pegasus_version,
        pegasus_version,
        "pegasus_version",
        conflicts,
    )

    merged_universe = _merge_scalar_evidence(
        base.universe,
        universe,
        "universe",
        conflicts,
    )

    merged_should_transfer = _merge_scalar_evidence(
        base.should_transfer_files,
        should_transfer_files,
        "should_transfer_files",
        conflicts,
    )

    merged_when_output = _merge_scalar_evidence(
        base.when_to_transfer_output,
        when_to_transfer_output,
        "when_to_transfer_output",
        conflicts,
    )

    if (
        base.clustered_jobs is not None
        and clustered_jobs is not None
        and base.clustered_jobs != clustered_jobs
    ):
        if "clustered_jobs" not in conflicts:
            conflicts.append("clustered_jobs")
        merged_clustered = None
    else:
        merged_clustered = (
            base.clustered_jobs
            if base.clustered_jobs is not None
            else clustered_jobs
        )

    merged_plugins = sorted(
        set(base.plugin_methods)
        | set(protocol_methods)
    )

    return ExecutionModelEvidence(
        pegasus_version=merged_pegasus_version,
        htcondor_version=base.htcondor_version,

        # Not inferred from absence of a property.
        data_configuration=base.data_configuration,

        universe=merged_universe,
        submit_host=base.submit_host,

        should_transfer_files=merged_should_transfer,
        when_to_transfer_output=merged_when_output,

        # Submit files alone do not prove these two properties.
        bypass_enabled=base.bypass_enabled,
        shared_filesystem=base.shared_filesystem,

        plugin_methods=merged_plugins,
        plugin_methods_known=(
            base.plugin_methods_known
            or plugin_methods_known
        ),

        clustered_jobs=merged_clustered,

        provenance=provenance,
        conflicting_fields=sorted(set(conflicts)),
    )



# ---------------------------------------------------------------------------
# I4D — Evidence extraction from preserved Pegasus/HTCondor artifacts
# ---------------------------------------------------------------------------

_CONDOR_VERSION_RE = re.compile(
    r'\$CondorVersion:\s+([^\s]+)'
)


def _artifact_provenance(
    path: Path,
    attribute: str,
    *,
    source_kind: str = "config",
    notes: str | None = None,
) -> ProvenanceRef:
    return ProvenanceRef(
        source_kind=source_kind,
        source_path=str(path),
        attribute=attribute,
        notes=notes,
    )


def _parse_bool_scalar(value: str) -> bool | None:
    cleaned = value.strip().strip('"').strip("'").lower()

    if cleaned == "true":
        return True

    if cleaned == "false":
        return False

    return None


def _yaml_scalar_values(
    path: Path,
    key: str,
) -> tuple[list[str], list[ProvenanceRef]]:
    values: list[str] = []
    provenance: list[ProvenanceRef] = []

    if not path.exists():
        return values, provenance

    pattern = re.compile(
        rf"^\s*{re.escape(key)}\s*:\s*(.*?)\s*$",
        re.IGNORECASE,
    )

    for line_number, raw in enumerate(
        path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines(),
        start=1,
    ):
        match = pattern.match(raw)

        if not match:
            continue

        value = match.group(1)

        # Strip simple trailing YAML comment.
        value = value.split(" #", 1)[0].strip()

        values.append(value)

        provenance.append(
            _artifact_provenance(
                path,
                key,
                notes=f"line={line_number}",
            )
        )

    return values, provenance


def _properties_values(
    paths: list[Path],
    key: str,
) -> tuple[list[str], list[ProvenanceRef]]:
    values: list[str] = []
    provenance: list[ProvenanceRef] = []

    for path in paths:
        if not path.exists():
            continue

        for line_number, raw in enumerate(
            path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines(),
            start=1,
        ):
            stripped = raw.strip()

            if (
                not stripped
                or stripped.startswith("#")
                or "=" not in stripped
            ):
                continue

            raw_key, raw_value = stripped.split("=", 1)

            if raw_key.strip() != key:
                continue

            values.append(raw_value.strip())

            provenance.append(
                _artifact_provenance(
                    path,
                    key,
                    notes=f"line={line_number}",
                )
            )

    return values, provenance


def _unique_clean_values(
    values: list[str],
) -> tuple[str | None, bool]:
    cleaned = {
        value.strip().strip('"').strip("'")
        for value in values
        if value.strip()
    }

    if not cleaned:
        return None, False

    if len(cleaned) != 1:
        return None, True

    return next(iter(cleaned)), False


def _extract_data_configuration(
    run_dir: Path,
) -> tuple[str | None, list[ProvenanceRef], bool]:
    metrics_files = sorted(run_dir.glob("*.metrics"))

    values: list[str] = []
    provenance: list[ProvenanceRef] = []

    for path in metrics_files:
        try:
            raw = json.loads(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
        except (OSError, json.JSONDecodeError):
            continue

        value = raw.get("data_config")

        if value is None:
            continue

        values.append(str(value))

        provenance.append(
            _artifact_provenance(
                path,
                "data_config",
            )
        )

    value, conflict = _unique_clean_values(values)

    return value, provenance, conflict


def _extract_submit_host(
    run_dir: Path,
) -> tuple[str | None, list[ProvenanceRef], bool]:
    candidates = [
        run_dir / "braindump.yml",
        run_dir / "braindump.yaml",
    ]

    values: list[str] = []
    provenance: list[ProvenanceRef] = []

    for path in candidates:
        vals, prov = _yaml_scalar_values(
            path,
            "submit_hostname",
        )
        values.extend(vals)
        provenance.extend(prov)

    value, conflict = _unique_clean_values(values)

    return value, provenance, conflict


def _extract_shared_filesystem(
    run_dir: Path,
) -> tuple[
    bool | None,
    list[ProvenanceRef],
    bool,
]:
    workflow = run_dir / "workflow.yml"

    values, provenance = _yaml_scalar_values(
        workflow,
        "sharedFileSystem",
    )

    parsed = [
        _parse_bool_scalar(value)
        for value in values
    ]

    parsed = [
        value
        for value in parsed
        if value is not None
    ]

    if not parsed:
        return None, provenance, False

    unique = set(parsed)

    if len(unique) != 1:
        return None, provenance, True

    return next(iter(unique)), provenance, False


def _extract_htcondor_version(
    history_path: Path | None,
) -> tuple[
    str | None,
    list[ProvenanceRef],
    bool,
]:
    if history_path is None or not history_path.exists():
        return None, [], False

    versions: set[str] = set()
    provenance: list[ProvenanceRef] = []

    for line_number, raw in enumerate(
        history_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines(),
        start=1,
    ):
        if not (
            raw.startswith("CondorVersion")
            or raw.startswith("SubmitVersion")
        ):
            continue

        match = _CONDOR_VERSION_RE.search(raw)

        if not match:
            continue

        versions.add(match.group(1))

        provenance.append(
            _artifact_provenance(
                history_path,
                "CondorVersion",
                source_kind="history",
                notes=f"line={line_number}",
            )
        )

    if not versions:
        return None, provenance, False

    if len(versions) != 1:
        return None, provenance, True

    return next(iter(versions)), provenance, False


def _extract_bypass_state(
    run_dir: Path,
    pegasus_version: str | None,
) -> tuple[
    bool | None,
    list[ProvenanceRef],
    bool,
]:
    """
    Establish whether bypass input staging is enabled.

    Evidence precedence:
      1. explicit Pegasus runtime property;
      2. explicit per-file workflow `bypass`;
      3. for Pegasus 5.x only, documented default False when neither
         enabling mechanism appears in the preserved complete inputs.

    The default-derived case is explicitly recorded as derived
    provenance instead of being a silent assumption.
    """

    properties = sorted(
        run_dir.glob("pegasus.*.properties")
    )

    prop_values, provenance = _properties_values(
        properties,
        "pegasus.transfer.bypass.input.staging",
    )

    parsed_props = [
        _parse_bool_scalar(value)
        for value in prop_values
    ]

    if any(value is True for value in parsed_props):
        return True, provenance, False

    workflow = run_dir / "workflow.yml"

    workflow_values, workflow_prov = _yaml_scalar_values(
        workflow,
        "bypass",
    )

    provenance.extend(workflow_prov)

    parsed_workflow = [
        _parse_bool_scalar(value)
        for value in workflow_values
    ]

    if any(value is True for value in parsed_workflow):
        return True, provenance, False

    explicit_values = [
        value
        for value in parsed_props + parsed_workflow
        if value is not None
    ]

    if explicit_values:
        if len(set(explicit_values)) != 1:
            return None, provenance, True

        return explicit_values[0], provenance, False

    # Pegasus 5.x documentation defines the global bypass property
    # default as false. Per-file bypass is also explicit.
    if (
        pegasus_version is not None
        and pegasus_version.startswith("5.")
        and workflow.exists()
        and properties
    ):
        provenance.append(
            ProvenanceRef(
                source_kind="derived",
                source_path=str(run_dir),
                attribute=(
                    "pegasus.transfer."
                    "bypass.input.staging"
                ),
                notes=(
                    "Pegasus 5.x documented default=false; "
                    "no enabling runtime property or per-file "
                    "bypass declaration found in preserved "
                    "workflow/config artifacts"
                ),
            )
        )

        return False, provenance, False

    return None, provenance, False


def build_execution_model_evidence_from_run(
    run_dir: str | Path,
    *,
    history_path: str | Path | None = None,
) -> ExecutionModelEvidence:
    """
    Build v1 execution-model evidence from one preserved Pegasus run.

    This function does not calculate movement. It only integrates
    execution-model facts required to decide whether the run is
    supported by CondorIOStandardAdapter.
    """

    run = Path(run_dir).expanduser().resolve()

    history = (
        Path(history_path).expanduser().resolve()
        if history_path is not None
        else None
    )

    submits = [
        parse_submit_file(path)
        for path in sorted(run.rglob("*.sub"))
    ]

    # First extract Pegasus version and submit semantics.
    submit_evidence = (
        build_execution_model_evidence_from_submits(
            submits
        )
    )

    provenance: list[ProvenanceRef] = []
    conflicts: list[str] = []

    data_configuration, prov, conflict = (
        _extract_data_configuration(run)
    )
    provenance.extend(prov)

    if conflict:
        conflicts.append("data_configuration")

    submit_host, prov, conflict = _extract_submit_host(
        run
    )
    provenance.extend(prov)

    if conflict:
        conflicts.append("submit_host")

    shared_filesystem, prov, conflict = (
        _extract_shared_filesystem(run)
    )
    provenance.extend(prov)

    if conflict:
        conflicts.append("shared_filesystem")

    htcondor_version, prov, conflict = (
        _extract_htcondor_version(history)
    )
    provenance.extend(prov)

    if conflict:
        conflicts.append("htcondor_version")

    bypass_enabled, prov, conflict = (
        _extract_bypass_state(
            run,
            submit_evidence.pegasus_version,
        )
    )
    provenance.extend(prov)

    if conflict:
        conflicts.append("bypass_enabled")

    explicit = ExecutionModelEvidence(
        htcondor_version=htcondor_version,
        data_configuration=data_configuration,
        submit_host=submit_host,
        bypass_enabled=bypass_enabled,
        shared_filesystem=shared_filesystem,
        provenance=provenance,
        conflicting_fields=conflicts,
    )

    return build_execution_model_evidence_from_submits(
        submits,
        explicit=explicit,
    )
