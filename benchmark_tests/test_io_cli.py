import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uav_benchmark import Sample
from uav_benchmark.aggregate import summarize, wilson
from uav_benchmark.batch import evaluate_manifest
from uav_benchmark.demo import demo
from uav_benchmark.io import dump_json, load_json, load_trajectory, parse_bool, save_trajectory
from uav_benchmark.metrics import evaluate_run
from test_metrics import CONFIG, scene, straight


class IoTests(unittest.TestCase):
    def test_boolean_parsing(self):
        self.assertFalse(parse_bool("False"))
        self.assertFalse(parse_bool("0"))
        self.assertTrue(parse_bool("True"))
        with self.assertRaises(ValueError):
            parse_bool("maybe")

    def test_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"flight.csv"
            save_trajectory(path, straight(), scene(), "one")
            samples = load_trajectory(path, scene())
            self.assertEqual(samples, straight())
            self.assertFalse(samples[0].collision)

    def test_scene_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"flight.csv"
            save_trajectory(path, straight(), scene(), "one")
            with self.assertRaises(ValueError):
                load_trajectory(path, scene(scene_id="other"))

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"bad.json"
            path.write_text('{"x": NaN}')
            with self.assertRaises(ValueError):
                load_json(path)

    def test_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"output.json"
            dump_json(path, {"first": True})
            with self.assertRaises(FileExistsError):
                dump_json(path, {"second": True})
            self.assertEqual(load_json(path), {"first": True})


class StatisticsTests(unittest.TestCase):
    def test_wilson_all_success_is_not_zero_uncertainty(self):
        lo, hi = wilson([1]*10)
        self.assertLess(lo, 1)
        self.assertAlmostEqual(hi, 1)

    def test_incomplete_and_numerical_failures_excluded_from_rates(self):
        success = evaluate_run(straight(), scene(), CONFIG, metadata={"source": "synthetic"})
        partial = evaluate_run(straight()[:3], scene(), CONFIG, metadata={"source": "synthetic"})
        numerical = dict(partial, termination="numerical_failure")
        group = summarize([success, partial, numerical])["groups"][0]
        self.assertEqual(group["eligible_runs"], 1)
        self.assertEqual(group["incomplete_or_numerical"], 2)
        self.assertEqual(group["termination_counts"], {
            "goal_reached": 1, "incomplete": 1, "numerical_failure": 1,
        })
        self.assertEqual(group["metrics"]["goal_success"]["mean"], 1)

    def test_duplicate_runs_rejected(self):
        result = evaluate_run(straight(), scene(), CONFIG, metadata={"run_fingerprint": "abc"})
        with self.assertRaises(ValueError):
            summarize([result, result])

    def test_different_sources_are_not_pooled(self):
        a = evaluate_run(straight(), scene(), CONFIG, metadata={"source": "synthetic"})
        b = evaluate_run(straight(), scene(), CONFIG, metadata={"source": "diffphys_cuda"})
        self.assertEqual(len(summarize([a, b])["groups"]), 2)


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, "-m", "uav_benchmark", *args], text=True, capture_output=True)

    def test_cpu_demo_and_saved_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/"demo"
            process = self.invoke("demo", "--out", str(output))
            self.assertEqual(process.returncode, 0, process.stderr)
            result = load_json(output/"success.metrics.json")
            self.assertEqual(result["metrics"]["relative_gap_size"]["value"], 2.5)
            self.assertEqual(result["metrics"]["average_speed_mps"]["value"], 2)
            self.assertEqual(result["metrics"]["goal_success"]["value"], 1)

    def test_evaluate_existing_csv_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = demo(Path(tmp)/"demo")
            process = self.invoke("evaluate", "--trajectory", str(output/"success.csv"),
                "--scene", str(output/"scene.json"), "--config", str(output/"config.json"),
                "--out", str(Path(tmp)/"evaluated.json"))
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(load_json(Path(tmp)/"evaluated.json")["termination"], "goal_reached")

    def test_medium_near_goal_boundary_exit(self):
        root = Path(__file__).resolve().parents[1]
        scene_path = root/"scenes/medium_seed_42.json"
        medium = load_json(scene_path)
        # Hand-built geometry fixture on the checked-in medium scene.
        positions = [tuple(medium["start"]), (0, -6.5, 5.5), (20, -6.5, 5.5),
                     (19.5, .75, 1.5), (20.9, .75, 1.5)]
        samples = [Sample(t, p, (0, 0, 0)) for t, p in enumerate(positions)]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            trajectory = folder/"trajectory.csv"
            output = folder/"medium.metrics.json"
            save_trajectory(trajectory, samples, medium, "synthetic_medium_exit")
            process = self.invoke("evaluate", "--trajectory", str(trajectory),
                                  "--scene", str(scene_path), "--source", "synthetic",
                                  "--out", str(output))
            self.assertEqual(process.returncode, 0, process.stderr)
            result = load_json(output)
            summary = folder/"summary.json"
            process = self.invoke("summarize", "--inputs", str(folder), "--out", str(summary))
            self.assertEqual(process.returncode, 0, process.stderr)
            group = load_json(summary)["groups"][0]

        self.assertEqual(result["difficulty"], "medium")
        self.assertEqual(result["termination"], "out_of_bounds")
        self.assertEqual(len(result["metrics"]), 10)
        self.assertEqual(result["metrics"]["goal_success"]["value"], 0)
        self.assertEqual(result["metrics"]["collision"]["value"], 0)
        self.assertGreater(result["metrics"]["min_obstacle_clearance_m"]["value"], 0)
        self.assertEqual(result["metrics"]["relative_gap_size"]["status"], "not_applicable")
        diagnostics = result["diagnostics"]
        # The segment passes 0.75 m from the goal. The closest logged point is farther.
        self.assertAlmostEqual(diagnostics["closest_sampled_goal_distance_m"], (.5**2 + .75**2)**.5)
        self.assertEqual(diagnostics["closest_sampled_goal_time_s"], 3)
        self.assertAlmostEqual(diagnostics["final_goal_distance_m"], (.9**2 + .75**2)**.5)
        self.assertEqual(group["termination_counts"], {"out_of_bounds": 1})
        self.assertEqual(group["eligible_runs"], 1)

    def test_offline_batch_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = demo(Path(tmp)/"demo")
            results = evaluate_manifest(output/"manifest.json", Path(tmp)/"batch")
            summary = load_json(Path(tmp)/"batch/summary.json")
            self.assertEqual(len(results), 4)
            self.assertEqual(summary["groups"][0]["eligible_runs"], 3)

    def test_summarize_command_and_flat_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = demo(Path(tmp)/"demo")
            process = self.invoke("summarize", "--inputs", str(output), "--out", str(Path(tmp)/"summary.json"),
                                  "--csv", str(Path(tmp)/"runs.csv"))
            self.assertEqual(process.returncode, 0, process.stderr)
            with (Path(tmp)/"runs.csv").open(newline="") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 4)

    def test_invalid_input_returns_nonzero(self):
        result = self.invoke("evaluate", "--trajectory", "not-present.csv", "--scene", "not-present.json", "--out", "unused.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR", result.stderr)


if __name__ == "__main__":
    unittest.main()
