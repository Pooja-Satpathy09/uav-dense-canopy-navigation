
from trajectory_recorder import TrajectoryRecorder


recorder = TrajectoryRecorder(
    "empty_demo_scene",
    "synthetic_run_01"
)

goal = (10.0, 0.0, 1.5)

for step in range(11):
    time = step * 0.5
    x = float(step)

    recorder.record(
        time=time,
        position=(x, 0.0, 1.5),
        velocity=(2.0, 0.0, 0.0),
        goal=goal,
        reached_goal=(step == 10)
    )

output = recorder.save_csv()

print("CSV saved:", output)
print("Flight duration:", recorder.get_duration(), "seconds")
print("Path length:", recorder.get_path_length(), "meters")
