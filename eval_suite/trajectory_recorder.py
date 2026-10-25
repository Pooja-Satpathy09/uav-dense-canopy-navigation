
import csv
import math
from pathlib import Path


class TrajectoryRecorder:
    def __init__(self, scene_id, run_id):
        self.scene_id = scene_id
        self.run_id = run_id
        self.records = []

    def record(self, time, position, velocity,
               goal, collision=False, reached_goal=False):

        if not math.isfinite(time) or time < 0:
            raise ValueError("Time must be finite and nonnegative")

        if self.records and time <= self.records[-1]["time"]:
            raise ValueError("Timestamps must strictly increase")

        if any(len(v) != 3 for v in (position, velocity, goal)):
            raise ValueError("Position, velocity and goal need 3 values")

        values = [*position, *velocity, *goal]

        if not all(math.isfinite(float(v)) for v in values):
            raise ValueError("All state values must be finite")

        if self.records and (
            self.records[-1]["collision"]
            or self.records[-1]["reached_goal"]
        ):
            raise ValueError("Cannot record after a terminal event")

        x, y, z = map(float, position)
        vx, vy, vz = map(float, velocity)
        gx, gy, gz = map(float, goal)

        speed = math.sqrt(vx**2 + vy**2 + vz**2)

        distance_to_goal = math.dist(
            (x, y, z), (gx, gy, gz)
        )

        self.records.append({
            "scene_id": self.scene_id,
            "run_id": self.run_id,
            "time": float(time),
            "x": x,
            "y": y,
            "z": z,
            "vx": vx,
            "vy": vy,
            "vz": vz,
            "speed": speed,
            "distance_to_goal": distance_to_goal,
            "collision": bool(collision),
            "reached_goal": bool(reached_goal)
        })

    def get_path_length(self):
        total = 0.0

        for i in range(1, len(self.records)):
            previous = self.records[i - 1]
            current = self.records[i]

            total += math.dist(
                (previous["x"], previous["y"], previous["z"]),
                (current["x"], current["y"], current["z"])
            )

        return total

    def get_duration(self):
        if len(self.records) < 2:
            return 0.0

        return (
            self.records[-1]["time"]
            - self.records[0]["time"]
        )

    def save_csv(self, output_dir="results/trajectories"):
        if not self.records:
            raise ValueError("No trajectory records to save")

        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)

        safe_scene = self.scene_id.replace("/", "_").replace("\\", "_")
        safe_run = self.run_id.replace("/", "_").replace("\\", "_")

        output_file = directory / f"{safe_scene}_{safe_run}.csv"

        with open(
            output_file, "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(self.records[0].keys())
            )

            writer.writeheader()
            writer.writerows(self.records)

        return output_file
