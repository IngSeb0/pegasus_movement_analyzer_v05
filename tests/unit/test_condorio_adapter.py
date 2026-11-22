import unittest

from pegasus_movement.condorio_adapter import (
    CondorIOStandardAdapter,
)
from pegasus_movement.execution_model import (
    CONDORIO_ADAPTER_NAME,
    ExecutionModelEvidence,
)


def valid_evidence(**overrides):
    values = dict(
        pegasus_version="5.1.2",
        htcondor_version="25.12.2",
        data_configuration="condorio",
        universe="vanilla",
        submit_host="pegasus-master",
        should_transfer_files="YES",
        when_to_transfer_output="ON_EXIT",
        bypass_enabled=False,
        plugin_methods=[],
        plugin_methods_known=True,
        clustered_jobs=False,
        shared_filesystem=False,
    )

    values.update(overrides)

    return ExecutionModelEvidence(**values)


class CondorIOStandardAdapterTests(unittest.TestCase):
    def test_adapter_has_canonical_name(self):
        self.assertEqual(
            CondorIOStandardAdapter.name,
            CONDORIO_ADAPTER_NAME,
        )

    def test_supported_profile_is_accepted(self):
        self.assertTrue(
            CondorIOStandardAdapter.supports(
                valid_evidence()
            )
        )

    def test_missing_evidence_is_rejected(self):
        self.assertFalse(
            CondorIOStandardAdapter.supports(
                valid_evidence(
                    data_configuration=None,
                )
            )
        )

    def test_shared_filesystem_is_rejected(self):
        self.assertFalse(
            CondorIOStandardAdapter.supports(
                valid_evidence(
                    shared_filesystem=True,
                )
            )
        )

    def test_transfer_plugin_is_rejected(self):
        self.assertFalse(
            CondorIOStandardAdapter.supports(
                valid_evidence(
                    plugin_methods=["https"],
                )
            )
        )

    def test_clustered_job_is_rejected(self):
        self.assertFalse(
            CondorIOStandardAdapter.supports(
                valid_evidence(
                    clustered_jobs=True,
                )
            )
        )

    def test_wrong_data_configuration_is_rejected(self):
        self.assertFalse(
            CondorIOStandardAdapter.supports(
                valid_evidence(
                    data_configuration="sharedfs",
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
