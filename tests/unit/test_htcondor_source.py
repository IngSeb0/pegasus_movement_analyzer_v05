import tempfile
import unittest
from pathlib import Path

from pegasus_movement.htcondor_source import (
    ParsedHistoryFile,
    parse_history_file,
)
from pegasus_movement.model import SourceKind


class HTCondorHistoryParserTests(unittest.TestCase):
    def write_history(self, root: Path, text: str) -> Path:
        path = root / "history.long"
        path.write_text(text, encoding="utf-8")
        return path

    def real_fixture(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "distribution_real_reconstructed"
            / "trace"
            / "history.long"
        )

    def test_real_fixture_contains_five_records(self):
        parsed = parse_history_file(self.real_fixture())

        self.assertIsInstance(parsed, ParsedHistoryFile)
        self.assertEqual(len(parsed.records), 5)

    def test_real_fixture_preserves_job_and_host_values(self):
        parsed = parse_history_file(self.real_fixture())

        first = parsed.records[0]

        self.assertEqual(first.value("ClusterId"), "473")
        self.assertEqual(first.value("ProcId"), "0")
        self.assertEqual(
            first.value("DAGNodeName"),
            '"data_task_ID0000001"',
        )
        self.assertEqual(
            first.value("LastRemoteHost"),
            '"slot1_1@pegasus-worker2"',
        )

    def test_records_are_separated_by_blank_lines(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_history(
                Path(td),
                """
ClusterId = 10
ProcId = 0

ClusterId = 11
ProcId = 0
""".lstrip(),
            )

            parsed = parse_history_file(path)

            self.assertEqual(len(parsed.records), 2)
            self.assertEqual(
                parsed.records[0].value("ClusterId"),
                "10",
            )
            self.assertEqual(
                parsed.records[1].value("ClusterId"),
                "11",
            )

    def test_unknown_attributes_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_history(
                Path(td),
                """
ClusterId = 10
SomeFutureHTCondorAttribute = "preserve-me"
""".lstrip(),
            )

            parsed = parse_history_file(path)

            self.assertEqual(
                parsed.records[0].value(
                    "SomeFutureHTCondorAttribute"
                ),
                '"preserve-me"',
            )

    def test_duplicate_attributes_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_history(
                Path(td),
                """
ClusterId = 10
Example = 1
Example = 2
""".lstrip(),
            )

            parsed = parse_history_file(path)
            values = parsed.records[0].get_all("Example")

            self.assertEqual(len(values), 2)
            self.assertEqual(values[0].raw_value, "1")
            self.assertEqual(values[1].raw_value, "2")
            self.assertEqual(
                parsed.records[0].value("Example"),
                "2",
            )

    def test_multiline_nested_classad_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_history(
                Path(td),
                """
ClusterId = 10
TransferInputStats = [
    Cedar = [
        FilesCount = 3;
        TotalBytes = 10485760;
    ];
]
JobStatus = 4
""".lstrip(),
            )

            parsed = parse_history_file(path)

            self.assertEqual(len(parsed.records), 1)

            value = parsed.records[0].value(
                "TransferInputStats"
            )

            self.assertIsNotNone(value)
            self.assertIn("Cedar", value)
            self.assertIn("FilesCount = 3", value)
            self.assertIn("TotalBytes = 10485760", value)

            attr = parsed.records[0].get_last(
                "TransferInputStats"
            )

            self.assertIsNotNone(attr)
            self.assertGreater(attr.line_end, attr.line_start)

    def test_provenance_points_to_history_attribute(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_history(
                Path(td),
                "ClusterId = 99\n",
            )

            parsed = parse_history_file(path)
            attr = parsed.records[0].get_last("ClusterId")

            self.assertIsNotNone(attr)
            self.assertEqual(
                attr.provenance.source_kind,
                SourceKind.HISTORY,
            )
            self.assertEqual(
                attr.provenance.source_path,
                str(path.resolve()),
            )
            self.assertEqual(
                attr.provenance.attribute,
                "clusterid",
            )
            self.assertEqual(attr.line_start, 1)
            self.assertEqual(attr.line_end, 1)

    def test_missing_history_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.long"

            with self.assertRaises(FileNotFoundError):
                parse_history_file(missing)


if __name__ == "__main__":
    unittest.main()
