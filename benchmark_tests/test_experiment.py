import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uav_benchmark.experiment import experiment
from uav_benchmark.io import dump_json, load_json
from uav_benchmark.metrics import evaluate_run
from test_metrics import CONFIG, scene, straight


class ExperimentTests(unittest.TestCase):
    def setup_case(self, tmp):
        root = Path(tmp)
        dump_json(root/"scenes/test.json", scene())
        dump_json(root/"config.json", CONFIG.to_dict())
        dump_json(root/"plan.json", {"config": "config.json", "scene_glob": "scenes/*.json",
                                  "speeds_mps": [2], "noise_sigmas": [0], "seeds": [42]})
        checkpoint = root/"checkpoint.pth"
        checkpoint.write_bytes(b"mock-weights-for-orchestration-test")
        return root, checkpoint

    def fake_rollout(self, *args, **kwargs):
        result = evaluate_run(straight(), scene(), CONFIG,
                              metadata={"source": "mock", "run_fingerprint": "fake-one"})
        return straight(), scene(), result

    def test_resuming_does_not_rerun_completed_flight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, checkpoint = self.setup_case(tmp)
            with patch("uav_benchmark.experiment.run_diffphys", side_effect=self.fake_rollout) as runner:
                experiment(root, checkpoint, root/"plan.json", root/"results")
                report = experiment(root, checkpoint, root/"plan.json", root/"results", resume=True)
                self.assertEqual(runner.call_count, 1)
                self.assertEqual(report["completed_result_files"], 1)

    def test_checkpoint_change_rejects_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, checkpoint = self.setup_case(tmp)
            with patch("uav_benchmark.experiment.run_diffphys", side_effect=self.fake_rollout):
                experiment(root, checkpoint, root/"plan.json", root/"results")
            checkpoint.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                experiment(root, checkpoint, root/"plan.json", root/"results", resume=True)

    def test_failure_logged_and_resumed_in_new_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, checkpoint = self.setup_case(tmp)
            with patch("uav_benchmark.experiment.run_diffphys", side_effect=RuntimeError("mock CUDA failure")):
                report = experiment(root, checkpoint, root/"plan.json", root/"results")
                self.assertEqual(len(report["attempt_errors"]), 1)
            with patch("uav_benchmark.experiment.run_diffphys", side_effect=self.fake_rollout):
                report = experiment(root, checkpoint, root/"plan.json", root/"results", resume=True)
            self.assertEqual(report["completed_result_files"], 1)
            self.assertTrue((root/"results/run_00000/error.json").exists())
            self.assertTrue((root/"results/run_00000_attempt_1/trajectory.csv").exists())


if __name__ == "__main__":
    unittest.main()
