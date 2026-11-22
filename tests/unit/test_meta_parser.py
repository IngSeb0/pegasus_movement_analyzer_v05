import tempfile
import unittest
from pathlib import Path

from pegasus_movement.model import SourceKind
from pegasus_movement.pegasus_source import (
    load_run_sources,
    parse_meta_file,
    parse_meta_files,
)


class MetaParserTests(unittest.TestCase):
    def write_meta(
        self,
        root: Path,
        name: str,
        text: str,
    ) -> Path:
        path = root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_parse_single_object_and_size(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "job.meta",
                """
{
  "_id": "stage1.dat",
  "_attributes": {
    "size": "10485760",
    "checksum": "abc"
  }
}
""",
            )

            parsed = parse_meta_file(path)

            self.assertIsNone(parsed.parse_error)
            self.assertEqual(len(parsed.objects), 1)

            obj = parsed.objects[0]

            self.assertEqual(obj.object_id, "stage1.dat")
            self.assertEqual(obj.raw_size, "10485760")
            self.assertEqual(obj.size_bytes, 10485760)
            self.assertIsNone(obj.size_error)

            # Preserve arbitrary metadata, not only size.
            self.assertEqual(
                obj.attributes["checksum"],
                "abc",
            )

    def test_parse_list_of_objects(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "job.meta",
                """
[
  {
    "_id": "a.dat",
    "_attributes": {"size": "10"}
  },
  {
    "_id": "b.dat",
    "_attributes": {"size": 20}
  }
]
""",
            )

            parsed = parse_meta_file(path)

            self.assertEqual(
                [obj.object_id for obj in parsed.objects],
                ["a.dat", "b.dat"],
            )
            self.assertEqual(
                [obj.size_bytes for obj in parsed.objects],
                [10, 20],
            )

    def test_invalid_json_is_preserved_as_parse_error(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "broken.meta",
                '{"_id": "x.dat",',
            )

            parsed = parse_meta_file(path)

            self.assertIsNotNone(parsed.parse_error)
            self.assertEqual(parsed.objects, [])

    def test_invalid_size_is_not_silently_coerced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "bad-size.meta",
                """
{
  "_id": "x.dat",
  "_attributes": {
    "size": "10.5"
  }
}
""",
            )

            parsed = parse_meta_file(path)
            obj = parsed.objects[0]

            self.assertEqual(obj.raw_size, "10.5")
            self.assertIsNone(obj.size_bytes)
            self.assertEqual(
                obj.size_error,
                "size_is_not_an_integer",
            )

    def test_negative_size_is_rejected_but_raw_value_is_kept(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "negative.meta",
                """
{
  "_id": "x.dat",
  "_attributes": {
    "size": "-1"
  }
}
""",
            )

            parsed = parse_meta_file(path)
            obj = parsed.objects[0]

            self.assertEqual(obj.raw_size, "-1")
            self.assertIsNone(obj.size_bytes)
            self.assertEqual(obj.size_error, "negative_size")

    def test_size_provenance_points_to_exact_attribute(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "job.meta",
                """
{
  "_id": "x.dat",
  "_attributes": {
    "size": "123"
  }
}
""",
            )

            parsed = parse_meta_file(path)
            obj = parsed.objects[0]

            self.assertIsNotNone(obj.size_provenance)
            self.assertEqual(
                obj.size_provenance.source_kind,
                SourceKind.META,
            )
            self.assertEqual(
                obj.size_provenance.source_path,
                str(path.resolve()),
            )
            self.assertEqual(
                obj.size_provenance.attribute,
                "_attributes.size",
            )

    def test_cache_meta_is_marked_without_changing_parser_semantics(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            path = self.write_meta(
                root,
                "workflow.cache.meta",
                """
{
  "_id": "input.dat",
  "_attributes": {
    "size": "50"
  }
}
""",
            )

            parsed = parse_meta_file(path)

            self.assertTrue(parsed.is_cache_meta)
            self.assertEqual(
                parsed.objects[0].size_bytes,
                50,
            )

    def test_existing_fixture_meta_files_are_parseable(self):
        fixture = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "distribution_real_reconstructed"
            / "run0001"
        )

        sources = load_run_sources(fixture)
        parsed = parse_meta_files(
            sources.meta_files
            + sources.cache_meta_files
        )

        self.assertEqual(len(parsed), 5)
        self.assertTrue(
            all(item.parse_error is None for item in parsed)
        )

        objects = [
            obj
            for meta in parsed
            for obj in meta.objects
        ]

        self.assertTrue(
            any(obj.size_bytes is not None for obj in objects)
        )


if __name__ == "__main__":
    unittest.main()
