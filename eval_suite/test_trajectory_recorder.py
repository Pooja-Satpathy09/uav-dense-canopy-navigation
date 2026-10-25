
import csv
import tempfile

from trajectory_recorder import TrajectoryRecorder


recorder = TrajectoryRecorder(
    scene_id="easy_seed_42",
    run_id="synthetic_test_01"
)

goal = (20.0, 0.0, 1.5)

recorder.record(
    time=0.0,
    position=(0.0, 0.0, 1.5),
    velocity=(0.0, 0.0, 0.0),
    goal=goal
)

recorder.record(
    time=0.5,
    position=(1.0, 0.0, 1.5),
    velocity=(2.0, 0.0, 0.0),
    goal=goal
)

recorder.record(
    time=1.0,
    position=(2.0, 0.0, 1.5),
    velocity=(2.0, 0.0, 0.0),
    goal=goal
)

assert len(recorder.records) == 3
print("Test 1 passed: Three trajectory records")

assert abs(recorder.get_path_length() - 2.0) < 1e-9
print("Test 2 passed: Path length")

assert abs(recorder.get_duration() - 1.0) < 1e-9
print("Test 3 passed: Flight duration")

assert abs(
    recorder.records[-1]["distance_to_goal"] - 18.0
) < 1e-9
print("Test 4 passed: Distance to goal")

assert abs(recorder.records[1]["speed"] - 2.0) < 1e-9
print("Test 5 passed: Speed calculation")

try:
    recorder.record(
        time=0.5,
        position=(3.0, 0.0, 1.5),
        velocity=(2.0, 0.0, 0.0),
        goal=goal
    )
except ValueError:
    print("Test 6 passed: Invalid timestamp rejected")
else:
    raise AssertionError("Invalid timestamp accepted")

with tempfile.TemporaryDirectory() as folder:
    output = recorder.save_csv(folder)

    assert output.exists()

    with open(output, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 3
    assert float(rows[-1]["x"]) == 2.0

print("Test 7 passed: CSV export")
print("\nAll trajectory recorder tests passed!")
