"""Shadow launches are not scientific executions or completed deliveries."""
from pathlib import Path
import tempfile
import unittest

from pegasus_movement.analyzer_v1 import _attempt_contexts
from pegasus_movement.htcondor_source import build_transfer_evidence, parse_history_file
from pegasus_movement.model import TaskExecution


class ShadowLaunchSeparationTests(unittest.TestCase):
    def evidence(self, **changes):
        fields = {
            'ClusterId': '100', 'ProcId': '0', 'JobStatus': '4', 'ExitCode': '0',
            'JobRunCount': '2', 'NumShadowStarts': '2', 'NumJobStarts': '1',
            'NumInputTransferStarts': '1', 'NumOutputTransferStarts': '1',
            'LastRemoteHost': '"slot1@pegasus-worker1"',
            'TransferInputStats': '[ CedarSizeBytesTotal = 10; CedarFilesCountTotal = 2; CedarSizeBytesLastRun = 10; CedarFilesCountLastRun = 2 ]',
            'TransferOutputStats': '[ CedarSizeBytesTotal = 20; CedarFilesCountTotal = 3; CedarSizeBytesLastRun = 20; CedarFilesCountLastRun = 3 ]',
        }
        fields.update(changes)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'history.long'
            path.write_text('\n'.join(f'{k} = {v}' for k, v in fields.items() if v is not None) + '\n', encoding='utf-8')
            return build_transfer_evidence(parse_history_file(path), scientific_job_ids={'100.0'})

    def test_two_shadows_one_execution_and_transfer_pair_are_separable(self):
        records = self.evidence()
        self.assertEqual([e.attempt_context for e in records], ['attempt:1', 'attempt:1'])
        self.assertEqual(records[0].raw_stats['job_run_count'], 2)
        self.assertEqual(records[0].raw_stats['num_input_transfer_starts'], 1)
        self.assertEqual(records[0].raw_stats['num_shadow_starts'], 2)

    def test_two_executions_remain_unseparable(self):
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(NumJobStarts='2')))

    def test_repeated_input_transfer_remains_unseparable(self):
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(NumInputTransferStarts='2')))

    def test_repeated_output_transfer_remains_unseparable(self):
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(NumOutputTransferStarts='2')))

    def test_missing_transfer_counter_does_not_resolve_extra_launches(self):
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(NumInputTransferStarts=None)))

    def test_extra_bytes_in_total_do_not_resolve_extra_launches(self):
        stats = '[ CedarSizeBytesTotal = 30; CedarFilesCountTotal = 4; CedarSizeBytesLastRun = 10; CedarFilesCountLastRun = 2 ]'
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(TransferInputStats=stats)))

    def test_contradictory_legacy_alias_does_not_resolve_launches(self):
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(NumShadowStarts='3')))

    def test_unknown_protocol_does_not_resolve_extra_launches(self):
        stats = '[ HttpSizeBytesTotal = 10; HttpFilesCountTotal = 2; HttpSizeBytesLastRun = 10; HttpFilesCountLastRun = 2 ]'
        self.assertTrue(all(e.attempt_context is None for e in self.evidence(TransferInputStats=stats)))

    def test_manifest_context_uses_execution_counter_not_shadow_alias(self):
        task = TaskExecution(task_id='T1', pegasus_node_id='merge', job_id='100.0', job_run_count=2, num_job_starts=1)
        self.assertEqual(_attempt_contexts({'T1': task}), {'100.0': 'attempt:1'})


if __name__ == '__main__':
    unittest.main()
