import unittest
import math

from uav_benchmark.aggregate import (
    wilson,
    percentile,
    describe,
    cluster_interval,
)


class WilsonTests(unittest.TestCase):

    def test_empty_input(self):
        self.assertIsNone(wilson([]))

    def test_all_success(self):
        lo, hi = wilson([1] * 10)
        self.assertLess(lo, 1)
        self.assertAlmostEqual(hi, 1)

    def test_all_failure(self):
        lo, hi = wilson([0] * 10)
        self.assertAlmostEqual(lo, 0)
        self.assertGreater(hi, 0)

    def test_half_success(self):
        lo, hi = wilson([1, 0, 1, 0])
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_single_success(self):
        lo, hi = wilson([1])
        self.assertGreaterEqual(lo, 0)
        self.assertLessEqual(hi, 1)


class PercentileTests(unittest.TestCase):

    def test_minimum_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0), 1)

    def test_maximum_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 1), 5)

    def test_median_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4, 5], 0.5), 3)

    def test_interpolation(self):
        self.assertEqual(percentile([1, 3], 0.25), 1.5)

    def test_unsorted_input(self):
        self.assertEqual(percentile([5, 1, 4, 2, 3], 0.5), 3)


class DescribeTests(unittest.TestCase):

    def test_empty_values(self):
        result = describe([])
        self.assertEqual(result["n"], 0)
        self.assertIsNone(result["mean"])

    def test_single_value(self):
        result = describe([5])
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["mean"], 5)
        self.assertIsNone(result["std"])

    def test_known_statistics(self):
        result = describe([1, 2, 3, 4, 5])

        self.assertEqual(result["n"], 5)
        self.assertEqual(result["mean"], 3)
        self.assertEqual(result["median"], 3)
        self.assertEqual(result["std"], math.sqrt(2.5))
        self.assertEqual(result["p05"], 1.2)
        self.assertEqual(result["p95"], 4.8)

    def test_unsorted_values(self):
        result = describe([5, 1, 4, 2, 3])
        self.assertEqual(result["median"], 3)


class ClusterIntervalTests(unittest.TestCase):

    def test_single_cluster_returns_none(self):
        pairs = [("scene1", 1), ("scene1", 0)]
        self.assertIsNone(cluster_interval(pairs))

    def test_multiple_clusters_return_interval(self):
        pairs = [
            ("scene1", 1),
            ("scene2", 0),
            ("scene3", 1),
        ]

        result = cluster_interval(pairs)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertLessEqual(result[0], result[1])

    def test_reproducible_results(self):
        pairs = [
            ("scene1", 1),
            ("scene2", 0),
            ("scene3", 1),
            ("scene4", 1),
        ]

        first = cluster_interval(pairs)
        second = cluster_interval(pairs)

        self.assertEqual(first, second)

    def test_repeated_runs_within_scene(self):
        pairs = [
            ("scene1", 1),
            ("scene1", 0),
            ("scene2", 1),
            ("scene2", 1),
        ]

        result = cluster_interval(pairs)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
