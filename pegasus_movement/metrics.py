from __future__ import annotations

from typing import Iterable

from .diagnostics import (
    AnalysisStatus,
    MetricStatus,
    ReasonCode,
)
from .model import (
    DeclaredMovementRecord,
    EvidenceLevel,
    MetricResult,
    RequiredMovementRecord,
)


def _unique_reasons(
    records: Iterable[DeclaredMovementRecord],
) -> list[ReasonCode]:
    result: list[ReasonCode] = []

    for record in records:
        reason = record.verification_reason

        if (
            reason is not None
            and reason not in result
        ):
            result.append(reason)

    return result


def _unique_levels(
    records: Iterable[DeclaredMovementRecord],
) -> list[EvidenceLevel]:
    result: list[EvidenceLevel] = []

    for record in records:
        level = record.verification_level

        if level not in result:
            result.append(level)

    return result


def _incomplete_status(
    reasons: list[ReasonCode],
) -> AnalysisStatus:
    if (
        ReasonCode.UNACCOUNTED_PROTOCOL
        in reasons
    ):
        return AnalysisStatus.UNSUPPORTED

    if (
        ReasonCode.FAILED_SCIENTIFIC_JOB
        in reasons
    ):
        return AnalysisStatus.FAILED_WORKFLOW

    return AnalysisStatus.INCOMPLETE_EVIDENCE


def calculate_metrics(
    *,
    required_movements: Iterable[
        RequiredMovementRecord
    ],
    declared_movements: Iterable[
        DeclaredMovementRecord
    ],
) -> MetricResult:
    """
    Calculate Coverage, ObservedMovement and DME.

    Important:
    - declared bytes are not observed bytes;
    - ObservedMovement exists only when Coverage == 1;
    - every calculation uses scientific payload bytes;
    - zero-byte movements still participate in Coverage count.
    """

    required = list(required_movements)
    declared = list(declared_movements)

    required_bytes = sum(
        record.required_bytes
        for record in required
    )

    declared_bytes = sum(
        record.size_bytes
        for record in declared
    )

    confirmed = [
        record
        for record in declared
        if record.confirmed
    ]

    confirmed_bytes = sum(
        record.size_bytes
        for record in confirmed
    )

    # Design convention: an empty declared set is fully covered.
    if declared:
        coverage = (
            len(confirmed)
            / len(declared)
        )
    else:
        coverage = 1.0

    # ByteCoverage is diagnostic only.
    if declared_bytes > 0:
        byte_coverage = (
            confirmed_bytes
            / declared_bytes
        )
    else:
        byte_coverage = None

    reasons = _unique_reasons(
        declared
    )

    levels = _unique_levels(
        declared
    )

    # --------------------------------------------------------
    # COVERAGE INCOMPLETE
    # --------------------------------------------------------

    if coverage < 1.0:
        return MetricResult(
            required_movement_bytes=(
                required_bytes
            ),
            declared_movement_bytes=(
                declared_bytes
            ),
            observed_movement_bytes=None,
            coverage=coverage,
            byte_coverage=byte_coverage,
            dme=None,
            observed_minus_required_bytes=None,
            analysis_status=(
                _incomplete_status(
                    reasons
                )
            ),
            metric_status=(
                MetricStatus.INDETERMINATE
            ),
            validation_reasons=reasons,
            evidence_levels=levels,
        )

    # --------------------------------------------------------
    # FULL COVERAGE
    # --------------------------------------------------------

    observed_bytes = confirmed_bytes

    observed_minus_required = (
        observed_bytes
        - required_bytes
    )

    # RM = 0, OM = 0
    if (
        required_bytes == 0
        and observed_bytes == 0
    ):
        if (
            ReasonCode.ZERO_MOVEMENT
            not in reasons
        ):
            reasons.append(
                ReasonCode.ZERO_MOVEMENT
            )

        return MetricResult(
            required_movement_bytes=0,
            declared_movement_bytes=(
                declared_bytes
            ),
            observed_movement_bytes=0,
            coverage=coverage,
            byte_coverage=byte_coverage,
            dme=None,
            observed_minus_required_bytes=0,
            analysis_status=(
                AnalysisStatus.NOT_APPLICABLE
            ),
            metric_status=(
                MetricStatus.NOT_APPLICABLE
            ),
            validation_reasons=reasons,
            evidence_levels=levels,
        )

    # RM > 0, OM = 0 or generally OM < RM.
    if observed_bytes < required_bytes:
        if (
            ReasonCode.OBSERVED_LT_REQUIRED
            not in reasons
        ):
            reasons.append(
                ReasonCode.OBSERVED_LT_REQUIRED
            )

        return MetricResult(
            required_movement_bytes=(
                required_bytes
            ),
            declared_movement_bytes=(
                declared_bytes
            ),
            observed_movement_bytes=(
                observed_bytes
            ),
            coverage=coverage,
            byte_coverage=byte_coverage,
            dme=None,
            observed_minus_required_bytes=(
                observed_minus_required
            ),
            analysis_status=(
                AnalysisStatus.INCONSISTENT
            ),
            metric_status=(
                MetricStatus.INVALID
            ),
            validation_reasons=reasons,
            evidence_levels=levels,
        )

    # RM = 0, OM > 0
    if required_bytes == 0:
        dme = 0.0

    else:
        dme = (
            required_bytes
            / observed_bytes
        )

    return MetricResult(
        required_movement_bytes=(
            required_bytes
        ),
        declared_movement_bytes=(
            declared_bytes
        ),
        observed_movement_bytes=(
            observed_bytes
        ),
        coverage=coverage,
        byte_coverage=byte_coverage,
        dme=dme,
        observed_minus_required_bytes=(
            observed_minus_required
        ),
        analysis_status=(
            AnalysisStatus.VALID
        ),
        metric_status=(
            MetricStatus.CALCULATED
        ),
        validation_reasons=reasons,
        evidence_levels=levels,
    )
