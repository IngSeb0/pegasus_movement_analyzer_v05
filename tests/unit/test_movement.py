import tempfile
import unittest
from pathlib import Path

from pegasus_movement.execution_model import (
    ExecutionModelEvidence,
    detect_execution_model,
)
from pegasus_movement.model import (
    EvidenceLevel,
    FileClassification,
    FileRole,
    ProvenanceRef,
    ScientificFile,
    SourceKind,
    TaskExecution,
    TransferDirection,
)
from pegasus_movement.movement import (
    build_condorio_manifests,
    build_declared_movements,
    build_required_movements,
)
from pegasus_movement.pegasus_source import (
    parse_submit_file,
)


def task(
    task_id: str,
    worker: str | None,
    job_id: str,
):
    return TaskExecution(
        task_id=task_id,
        pegasus_node_id=task_id,
        job_id=job_id,
        worker_location_id=worker,
        job_status=4,
        exit_code=0,
        job_run_count=1,
        num_job_starts=1,
        successful=True,
        provenance=[],
    )


def scientific_file(
    *,
    file_id: str,
    logical_name: str,
    roles: set[FileRole],
    size: int | None,
    producer: str | None = None,
    consumers: list[str] | None = None,
    origin: str | None = None,
    finals: list[str] | None = None,
):
    return ScientificFile(
        file_id=file_id,
        logical_name=logical_name,
        physical_refs=[],
        roles=roles,
        size_bytes=size,
        size_provenance=[],
        producer_task_id=producer,
        consumer_task_ids=(
            consumers or []
        ),
        origin_location_id=origin,
        final_destination_ids=(
            finals or []
        ),
        identity_provenance=[],
    )


def supported_profile():
    return detect_execution_model(
        ExecutionModelEvidence(
            pegasus_version="5.1.2",
            htcondor_version="25.12.2",
            data_configuration="condorio",
            universe="vanilla",
            submit_host="submit",
            should_transfer_files="YES",
            when_to_transfer_output="ON_EXIT",
            bypass_enabled=False,
            plugin_methods=[],
            plugin_methods_known=True,
            clustered_jobs=False,
            shared_filesystem=False,
        )
    )


class RequiredMovementTests(unittest.TestCase):
    def test_external_input_cross_location(self):
        file = scientific_file(
            file_id="lfn:input.dat",
            logical_name="input.dat",
            roles={FileRole.EXTERNAL_INPUT},
            size=10,
            consumers=["task_A"],
            origin="submit",
        )

        result = build_required_movements(
            [file],
            [task("task_A", "w1", "1.0")],
        )

        self.assertEqual(
            result.total_bytes,
            10,
        )
        self.assertEqual(
            len(result.records),
            1,
        )
        self.assertEqual(
            result.records[0].from_location_id,
            "submit",
        )
        self.assertEqual(
            result.records[0].to_location_id,
            "w1",
        )

    def test_same_worker_intermediate_is_zero(self):
        file = scientific_file(
            file_id="lfn:mid.dat",
            logical_name="mid.dat",
            roles={FileRole.INTERMEDIATE},
            size=20,
            producer="task_A",
            consumers=["task_B"],
        )

        result = build_required_movements(
            [file],
            [
                task("task_A", "w1", "1.0"),
                task("task_B", "w1", "2.0"),
            ],
        )

        self.assertEqual(
            result.total_bytes,
            0,
        )
        self.assertEqual(
            result.records,
            [],
        )

    def test_fanout_counts_distinct_workers_once(self):
        file = scientific_file(
            file_id="lfn:shared.dat",
            logical_name="shared.dat",
            roles={FileRole.INTERMEDIATE},
            size=8,
            producer="task_A",
            consumers=[
                "task_B",
                "task_C",
                "task_D",
            ],
        )

        result = build_required_movements(
            [file],
            [
                task("task_A", "w1", "1.0"),
                task("task_B", "w2", "2.0"),
                task("task_C", "w2", "3.0"),
                task("task_D", "w3", "4.0"),
            ],
        )

        self.assertEqual(
            result.total_bytes,
            16,
        )
        self.assertEqual(
            {
                record.to_location_id
                for record in result.records
            },
            {"w2", "w3"},
        )

    def test_consumer_and_final_same_destination_not_duplicated(self):
        file = scientific_file(
            file_id="lfn:mid.dat",
            logical_name="mid.dat",
            roles={
                FileRole.INTERMEDIATE,
                FileRole.FINAL_OUTPUT,
            },
            size=11,
            producer="task_A",
            consumers=["task_B"],
            finals=["w2"],
        )

        result = build_required_movements(
            [file],
            [
                task("task_A", "w1", "1.0"),
                task("task_B", "w2", "2.0"),
            ],
        )

        self.assertEqual(
            result.total_bytes,
            11,
        )
        self.assertEqual(
            len(result.records),
            1,
        )

    def test_zero_byte_movement_keeps_record(self):
        file = scientific_file(
            file_id="lfn:zero.dat",
            logical_name="zero.dat",
            roles={FileRole.EXTERNAL_INPUT},
            size=0,
            consumers=["task_A"],
            origin="submit",
        )

        result = build_required_movements(
            [file],
            [task("task_A", "w1", "1.0")],
        )

        self.assertEqual(
            len(result.records),
            1,
        )
        self.assertEqual(
            result.total_bytes,
            0,
        )


