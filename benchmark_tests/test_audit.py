
import tempfile
import unittest
from pathlib import Path

from uav_benchmark.audit import audit_experiment
from uav_benchmark.io import dump_json


class AuditTests(unittest.TestCase):

    def setup_case(self, tmp):
        output = Path(tmp) / "results"
        output.mkdir()

        dump_json(output / "experiment.json", {
            "fingerprint": "test-fingerprint",
            "plan": {
                "speeds_mps": [2, 3],
                "noise_sigmas": [0],
                "seeds": [42, 43],
            },
            "scenes": {"scenes/test.json": "mock-hash"},
        })
        return output

    def test_all_four_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self.setup_case(tmp)

            completed = output / "run_00000"
            completed.mkdir()
            dump_json(completed / "result.metrics.json", {
                "metadata": {"raw_data_directory": "run_00000"}
            })

            failed = output / "run_00001"
            failed.mkdir()
            dump_json(failed / "error.json", {
                "exception_type": "RuntimeError",
                "message": "CUDA failure",
            })

            (output / "run_00002").mkdir()
            # run_00003 is missing entirely.

            report = audit_experiment(output)

            self.assertEqual(report["planned_runs"], 4)
            self.assertEqual(report["completed_runs"], 1)
            self.assertEqual(report["failed_runs"], 1)
            self.assertEqual(report["interrupted_runs"], 1)
            self.assertEqual(report["missing_runs"], 1)
            self.assertEqual(report["completion_percentage"], 25.0)
            self.assertEqual(
                [run["status"] for run in report["runs"]],
                ["completed", "failed", "interrupted", "missing"],
            )

    def test_successful_retry_preserves_failure_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self.setup_case(tmp)

            original = output / "run_00000"
            original.mkdir()
            dump_json(original / "error.json", {
                "exception_type": "RuntimeError",
                "message": "First attempt failed",
            })

            retry = output / "run_00000_attempt_1"
            retry.mkdir()

            dump_json(original / "result.metrics.json", {
                "metadata": {
                    "raw_data_directory": "run_00000_attempt_1"
                }
            })

            report = audit_experiment(output)
            run = report["runs"][0]

            self.assertEqual(run["status"], "completed")
            self.assertEqual(
                [attempt["status"] for attempt in run["attempts"]],
                ["failed", "completed"],
            )
            self.assertEqual(
                run["attempts"][0]["error"]["message"],
                "First attempt failed",
            )

    def test_latest_attempt_determines_incomplete_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self.setup_case(tmp)

            original = output / "run_00000"
            original.mkdir()
            dump_json(original / "error.json", {
                "exception_type": "RuntimeError",
                "message": "First attempt failed",
            })

            (output / "run_00000_attempt_1").mkdir()

            report = audit_experiment(output)
            run = report["runs"][0]

            self.assertEqual(run["status"], "interrupted")
            self.assertEqual(
                [attempt["status"] for attempt in run["attempts"]],
                ["failed", "interrupted"],
            )

    def test_audit_does_not_modify_experiment(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = self.setup_case(tmp)

            before = sorted(
                str(path.relative_to(output))
                for path in output.rglob("*")
            )

            audit_experiment(output)

            after = sorted(
                str(path.relative_to(output))
                for path in output.rglob("*")
            )
            self.assertEqual(before, after)
    
    def test_cli_generates_audit_report(self):
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            output = self.setup_case(tmp)
            audit_path = Path(tmp) / "experiment_audit.json"

            process = subprocess.run(
                [
                    sys.executable, "-m", "uav_benchmark",
                    "audit-experiment",
                    "--inputs", str(output),
                    "--out", str(audit_path),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(process.returncode, 1)
            self.assertTrue(audit_path.exists())

            report = __import__(
                "uav_benchmark.io", fromlist=["load_json"]
            ).load_json(audit_path)

            self.assertEqual(report["planned_runs"], 4)
            self.assertEqual(report["missing_runs"], 4)

    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                audit_experiment(tmp)


if __name__ == "__main__":
    unittest.main()
