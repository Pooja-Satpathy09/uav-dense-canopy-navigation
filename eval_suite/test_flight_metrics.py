
import math

from trajectory_recorder import TrajectoryRecorder
from metrics import evaluate_flight


def make_test_flight():
    recorder = TrajectoryRecorder(
        "synthetic_scene",
        "test_run_01"
    )

    goal = (10.0, 0.0, 1.5)

    for step in range(6):
        time = float(step)
        x = float(step * 2)

        recorder.record(
            time=time,
            position=(x, 0.0, 1.5),
            velocity=(2.0, 0.0, 0.0),
            goal=goal,
            reached_goal=(step == 5)
        )

    return recorder


recorder = make_test_flight()

results = evaluate_flight(
    recorder.records,
    target_speed=2.0
)

assert results["success"] == 1
print("Test 1 passed: Goal success")

assert results["collision"] == 0
print("Test 2 passed: No collision")

assert math.isclose(results["duration_s"], 5.0)
print("Test 3 passed: Duration")

assert math.isclose(results["path_length_m"], 10.0)
print("Test 4 passed: Path length")

assert math.isclose(results["path_excess_factor"], 0.0)
print("Test 5 passed: Path efficiency")

assert math.isclose(results["average_speed_mps"], 2.0)
print("Test 6 passed: Average speed")

assert math.isclose(results["relative_end_distance"], 0.0)
assert math.isclose(results["goal_progress"], 1.0)
print("Test 7 passed: Goal progress")

assert math.isclose(results["speed_rmse_mps"], 0.0)
print("Test 8 passed: Speed tracking")

assert math.isclose(results["jerk_rms_mps3"], 0.0)
print("Test 9 passed: Smoothness")

# A flight that ends without reaching the goal
failed = TrajectoryRecorder("synthetic_scene", "failed_run")

failed.record(
    0.0, (0, 0, 1.5), (0, 0, 0),
    (10, 0, 1.5)
)

failed.record(
    1.0, (1, 0, 1.5), (1, 0, 0),
    (10, 0, 1.5)
)

failed_result = evaluate_flight(
    failed.records, target_speed=2.0
)

assert failed_result["success"] == 0
assert failed_result["collision"] == 0

print("Test 10 passed: Timeout is not success")

print("\nAll flight metric tests passed!")

print("\nCalculated metrics:")
for key, value in results.items():
    print(f"{key}: {value}")
