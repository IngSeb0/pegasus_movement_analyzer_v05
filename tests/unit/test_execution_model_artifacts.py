import json
import tempfile
import unittest
from pathlib import Path

from pegasus_movement.execution_model import (
    build_execution_model_evidence_from_run,
    detect_execution_model,
)
from pegasus_movement.diagnostics import ReasonCode


class ExecutionModelArtifactEvidenceTests(unittest.TestCase):
    def make_run(
        self,
        root: Path,
        *,
        shared: bool = False,
        bypass: bool | None = None,
        when_output: str = "ON_EXIT",
    ):
        run = root / "run0001"
        run.mkdir()

        (run / "braindump.yml").write_text(
            'submit_hostname: "pegasus-master"\n',
            encoding="utf-8",
        )

        (run / "wf.metrics").write_text(
            json.dumps(
                {"data_config": "condorio"}
            ),
            encoding="utf-8",
        )

        workflow = [
            "sites:",
            "  - name: condorpool",
            f"    sharedFileSystem: {str(shared).lower()}",
            "jobs:",
            "  - id: ID0000001",
        ]

        if bypass is not None:
            workflow.append(
                f"    bypass: {str(bypass).lower()}"
            )

        (run / "workflow.yml").write_text(
            "\n".join(workflow) + "\n",
            encoding="utf-8",
        )

        (run / "pegasus.1.properties").write_text(
            "# Pegasus runtime properties\n",
            encoding="utf-8",
        )

        (run / "compute.sub").write_text(
            "\n".join(
                [
                    '+pegasus_wf_dax_job_id = "ID0000001"',
                    '+pegasus_job_class = 1',
                    '+pegasus_version = "5.1.2"',
                    "+pegasus_cluster_size = 1",
                    "universe = vanilla",
                    "should_transfer_files = YES",
                    f"when_to_transfer_output = {when_output}",
                    "transfer_input_files = input.dat",
                    "transfer_output_files = output.dat",
                    "queue",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        history = root / "condor_history.long"
        history.write_text(
            (
                'CondorVersion = '
                '"$CondorVersion: 25.12.2 2026-07-20 '
                'BuildID: 933077 $"\n'
            ),
            encoding="utf-8",
        )

        return run, history

    def test_real_artifact_shape_builds_supported_profile(self):
        with tempfile.TemporaryDirectory() as td:
            run, history = self.make_run(
                Path(td)
            )

            evidence = (
                build_execution_model_evidence_from_run(
                    run,
                    history_path=history,
                )
            )

            self.assertEqual(
                evidence.data_configuration,
                "condorio",
            )
            self.assertEqual(
                evidence.submit_host,
                "pegasus-master",
            )
            self.assertEqual(
                evidence.htcondor_version,
                "25.12.2",
            )
            self.assertFalse(
                evidence.shared_filesystem
            )
            self.assertFalse(
                evidence.bypass_enabled
            )
            self.assertEqual(
                evidence.universe,
                "vanilla",
            )

            profile = detect_execution_model(
                evidence
            )

            self.assertTrue(profile.supported)

    def test_explicit_bypass_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            run, history = self.make_run(
                Path(td),
                bypass=True,
            )

            evidence = (
                build_execution_model_evidence_from_run(
                    run,
                    history_path=history,
                )
            )

            profile = detect_execution_model(
                evidence
            )

            self.assertFalse(profile.supported)
            self.assertIn(
                ReasonCode.UNSUPPORTED_BYPASS,
                profile.unsupported_reasons,
            )

    def test_shared_filesystem_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            run, history = self.make_run(
                Path(td),
                shared=True,
            )

            evidence = (
                build_execution_model_evidence_from_run(
                    run,
                    history_path=history,
                )
            )

            profile = detect_execution_model(
                evidence
            )

            self.assertFalse(profile.supported)
            self.assertIn(
                ReasonCode.UNSUPPORTED_SHARED_FS,
                profile.unsupported_reasons,
            )

    def test_non_on_exit_output_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            run, history = self.make_run(
                Path(td),
                when_output="ON_EXIT_OR_EVICT",
            )

            evidence = (
                build_execution_model_evidence_from_run(
                    run,
                    history_path=history,
                )
            )

            profile = detect_execution_model(
                evidence
            )

            self.assertFalse(profile.supported)
            self.assertIn(
                ReasonCode.UNSUPPORTED_WHEN_TO_TRANSFER_OUTPUT,
                profile.unsupported_reasons,
            )


if __name__ == "__main__":
    unittest.main()
