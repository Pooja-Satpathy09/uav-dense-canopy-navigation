import math
import unittest
from dataclasses import replace
from uav_benchmark import RunConfig, Sample, evaluate_run, evaluate_scene
from uav_benchmark.geometry import clearance, segment_clearance
from uav_benchmark.registry import REGISTRY


def scene(**updates):
    value = {"scene_id": "test", "difficulty": "test", "start": [0, 0, 1.5], "goal": [10, 0, 1.5],
             "drone_radius": .2, "bounds": [[-1, 11], [-3, 3], [-1, 5]], "obstacles": []}
    value.update(updates)
    return value


CONFIG = RunConfig(traversability_grid=1, traversability_headings=4, traversability_step_m=.5)


def straight():
    return [Sample(i, (2*i, 0, 1.5), (2, 0, 0), reached_goal=i==5) for i in range(6)]


def values(result):
    return {name: metric["value"] for name, metric in result["metrics"].items()}


class MetricTests(unittest.TestCase):
    def test_exactly_ten_core_metrics(self):
        result = evaluate_run(straight(), scene(), CONFIG)
        self.assertEqual(len(result["metrics"]), 10)
        self.assertEqual({s.scope for s in REGISTRY.values()}, {"scene", "flight"})

    def test_known_straight_flight(self):
        result = evaluate_run(straight(), scene(), CONFIG)
        v = values(result)
        self.assertEqual(v["goal_success"], 1)
        self.assertEqual(v["collision"], 0)
        self.assertEqual(v["path_excess_factor"], 0)
        self.assertEqual(v["average_speed_mps"], 2)
        self.assertEqual(v["relative_end_distance"], 0)
        self.assertEqual(v["speed_rmse_mps"], 0)
        self.assertEqual(v["jerk_rms_mps3"], 0)
        self.assertEqual(result["diagnostics"]["path_length_m"], 10)
        self.assertEqual(result["diagnostics"]["duration_s"], 5)

    def test_incomplete_halfway(self):
        result = evaluate_run([Sample(0, (0, 0, 1.5), (1, 0, 0)), Sample(5, (5, 0, 1.5), (1, 0, 0))], scene(), CONFIG)
        self.assertEqual(result["termination"], "incomplete")
        self.assertFalse(result["complete"])
        self.assertEqual(values(result)["relative_end_distance"], .5)
        self.assertEqual(values(result)["path_excess_factor"], -.5)

    def test_stationary_timeout(self):
        result = evaluate_run([Sample(0, (0, 0, 1.5), (0, 0, 0)), Sample(12, (0, 0, 1.5), (0, 0, 0))], scene(), CONFIG)
        self.assertEqual(result["termination"], "timeout")
        self.assertEqual(values(result)["average_speed_mps"], 0)
        self.assertEqual(values(result)["speed_rmse_mps"], 2)

    def test_zero_duration(self):
        result = evaluate_run(straight()[:1], scene(), CONFIG)
        for key in ("average_speed_mps", "speed_rmse_mps", "jerk_rms_mps3"):
            self.assertEqual(result["metrics"][key]["status"], "undefined")

    def test_start_at_goal(self):
        result = evaluate_run([Sample(0, (0, 0, 1.5), (0, 0, 0), reached_goal=True)], scene(goal=[0, 0, 1.5]), CONFIG)
        self.assertEqual(result["termination"], "goal_reached")
        self.assertEqual(result["metrics"]["relative_end_distance"]["status"], "undefined")

    def test_constant_acceleration_irregular_timestamps(self):
        samples = [Sample(t, (t*t/2, 0, 1.5), (t, 0, 0)) for t in (0, .3, 1, 2)]
        result = evaluate_run(samples, scene(), CONFIG)
        self.assertAlmostEqual(values(result)["jerk_rms_mps3"], 0, places=12)

    def test_known_nonzero_jerk_irregular_timestamps(self):
        # v(t)=1.5*t^2 -> acceleration=3t -> jerk=3 m/s^3.
        samples = [Sample(t, (.5*t**3, 0, 1.5), (1.5*t*t, 0, 0)) for t in (0, .25, .75, 1.5)]
        result = evaluate_run(samples, scene(), CONFIG)
        self.assertAlmostEqual(values(result)["jerk_rms_mps3"], 3, places=12)

    def test_right_endpoint_time_weighted_speed(self):
        samples = [Sample(0, (0, 0, 1.5), (2, 0, 0)), Sample(1, (1, 0, 1.5), (1, 0, 0)), Sample(4, (4, 0, 1.5), (4, 0, 0))]
        self.assertAlmostEqual(values(evaluate_run(samples, scene(), CONFIG))["speed_rmse_mps"], math.sqrt(13/4))

    def test_sphere_crossing_between_samples(self):
        s = scene(obstacles=[{"type": "sphere", "center": [5, 0, 1.5], "radius": 1}])
        samples = [Sample(0, (0, 0, 1.5), (10, 0, 0)), Sample(1, (10, 0, 1.5), (10, 0, 0), reached_goal=True)]
        result = evaluate_run(samples, s, CONFIG)
        self.assertEqual(result["termination"], "collision")
        self.assertAlmostEqual(values(result)["min_obstacle_clearance_m"], -1.2)

    def test_goal_and_contact_collision_wins(self):
        samples = straight()
        samples[-1] = replace(samples[-1], collision=True)
        result = evaluate_run(samples, scene(), CONFIG)
        self.assertEqual(values(result)["goal_success"], 0)
        self.assertEqual(values(result)["collision"], 1)

    def test_ground_is_separate_from_obstacles(self):
        result = evaluate_run(straight(), scene(), CONFIG)
        self.assertAlmostEqual(result["diagnostics"]["min_ground_clearance_m"], 2.3)
        self.assertEqual(result["metrics"]["min_obstacle_clearance_m"]["status"], "unbounded")

    def test_ground_collision(self):
        samples = [Sample(0, (0, 0, 1.5), (0, 0, 0)), Sample(1, (1, 0, -.9), (1, 0, -2.4))]
        self.assertEqual(evaluate_run(samples, scene(), CONFIG)["termination"], "collision")

    def test_false_goal_flag_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_run([Sample(0, (0, 0, 1.5), (0, 0, 0), reached_goal=True)], scene(), CONFIG)

    def test_out_of_bounds(self):
        samples = [Sample(0, (0, 0, 1.5), (0, 0, 0)), Sample(1, (0, 4, 1.5), (0, 4, 0))]
        self.assertEqual(evaluate_run(samples, scene(), CONFIG)["termination"], "out_of_bounds")

    def test_invalid_trajectories(self):
        cases = [[], [Sample(0, (0, 0, 1.5), (0, 0, 0))]*2,
                 [Sample(0, (0, 0, 1.5), (0, 0, 0)), Sample(1, (math.nan, 0, 1.5), (0, 0, 0))],
                 [Sample(0, (1, 0, 1.5), (0, 0, 0))],
                 [Sample(0, (0, 0, 1.5), (0, 0, 0), collision=True), Sample(1, (1, 0, 1.5), (0, 0, 0))]]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                evaluate_run(case, scene(), CONFIG)

    def test_invalid_scene_and_configuration(self):
        for bad in (scene(drone_radius=0), scene(bounds=[[1, 0], [-3, 3], [-1, 5]]),
                    scene(obstacles=[{"type": "sphere", "center": [2, 0, 0], "radius": -1}])):
            with self.assertRaises(ValueError):
                evaluate_scene(bad, CONFIG)
        with self.assertRaises(ValueError):
            evaluate_scene(scene(), replace(CONFIG, target_speed_mps=math.nan))


