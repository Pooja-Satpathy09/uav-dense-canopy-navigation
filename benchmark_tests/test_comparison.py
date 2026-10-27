import unittest
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from uav_benchmark.comparison import compare_results
from uav_benchmark.demo import demo
from uav_benchmark.io import load_json


class ComparisonTests(unittest.TestCase):
    def make_demo_results(self, tmp):
        demo_dir = Path(tmp) / "demo"
        demo(demo_dir)
        return [
            load_json(f)
            for f in sorted(demo_dir.glob("*.metrics.json"))
        ], demo_dir

    def test_demo_results_are_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            results, _ = self.make_demo_results(tmp)
            report = compare_results(results)

            self.assertEqual(report["comparison_count"], 1)
            group = report["comparisons"][0]
            self.assertIn("synthetic", group["by_difficulty"])
            self.assertEqual(
                group["by_difficulty"]["synthetic"]["runs"], 4
            )

    def test_empty_results(self):
        report = compare_results([])
        self.assertEqual(report["comparison_count"], 0)

    def test_incompatible_sources_stay_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            results, _ = self.make_demo_results(tmp)
            results[0]["metadata"]["source"] = "different_source"

            report = compare_results(results)
            self.assertEqual(report["comparison_count"], 2)

    def test_easy_medium_hard_are_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            results, _ = self.make_demo_results(tmp)

            results[0]["difficulty"] = "easy"
            results[1]["difficulty"] = "medium"
            results[2]["difficulty"] = "hard"
            results[3]["difficulty"] = "easy"

            self.assertEqual(
                [r["difficulty"] for r in results[:3]],
                ["easy", "medium", "hard"],
            )

            report = compare_results(results)
            self.assertEqual(report["comparison_count"], 1)

            difficulties = set(
                report["comparisons"][0]["by_difficulty"]
            )
            self.assertEqual(
                difficulties, {"easy", "medium", "hard"}
            )

    def test_cli_writes_json_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, demo_dir = self.make_demo_results(tmp)
            json_out = Path(tmp) / "comparison.json"
            csv_out = Path(tmp) / "comparison.csv"

            process = subprocess.run(
                [
                    sys.executable, "-m", "uav_benchmark", "compare",
                    "--inputs", str(demo_dir),
                    "--out", str(json_out),
                    "--csv", str(csv_out),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(json_out.exists())
            self.assertTrue(csv_out.exists())

            report = json.loads(json_out.read_text())
            self.assertEqual(report["comparison_count"], 1)

            with csv_out.open(
                newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertGreater(len(rows), 0)
            self.assertIn("difficulty", rows[0])
            self.assertIn("metric", rows[0])


if __name__ == "__main__":
    unittest.main()
