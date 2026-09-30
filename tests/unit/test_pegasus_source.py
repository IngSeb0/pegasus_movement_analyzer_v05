import tempfile
import unittest
from pathlib import Path

from pegasus_movement.pegasus_source import (
    RawRunSources,
    load_run_sources,
)


class PegasusSourceLoaderTests(unittest.TestCase):
    def legacy_fixture(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "distribution_real_reconstructed"
            / "run0001"
        )

    def test_load_existing_reconstructed_fixture(self):
        sources = load_run_sources(self.legacy_fixture())

        self.assertIsInstance(sources, RawRunSources)
        self.assertTrue(sources.run_path.is_absolute())

        self.assertEqual(len(sources.submit_files), 5)
        self.assertEqual(len(sources.meta_files), 5)

        self.assertTrue(all(p.is_absolute() for p in sources.submit_files))
        self.assertTrue(all(p.is_absolute() for p in sources.meta_files))

    def test_loader_discovers_nested_sources(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run0001"
            nested = run / "00" / "00"
            nested.mkdir(parents=True)

            (nested / "job.sub").write_text("", encoding="utf-8")
            (nested / "job.meta").write_text("{}", encoding="utf-8")
            (run / "workflow.cache.meta").write_text("{}", encoding="utf-8")
            (run / "workflow.dag").write_text("", encoding="utf-8")
            (run / "braindump.txt").write_text("", encoding="utf-8")
            (run / "pegasus.properties").write_text("", encoding="utf-8")
            (run / "job.log").write_text("", encoding="utf-8")

            sources = load_run_sources(run)

            self.assertEqual(len(sources.submit_files), 1)
            self.assertEqual(len(sources.meta_files), 1)
            self.assertEqual(len(sources.cache_meta_files), 1)
            self.assertEqual(len(sources.dag_files), 1)
            self.assertEqual(len(sources.braindump_files), 1)
            self.assertEqual(len(sources.config_files), 1)
            self.assertEqual(len(sources.event_log_files), 1)

    def test_cache_meta_is_not_duplicated_as_regular_meta(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td)
            (run / "x.cache.meta").write_text("{}", encoding="utf-8")

            sources = load_run_sources(run)

            self.assertEqual(len(sources.cache_meta_files), 1)
            self.assertEqual(len(sources.meta_files), 0)

    def test_missing_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "does-not-exist"

            with self.assertRaises(FileNotFoundError):
                load_run_sources(missing)

    def test_file_instead_of_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "not-a-run"
            p.write_text("x", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                load_run_sources(p)


if __name__ == "__main__":
    unittest.main()


class PegasusSourceOptionalArtifactsTests(unittest.TestCase):
    def test_real_fixture_allows_missing_optional_artifacts(self):
        fixture = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "distribution_real_reconstructed"
            / "run0001"
        )

        sources = load_run_sources(fixture)

        self.assertEqual(sources.dag_files, [])
        self.assertEqual(sources.braindump_files, [])
        self.assertEqual(sources.config_files, [])
        self.assertEqual(sources.event_log_files, [])
