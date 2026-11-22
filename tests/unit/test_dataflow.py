import json
import tempfile
import unittest
from pathlib import Path

from pegasus_movement.dataflow import (
    build_scientific_dataflow,
)
from pegasus_movement.diagnostics import ReasonCode
from pegasus_movement.model import FileRole
from pegasus_movement.pegasus_source import (
    parse_submit_file,
)


def write_compute_submit(
    root: Path,
    dax_id: str,
    dag_id: str,
):
    path = root / f"{dax_id}.sub"

    path.write_text(
        "\n".join(
            [
                f'+pegasus_wf_dax_job_id = "{dax_id}"',
                f'+pegasus_wf_dag_job_id = "{dag_id}"',
                "+pegasus_job_class = 1",
                "queue",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return parse_submit_file(path)


class ScientificDataflowTests(unittest.TestCase):
    def make_workflow(
        self,
        root: Path,
        *,
        duplicate_producer=False,
    ):
        jobs = """
jobs:
  - type: job
    name: first
    id: A
    uses:
      - lfn: input.dat
        type: input
      - lfn: middle.dat
        type: output
  - type: job
    name: second
    id: B
    uses:
      - lfn: middle.dat
        type: input
      - lfn: result.dat
        type: output
        stageOut: true
"""

        if duplicate_producer:
            jobs += """
  - type: job
    name: third
    id: C
    uses:
      - lfn: middle.dat
        type: output
"""

        workflow = root / "workflow.yml"

        workflow.write_text(
            """
replicaCatalog:
  replicas:
    - lfn: input.dat
      pfns:
        - site: local
          pfn: /does/not/need/to/exist/input.dat
"""
            + jobs,
            encoding="utf-8",
        )

        return workflow

    def make_meta(self, root: Path):
        path = root / "wf.cache.meta"

        path.write_text(
            json.dumps(
                [
                    {
                        "_id": "input.dat",
                        "_attributes": {
                            "size": 10
                        },
                    },
                    {
                        "_id": "middle.dat",
                        "_attributes": {
                            "size": 20
                        },
                    },
                    {
                        "_id": "result.dat",
                        "_attributes": {
                            "size": 30
                        },
                    },
                ]
            ),
            encoding="utf-8",
        )

        return path

    def test_builds_roles_producer_consumers_and_sizes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            workflow = self.make_workflow(
                root
            )
            meta = self.make_meta(root)

            submits = [
                write_compute_submit(
                    root,
                    "A",
                    "task_A",
                ),
                write_compute_submit(
                    root,
                    "B",
                    "task_B",
                ),
            ]

            result = build_scientific_dataflow(
                workflow,
                submits=submits,
                site_location_map={
                    "local": "submit"
                },
                final_destination_location_id=(
                    "submit"
                ),
                meta_paths=[meta],
            )

            files = result.scientific_files

            external = files[
                "lfn:input.dat"
            ]
            middle = files[
                "lfn:middle.dat"
            ]
            final = files[
                "lfn:result.dat"
            ]

            self.assertEqual(
                external.roles,
                {FileRole.EXTERNAL_INPUT},
            )
            self.assertEqual(
                external.consumer_task_ids,
                ["task_A"],
            )
            self.assertEqual(
                external.origin_location_id,
                "submit",
            )
            self.assertEqual(
                external.size_bytes,
                10,
            )

            self.assertEqual(
                middle.roles,
                {FileRole.INTERMEDIATE},
            )
            self.assertEqual(
                middle.producer_task_id,
                "task_A",
            )
            self.assertEqual(
                middle.consumer_task_ids,
                ["task_B"],
            )
            self.assertEqual(
                middle.size_bytes,
                20,
            )

            self.assertEqual(
                final.roles,
                {FileRole.FINAL_OUTPUT},
            )
            self.assertEqual(
                final.producer_task_id,
                "task_B",
            )
            self.assertEqual(
                final.final_destination_ids,
                ["submit"],
            )
            self.assertEqual(
                final.size_bytes,
                30,
            )

    def test_multiple_producers_are_inconsistent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            workflow = self.make_workflow(
                root,
                duplicate_producer=True,
            )

            submits = [
                write_compute_submit(
                    root,
                    "A",
                    "task_A",
                ),
                write_compute_submit(
                    root,
                    "B",
                    "task_B",
                ),
                write_compute_submit(
                    root,
                    "C",
                    "task_C",
                ),
            ]

            result = build_scientific_dataflow(
                workflow,
                submits=submits,
                site_location_map={
                    "local": "submit"
                },
                final_destination_location_id=(
                    "submit"
                ),
            )

            self.assertIn(
                ReasonCode.MULTIPLE_PRODUCERS,
                {
                    item.reason_code
                    for item in result.diagnostics
                },
            )

    def test_missing_size_is_not_estimated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            workflow = self.make_workflow(
                root
            )

            submits = [
                write_compute_submit(
                    root,
                    "A",
                    "task_A",
                ),
                write_compute_submit(
                    root,
                    "B",
                    "task_B",
                ),
            ]

            result = build_scientific_dataflow(
                workflow,
                submits=submits,
                site_location_map={
                    "local": "submit"
                },
                final_destination_location_id=(
                    "submit"
                ),
            )

            self.assertIsNone(
                result.scientific_files[
                    "lfn:middle.dat"
                ].size_bytes
            )

            self.assertIn(
                ReasonCode.MISSING_FILE_SIZE,
                {
                    item.reason_code
                    for item in result.diagnostics
                },
            )

    def test_unconsumed_declared_output_is_final(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            workflow = self.make_workflow(
                root
            )
            meta = self.make_meta(root)

            submits = [
                write_compute_submit(
                    root,
                    "A",
                    "task_A",
                ),
                write_compute_submit(
                    root,
                    "B",
                    "task_B",
                ),
            ]

            result = build_scientific_dataflow(
                workflow,
                submits=submits,
                site_location_map={
                    "local": "submit"
                },
                final_destination_location_id=(
                    "submit"
                ),
                meta_paths=[meta],
            )

            self.assertIn(
                FileRole.FINAL_OUTPUT,
                result.scientific_files[
                    "lfn:result.dat"
                ].roles,
            )


if __name__ == "__main__":
    unittest.main()
