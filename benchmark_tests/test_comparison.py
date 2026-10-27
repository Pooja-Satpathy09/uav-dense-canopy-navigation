import unittest

from uav_benchmark.comparison import compare_results
from uav_benchmark.demo import demo
from uav_benchmark.io import load_json
from pathlib import Path
import tempfile


class ComparisonTests(unittest.TestCase):
    def test_demo_results_are_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            demo_dir = Path(tmp) / "demo"
            demo(demo_dir)

            results = [
                load_json(p)
                for p in demo_dir.glob("*.metrics.json")
            ]
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
            demo_dir = Path(tmp) / "demo"
            demo(demo_dir)

            results = [
                load_json(p)
                for p in demo_dir.glob("*.metrics.json")
            ]
            results[0]["metadata"]["source"] = "different_source"

            report = compare_results(results)
            self.assertEqual(report["comparison_count"], 2)


if __name__ == "__main__":
    unittest.main()
