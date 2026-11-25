from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from .diagnostics import (
    AnalysisStatus,
    Diagnostic,
    ReasonCode,
)
from .model import (
    DeclaredMovementRecord,
    EvidenceLevel,
    FileClassification,
    JobTransferManifest,
    MovementVerification,
    ReconciliationMode,
    TransferDirection,
    TransferEvidence,
)


@dataclass(slots=True)
class ReconciliationResult:
    verifications: list[MovementVerification] = field(
        default_factory=list
    )
    declared_movements: list[
        DeclaredMovementRecord
    ] = field(default_factory=list)
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


def _verification(
    *,
    manifest: JobTransferManifest,
    evidence: TransferEvidence | None,
    level: EvidenceLevel,
    mode: ReconciliationMode | None,
    confirmed: bool,
    reason: ReasonCode | None,
    observed_count: int | None = None,
    observed_bytes: int | None = None,
    unexplained_bytes: int | None = None,
    confirmed_ids: list[str] | None = None,
) -> MovementVerification:
    return MovementVerification(
        job_id=manifest.job_id,
        direction=manifest.direction,
        attempt_context=(
            evidence.attempt_context
            if evidence is not None
            else manifest.attempt_context
        ),
        level=level,
        reconciliation_mode=mode,
        confirmed=confirmed,
        reason_code=reason,
        expected_file_count=(
            manifest.expected_file_count
        ),
        observed_file_count=observed_count,
        expected_total_bytes=(
            manifest.expected_total_bytes
        ),
        observed_total_bytes=observed_bytes,
        unexplained_bytes=unexplained_bytes,
        confirmed_scientific_file_ids=(
            confirmed_ids or []
        ),
        provenance=(
            list(evidence.provenance)
            if evidence is not None
            else []
        ),
    )


def _status_for_reason(
    reason: ReasonCode,
) -> AnalysisStatus:
    if reason == ReasonCode.UNACCOUNTED_PROTOCOL:
        return AnalysisStatus.UNSUPPORTED

    if reason == ReasonCode.FAILED_SCIENTIFIC_JOB:
        return AnalysisStatus.FAILED_WORKFLOW

    return AnalysisStatus.INCOMPLETE_EVIDENCE


def _failed(
    *,
    manifest: JobTransferManifest,
    evidence: TransferEvidence | None,
    reason: ReasonCode,
    message: str,
    context: dict | None = None,
    observed_count: int | None = None,
    observed_bytes: int | None = None,
    unexplained_bytes: int | None = None,
) -> tuple[MovementVerification, Diagnostic]:
    verification = _verification(
        manifest=manifest,
        evidence=evidence,
        level=EvidenceLevel.INSUFFICIENT,
        mode=None,
        confirmed=False,
        reason=reason,
        observed_count=observed_count,
        observed_bytes=observed_bytes,
        unexplained_bytes=unexplained_bytes,
    )

    diagnostic = _diagnostic(
        _status_for_reason(reason),
        reason,
        message,
        context=context,
    )

    return verification, diagnostic


def _scientific_file_ids(
    manifest: JobTransferManifest,
) -> list[str]:
    return sorted(
        {
            item.logical_file_id
            for item in manifest.files
            if (
                item.classification
                == FileClassification.SCIENTIFIC
                and item.logical_file_id
                is not None
            )
        }
    )


def _scientific_sizes_known(
    manifest: JobTransferManifest,
) -> bool:
    return all(
        item.size_bytes is not None
        for item in manifest.files
        if (
            item.classification
            == FileClassification.SCIENTIFIC
        )
    )


def _execution_successful(
    evidence: TransferEvidence,
) -> bool:
    stats = evidence.raw_stats

    if stats.get("job_status") != 4:
        return False

    if stats.get("exit_code") != 0:
        return False

    exit_by_signal = stats.get(
        "exit_by_signal"
    )

    if (
        exit_by_signal is not None
        and str(exit_by_signal)
        .strip()
        .lower()
        not in {"false", "0"}
    ):
        return False

    hold_reason = stats.get(
        "hold_reason"
    )

    if (
        hold_reason is not None
        and str(hold_reason).strip()
    ):
        return False

    return True


def _select_evidence(
    manifest: JobTransferManifest,
    candidates: list[TransferEvidence],
) -> tuple[
    TransferEvidence | None,
    ReasonCode | None,
]:
    matching = [
        item
        for item in candidates
        if (
            item.job_id == manifest.job_id
            and item.direction
            == manifest.direction
        )
    ]

    if manifest.attempt_context is not None:
        exact = [
            item
            for item in matching
            if item.attempt_context
            == manifest.attempt_context
        ]

        if len(exact) == 1:
            return exact[0], None

        if len(exact) > 1:
            return (
                None,
                ReasonCode.RETRY_NOT_SEPARABLE,
            )

    if len(matching) == 1:
        return matching[0], None

    if not matching:
        return (
            None,
            ReasonCode.HISTORY_MISSING,
        )

    return (
        None,
        ReasonCode.RETRY_NOT_SEPARABLE,
    )


