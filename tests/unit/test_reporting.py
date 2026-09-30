import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pegasus_movement.diagnostics import (
    AnalysisStatus,
    MetricStatus,
    ReasonCode,
)
from pegasus_movement.model import (
    EvidenceLevel,
    MetricResult,
)
from pegasus_movement.reporting import (
    exit_code_for_status,
    write_reports,
)


def run_fixture():
    metric = MetricResult(
        required_movement_bytes=30,
        declared_movement_bytes=60,
        observed_movement_bytes=60,
        coverage=1.0,
        byte_coverage=1.0,
        dme=0.5,
        observed_minus_required_bytes=30,
        analysis_status=AnalysisStatus.VALID,
        metric_status=MetricStatus.CALCULATED,
        validation_reasons=[],
        evidence_levels=[
            EvidenceLevel.JOB_LEVEL_RECONCILED
        ],
    )

    return SimpleNamespace(
        run_id="run-test",
        run_path="/tmp/run-test",
        workflow_name="wf",
        pattern_context=None,
        experiment_parameters={},
        tasks={},
        scientific_files={},
        locations={},
        execution_model=None,
        manifests=[],
        evidence=[],
        required_movements=[],
        declared_movements=[],
        metric_result=metric,
        provenance=[],
    )


class ReportingTests(unittest.TestCase):
    def test_writes_all_canonical_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            created = write_reports(
                run_fixture(),
                td,
            )

            names = {
                path.name
                for path in created
            }

            self.assertEqual(
                names,
                {
                    "analysis.json",
                    "scientific_files.tsv",
                    "task_placement.tsv",
                    "required_movement.tsv",
                    "declared_movement.tsv",
                    "transfer_evidence.tsv",
                    "summary.tsv",
                    "REPORT.txt",
                },
            )

    def test_analysis_json_uses_null_not_nan(self):
        with tempfile.TemporaryDirectory() as td:
            run = run_fixture()

            run.metric_result = MetricResult(
                required_movement_bytes=0,
                declared_movement_bytes=0,
                observed_movement_bytes=0,
                coverage=1.0,
                byte_coverage=None,
                dme=None,
                observed_minus_required_bytes=0,
                analysis_status=(
                    AnalysisStatus.NOT_APPLICABLE
                ),
                metric_status=(
                    MetricStatus.NOT_APPLICABLE
                ),
                validation_reasons=[
                    ReasonCode.ZERO_MOVEMENT
                ],
                evidence_levels=[],
            )

            write_reports(
                run,
                td,
            )

            raw = (
                Path(td)
                / "analysis.json"
            ).read_text(
                encoding="utf-8"
            )

            self.assertNotIn(
                "NaN",
                raw,
            )

            payload = json.loads(raw)

            self.assertIsNone(
                payload[
                    "metrics"
                ]["dme"]
            )
            self.assertIsNone(
                payload[
                    "metrics"
                ]["byte_coverage"]
            )

    def test_summary_tsv_matches_metric(self):
        with tempfile.TemporaryDirectory() as td:
            write_reports(
                run_fixture(),
                td,
            )

            with (
                Path(td)
                / "summary.tsv"
            ).open(
                encoding="utf-8"
            ) as handle:
                row = next(
                    csv.DictReader(
                        handle,
                        delimiter="\t",
                    )
                )

            self.assertEqual(
                row["RequiredMovement"],
                "30",
            )
            self.assertEqual(
                row["ObservedMovement"],
                "60",
            )
            self.assertEqual(
                row["DME"],
                "0.5",
            )
            self.assertEqual(
                row["status"],
                "VALID",
            )

    def test_exit_codes_follow_design(self):
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.VALID
            ),
            0,
        )
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.NOT_APPLICABLE
            ),
            0,
        )
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.INCOMPLETE_EVIDENCE
            ),
            2,
        )
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.UNSUPPORTED
            ),
            3,
        )
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.INCONSISTENT
            ),
            4,
        )
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.FAILED_WORKFLOW
            ),
            4,
        )
        self.assertEqual(
            exit_code_for_status(
                AnalysisStatus.ERROR
            ),
            5,
        )


if __name__ == "__main__":
    unittest.main()
