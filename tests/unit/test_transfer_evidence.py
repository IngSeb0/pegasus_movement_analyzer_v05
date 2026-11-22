import tempfile
import unittest
from pathlib import Path

from pegasus_movement.htcondor_source import (
    build_transfer_evidence,
    parse_history_file,
)
from pegasus_movement.model import (
    TransferDirection,
)


class TransferEvidenceTests(unittest.TestCase):
    def make_history(self, root: Path):
        path = root / "history.long"

        path.write_text(
            """
ClusterId = 100
ProcId = 0
JobStatus = 4
ExitCode = 0
JobRunCount = 1
NumJobStarts = 1
NumShadowStarts = 1
LastRemoteHost = "slot1@pegasus-worker1"
BytesRecvd = 28813811.0
BytesSent = 10491967.0
TransferInputStats = [ CedarSizeBytesTotal = 28813811; CedarFilesCountTotal = 7; CedarSizeBytesLastRun = 28813811; CedarFilesCountLastRun = 7 ]
TransferOutputStats = [ CedarSizeBytesTotal = 10491967; CedarFilesCountTotal = 3; CedarSizeBytesLastRun = 10491967; CedarFilesCountLastRun = 3 ]

ClusterId = 999
ProcId = 0
JobStatus = 4
JobRunCount = 1
NumJobStarts = 1
TransferInputStats = [ CedarSizeBytesTotal = 1; CedarFilesCountTotal = 1; CedarSizeBytesLastRun = 1; CedarFilesCountLastRun = 1 ]
""".lstrip(),
            encoding="utf-8",
        )

        return path

    def test_builds_two_directions_for_scientific_job(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            parsed = parse_history_file(
                self.make_history(root)
            )

            evidence = (
                build_transfer_evidence(
                    parsed,
                    scientific_job_ids={
                        "100.0"
                    },
                )
            )

            self.assertEqual(
                len(evidence),
                2,
            )

            by_direction = {
                item.direction: item
                for item in evidence
            }

            input_ev = by_direction[
                TransferDirection.INPUT
            ]
            output_ev = by_direction[
                TransferDirection.OUTPUT
            ]

            self.assertEqual(
                input_ev.job_id,
                "100.0",
            )
            self.assertEqual(
                input_ev.worker_location_id,
                "pegasus-worker1",
            )
            self.assertEqual(
                input_ev.attempt_context,
                "attempt:1",
            )

            self.assertEqual(
                input_ev.methods,
                ["Cedar"],
            )
            self.assertEqual(
                input_ev.observed_file_count_last,
                7,
            )
            self.assertEqual(
                input_ev.observed_file_count_total,
                7,
            )
            self.assertEqual(
                input_ev.observed_bytes_last,
                28813811,
            )
            self.assertEqual(
                input_ev.observed_bytes_total,
                28813811,
            )

            self.assertEqual(
                output_ev.observed_file_count_last,
                3,
            )
            self.assertEqual(
                output_ev.observed_bytes_last,
                10491967,
            )

    def test_preserves_raw_protocol_stats(self):
        with tempfile.TemporaryDirectory() as td:
            parsed = parse_history_file(
                self.make_history(
                    Path(td)
                )
            )

            evidence = (
                build_transfer_evidence(
                    parsed,
                    scientific_job_ids={
                        "100.0"
                    },
                )
            )

            raw = evidence[
                0
            ].raw_stats[
                "transfer_stats_raw"
            ]

            self.assertIn(
                "CedarSizeBytesTotal",
                raw,
            )

            parsed_stats = evidence[
                0
            ].raw_stats[
                "transfer_stats_parsed"
            ]

            self.assertEqual(
                parsed_stats["Cedar"][
                    "FilesCountTotal"
                ],
                7,
            )

    def test_multiple_attempts_are_not_silently_collapsed(self):
        with tempfile.TemporaryDirectory() as td:
            path = (
                Path(td)
                / "history.long"
            )

            path.write_text(
                """
ClusterId = 200
ProcId = 0
JobStatus = 4
ExitCode = 0
JobRunCount = 2
NumJobStarts = 2
LastRemoteHost = "slot1@pegasus-worker1"
TransferInputStats = [ CedarSizeBytesTotal = 20; CedarFilesCountTotal = 2; CedarSizeBytesLastRun = 10; CedarFilesCountLastRun = 1 ]
TransferOutputStats = [ CedarSizeBytesTotal = 20; CedarFilesCountTotal = 2; CedarSizeBytesLastRun = 10; CedarFilesCountLastRun = 1 ]
""".lstrip(),
                encoding="utf-8",
            )

            evidence = (
                build_transfer_evidence(
                    parse_history_file(
                        path
                    ),
                    scientific_job_ids={
                        "200.0"
                    },
                )
            )

            self.assertIsNone(
                evidence[
                    0
                ].attempt_context
            )
            self.assertEqual(
                evidence[
                    0
                ].raw_stats[
                    "job_run_count"
                ],
                2,
            )


if __name__ == "__main__":
    unittest.main()