class GeometryTests(unittest.TestCase):
    def test_sphere_signed_distance(self):
        o = {"type": "sphere", "center": [0, 0, 0], "radius": 1}
        self.assertAlmostEqual(clearance((3, 0, 0), .2, o), 1.8)
        self.assertAlmostEqual(clearance((1.2, 0, 0), .2, o), 0)
        self.assertLess(clearance((1.1, 0, 0), .2, o), 0)

    def test_infinite_cylinder(self):
        o = {"type": "cylinder", "center": [0, 0, 0], "radius": 1}
        self.assertAlmostEqual(clearance((3, 0, 100), .2, o), 1.8)
        self.assertAlmostEqual(segment_clearance((-3, 0, 3), (3, 0, 3), .2, o), -1.2)

    def test_box_corner(self):
        o = {"type": "box", "center": [0, 0, 0], "half_extents": [1, 1, 1]}
        self.assertAlmostEqual(clearance((2, 2, 0), .2, o), math.sqrt(2)-.2)
        self.assertAlmostEqual(segment_clearance((-3, 0, 0), (3, 0, 0), .2, o), -1.2, places=10)

    def test_box_segment_tangent(self):
        o = {"type": "box", "center": [0, 0, 0], "half_extents": [1, 1, 1]}
        self.assertAlmostEqual(segment_clearance((-3, 1.2, 0), (3, 1.2, 0), .2, o), 0, places=10)

    def test_box_stationary_segment(self):
        o = {"type": "box", "center": [0, 0, 0], "half_extents": [1, 1, 1]}
        self.assertAlmostEqual(segment_clearance((3, 0, 0), (3, 0, 0), .2, o), 1.8)


class DifficultyTests(unittest.TestCase):
    def test_empty_domain_known_ray_lengths(self):
        # Central origin x=5,y=0; inset distances are 5.8,5.8,2.8,2.8.
        result = evaluate_scene(scene(), CONFIG)
        self.assertAlmostEqual(result["metrics"]["traversability"]["value"], 4.3/.4, places=6)

    def test_blocked_origin_counts_as_zero(self):
        s = scene(obstacles=[{"type": "sphere", "center": [5, 0, 1.5], "radius": 1}])
        result = evaluate_scene(s, CONFIG)
        self.assertEqual(result["metrics"]["traversability"]["value"], 0)
        self.assertEqual(result["diagnostics"]["blocked_grid_positions"], 1)

    def test_adding_obstacles_does_not_increase_fixed_grid_score(self):
        empty = evaluate_scene(scene(), CONFIG)["metrics"]["traversability"]["value"]
        s = scene(obstacles=[{"type": "sphere", "center": [7, 0, 1.5], "radius": .5}])
        self.assertLess(evaluate_scene(s, CONFIG)["metrics"]["traversability"]["value"], empty)

    def test_gap_ratio(self):
        s = scene(passages=[{"id": "test_gap", "free_width_m": 1, "geometry_verified": True}])
        self.assertEqual(evaluate_scene(s, CONFIG)["metrics"]["relative_gap_size"]["value"], 2.5)

    def test_no_gap_is_not_applicable(self):
        self.assertEqual(evaluate_scene(scene(), CONFIG)["metrics"]["relative_gap_size"]["status"], "not_applicable")

    def test_unverified_gap_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_scene(scene(passages=[{"id": "x", "free_width_m": 1}]), CONFIG)


if __name__ == "__main__":
    unittest.main()
