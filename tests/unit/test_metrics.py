import unittest

from pegasus_movement.diagnostics import (
    AnalysisStatus,
    MetricStatus,
    ReasonCode,
)
from pegasus_movement.metrics import (
    calculate_metrics,
)
from pegasus_movement.model import (
    DeclaredMovementRecord,
    EvidenceLevel,
    RequiredMovementRecord,
    RequiredReason,
    TransferDirection,
)


def required(
    movement_id: str,
    size: int,
):
    return RequiredMovementRecord(
        file_id=movement_id,
        from_location_id="A",
        to_location_id="B",
        size_bytes=size,
        required_bytes=size,
        reason=RequiredReason.CONSUMER,
    )


def declared(
    movement_id: str,
    size: int,
    *,
    confirmed: bool = True,
    reason=None,
):
    return DeclaredMovementRecord(
        movement_id=movement_id,
        job_id="10.0",
        attempt_context="attempt:1",
        file_id=movement_id,
        direction=TransferDirection.INPUT,
        from_location_id="submit",
        to_location_id="worker1",
        size_bytes=size,
        verification_level=(
            EvidenceLevel.JOB_LEVEL_RECONCILED
            if confirmed
            else EvidenceLevel.INSUFFICIENT
        ),
        confirmed=confirmed,
        verification_reason=reason,
    )


class MetricsTests(unittest.TestCase):
    def test_full_coverage_calculates_dme(self):
        result = calculate_metrics(
            required_movements=[
                required("f1", 30),
            ],
            declared_movements=[
                declared("f1", 60),
            ],
        )

        self.assertEqual(
            result.required_movement_bytes,
            30,
        )
        self.assertEqual(
            result.declared_movement_bytes,
            60,
        )
        self.assertEqual(
            result.observed_movement_bytes,
            60,
        )
        self.assertEqual(
            result.coverage,
            1.0,
        )
        self.assertEqual(
            result.byte_coverage,
            1.0,
        )
        self.assertEqual(
            result.dme,
            0.5,
        )
        self.assertEqual(
            result.observed_minus_required_bytes,
            30,
        )
        self.assertEqual(
            result.analysis_status,
            AnalysisStatus.VALID,
        )
        self.assertEqual(
            result.metric_status,
            MetricStatus.CALCULATED,
        )

    def test_partial_coverage_makes_observed_indeterminate(self):
        result = calculate_metrics(
            required_movements=[
                required("f1", 10),
            ],
            declared_movements=[
                declared(
                    "f1",
                    10,
                    confirmed=True,
                ),
                declared(
                    "f2",
                    10,
                    confirmed=False,
                    reason=(
                        ReasonCode
                        .MANIFEST_INCOMPLETE
                    ),
                ),
            ],
        )

        self.assertEqual(
            result.coverage,
            0.5,
        )
        self.assertEqual(
            result.byte_coverage,
            0.5,
        )
        self.assertIsNone(
            result.observed_movement_bytes
        )
        self.assertIsNone(
            result.dme
        )
        self.assertEqual(
            result.analysis_status,
            AnalysisStatus.INCOMPLETE_EVIDENCE,
        )
        self.assertEqual(
            result.metric_status,
            MetricStatus.INDETERMINATE,
        )

    def test_zero_zero_is_not_applicable(self):
        result = calculate_metrics(
            required_movements=[],
            declared_movements=[],
        )

        self.assertEqual(
            result.coverage,
            1.0,
        )
        self.assertIsNone(
            result.byte_coverage
        )
        self.assertEqual(
            result.observed_movement_bytes,
            0,
        )
        self.assertIsNone(
            result.dme
        )
        self.assertEqual(
            result.analysis_status,
            AnalysisStatus.NOT_APPLICABLE,
        )
        self.assertEqual(
            result.metric_status,
            MetricStatus.NOT_APPLICABLE,
        )
        self.assertIn(
            ReasonCode.ZERO_MOVEMENT,
            result.validation_reasons,
        )

    def test_required_zero_observed_positive_gives_zero_dme(self):
        result = calculate_metrics(
            required_movements=[],
            declared_movements=[
                declared("f1", 25),
            ],
        )

        self.assertEqual(
            result.dme,
            0.0,
        )
        self.assertEqual(
            result.analysis_status,
            AnalysisStatus.VALID,
        )

    def test_observed_less_than_required_is_invalid(self):
        result = calculate_metrics(
            required_movements=[
                required("f1", 100),
            ],
            declared_movements=[
                declared("f1", 80),
            ],
        )

        self.assertIsNone(
            result.dme
        )
        self.assertEqual(
            result.observed_minus_required_bytes,
            -20,
        )
        self.assertEqual(
            result.analysis_status,
            AnalysisStatus.INCONSISTENT,
        )
        self.assertEqual(
            result.metric_status,
            MetricStatus.INVALID,
        )
        self.assertIn(
            ReasonCode.OBSERVED_LT_REQUIRED,
            result.validation_reasons,
        )

    def test_zero_byte_movement_counts_for_coverage(self):
        result = calculate_metrics(
            required_movements=[],
            declared_movements=[
                declared(
                    "zero",
                    0,
                    confirmed=True,
                ),
            ],
        )

        self.assertEqual(
            result.coverage,
            1.0,
        )
        self.assertIsNone(
            result.byte_coverage
        )
        self.assertEqual(
            result.observed_movement_bytes,
            0,
        )

    def test_unsupported_evidence_propagates_status(self):
        result = calculate_metrics(
            required_movements=[
                required("f1", 10),
            ],
            declared_movements=[
                declared(
                    "f1",
                    10,
                    confirmed=False,
                    reason=(
                        ReasonCode
                        .UNACCOUNTED_PROTOCOL
                    ),
                ),
            ],
        )

        self.assertEqual(
            result.analysis_status,
            AnalysisStatus.UNSUPPORTED,
        )
        self.assertEqual(
            result.metric_status,
            MetricStatus.INDETERMINATE,
        )


if __name__ == "__main__":
    unittest.main()
