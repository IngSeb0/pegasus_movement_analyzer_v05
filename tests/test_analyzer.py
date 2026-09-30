import tempfile
import unittest
from pathlib import Path

from pegasus_movement.analyzer import MIB, analyze_run, parse_classad_history


class AnalyzerTests(unittest.TestCase):
    def fixture(self):
        return Path(__file__).resolve().parents[1] / "fixtures" / "distribution_real_reconstructed"

    def test_real_distribution_reconstructed(self):
        root = self.fixture()
        result = analyze_run(
            root / "run0001",
            history_file=root / "trace" / "history.long",
        )
        s = result["summary"]
        self.assertTrue(s["valid"], s["errors"])
        self.assertEqual(s["tasks"], 5)
        self.assertAlmostEqual(s["m_req_mib"], 22.5)
        self.assertAlmostEqual(s["m_obs_mib"], 40.0)
        self.assertAlmostEqual(s["observed_minus_required_mib"], 17.5)
        self.assertAlmostEqual(s["m_req_over_m_obs"], 0.5625)

        placement = {r["task"]: r["worker"] for r in result["placement"]}
        self.assertEqual(placement[1], "worker2")
        self.assertEqual(placement[2], "worker2")
        self.assertEqual(placement[3], "worker2")
        self.assertEqual(placement[4], "worker2")
        self.assertEqual(placement[5], "worker1")

        req = {r["logical_file"]: r for r in result["required_movement"] if r["edge_type"] == "intermediate"}
        self.assertEqual(req["dist.chunk0.dat"]["required_bytes"], 0)
        self.assertEqual(req["dist.chunk1.dat"]["required_bytes"], 0)
        self.assertEqual(req["dist.chunk2.dat"]["required_bytes"], 0)
        self.assertEqual(req["dist.chunk3.dat"]["required_bytes"], int(2.5 * MIB))

    def test_history_parser(self):
        root = self.fixture()
        p = parse_classad_history(root / "trace" / "history.long")
        self.assertEqual(p[1], "worker2")
        self.assertEqual(p[5], "worker1")

    def test_same_worker_pipeline_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run0001" / "00" / "00"
            run.mkdir(parents=True)
            (root / "inputs").mkdir()
            (root / "inputs" / "input.dat").write_bytes(b"x" * MIB)
            for tid, ins, outs in [
                (1, "data_task,input.dat", "stage1.dat"),
                (2, "data_task,stage1.dat", "stage2.dat"),
                (3, "data_task,stage2.dat", "final.dat"),
            ]:
                (run / f"data_task_ID{tid:07d}.sub").write_text(
                    f"transfer_input_files = {ins}\ntransfer_output_files = {outs}\n"
                )
                size = MIB
                (run / f"data_task_ID{tid:07d}.meta").write_text(
                    '[{"_id":"%s","_attributes":{"size":"%s"}}]' % (outs, size)
                )
            placement = root / "placement.tsv"
            placement.write_text("task\tworker\n" + "\n".join([f"data_task_ID{i:07d}\tworker2" for i in (1,2,3)]) + "\n")
            result = analyze_run(root / "run0001", placement_tsv=placement)
            s = result["summary"]
            self.assertTrue(s["valid"], s["errors"])
            self.assertAlmostEqual(s["m_req_mib"], 2.0)  # input + final
            self.assertAlmostEqual(s["m_obs_mib"], 6.0)  # 3 inputs + 3 outputs


if __name__ == "__main__":
    unittest.main()
