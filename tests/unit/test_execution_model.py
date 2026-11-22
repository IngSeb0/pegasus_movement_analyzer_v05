import unittest

from pegasus_movement.diagnostics import ReasonCode
from pegasus_movement.execution_model import (
    CONDORIO_ADAPTER_NAME,
    ExecutionModelEvidence,
    detect_execution_model,
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


class ExecutionModelDetectionTests(unittest.TestCase):
    def test_supported_condorio_profile(self):
        profile = detect_execution_model(
            valid_evidence()
        )

        self.assertTrue(profile.supported)
        self.assertEqual(
            profile.adapter_name,
            CONDORIO_ADAPTER_NAME,
        )
        self.assertEqual(
            profile.unsupported_reasons,
            [],
        )

    def test_missing_critical_evidence_fails_closed(self):
        profile = detect_execution_model(
            valid_evidence(
                data_configuration=None,
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
            profile.unsupported_reasons,
        )

    def test_missing_submit_host_fails_closed(self):
        profile = detect_execution_model(
            valid_evidence(
                submit_host=None,
            )
        )

        self.assertFalse(profile.supported)
        self.assertIsNone(profile.adapter_name)
        self.assertIn(
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
            profile.unsupported_reasons,
        )

    def test_shared_filesystem_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                shared_filesystem=True,
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_SHARED_FS,
            profile.unsupported_reasons,
        )

    def test_bypass_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                bypass_enabled=True,
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_BYPASS,
            profile.unsupported_reasons,
        )

    def test_transfer_plugin_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                plugin_methods=["https"],
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_TRANSFER_PLUGIN,
            profile.unsupported_reasons,
        )

    def test_unknown_plugin_state_is_not_treated_as_none(self):
        profile = detect_execution_model(
            valid_evidence(
                plugin_methods=[],
                plugin_methods_known=False,
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.MISSING_EXECUTION_MODEL_EVIDENCE,
            profile.unsupported_reasons,
        )

    def test_clustered_job_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                clustered_jobs=True,
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_CLUSTERED_JOB,
            profile.unsupported_reasons,
        )

    def test_wrong_data_configuration_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                data_configuration="sharedfs",
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_DATA_CONFIGURATION,
            profile.unsupported_reasons,
        )

    def test_non_vanilla_universe_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                universe="docker",
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_UNIVERSE,
            profile.unsupported_reasons,
        )

    def test_disabled_file_transfer_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                should_transfer_files="NO",
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_FILE_TRANSFER,
            profile.unsupported_reasons,
        )

    def test_non_pegasus_5_version_is_unsupported(self):
        profile = detect_execution_model(
            valid_evidence(
                pegasus_version="6.0.0",
            )
        )

        self.assertFalse(profile.supported)
        self.assertIn(
            ReasonCode.UNSUPPORTED_PEGASUS_VERSION,
            profile.unsupported_reasons,
        )

    def test_if_needed_is_still_htcondor_file_transfer(self):
        profile = detect_execution_model(
            valid_evidence(
                should_transfer_files="IF_NEEDED",
            )
        )

        self.assertTrue(profile.supported)

    def test_unsupported_profile_does_not_select_adapter(self):
        profile = detect_execution_model(
            valid_evidence(
                bypass_enabled=True,
            )
        )

        self.assertIsNone(profile.adapter_name)


if __name__ == "__main__":
    unittest.main()


import tempfile
from pathlib import Path

from pegasus_movement.execution_model import (
    build_execution_model_evidence_from_submits,
    is_pegasus_compute_submit,
)
from pegasus_movement.pegasus_source import parse_submit_file


