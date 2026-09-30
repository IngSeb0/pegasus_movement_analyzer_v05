import tempfile
import unittest
from pathlib import Path

from pegasus_movement.htcondor_source import (
    parse_history_file,
)
from pegasus_movement.normalize import (
    normalize_history_identities,
    normalize_history_identity,
    normalize_remote_host,
    strip_classad_quotes,
)


class IdentityNormalizationTests(unittest.TestCase):
    def write_history(self, text: str) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)

        path = Path(td.name) / "history.long"
        path.write_text(text, encoding="utf-8")
        return path

    def real_fixture(self) -> Path:
        return (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "distribution_real_reconstructed"
            / "trace"
            / "history.long"
        )

    def test_classad_quotes_are_removed_only_at_outer_boundary(self):
        self.assertEqual(
            strip_classad_quotes('"data_task_ID0000001"'),
            "data_task_ID0000001",
        )

    def test_slot_remote_host_normalizes_to_hostname(self):
        self.assertEqual(
            normalize_remote_host(
                '"slot1_1@pegasus-worker2"'
            ),
            "pegasus-worker2",
        )

    def test_plain_hostname_is_preserved(self):
        self.assertEqual(
            normalize_remote_host(
                '"worker.example.org"'
            ),
            "worker.example.org",
        )

    def test_real_fixture_resolves_exact_job_ids(self):
        parsed = parse_history_file(self.real_fixture())
        identities = normalize_history_identities(parsed)

        self.assertEqual(
            [item.job_id for item in identities],
            [
                "473.0",
                "477.0",
                "476.0",
                "479.0",
                "478.0",
            ],
        )

        self.assertEqual(
            [item.task_id for item in identities],
            [
                "data_task_ID0000001",
                "data_task_ID0000002",
                "data_task_ID0000003",
                "data_task_ID0000004",
                "data_task_ID0000005",
            ],
        )

    def test_real_fixture_resolves_locations_without_hardcoding(self):
        parsed = parse_history_file(self.real_fixture())
        identities = normalize_history_identities(parsed)

        self.assertEqual(
            [item.location_id for item in identities],
            [
                "pegasus-worker2",
                "pegasus-worker2",
                "pegasus-worker2",
                "pegasus-worker2",
                "pegasus-worker1",
            ],
        )

    def test_missing_job_identity_fails_closed(self):
        path = self.write_history(
            """
DAGNodeName = "task-A"
LastRemoteHost = "slot1@worker1"
""".lstrip()
        )

        parsed = parse_history_file(path)
        identity = normalize_history_identity(
            parsed.records[0]
        )

        self.assertIsNone(identity.job_id)
        self.assertIn(
            "missing_cluster_id",
            identity.issues,
        )
        self.assertIn(
            "missing_proc_id",
            identity.issues,
        )

    def test_conflicting_cluster_ids_are_ambiguous(self):
        path = self.write_history(
            """
ClusterId = 10
ClusterId = 11
ProcId = 0
DAGNodeName = "task-A"
LastRemoteHost = "slot1@worker1"
""".lstrip()
        )

        parsed = parse_history_file(path)
        identity = normalize_history_identity(
            parsed.records[0]
        )

        self.assertIsNone(identity.job_id)
        self.assertIn(
            "ambiguous_cluster_id",
            identity.issues,
        )

    def test_conflicting_remote_hosts_are_ambiguous(self):
        path = self.write_history(
            """
ClusterId = 10
ProcId = 0
DAGNodeName = "task-A"
LastRemoteHost = "slot1@worker1"
RemoteHost = "slot1@worker2"
""".lstrip()
        )

        parsed = parse_history_file(path)
        identity = normalize_history_identity(
            parsed.records[0]
        )

        self.assertIsNone(identity.location_id)
        self.assertIn(
            "ambiguous_remote_host",
            identity.issues,
        )

    def test_normalized_identity_retains_provenance(self):
        path = self.write_history(
            """
ClusterId = 10
ProcId = 0
DAGNodeName = "task-A"
LastRemoteHost = "slot1@worker1"
""".lstrip()
        )

        parsed = parse_history_file(path)
        identity = normalize_history_identity(
            parsed.records[0]
        )

        attributes = {
            provenance.attribute
            for provenance in identity.provenance
        }

        self.assertIn("clusterid", attributes)
        self.assertIn("procid", attributes)
        self.assertIn("dagnodename", attributes)
        self.assertIn("lastremotehost", attributes)


