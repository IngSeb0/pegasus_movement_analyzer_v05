from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from .diagnostics import (
    AnalysisStatus,
    Diagnostic,
    MetricStatus,
    ReasonCode,
)


class SourceKind(StrEnum):
    SUBMIT = "submit"
    META = "meta"
    HISTORY = "history"
    EVENT_LOG = "event_log"
    PHYSICAL_FILE = "physical_file"
    CONFIG = "config"
    DERIVED = "derived"


class LocationType(StrEnum):
    SUBMIT_HOST = "submit_host"
    WORKER = "worker"
    EXTERNAL_SITE = "external_site"
    FINAL_SITE = "final_site"


class FileRole(StrEnum):
    EXTERNAL_INPUT = "external_input"
    INTERMEDIATE = "intermediate"
    FINAL_OUTPUT = "final_output"


class TransferDirection(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


class FileClassification(StrEnum):
    SCIENTIFIC = "scientific"
    AUXILIARY = "auxiliary"


class EvidenceLevel(StrEnum):
    FILE_LEVEL_CONFIRMED = "FILE_LEVEL_CONFIRMED"
    JOB_LEVEL_RECONCILED = "JOB_LEVEL_RECONCILED"
    INSUFFICIENT = "INSUFFICIENT"


class ReconciliationMode(StrEnum):
    EXACT_BYTES = "EXACT_BYTES"
    SUCCESSFUL_MANIFEST = "SUCCESSFUL_MANIFEST"


class RequiredReason(StrEnum):
    INPUT = "input"
    CONSUMER = "consumer"
    FINAL_DESTINATION = "final_destination"


@dataclass(slots=True)
class ProvenanceRef:
    source_kind: SourceKind
    source_path: str
    attribute: str | None = None
    source_hash: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class Location:
    location_id: str
    location_type: LocationType
    raw_values: list[str] = field(default_factory=list)
    provenance: list[ProvenanceRef] = field(default_factory=list)


@dataclass(slots=True)
class TaskExecution:
    task_id: str
    pegasus_node_id: str
    job_id: str | None = None
    worker_location_id: str | None = None
    job_status: int | None = None
    exit_code: int | None = None
    job_run_count: int | None = None
    num_job_starts: int | None = None
    successful: bool | None = None
    provenance: list[ProvenanceRef] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.job_run_count is not None and self.job_run_count < 0:
            raise ValueError("job_run_count must be >= 0")
        if self.num_job_starts is not None and self.num_job_starts < 0:
            raise ValueError("num_job_starts must be >= 0")


@dataclass(slots=True)
class ScientificFile:
    file_id: str
    logical_name: str
    physical_refs: list[str] = field(default_factory=list)
    roles: set[FileRole] = field(default_factory=set)
    size_bytes: int | None = None
    size_provenance: list[ProvenanceRef] = field(default_factory=list)
    producer_task_id: str | None = None
    consumer_task_ids: list[str] = field(default_factory=list)
    origin_location_id: str | None = None
    final_destination_ids: list[str] = field(default_factory=list)
    identity_provenance: list[ProvenanceRef] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")


@dataclass(slots=True)
class ManifestFile:
    job_id: str
    direction: TransferDirection
    logical_file_id: str | None
    physical_path: str
    basename: str
    classification: FileClassification
    size_bytes: int | None = None
    size_provenance: list[ProvenanceRef] = field(default_factory=list)
    protocol: str | None = None
    remap_from: str | None = None
    remap_to: str | None = None

    def __post_init__(self) -> None:
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")


@dataclass(slots=True)
class JobTransferManifest:
    job_id: str
    direction: TransferDirection
    attempt_context: str | None
    files: list[ManifestFile] = field(default_factory=list)
    expected_file_count: int | None = None
    expected_total_bytes: int | None = None
    scientific_file_count: int | None = None
    scientific_total_bytes: int | None = None
    complete: bool = False

    def __post_init__(self) -> None:
        for name in (
            "expected_file_count",
            "expected_total_bytes",
            "scientific_file_count",
            "scientific_total_bytes",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0")


@dataclass(slots=True)
class TransferEvidence:
    job_id: str
    direction: TransferDirection
    attempt_context: str | None
    worker_location_id: str | None
    raw_stats: dict[str, Any] = field(default_factory=dict)
    methods: list[str] = field(default_factory=list)
    observed_file_count_last: int | None = None
    observed_file_count_total: int | None = None
    observed_bytes_last: int | None = None
    observed_bytes_total: int | None = None
    bytes_recvd: int | None = None
    bytes_sent: int | None = None
    transfer_started: str | None = None
    transfer_finished: str | None = None
    provenance: list[ProvenanceRef] = field(default_factory=list)


@dataclass(slots=True)
class MovementVerification:
    job_id: str
    direction: TransferDirection
    attempt_context: str | None
    level: EvidenceLevel
    reconciliation_mode: ReconciliationMode | None
    confirmed: bool
    reason_code: ReasonCode | None = None
    expected_file_count: int | None = None
    observed_file_count: int | None = None
    expected_total_bytes: int | None = None
    observed_total_bytes: int | None = None
    unexplained_bytes: int | None = None
    confirmed_scientific_file_ids: list[str] = field(default_factory=list)
    provenance: list[ProvenanceRef] = field(default_factory=list)


@dataclass(slots=True)
class RequiredMovementRecord:
    file_id: str
    from_location_id: str
    to_location_id: str
    size_bytes: int
    required_bytes: int
    reason: RequiredReason

    def __post_init__(self) -> None:
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")
        if self.required_bytes < 0:
            raise ValueError("required_bytes must be >= 0")


@dataclass(slots=True)
class DeclaredMovementRecord:
    movement_id: str
    job_id: str
    attempt_context: str | None
    file_id: str
    direction: TransferDirection
    from_location_id: str
    to_location_id: str
    size_bytes: int
    verification_level: EvidenceLevel = EvidenceLevel.INSUFFICIENT
    confirmed: bool = False
    verification_reason: ReasonCode | None = None

    def __post_init__(self) -> None:
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")


@dataclass(slots=True)
class ExecutionModelProfile:
    pegasus_version: str | None = None
    htcondor_version: str | None = None
    data_configuration: str | None = None
    universe: str | None = None
    submit_host: str | None = None
    should_transfer_files: str | None = None
    when_to_transfer_output: str | None = None
    bypass_enabled: bool | None = None
    plugin_methods: list[str] = field(default_factory=list)
    clustered_jobs: bool | None = None
    shared_filesystem: bool | None = None
    adapter_name: str | None = None
    supported: bool = False
    unsupported_reasons: list[ReasonCode] = field(default_factory=list)
    provenance: list[ProvenanceRef] = field(default_factory=list)


@dataclass(slots=True)
class MetricResult:
    required_movement_bytes: int = 0
    declared_movement_bytes: int = 0
    observed_movement_bytes: int | None = None
    coverage: float | None = None
    byte_coverage: float | None = None
    dme: float | None = None
    observed_minus_required_bytes: int | None = None
    analysis_status: AnalysisStatus = AnalysisStatus.VALID
    metric_status: MetricStatus = MetricStatus.INDETERMINATE
    validation_reasons: list[ReasonCode] = field(default_factory=list)
    evidence_levels: list[EvidenceLevel] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.required_movement_bytes < 0:
            raise ValueError("required_movement_bytes must be >= 0")
        if self.declared_movement_bytes < 0:
            raise ValueError("declared_movement_bytes must be >= 0")
        if (
            self.observed_movement_bytes is not None
            and self.observed_movement_bytes < 0
        ):
            raise ValueError("observed_movement_bytes must be >= 0")

        for name in ("coverage", "byte_coverage", "dme"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(slots=True)
class RunExecution:
    run_id: str
    run_path: str
    workflow_name: str | None = None
    pattern_context: str | None = None
    experiment_parameters: dict[str, Any] = field(default_factory=dict)

    tasks: dict[str, TaskExecution] = field(default_factory=dict)
    scientific_files: dict[str, ScientificFile] = field(default_factory=dict)
    locations: dict[str, Location] = field(default_factory=dict)

    execution_model: ExecutionModelProfile | None = None

    manifests: list[JobTransferManifest] = field(default_factory=list)
    evidence: list[TransferEvidence] = field(default_factory=list)
    verifications: list[MovementVerification] = field(default_factory=list)

    required_movements: list[RequiredMovementRecord] = field(default_factory=list)
    declared_movements: list[DeclaredMovementRecord] = field(default_factory=list)

    metric_result: MetricResult | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    provenance: list[ProvenanceRef] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return Path(self.run_path)
