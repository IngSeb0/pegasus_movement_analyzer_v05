import json
import os
import tempfile
import unittest
from pathlib import Path

from pegasus_movement.analyzer_v1 import (
    analyze_run_v1,
    overall_status,
)
from pegasus_movement.diagnostics import (
    AnalysisStatus,
)
from pegasus_movement.model import (
    EvidenceLevel,
    ReconciliationMode,
)
from pegasus_movement.reporting import (
    write_reports,
)


ROOT = Path(__file__).resolve().parents[2]

EXPERIMENTS = Path(
    os.environ.get(
        "PEGASUS_EXPERIMENTS_ROOT",
        str(
            Path.home()
            / "pegasus-lab"
            / "pegasus_avance_semana_1_6"
            / "experiments"
        ),
    )
)

CASES = json.loads(
    (
        ROOT
        / "fixtures"
        / "audited"
        / "integration_runs.json"
    ).read_text(
        encoding="utf-8"
    )
)


@unittest.skipUnless(
    os.environ.get(
        "PEGASUS_RUN_INTEGRATION"
    ) == "1",
    (
        "Set PEGASUS_RUN_INTEGRATION=1 "
        "to run preserved-run integration."
    ),
)
class PreservedRunIntegrationTests(
    unittest.TestCase
):
    def test_audited_real_runs(self):
        for name, expected in (
            CASES.items()
        ):
            with self.subTest(
                case=name
            ):
                run_path = (
                    EXPERIMENTS
                    / expected["run_rel"]
                )

                history_path = (
                    ROOT
                    / "fixtures"
                    / "audited"
                    / "history"
                    / expected["history"]
                )

                self.assertTrue(
                    run_path.is_dir(),
                    run_path,
                )

                self.assertTrue(
                    history_path.is_file(),
                    history_path,
                )

                run = analyze_run_v1(
                    run_path,
                    history_file=(
                        history_path
                    ),
                )

                self.assertEqual(
                    overall_status(run),
                    AnalysisStatus.VALID,
                )

                self.assertEqual(
                    len(run.tasks),
                    expected[
                        "scientific_tasks"
                    ],
                )

                self.assertEqual(
                    len(run.verifications),
                    expected[
                        "verifications"
                    ],
                )

                self.assertTrue(
                    all(
                        item.confirmed
                        for item
                        in run.verifications
                    )
                )

                self.assertTrue(
                    all(
                        item.level
                        == EvidenceLevel
                        .JOB_LEVEL_RECONCILED
                        for item
                        in run.verifications
                    )
                )

                expected_mode = (
                    ReconciliationMode[
                        expected[
                            "reconciliation_mode"
                        ]
                    ]
                )

                self.assertTrue(
                    all(
                        item.reconciliation_mode
                        == expected_mode
                        for item
                        in run.verifications
                    )
                )

                metric = run.metric_result

                self.assertIsNotNone(
                    metric
                )

                self.assertEqual(
                    metric.required_movement_bytes,
                    expected[
                        "required_movement_bytes"
                    ],
                )

                self.assertEqual(
                    metric.declared_movement_bytes,
                    expected[
                        "declared_movement_bytes"
                    ],
                )

                self.assertEqual(
                    metric.observed_movement_bytes,
                    expected[
                        "observed_movement_bytes"
                    ],
                )

                self.assertEqual(
                    metric.coverage,
                    expected["coverage"],
                )

                self.assertAlmostEqual(
                    metric.dme,
                    expected["dme"],
                    places=12,
                )

                with (
                    tempfile.TemporaryDirectory()
                ) as td:
                    write_reports(
                        run,
                        td,
                        verifications=(
                            run.verifications
                        ),
                        diagnostics=(
                            run.diagnostics
                        ),
                        analyzer_version=(
                            "integration-test"
                        ),
                    )

                    payload = json.loads(
                        (
                            Path(td)
                            / "analysis.json"
                        ).read_text(
                            encoding="utf-8"
                        )
                    )

                    self.assertEqual(
                        payload[
                            "metrics"
                        ][
                            "required_movement_bytes"
                        ],
                        expected[
                            "required_movement_bytes"
                        ],
                    )

                    self.assertEqual(
                        payload[
                            "metrics"
                        ][
                            "observed_movement_bytes"
                        ],
                        expected[
                            "observed_movement_bytes"
                        ],
                    )


if __name__ == "__main__":
    unittest.main()
