import unittest

from pegasus_movement.diagnostics import (
    ReasonCode,
)
from pegasus_movement.model import (
    DeclaredMovementRecord,
    EvidenceLevel,
    FileClassification,
    JobTransferManifest,
    ManifestFile,
    ReconciliationMode,
    TransferDirection,
    TransferEvidence,
)
from pegasus_movement.reconciliation import (
    reconcile_movements,
)


def manifest(
    *,
    expected_total=100,
    complete=True,
):
    sci = ManifestFile(
        job_id="10.0",
        direction=TransferDirection.INPUT,
        logical_file_id="lfn:input.dat",
        physical_path="input.dat",
        basename="input.dat",
        classification=(
            FileClassification.SCIENTIFIC
        ),
        size_bytes=80,
        size_provenance=[],
        protocol="cedar",
        remap_from=None,
        remap_to=None,
    )

    aux = ManifestFile(
        job_id="10.0",
        direction=TransferDirection.INPUT,
        logical_file_id=None,
        physical_path="aux.dat",
        basename="aux.dat",
        classification=(
            FileClassification.AUXILIARY
        ),
        size_bytes=(
            20
            if expected_total is not None
            else None
        ),
        size_provenance=[],
        protocol="cedar",
        remap_from=None,
        remap_to=None,
    )

    return JobTransferManifest(
        job_id="10.0",
        direction=TransferDirection.INPUT,
        attempt_context=None,
        files=[sci, aux],
        expected_file_count=2,
        expected_total_bytes=(
            expected_total
        ),
        scientific_file_count=1,
        scientific_total_bytes=80,
        complete=complete,
    )


def evidence(
    *,
    count=2,
    bytes_value=100,
    methods=None,
    attempt="attempt:1",
    job_status=4,
    exit_code=0,
):
    return TransferEvidence(
        job_id="10.0",
        direction=TransferDirection.INPUT,
        attempt_context=attempt,
        worker_location_id="worker1",
        raw_stats={
            "job_status": job_status,
            "exit_code": exit_code,
            "exit_by_signal": None,
            "hold_reason": None,
            "job_run_count": (
                1 if attempt else 2
            ),
            "num_job_starts": (
                1 if attempt else 2
            ),
        },
        methods=(
            ["Cedar"]
            if methods is None
            else methods
        ),
        observed_file_count_last=count,
        observed_file_count_total=count,
        observed_bytes_last=bytes_value,
        observed_bytes_total=bytes_value,
        bytes_recvd=bytes_value,
        bytes_sent=None,
        transfer_started=None,
        transfer_finished=None,
        provenance=[],
    )


def declared():
    return DeclaredMovementRecord(
        movement_id="10.0:input:1",
        job_id="10.0",
        attempt_context=None,
        file_id="lfn:input.dat",
        direction=TransferDirection.INPUT,
        from_location_id="submit",
        to_location_id="worker1",
        size_bytes=80,
        verification_level=(
            EvidenceLevel.INSUFFICIENT
        ),
        confirmed=False,
        verification_reason=None,
    )


class ReconciliationTests(unittest.TestCase):
    def test_exact_bytes_confirms_scientific_movement(self):
        result = reconcile_movements(
            manifests=[manifest()],
            evidence=[evidence()],
            declared_movements=[declared()],
        )

        verification = (
            result.verifications[0]
        )

        self.assertTrue(
            verification.confirmed
        )
        self.assertEqual(
            verification.level,
            EvidenceLevel.JOB_LEVEL_RECONCILED,
        )
        self.assertEqual(
            verification.reconciliation_mode,
            ReconciliationMode.EXACT_BYTES,
        )
        self.assertEqual(
            verification.unexplained_bytes,
            0,
        )

        self.assertTrue(
            result.declared_movements[
                0
            ].confirmed
        )
        self.assertEqual(
            result.declared_movements[
                0
            ].attempt_context,
            "attempt:1",
        )

    def test_successful_manifest_allows_unknown_aux_size(self):
        result = reconcile_movements(
            manifests=[
                manifest(
                    expected_total=None
                )
            ],
            evidence=[
                evidence(
                    bytes_value=95
                )
            ],
            declared_movements=[declared()],
        )

        verification = (
            result.verifications[0]
        )

        self.assertTrue(
            verification.confirmed
        )
        self.assertEqual(
            verification.reconciliation_mode,
            ReconciliationMode.SUCCESSFUL_MANIFEST,
        )

    def test_file_count_mismatch_is_insufficient(self):
        result = reconcile_movements(
            manifests=[manifest()],
            evidence=[
                evidence(count=3)
            ],
            declared_movements=[declared()],
        )

        verification = (
            result.verifications[0]
        )

        self.assertFalse(
            verification.confirmed
        )
        self.assertEqual(
            verification.reason_code,
            ReasonCode.TRANSFER_COUNT_MISMATCH,
        )
        self.assertFalse(
            result.declared_movements[
                0
            ].confirmed
        )

    def test_retry_without_separable_attempt_is_insufficient(self):
        result = reconcile_movements(
            manifests=[manifest()],
            evidence=[
                evidence(attempt=None)
            ],
            declared_movements=[declared()],
        )

        self.assertEqual(
            result.verifications[
                0
            ].reason_code,
            ReasonCode.RETRY_NOT_SEPARABLE,
        )

    def test_unknown_protocol_is_not_reconciled(self):
        result = reconcile_movements(
            manifests=[manifest()],
            evidence=[
                evidence(
                    methods=["Cedar", "HTTP"]
                )
            ],
            declared_movements=[declared()],
        )

        self.assertEqual(
            result.verifications[
                0
            ].reason_code,
            ReasonCode.UNACCOUNTED_PROTOCOL,
        )

    def test_fully_sized_byte_mismatch_does_not_fall_back(self):
        result = reconcile_movements(
            manifests=[manifest()],
            evidence=[
                evidence(
                    bytes_value=101
                )
            ],
            declared_movements=[declared()],
        )

        verification = (
            result.verifications[0]
        )

        self.assertFalse(
            verification.confirmed
        )
        self.assertEqual(
            verification.reason_code,
            ReasonCode.TRANSFER_BYTES_MISMATCH,
        )


if __name__ == "__main__":
    unittest.main()