class ExecutionModelEvidenceBuilderTests(unittest.TestCase):
    def write_submit(
        self,
        root: Path,
        name: str,
        text: str,
    ):
        path = root / name
        path.write_text(text, encoding="utf-8")
        return parse_submit_file(path)

    def compute_submit(
        self,
        root: Path,
        name: str = "arbitrary-name.sub",
        *,
        universe: str = "vanilla",
        cluster_size: str | None = "1",
        transfer_plugins: str | None = None,
    ):
        lines = [
            '+pegasus_wf_dax_job_id = "ID0000001"',
            '+pegasus_job_class = 1',
            '+pegasus_version = "5.1.2"',
            f"universe = {universe}",
            "should_transfer_files = YES",
            "when_to_transfer_output = ON_EXIT",
            "transfer_input_files = input.dat,runtime.tar.gz",
            "transfer_output_files = output.dat",
        ]

        if cluster_size is not None:
            lines.append(
                f"+pegasus_cluster_size = {cluster_size}"
            )

        if transfer_plugins is not None:
            lines.append(
                f"transfer_plugins = {transfer_plugins}"
            )

        lines.append("queue")

        return self.write_submit(
            root,
            name,
            "\n".join(lines) + "\n",
        )

    def test_compute_job_is_identified_semantically_not_by_filename(self):
        with tempfile.TemporaryDirectory() as td:
            submit = self.compute_submit(
                Path(td),
                name="totally-unrelated-name.sub",
            )

            self.assertTrue(
                is_pegasus_compute_submit(submit)
            )

    def test_literal_null_dax_id_is_not_compute(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            submit = self.write_submit(
                root,
                "anything.sub",
                """
+pegasus_wf_dax_job_id = "null"
+pegasus_job_class = 1
universe = vanilla
queue
""".lstrip(),
            )

            self.assertFalse(
                is_pegasus_compute_submit(submit)
            )

    def test_non_compute_job_class_is_not_compute(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            submit = self.write_submit(
                root,
                "anything.sub",
                """
+pegasus_wf_dax_job_id = "ID0000001"
+pegasus_job_class = 8
universe = local
queue
""".lstrip(),
            )

            self.assertFalse(
                is_pegasus_compute_submit(submit)
            )

    def test_auxiliary_submit_is_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            control = self.write_submit(
                root,
                "cleanup.sub",
                """
+pegasus_wf_xformation = "pegasus::cleanup"
+pegasus_wf_dax_job_id = "null"
+pegasus_job_class = 8
universe = local
should_transfer_files = NO
queue
""".lstrip(),
            )

            compute = self.compute_submit(
                root,
                "compute.sub",
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [control, compute]
                )
            )

            self.assertEqual(
                evidence.universe,
                "vanilla",
            )
            self.assertEqual(
                evidence.should_transfer_files,
                "YES",
            )

    def test_consistent_compute_values_are_extracted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            first = self.compute_submit(
                root,
                "one.sub",
            )
            second = self.compute_submit(
                root,
                "two.sub",
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [first, second]
                )
            )

            self.assertEqual(
                evidence.pegasus_version,
                "5.1.2",
            )
            self.assertEqual(
                evidence.universe,
                "vanilla",
            )
            self.assertEqual(
                evidence.should_transfer_files,
                "YES",
            )
            self.assertEqual(
                evidence.when_to_transfer_output,
                "ON_EXIT",
            )
            self.assertTrue(
                evidence.plugin_methods_known
            )
            self.assertEqual(
                evidence.plugin_methods,
                [],
            )

    def test_conflicting_universe_is_preserved_as_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            first = self.compute_submit(
                root,
                "one.sub",
                universe="vanilla",
            )
            second = self.compute_submit(
                root,
                "two.sub",
                universe="docker",
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [first, second]
                )
            )

            self.assertIsNone(evidence.universe)
            self.assertIn(
                "universe",
                evidence.conflicting_fields,
            )

    def test_cluster_size_one_means_not_clustered(self):
        with tempfile.TemporaryDirectory() as td:
            submit = self.compute_submit(
                Path(td),
                cluster_size="1",
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [submit]
                )
            )

            self.assertFalse(
                evidence.clustered_jobs
            )

    def test_cluster_size_greater_than_one_is_clustered(self):
        with tempfile.TemporaryDirectory() as td:
            submit = self.compute_submit(
                Path(td),
                cluster_size="2",
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [submit]
                )
            )

            self.assertTrue(
                evidence.clustered_jobs
            )

    def test_missing_cluster_size_remains_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            submit = self.compute_submit(
                Path(td),
                cluster_size=None,
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [submit]
                )
            )

            self.assertIsNone(
                evidence.clustered_jobs
            )

    def test_explicit_transfer_plugin_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            submit = self.compute_submit(
                Path(td),
                transfer_plugins=(
                    '"https=/opt/condor/libexec/https_plugin"'
                ),
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [submit]
                )
            )

            self.assertTrue(
                evidence.plugin_methods_known
            )
            self.assertTrue(
                evidence.plugin_methods
            )

    def test_submit_provenance_is_retained(self):
        with tempfile.TemporaryDirectory() as td:
            submit = self.compute_submit(
                Path(td),
            )

            evidence = (
                build_execution_model_evidence_from_submits(
                    [submit]
                )
            )

            attributes = {
                prov.attribute
                for prov in evidence.provenance
            }

            self.assertIn(
                "+pegasus_version",
                attributes,
            )
            self.assertIn(
                "universe",
                attributes,
            )


class ExecutionModelConflictDetectionTests(unittest.TestCase):
    def test_conflicting_evidence_rejects_profile(self):
        evidence = valid_evidence()
        evidence.conflicting_fields.append(
            "universe"
        )

        profile = detect_execution_model(evidence)

        self.assertFalse(profile.supported)
        self.assertIsNone(profile.adapter_name)
        self.assertIn(
            ReasonCode.CONFLICTING_EXECUTION_MODEL_EVIDENCE,
            profile.unsupported_reasons,
        )


if __name__ == "__main__":
    unittest.main()