def reconcile_manifest(
    manifest: JobTransferManifest,
    evidence: TransferEvidence,
) -> tuple[
    MovementVerification,
    Diagnostic | None,
]:
    """
    Reconcile one (job, direction, attempt) sandbox.

    This confirms occurrence of scientific files only when the
    complete manifest can be tied to successful HTCondor evidence.
    It never allocates aggregate bytes proportionally.
    """

    observed_count = (
        evidence.observed_file_count_last
    )
    observed_bytes = (
        evidence.observed_bytes_last
    )

    # --------------------------------------------------------
    # ATTEMPT SEPARABILITY
    # --------------------------------------------------------

    if evidence.attempt_context is None:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.RETRY_NOT_SEPARABLE,
            message=(
                "Transfer evidence cannot be attributed "
                "to one exact execution attempt."
            ),
            context={
                "job_id": manifest.job_id,
                "direction": (
                    manifest.direction.value
                ),
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if (
        manifest.attempt_context is not None
        and manifest.attempt_context
        != evidence.attempt_context
    ):
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.RETRY_NOT_SEPARABLE,
            message=(
                "Manifest and transfer evidence refer "
                "to different attempt contexts."
            ),
            context={
                "job_id": manifest.job_id,
                "manifest_attempt": (
                    manifest.attempt_context
                ),
                "evidence_attempt": (
                    evidence.attempt_context
                ),
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    # --------------------------------------------------------
    # WORKER / PROTOCOL / JOB SUCCESS
    # --------------------------------------------------------

    if evidence.worker_location_id is None:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.MISSING_PLACEMENT,
            message=(
                "Transfer evidence has no worker "
                "location."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    unsupported_methods = [
        method
        for method in evidence.methods
        if method.lower() != "cedar"
    ]

    if unsupported_methods:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.UNACCOUNTED_PROTOCOL,
            message=(
                "Transfer evidence contains a protocol "
                "not accounted for by the v1 adapter."
            ),
            context={
                "job_id": manifest.job_id,
                "methods": evidence.methods,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if not evidence.methods:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.PARTIAL_TRANSFER,
            message=(
                "No protocol-specific transfer "
                "statistics are available."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if not _execution_successful(
        evidence
    ):
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.FAILED_SCIENTIFIC_JOB,
            message=(
                "Scientific job did not finish in a "
                "successful state."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    # --------------------------------------------------------
    # MANIFEST
    # --------------------------------------------------------

    if not manifest.complete:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.MANIFEST_INCOMPLETE,
            message=(
                "Effective sandbox file-set is not "
                "known completely."
            ),
            context={
                "job_id": manifest.job_id,
                "direction": (
                    manifest.direction.value
                ),
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if manifest.expected_file_count is None:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.MANIFEST_INCOMPLETE,
            message=(
                "Manifest has no expected file count."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if observed_count is None:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.PARTIAL_TRANSFER,
            message=(
                "HTCondor evidence has no observed "
                "file count for this attempt."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_bytes=observed_bytes,
        )

    if (
        observed_count
        != manifest.expected_file_count
    ):
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.TRANSFER_COUNT_MISMATCH,
            message=(
                "Observed sandbox file count does not "
                "match the effective manifest."
            ),
            context={
                "job_id": manifest.job_id,
                "expected": (
                    manifest.expected_file_count
                ),
                "observed": observed_count,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if not _scientific_sizes_known(
        manifest
    ):
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.MISSING_FILE_SIZE,
            message=(
                "At least one scientific manifest "
                "file has no authoritative size."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    if observed_bytes is None:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.PARTIAL_TRANSFER,
            message=(
                "HTCondor evidence has no observed "
                "sandbox bytes for this attempt."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
        )

    scientific_ids = (
        _scientific_file_ids(
            manifest
        )
    )

    scientific_total = (
        manifest.scientific_total_bytes
    )

    if scientific_total is None:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.MISSING_FILE_SIZE,
            message=(
                "Scientific payload total cannot be "
                "constructed."
            ),
            context={
                "job_id": manifest.job_id,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    # --------------------------------------------------------
    # MODE A — EXACT_BYTES
    # --------------------------------------------------------

    if manifest.expected_total_bytes is not None:
        if (
            observed_bytes
            != manifest.expected_total_bytes
        ):
            return _failed(
                manifest=manifest,
                evidence=evidence,
                reason=ReasonCode.TRANSFER_BYTES_MISMATCH,
                message=(
                    "Observed sandbox bytes do not "
                    "match the fully-sized manifest."
                ),
                context={
                    "job_id": manifest.job_id,
                    "expected": (
                        manifest.expected_total_bytes
                    ),
                    "observed": observed_bytes,
                },
                observed_count=observed_count,
                observed_bytes=observed_bytes,
                unexplained_bytes=(
                    observed_bytes
                    - manifest.expected_total_bytes
                ),
            )

        return (
            _verification(
                manifest=manifest,
                evidence=evidence,
                level=(
                    EvidenceLevel
                    .JOB_LEVEL_RECONCILED
                ),
                mode=(
                    ReconciliationMode
                    .EXACT_BYTES
                ),
                confirmed=True,
                reason=None,
                observed_count=observed_count,
                observed_bytes=observed_bytes,
                unexplained_bytes=0,
                confirmed_ids=scientific_ids,
            ),
            None,
        )

    # --------------------------------------------------------
    # MODE B — SUCCESSFUL_MANIFEST
    # --------------------------------------------------------

    if observed_bytes < scientific_total:
        return _failed(
            manifest=manifest,
            evidence=evidence,
            reason=ReasonCode.TRANSFER_BYTES_MISMATCH,
            message=(
                "Observed sandbox bytes are smaller "
                "than the authoritative scientific "
                "payload contained in the manifest."
            ),
            context={
                "job_id": manifest.job_id,
                "scientific_total": (
                    scientific_total
                ),
                "observed": observed_bytes,
            },
            observed_count=observed_count,
            observed_bytes=observed_bytes,
        )

    return (
        _verification(
            manifest=manifest,
            evidence=evidence,
            level=(
                EvidenceLevel
                .JOB_LEVEL_RECONCILED
            ),
            mode=(
                ReconciliationMode
                .SUCCESSFUL_MANIFEST
            ),
            confirmed=True,
            reason=None,
            observed_count=observed_count,
            observed_bytes=observed_bytes,
            unexplained_bytes=None,
            confirmed_ids=scientific_ids,
        ),
        None,
    )


def reconcile_movements(
    *,
    manifests: Iterable[
        JobTransferManifest
    ],
    evidence: Iterable[
        TransferEvidence
    ],
    declared_movements: Iterable[
        DeclaredMovementRecord
    ],
) -> ReconciliationResult:
    manifests = list(manifests)
    evidence = list(evidence)
    declared = list(declared_movements)

    verifications: list[
        MovementVerification
    ] = []

    diagnostics: list[Diagnostic] = []

    verification_by_key: dict[
        tuple[str, TransferDirection],
        MovementVerification,
    ] = {}

    for manifest in manifests:
        selected, selection_reason = (
            _select_evidence(
                manifest,
                evidence,
            )
        )

        if selected is None:
            reason = (
                selection_reason
                or ReasonCode.HISTORY_MISSING
            )

            verification, diagnostic = (
                _failed(
                    manifest=manifest,
                    evidence=None,
                    reason=reason,
                    message=(
                        "No unique transfer evidence "
                        "can be matched to this manifest."
                    ),
                    context={
                        "job_id": (
                            manifest.job_id
                        ),
                        "direction": (
                            manifest
                            .direction
                            .value
                        ),
                    },
                )
            )

        else:
            (
                verification,
                diagnostic,
            ) = reconcile_manifest(
                manifest,
                selected,
            )

        verifications.append(
            verification
        )

        verification_by_key[
            (
                manifest.job_id,
                manifest.direction,
            )
        ] = verification

        if diagnostic is not None:
            diagnostics.append(
                diagnostic
            )

    updated_declared: list[
        DeclaredMovementRecord
    ] = []

    for record in declared:
        verification = (
            verification_by_key.get(
                (
                    record.job_id,
                    record.direction,
                )
            )
        )

        if verification is None:
            updated_declared.append(
                replace(
                    record,
                    verification_level=(
                        EvidenceLevel
                        .INSUFFICIENT
                    ),
                    confirmed=False,
                    verification_reason=(
                        ReasonCode
                        .HISTORY_MISSING
                    ),
                )
            )
            continue

        is_confirmed_file = (
            verification.confirmed
            and record.file_id
            in verification
            .confirmed_scientific_file_ids
        )

        updated_declared.append(
            replace(
                record,
                attempt_context=(
                    record.attempt_context
                    or verification
                    .attempt_context
                ),
                verification_level=(
                    verification.level
                ),
                confirmed=(
                    is_confirmed_file
                ),
                verification_reason=(
                    None
                    if is_confirmed_file
                    else verification
                    .reason_code
                ),
            )
        )

    return ReconciliationResult(
        verifications=verifications,
        declared_movements=(
            updated_declared
        ),
        diagnostics=diagnostics,
    )
