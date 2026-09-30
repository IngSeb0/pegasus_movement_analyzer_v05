import json
import unittest
from pathlib import Path

from pegasus_movement.diagnostics import (
    AnalysisStatus,
    ReasonCode,
)
from pegasus_movement.metrics import (
    calculate_metrics,
)
from pegasus_movement.model import (
    DeclaredMovementRecord,
    EvidenceLevel,
    FileClassification,
    FileRole,
    JobTransferManifest,
    ManifestFile,
    ReconciliationMode,
    RequiredMovementRecord,
    RequiredReason,
    ScientificFile,
    TaskExecution,
    TransferDirection,
    TransferEvidence,
)
from pegasus_movement.movement import (
    build_required_movements,
)
from pegasus_movement.reconciliation import (
    reconcile_movements,
)


ROOT = Path(__file__).resolve().parents[2]

ORACLES = json.loads(
    (
        ROOT
        / "fixtures"
        / "audited"
        / "regression_oracles.json"
    ).read_text(encoding="utf-8")
)


def task(task_id, job_id, worker):
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


def pipeline_files(size):
    return [
        ScientificFile(
            file_id="lfn:input.dat",
            logical_name="input.dat",
            roles={FileRole.EXTERNAL_INPUT},
            size_bytes=size,
            producer_task_id=None,
            consumer_task_ids=["T1"],
            origin_location_id="pegasus-master",
        ),
        ScientificFile(
            file_id="lfn:pipeline.stage1.dat",
            logical_name="pipeline.stage1.dat",
            roles={FileRole.INTERMEDIATE},
            size_bytes=size,
            producer_task_id="T1",
            consumer_task_ids=["T2"],
        ),
        ScientificFile(
            file_id="lfn:pipeline.stage2.dat",
            logical_name="pipeline.stage2.dat",
            roles={FileRole.INTERMEDIATE},
            size_bytes=size,
            producer_task_id="T2",
            consumer_task_ids=["T3"],
        ),
        ScientificFile(
            file_id="lfn:pipeline.stage3.dat",
            logical_name="pipeline.stage3.dat",
            roles={FileRole.FINAL_OUTPUT},
            size_bytes=size,
            producer_task_id="T3",
            consumer_task_ids=[],
            final_destination_ids=[
                "pegasus-master"
            ],
        ),
    ]


def confirmed_pipeline_declared(
    size,
    workers,
):
    w1, w2, w3 = workers

    rows = [
        (
            "1.0:input",
            "1.0",
            "lfn:input.dat",
            TransferDirection.INPUT,
            "pegasus-master",
            w1,
        ),
        (
            "1.0:output",
            "1.0",
            "lfn:pipeline.stage1.dat",
            TransferDirection.OUTPUT,
            w1,
            "pegasus-master",
        ),
        (
            "2.0:input",
            "2.0",
            "lfn:pipeline.stage1.dat",
            TransferDirection.INPUT,
            "pegasus-master",
            w2,
        ),
        (
            "2.0:output",
            "2.0",
            "lfn:pipeline.stage2.dat",
            TransferDirection.OUTPUT,
            w2,
            "pegasus-master",
        ),
        (
            "3.0:input",
            "3.0",
            "lfn:pipeline.stage2.dat",
            TransferDirection.INPUT,
            "pegasus-master",
            w3,
        ),
        (
            "3.0:output",
            "3.0",
            "lfn:pipeline.stage3.dat",
            TransferDirection.OUTPUT,
            w3,
            "pegasus-master",
        ),
    ]

    return [
        DeclaredMovementRecord(
            movement_id=movement_id,
            job_id=job_id,
            attempt_context="attempt:1",
            file_id=file_id,
            direction=direction,
            from_location_id=source,
            to_location_id=destination,
            size_bytes=size,
            verification_level=(
                EvidenceLevel
                .JOB_LEVEL_RECONCILED
            ),
            confirmed=True,
            verification_reason=None,
        )
        for (
            movement_id,
            job_id,
            file_id,
            direction,
            source,
            destination,
        ) in rows
    ]


def process_manifest(
    direction,
    *,
    file_id,
    filename,
    scientific_size,
    expected_count,
):
    files = [
        ManifestFile(
            job_id="2435.0",
            direction=direction,
            logical_file_id=file_id,
            physical_path=filename,
            basename=filename,
            classification=(
                FileClassification.SCIENTIFIC
            ),
            size_bytes=scientific_size,
            size_provenance=[],
            protocol="Cedar",
            remap_from=None,
            remap_to=None,
        )
    ]

    for index in range(
        expected_count - 1
    ):
        name = f"aux-{direction.value}-{index}"

        files.append(
            ManifestFile(
                job_id="2435.0",
                direction=direction,
                logical_file_id=None,
                physical_path=name,
                basename=name,
                classification=(
                    FileClassification.AUXILIARY
                ),
                size_bytes=None,
                size_provenance=[],
                protocol="Cedar",
                remap_from=None,
                remap_to=None,
            )
        )

    return JobTransferManifest(
        job_id="2435.0",
        direction=direction,
        attempt_context="attempt:1",
        files=files,
        expected_file_count=expected_count,
        expected_total_bytes=None,
        scientific_file_count=1,
        scientific_total_bytes=(
            scientific_size
        ),
        complete=True,
    )


