import copy
import math
from benchmark_metrics import evaluate_benchmark_run
from trajectory_recorder import TrajectoryRecorder

scene = {
    "scene_id": "numerical_validation", "difficulty": "test",
    "start": [0.0, 0.0, 1.5], "goal": [10.0, 0.0, 1.5], "drone_radius": 0.2,
    "obstacles": [
        {"type": "cylinder", "center": [5.0, 3.0, 0.0], "radius": 1.0},
        {"type": "cylinder", "center": [5.0, 6.0, 0.0], "radius": 1.0},
    ],
}
recorder = TrajectoryRecorder(scene["scene_id"], "synthetic_check")
for step in range(11):
    recorder.record(time=step * 0.5, position=(float(step), 0.0, 1.5),
                    velocity=(2.0, 0.0, 0.0), goal=tuple(scene["goal"]),
                    reached_goal=(step == 10))
result = evaluate_benchmark_run(recorder.records, scene, 2.0)
expected = {
    "success": 1, "collision": 0, "duration_s": 5.0, "path_length_m": 10.0,
    "path_excess_factor": 0.0, "minimum_obstacle_clearance_m": 1.8,
    "average_speed_mps": 2.0, "relative_end_distance": 0.0,
    "speed_rmse_mps": 0.0, "jerk_rms_mps3": 0.0, "observed_gap_proxy": 2.5,
}
for key, value in expected.items():
    assert math.isclose(result[key], value, abs_tol=1e-9), (key, result[key], value)
assert result["traversability"] is not None
blocked_scene = copy.deepcopy(scene)
blocked_scene["obstacles"][0]["center"] = [5.0, 0.0, 0.0]
blocked = evaluate_benchmark_run(recorder.records, blocked_scene, 2.0)
assert blocked["collision"] == 1 and blocked["success"] == 0
assert blocked["minimum_obstacle_clearance_m"] < 0
print("All combined benchmark checks passed.")
print("These checks use synthetic data, not a policy flight.")