if __name__ == "__main__":
    unittest.main()


from pegasus_movement.normalize import (
    FileIdentityMethod,
    file_basename_for_display,
    normalize_meta_object_identity,
    resolve_file_identity,
)
from pegasus_movement.pegasus_source import ParsedMetaObject


class FileIdentityNormalizationTests(unittest.TestCase):
    def test_explicit_lfn_has_highest_precedence(self):
        identity = resolve_file_identity(
            explicit_lfns=["science/input.dat"],
            mapped_lfns=["mapped/other.dat"],
            physical_paths=["scratch/input.dat"],
        )

        self.assertTrue(identity.resolved)
        self.assertEqual(
            identity.file_id,
            "science/input.dat",
        )
        self.assertEqual(
            identity.resolution_method,
            FileIdentityMethod.EXPLICIT_LFN,
        )

    def test_explicit_mapping_precedes_physical_path(self):
        identity = resolve_file_identity(
            mapped_lfns=["workflow/input.dat"],
            physical_paths=["scratch/input.dat"],
        )

        self.assertEqual(
            identity.file_id,
            "workflow/input.dat",
        )
        self.assertEqual(
            identity.resolution_method,
            FileIdentityMethod.EXPLICIT_MAPPING,
        )

    def test_physical_path_fallback_keeps_full_path(self):
        identity = resolve_file_identity(
            physical_paths=["foo/input.dat"],
            physical_relation_unambiguous=True,
        )

        self.assertEqual(
            identity.file_id,
            "path:foo/input.dat",
        )
        self.assertNotEqual(
            identity.file_id,
            "input.dat",
        )
        self.assertEqual(
            identity.resolution_method,
            FileIdentityMethod.PHYSICAL_PATH,
        )


    def test_physical_path_alone_is_not_sufficient_identity(self):
        result = resolve_file_identity(
            physical_paths=[
                "/scratch/run0001/input.dat"
            ],
        )

        self.assertIsNone(result.file_id)
        self.assertIsNone(result.resolution_method)
        self.assertIn(
            "physical_path_not_semantically_resolved",
            result.issues,
        )

    def test_duplicate_basename_does_not_merge_files(self):
        left = resolve_file_identity(
            physical_paths=["foo/input.dat"],
        
            physical_relation_unambiguous=True,)
        right = resolve_file_identity(
            physical_paths=["bar/input.dat"],
        
            physical_relation_unambiguous=True,)

        self.assertEqual(
            file_basename_for_display(left),
            "input.dat",
        )
        self.assertEqual(
            file_basename_for_display(right),
            "input.dat",
        )

        self.assertNotEqual(
            left.file_id,
            right.file_id,
        )

    def test_conflicting_explicit_lfns_fail_closed(self):
        identity = resolve_file_identity(
            explicit_lfns=[
                "a.dat",
                "b.dat",
            ],
            physical_paths=["scratch/x.dat"],
        )

        self.assertFalse(identity.resolved)
        self.assertIsNone(identity.file_id)
        self.assertIn(
            "ambiguous_file_identity",
            identity.issues,
        )

    def test_multiple_unmapped_paths_are_ambiguous(self):
        identity = resolve_file_identity(
            physical_paths=[
                "dir-a/x.dat",
                "dir-b/x.dat",
            ],
        )

        self.assertFalse(identity.resolved)
        self.assertIn(
            "ambiguous_file_identity",
            identity.issues,
        )

    def test_remap_does_not_change_explicit_lfn(self):
        identity = resolve_file_identity(
            explicit_lfns=["logical/result.dat"],
            physical_paths=["scratch/result.tmp"],
            remap_from="result.tmp",
            remap_to="/final/result.dat",
        )

        self.assertEqual(
            identity.file_id,
            "logical/result.dat",
        )
        self.assertEqual(
            identity.remap_from,
            "result.tmp",
        )
        self.assertEqual(
            identity.remap_to,
            "/final/result.dat",
        )

    def test_meta_id_is_treated_as_explicit_lfn(self):
        obj = ParsedMetaObject(
            object_index=0,
            object_id="dist.chunk0.dat",
            attributes={"size": "2621440"},
            raw_object={
                "_id": "dist.chunk0.dat",
                "_attributes": {
                    "size": "2621440",
                },
            },
            raw_size="2621440",
            size_bytes=2621440,
        )

        identity = normalize_meta_object_identity(obj)

        self.assertEqual(
            identity.file_id,
            "dist.chunk0.dat",
        )
        self.assertEqual(
            identity.logical_name,
            "dist.chunk0.dat",
        )
        self.assertEqual(
            identity.resolution_method,
            FileIdentityMethod.EXPLICIT_LFN,
        )

    def test_no_identity_evidence_remains_unresolved(self):
        identity = resolve_file_identity()

        self.assertFalse(identity.resolved)
        self.assertIsNone(identity.file_id)
        self.assertIn(
            "missing_file_identity",
            identity.issues,
        )


