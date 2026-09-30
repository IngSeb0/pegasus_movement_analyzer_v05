import tempfile
import unittest
from pathlib import Path

from pegasus_movement.model import SourceKind
from pegasus_movement.pegasus_source import (
    ParsedSubmitFile,
    load_run_sources,
    parse_submit_file,
    parse_submit_files,
)


class SubmitParserTests(unittest.TestCase):
    def write_submit(self, root: Path, text: str) -> Path:
        path = root / "job.sub"
        path.write_text(text, encoding="utf-8")
        return path

    def test_parse_attribute_and_preserve_raw_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_submit(
                root,
                """
# comment
Transfer_Input_Files = $(wf_submit_dir)/inputs/input.dat,data_task
transfer_output_files = results/stage1.dat
queue
""",
            )

            parsed = parse_submit_file(path)

            self.assertIsInstance(parsed, ParsedSubmitFile)

            attr = parsed.get_last("transfer_input_files")

            self.assertIsNotNone(attr)
            self.assertEqual(attr.key, "transfer_input_files")
            self.assertEqual(attr.raw_key, "Transfer_Input_Files")
            self.assertEqual(
                attr.raw_value,
                "$(wf_submit_dir)/inputs/input.dat,data_task",
            )

            # Critical v1 rule: do not collapse paths to basename.
            self.assertIn(
                "$(wf_submit_dir)/inputs/input.dat",
                attr.raw_value,
            )

    def test_non_assignment_directive_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_submit(
                root,
                "universe = vanilla\nqueue 1\n",
            )

            parsed = parse_submit_file(path)

            self.assertEqual(len(parsed.directives), 1)
            self.assertEqual(parsed.directives[0].text, "queue 1")

    def test_duplicate_attributes_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_submit(
                root,
                """
request_memory = 1024
request_memory = 2048
""",
            )

            parsed = parse_submit_file(path)

            values = parsed.get_all("request_memory")

            self.assertEqual(len(values), 2)
            self.assertEqual(values[0].raw_value, "1024")
            self.assertEqual(values[1].raw_value, "2048")
            self.assertEqual(
                parsed.value("request_memory"),
                "2048",
            )

    def test_backslash_continuation_is_joined(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_submit(
                root,
                "transfer_input_files = a.dat, \\\n"
                "    b.dat, \\\n"
                "    c.dat\n",
            )

            parsed = parse_submit_file(path)

            value = parsed.value("transfer_input_files")

            self.assertEqual(
                value,
                "a.dat, b.dat, c.dat",
            )

    def test_provenance_points_to_submit_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_submit(
                root,
                "universe = vanilla\n",
            )

            parsed = parse_submit_file(path)
            attr = parsed.get_last("universe")

            self.assertIsNotNone(attr)
            self.assertEqual(
                attr.provenance.source_kind,
                SourceKind.SUBMIT,
            )
            self.assertEqual(
                attr.provenance.source_path,
                str(path.resolve()),
            )
            self.assertEqual(
                attr.provenance.attribute,
                "universe",
            )

    def test_existing_fixture_submit_files_are_parseable(self):
        fixture = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "distribution_real_reconstructed"
            / "run0001"
        )

        sources = load_run_sources(fixture)
        parsed = parse_submit_files(sources.submit_files)

        self.assertEqual(len(parsed), 5)
        self.assertTrue(
            all(len(item.attributes) > 0 for item in parsed)
        )


if __name__ == "__main__":
    unittest.main()
