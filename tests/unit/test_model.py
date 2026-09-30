import unittest

from pegasus_movement.diagnostics import (
    AnalysisStatus,
    MetricStatus,
    ReasonCode,
    aggregate_analysis_status,
)
from pegasus_movement.model import (
    EvidenceLevel,
    FileRole,
    Location,
    LocationType,
    MetricResult,
    ScientificFile,
)


class DomainModelTests(unittest.TestCase):
    def test_scientific_file_supports_multiple_roles(self):
        f = ScientificFile(
            file_id="stage1",
            logical_name="stage1.dat",
            roles={FileRole.INTERMEDIATE, FileRole.FINAL_OUTPUT},
            size_bytes=1024,
            producer_task_id="T1",
            consumer_task_ids=["T2"],
            final_destination_ids=["pegasus-master"],
        )

        self.assertIn(FileRole.INTERMEDIATE, f.roles)
        self.assertIn(FileRole.FINAL_OUTPUT, f.roles)

    def test_zero_byte_scientific_file_is_valid(self):
        f = ScientificFile(
            file_id="empty",
            logical_name="empty.dat",
            roles={FileRole.EXTERNAL_INPUT},
            size_bytes=0,
            origin_location_id="external",
        )

        self.assertEqual(f.size_bytes, 0)

    def test_negative_file_size_is_rejected(self):
        with self.assertRaises(ValueError):
            ScientificFile(
                file_id="bad",
                logical_name="bad.dat",
                roles={FileRole.EXTERNAL_INPUT},
                size_bytes=-1,
            )

    def test_location_has_canonical_identity(self):
        loc = Location(
            location_id="pegasus-worker1",
            location_type=LocationType.WORKER,
            raw_values=[
                "slot1@pegasus-worker1",
                "pegasus-worker1",
            ],
        )

        self.assertEqual(loc.location_id, "pegasus-worker1")
        self.assertEqual(loc.location_type, LocationType.WORKER)

    def test_metric_result_rejects_invalid_coverage(self):
        with self.assertRaises(ValueError):
            MetricResult(coverage=1.01)

    def test_metric_result_allows_indeterminate_values(self):
        result = MetricResult(
            required_movement_bytes=10,
            declared_movement_bytes=20,
            observed_movement_bytes=None,
            coverage=0.5,
            byte_coverage=0.5,
            dme=None,
            analysis_status=AnalysisStatus.INCOMPLETE_EVIDENCE,
            metric_status=MetricStatus.INDETERMINATE,
            validation_reasons=[ReasonCode.MANIFEST_INCOMPLETE],
            evidence_levels=[EvidenceLevel.INSUFFICIENT],
        )

        self.assertIsNone(result.observed_movement_bytes)
        self.assertIsNone(result.dme)

    def test_analysis_status_precedence(self):
        status = aggregate_analysis_status(
            [
                AnalysisStatus.VALID,
                AnalysisStatus.INCOMPLETE_EVIDENCE,
                AnalysisStatus.INCONSISTENT,
            ]
        )

        self.assertEqual(status, AnalysisStatus.INCONSISTENT)


if __name__ == "__main__":
    unittest.main()

from pegasus_movement.diagnostics import Diagnostic
from pegasus_movement.model import (
    DeclaredMovementRecord,
    JobTransferManifest,
    RequiredMovementRecord,
    RequiredReason,
    TaskExecution,
    TransferDirection,
)


class DomainModelValidationTests(unittest.TestCase):
    def test_task_execution_rejects_negative_run_count(self):
        with self.assertRaises(ValueError):
            TaskExecution(
                task_id="T1",
                pegasus_node_id="data_task_ID0000001",
                job_run_count=-1,
            )

    def test_manifest_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            JobTransferManifest(
                job_id="100.0",
                direction=TransferDirection.INPUT,
                attempt_context="attempt-1",
                expected_file_count=-1,
            )

    def test_required_movement_rejects_negative_bytes(self):
        with self.assertRaises(ValueError):
            RequiredMovementRecord(
                file_id="f1",
                from_location_id="pegasus-master",
                to_location_id="pegasus-worker1",
                size_bytes=1024,
                required_bytes=-1,
                reason=RequiredReason.INPUT,
            )

    def test_declared_movement_rejects_negative_bytes(self):
        with self.assertRaises(ValueError):
            DeclaredMovementRecord(
                movement_id="m1",
                job_id="100.0",
                attempt_context="attempt-1",
                file_id="f1",
                direction=TransferDirection.INPUT,
                from_location_id="pegasus-master",
                to_location_id="pegasus-worker1",
                size_bytes=-1,
            )

    def test_diagnostic_keeps_reason_and_context(self):
        d = Diagnostic(
            status=AnalysisStatus.INCOMPLETE_EVIDENCE,
            reason_code=ReasonCode.HISTORY_MISSING,
            message="HTCondor history snapshot is missing",
            context={"job_id": "100.0"},
        )

        self.assertEqual(d.reason_code, ReasonCode.HISTORY_MISSING)
        self.assertEqual(d.context["job_id"], "100.0")

    def test_empty_status_list_is_valid(self):
        self.assertEqual(
            aggregate_analysis_status([]),
            AnalysisStatus.VALID,
        )