def transfer_evidence(
    direction,
    *,
    count,
    bytes_value,
    attempt="attempt:1",
):
    return TransferEvidence(
        job_id="2435.0",
        direction=direction,
        attempt_context=attempt,
        worker_location_id=(
            "pegasus-worker1"
        ),
        raw_stats={
            "job_status": 4,
            "exit_code": 0,
            "exit_by_signal": None,
            "hold_reason": None,
            "job_run_count": (
                1 if attempt else 2
            ),
            "num_job_starts": (
                1 if attempt else 2
            ),
        },
        methods=["Cedar"],
        observed_file_count_last=count,
        observed_file_count_total=count,
        observed_bytes_last=bytes_value,
        observed_bytes_total=bytes_value,
        bytes_recvd=(
            bytes_value
            if direction
            == TransferDirection.INPUT
            else None
        ),
        bytes_sent=(
            bytes_value
            if direction
            == TransferDirection.OUTPUT
            else None
        ),
        transfer_started=None,
        transfer_finished=None,
        provenance=[],
    )


class AuditedRegressionTests(
    unittest.TestCase
):
    def test_pipeline_10mib_oracles(self):
        fixture = ORACLES[
            "pipeline_10mib"
        ]

        size = fixture[
            "file_size_bytes"
        ]

        for name, oracle in (
            fixture["placements"].items()
        ):
            with self.subTest(
                placement=name
            ):
                workers = oracle[
                    "workers"
                ]

                tasks = [
                    task(
                        "T1",
                        "1.0",
                        workers[0],
                    ),
                    task(
                        "T2",
                        "2.0",
                        workers[1],
                    ),
                    task(
                        "T3",
                        "3.0",
                        workers[2],
                    ),
                ]

                required = (
                    build_required_movements(
                        pipeline_files(size),
                        tasks,
                    )
                )

                self.assertEqual(
                    required.diagnostics,
                    [],
                )

                self.assertEqual(
                    required.total_bytes,
                    oracle[
                        "required_movement_bytes"
                    ],
                )

                declared = (
                    confirmed_pipeline_declared(
                        size,
                        workers,
                    )
                )

                metric = calculate_metrics(
                    required_movements=(
                        required.records
                    ),
                    declared_movements=(
                        declared
                    ),
                )

                self.assertEqual(
                    metric.declared_movement_bytes,
                    fixture[
                        "declared_movement_bytes"
                    ],
                )
                self.assertEqual(
                    metric.observed_movement_bytes,
                    fixture[
                        "observed_movement_bytes"
                    ],
                )
                self.assertEqual(
                    metric.coverage,
                    fixture["coverage"],
                )
                self.assertAlmostEqual(
                    metric.dme,
                    oracle["dme"],
                    places=12,
                )
                self.assertEqual(
                    metric.analysis_status,
                    AnalysisStatus.VALID,
                )

    def test_process_50mib_freezes_successful_manifest_mode(
        self,
    ):
        fixture = ORACLES[
            "process_50mib_same_w1"
        ]

        size = fixture[
            "file_size_bytes"
        ]

        manifests = [
            process_manifest(
                TransferDirection.INPUT,
                file_id="lfn:input.dat",
                filename="input.dat",
                scientific_size=size,
                expected_count=fixture[
                    "input_sandbox"
                ]["file_count"],
            ),
            process_manifest(
                TransferDirection.OUTPUT,
                file_id="lfn:process.out",
                filename="process.out",
                scientific_size=size,
                expected_count=fixture[
                    "output_sandbox"
                ]["file_count"],
            ),
        ]

        declared = [
            DeclaredMovementRecord(
                movement_id="2435.0:input:1",
                job_id="2435.0",
                attempt_context="attempt:1",
                file_id="lfn:input.dat",
                direction=(
                    TransferDirection.INPUT
                ),
                from_location_id=(
                    "pegasus-master"
                ),
                to_location_id=(
                    "pegasus-worker1"
                ),
                size_bytes=size,
            ),
            DeclaredMovementRecord(
                movement_id="2435.0:output:2",
                job_id="2435.0",
                attempt_context="attempt:1",
                file_id="lfn:process.out",
                direction=(
                    TransferDirection.OUTPUT
                ),
                from_location_id=(
                    "pegasus-worker1"
                ),
                to_location_id=(
                    "pegasus-master"
                ),
                size_bytes=size,
            ),
        ]

        evidence = [
            transfer_evidence(
                TransferDirection.INPUT,
                count=fixture[
                    "input_sandbox"
                ]["file_count"],
                bytes_value=fixture[
                    "input_sandbox"
                ]["bytes"],
            ),
            transfer_evidence(
                TransferDirection.OUTPUT,
                count=fixture[
                    "output_sandbox"
                ]["file_count"],
                bytes_value=fixture[
                    "output_sandbox"
                ]["bytes"],
            ),
        ]

        reconciled = (
            reconcile_movements(
                manifests=manifests,
                evidence=evidence,
                declared_movements=declared,
            )
        )

        self.assertEqual(
            reconciled.diagnostics,
            [],
        )

        self.assertTrue(
            all(
                item.confirmed
                for item
                in reconciled.verifications
            )
        )

        self.assertTrue(
            all(
                item.level
                == EvidenceLevel
                .JOB_LEVEL_RECONCILED
                for item
                in reconciled.verifications
            )
        )

        self.assertTrue(
            all(
                item.reconciliation_mode
                == ReconciliationMode
                .SUCCESSFUL_MANIFEST
                for item
                in reconciled.verifications
            )
        )

        required = [
            RequiredMovementRecord(
                file_id="lfn:input.dat",
                from_location_id=(
                    "pegasus-master"
                ),
                to_location_id=(
                    "pegasus-worker1"
                ),
                size_bytes=size,
                required_bytes=size,
                reason=RequiredReason.INPUT,
            ),
            RequiredMovementRecord(
                file_id="lfn:process.out",
                from_location_id=(
                    "pegasus-worker1"
                ),
                to_location_id=(
                    "pegasus-master"
                ),
                size_bytes=size,
                required_bytes=size,
                reason=(
                    RequiredReason
                    .FINAL_DESTINATION
                ),
            ),
        ]

        metric = calculate_metrics(
            required_movements=required,
            declared_movements=(
                reconciled.declared_movements
            ),
        )

        self.assertEqual(
            metric.required_movement_bytes,
            fixture[
                "required_movement_bytes"
            ],
        )
        self.assertEqual(
            metric.declared_movement_bytes,
            fixture[
                "declared_movement_bytes"
            ],
        )
        self.assertEqual(
            metric.observed_movement_bytes,
            fixture[
                "observed_movement_bytes"
            ],
        )
        self.assertEqual(
            metric.coverage,
            fixture["coverage"],
        )
        self.assertEqual(
            metric.dme,
            fixture["dme"],
        )

    def test_ambiguous_retry_fails_closed(
        self,
    ):
        process = ORACLES[
            "process_50mib_same_w1"
        ]
        negative = ORACLES[
            "negative_retry"
        ]

        size = process[
            "file_size_bytes"
        ]

        manifest = process_manifest(
            TransferDirection.INPUT,
            file_id="lfn:input.dat",
            filename="input.dat",
            scientific_size=size,
            expected_count=process[
                "input_sandbox"
            ]["file_count"],
        )

        declared = DeclaredMovementRecord(
            movement_id="2435.0:input:1",
            job_id="2435.0",
            attempt_context="attempt:1",
            file_id="lfn:input.dat",
            direction=TransferDirection.INPUT,
            from_location_id="pegasus-master",
            to_location_id=(
                "pegasus-worker1"
            ),
            size_bytes=size,
        )

        evidence = transfer_evidence(
            TransferDirection.INPUT,
            count=process[
                "input_sandbox"
            ]["file_count"],
            bytes_value=process[
                "input_sandbox"
            ]["bytes"],
            attempt=None,
        )

        reconciled = reconcile_movements(
            manifests=[manifest],
            evidence=[evidence],
            declared_movements=[declared],
        )

        verification = (
            reconciled.verifications[0]
        )

        self.assertFalse(
            verification.confirmed
        )
        self.assertEqual(
            verification.reason_code,
            ReasonCode[
                negative[
                    "expected_reason"
                ]
            ],
        )

        required = [
            RequiredMovementRecord(
                file_id="lfn:input.dat",
                from_location_id=(
                    "pegasus-master"
                ),
                to_location_id=(
                    "pegasus-worker1"
                ),
                size_bytes=size,
                required_bytes=size,
                reason=RequiredReason.INPUT,
            )
        ]

        metric = calculate_metrics(
            required_movements=required,
            declared_movements=(
                reconciled.declared_movements
            ),
        )

        self.assertEqual(
            metric.coverage,
            negative[
                "expected_coverage"
            ],
        )
        self.assertIsNone(
            metric.observed_movement_bytes
        )
        self.assertIsNone(
            metric.dme
        )
        self.assertEqual(
            metric.analysis_status,
            AnalysisStatus.INCOMPLETE_EVIDENCE,
        )


if __name__ == "__main__":
    unittest.main()
