import json
from pathlib import Path
import tempfile
import unittest

import yaml

from pegasus_movement.grouping import resolve_task_job_mapping
from pegasus_movement.pegasus_source import parse_submit_file
from pegasus_movement.execution_model import build_execution_model_evidence_from_submits, detect_execution_model
from pegasus_movement.analyzer_v1 import _task_executions
from pegasus_movement.htcondor_source import parse_history_file


class GroupingMappingTests(unittest.TestCase):
    def fixture(self, root, order=('T1','T2'), size=2):
        raw={'jobs':[
            {'id':'T1','uses':[{'lfn':'A','type':'input'},{'lfn':'f','type':'output'}]},
            {'id':'T2','uses':[{'lfn':'f','type':'input'},{'lfn':'B','type':'output','stageOut':True}]}],
            'jobDependencies':[{'id':'T1','children':['T2']}]}
        wf=root/'workflow.yml';wf.write_text(yaml.safe_dump(raw),encoding='utf-8')
        sub=root/'merge_group.sub'
        sub.write_text('\n'.join([
            '+pegasus_job_class = 1','+pegasus_wf_dag_job_id = "merge_group"',
            '+pegasus_wf_dax_job_id = "null"','+pegasus_wf_xformation = "pegasus::seqexec"',
            f'+pegasus_cluster_size = {size}','+pegasus_version = "5.1.2"',
            'universe = vanilla','should_transfer_files = YES','when_to_transfer_output = ON_EXIT',
            'transfer_input_files = A','transfer_output_files = f,B','queue'])+'\n',encoding='utf-8')
        sub.with_suffix('.in').write_text(''.join(f'#@ {i} program {t}\npegasus-kickstart -n program -N {t} ./program\n' for i,t in enumerate(order,1)),encoding='utf-8')
        return wf,sub

    def test_preserves_two_scientific_ids_for_one_node(self):
        with tempfile.TemporaryDirectory() as td:
            wf,sub=self.fixture(Path(td))
            m=resolve_task_job_mapping(wf,[parse_submit_file(sub)])
            self.assertTrue(m.complete)
            self.assertEqual(m.task_to_node,{'T1':'merge_group','T2':'merge_group'})
            self.assertEqual(m.node_members['merge_group'],['T1','T2'])
            self.assertTrue(any(p.source_hash for p in m.provenance))

    def test_missing_native_members_remains_closed(self):
        with tempfile.TemporaryDirectory() as td:
            wf,sub=self.fixture(Path(td));sub.with_suffix('.in').unlink()
            m=resolve_task_job_mapping(wf,[parse_submit_file(sub)])
            self.assertFalse(m.complete);self.assertEqual(m.task_to_node,{})

    def test_reverse_dependency_order_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            wf,sub=self.fixture(Path(td),order=('T2','T1'))
            self.assertFalse(resolve_task_job_mapping(wf,[parse_submit_file(sub)]).complete)

    def test_annotation_command_disagreement_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            wf,sub=self.fixture(Path(td));p=sub.with_suffix('.in')
            p.write_text(p.read_text().replace('-N T1','-N T2'),encoding='utf-8')
            self.assertFalse(resolve_task_job_mapping(wf,[parse_submit_file(sub)]).complete)

    def test_member_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            wf,sub=self.fixture(Path(td),size=3)
            self.assertFalse(resolve_task_job_mapping(wf,[parse_submit_file(sub)]).complete)

    def test_duplicate_membership_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);wf,sub=self.fixture(root)
            other=root/'single.sub'
            other.write_text('+pegasus_job_class=1\n+pegasus_wf_dag_job_id="single"\n+pegasus_wf_dax_job_id="T1"\n+pegasus_cluster_size=1\n',encoding='utf-8')
            m=resolve_task_job_mapping(wf,[parse_submit_file(sub),parse_submit_file(other)])
            self.assertFalse(m.complete);self.assertEqual(m.node_members,{})

    def test_group_sizes_can_differ_between_jobs_without_false_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);wf,sub=self.fixture(root)
            other=root/'single.sub'
            other.write_text(sub.read_text().replace('= 2','= 1').replace('"merge_group"','"single"').replace('"null"','"T3"'),encoding='utf-8')
            evidence=build_execution_model_evidence_from_submits([parse_submit_file(sub),parse_submit_file(other)])
            self.assertTrue(evidence.clustered_jobs)
            self.assertNotIn('clustered_jobs',evidence.conflicting_fields)
            self.assertFalse(detect_execution_model(evidence).supported)

    def test_observed_job_maps_to_two_members_without_fictitious_attempts(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'history.long'
            p.write_text('ClusterId = 7\nProcId = 0\nDAGNodeName = "merge_group"\nLastRemoteHost = "slot1@worker1"\nJobStatus = 4\nExitCode = 0\nExitBySignal = false\nJobRunCount = 1\nNumJobStarts = 1\n',encoding='utf-8')
            tasks,errors=_task_executions(parse_history_file(p),scientific_task_ids=['T1','T2'],scientific_node_map={'T1':'merge_group','T2':'merge_group'})
            self.assertFalse(errors)
            self.assertEqual(set(tasks),{'T1','T2'})
            self.assertEqual({t.job_id for t in tasks.values()},{'7.0'})
            self.assertEqual({t.worker_location_id for t in tasks.values()},{'worker1'})

    def test_preserved_pegasus_512_native_group(self):
        root=Path(__file__).resolve().parents[1]/'fixtures'/'pegasus_grouping_u02'
        workflow=root/'workflow_for_plan.yml'
        submit=root/'merge_reuse_T01_T02.sub'
        individual=root/'campaign_task_T03.sub'
        result=resolve_task_job_mapping(workflow,[parse_submit_file(submit),parse_submit_file(individual)])
        self.assertTrue(result.complete,[d.message for d in result.diagnostics])
        self.assertEqual(set(result.task_to_node),{'T01','T02','T03'})
        self.assertEqual(result.task_to_node['T01'],result.task_to_node['T02'])
        self.assertNotEqual(result.task_to_node['T01'],result.task_to_node['T03'])


if __name__=='__main__':unittest.main()