if __name__ == "__main__":
    unittest.main()


from pegasus_movement.normalize import (
    LocationAliasRegistry,
    NormalizedHistoryIdentity,
    build_worker_locations,
    index_identity_relations,
)


class LocationAliasAndIdentityIndexTests(unittest.TestCase):
    def test_unregistered_location_is_not_guessed_as_alias(self):
        registry = LocationAliasRegistry()

        self.assertEqual(
            registry.resolve("worker1"),
            "worker1",
        )

    def test_documented_alias_maps_to_canonical_location(self):
        registry = LocationAliasRegistry()
        registry.register(
            "pegasus-worker1",
            aliases=["worker1"],
        )

        self.assertEqual(
            registry.resolve("worker1"),
            "pegasus-worker1",
        )
        self.assertEqual(
            registry.resolve("pegasus-worker1"),
            "pegasus-worker1",
        )

    def test_conflicting_alias_definition_is_rejected(self):
        registry = LocationAliasRegistry()

        registry.register(
            "pegasus-worker1",
            aliases=["worker"],
        )

        with self.assertRaises(ValueError):
            registry.register(
                "pegasus-worker2",
                aliases=["worker"],
            )

    def test_worker_locations_merge_only_with_documented_alias(self):
        identities = [
            NormalizedHistoryIdentity(
                record_index=0,
                task_id="T1",
                job_id="10.0",
                location_id="pegasus-worker1",
                raw_remote_hosts=[
                    '"slot1@pegasus-worker1"',
                ],
            ),
            NormalizedHistoryIdentity(
                record_index=1,
                task_id="T2",
                job_id="11.0",
                location_id="worker1",
                raw_remote_hosts=[
                    '"worker1"',
                ],
            ),
        ]

        without_aliases = build_worker_locations(
            identities
        )

        self.assertEqual(
            set(without_aliases),
            {
                "pegasus-worker1",
                "worker1",
            },
        )

        registry = LocationAliasRegistry()
        registry.register(
            "pegasus-worker1",
            aliases=["worker1"],
        )

        with_aliases = build_worker_locations(
            identities,
            registry,
        )

        self.assertEqual(
            set(with_aliases),
            {"pegasus-worker1"},
        )

    def test_same_job_claiming_two_tasks_is_detected(self):
        identities = [
            NormalizedHistoryIdentity(
                record_index=0,
                task_id="T1",
                job_id="10.0",
            ),
            NormalizedHistoryIdentity(
                record_index=1,
                task_id="T2",
                job_id="10.0",
            ),
        ]

        index = index_identity_relations(identities)

        self.assertEqual(
            index.conflicting_job_ids,
            {"10.0"},
        )

    def test_same_task_with_multiple_jobs_is_retry_candidate(self):
        identities = [
            NormalizedHistoryIdentity(
                record_index=0,
                task_id="T1",
                job_id="10.0",
            ),
            NormalizedHistoryIdentity(
                record_index=1,
                task_id="T1",
                job_id="11.0",
            ),
        ]

        index = index_identity_relations(identities)

        self.assertEqual(
            index.multi_job_task_ids,
            {"T1"},
        )

        # Important: I3 does not decide whether this is a valid retry.
        self.assertEqual(
            index.conflicting_job_ids,
            set(),
        )


if __name__ == "__main__":
    unittest.main()