class DeclaredMovementTests(unittest.TestCase):
    def make_submit(self, root: Path):
        wrapper = root / "wrapper.sh"
        wrapper.write_text(
            "#!/bin/sh\n",
            encoding="utf-8",
        )

        path = root / "compute.sub"

        path.write_text(
            "\n".join(
                [
                    '+pegasus_wf_dax_job_id = "A"',
                    '+pegasus_wf_dag_job_id = "task_A"',
                    "+pegasus_job_class = 1",
                    "transfer_executable = true",
                    f"executable = {wrapper}",
                    (
                        "transfer_input_files = "
                        "input.dat,support.meta"
                    ),
                    (
                        "transfer_output_files = "
                        "output.dat"
                    ),
                    "output = stdout.txt",
                    "error = stderr.txt",
                    (
                        'transfer_output_remaps = '
                        '"output.dat=renamed.dat"'
                    ),
                    "queue",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        return parse_submit_file(path)

    def files(self):
        return [
            scientific_file(
                file_id="lfn:input.dat",
                logical_name="input.dat",
                roles={
                    FileRole.EXTERNAL_INPUT
                },
                size=10,
                consumers=["task_A"],
                origin="submit",
            ),
            scientific_file(
                file_id="lfn:output.dat",
                logical_name="output.dat",
                roles={
                    FileRole.FINAL_OUTPUT
                },
                size=20,
                producer="task_A",
                finals=["submit"],
            ),
        ]

    def test_manifest_keeps_scientific_and_auxiliary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            result = build_condorio_manifests(
                submits=[
                    self.make_submit(root)
                ],
                task_executions=[
                    task(
                        "task_A",
                        "w1",
                        "10.0",
                    )
                ],
                scientific_files=self.files(),
                execution_model=(
                    supported_profile()
                ),
            )

            self.assertEqual(
                len(result.manifests),
                2,
            )

            input_manifest = next(
                item
                for item in result.manifests
                if item.direction
                == TransferDirection.INPUT
            )

            classes = {
                item.physical_path:
                item.classification
                for item
                in input_manifest.files
            }

            self.assertEqual(
                classes["input.dat"],
                FileClassification.SCIENTIFIC,
            )
            self.assertEqual(
                classes["support.meta"],
                FileClassification.AUXILIARY,
            )

    def test_only_scientific_files_become_declared_movement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            tasks = [
                task(
                    "task_A",
                    "w1",
                    "10.0",
                )
            ]

            manifests = (
                build_condorio_manifests(
                    submits=[
                        self.make_submit(root)
                    ],
                    task_executions=tasks,
                    scientific_files=(
                        self.files()
                    ),
                    execution_model=(
                        supported_profile()
                    ),
                )
            )

            result = build_declared_movements(
                manifests=(
                    manifests.manifests
                ),
                task_executions=tasks,
                execution_model=(
                    supported_profile()
                ),
            )

            self.assertEqual(
                len(result.records),
                2,
            )
            self.assertEqual(
                result.total_bytes,
                30,
            )

            self.assertEqual(
                {
                    record.file_id
                    for record in result.records
                },
                {
                    "lfn:input.dat",
                    "lfn:output.dat",
                },
            )

    def test_condorio_directions_use_confirmed_model(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            tasks = [
                task(
                    "task_A",
                    "w1",
                    "10.0",
                )
            ]

            manifests = (
                build_condorio_manifests(
                    submits=[
                        self.make_submit(root)
                    ],
                    task_executions=tasks,
                    scientific_files=(
                        self.files()
                    ),
                    execution_model=(
                        supported_profile()
                    ),
                )
            )

            result = build_declared_movements(
                manifests=(
                    manifests.manifests
                ),
                task_executions=tasks,
                execution_model=(
                    supported_profile()
                ),
            )

            by_direction = {
                record.direction: record
                for record in result.records
            }

            input_record = by_direction[
                TransferDirection.INPUT
            ]
            output_record = by_direction[
                TransferDirection.OUTPUT
            ]

            self.assertEqual(
                (
                    input_record
                    .from_location_id,
                    input_record
                    .to_location_id,
                ),
                ("submit", "w1"),
            )

            self.assertEqual(
                (
                    output_record
                    .from_location_id,
                    output_record
                    .to_location_id,
                ),
                ("w1", "submit"),
            )

            self.assertTrue(
                all(
                    record.verification_level
                    == EvidenceLevel.INSUFFICIENT
                    and not record.confirmed
                    for record
                    in result.records
                )
            )


if __name__ == "__main__":
    unittest.main()
