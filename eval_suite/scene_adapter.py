
import json
from pathlib import Path


CAPACITY = {
    "sphere": 30,
    "box": 30,
    "cylinder": 30
}

# Temporary inactive-object position.
# Must be verified against CUDA kernels.
FAR_AWAY = 10000.0


def convert_scene(scene):
    balls = []
    voxels = []
    cylinders = []

    for obstacle in scene["obstacles"]:
        kind = obstacle["type"]
        center = obstacle["center"]

        if kind == "sphere":
            balls.append([
                float(center[0]),
                float(center[1]),
                float(center[2]),
                float(obstacle["radius"])
            ])

        elif kind == "box":
            extents = obstacle["half_extents"]

            voxels.append([
                float(center[0]),
                float(center[1]),
                float(center[2]),
                float(extents[0]),
                float(extents[1]),
                float(extents[2])
            ])

        elif kind == "cylinder":
            cylinders.append([
                float(center[0]),
                float(center[1]),
                float(obstacle["radius"])
            ])

        else:
            raise ValueError(
                f"Unsupported obstacle type: {kind}"
            )

    counts = {
        "sphere": len(balls),
        "box": len(voxels),
        "cylinder": len(cylinders)
    }

    for kind, count in counts.items():
        if count > CAPACITY[kind]:
            raise ValueError(
                f"Too many {kind} obstacles: "
                f"{count} > {CAPACITY[kind]}"
            )

    balls += [
        [FAR_AWAY, FAR_AWAY, FAR_AWAY, 0.01]
        for _ in range(CAPACITY["sphere"] - len(balls))
    ]

    voxels += [
        [FAR_AWAY, FAR_AWAY, FAR_AWAY,
         0.01, 0.01, 0.01]
        for _ in range(CAPACITY["box"] - len(voxels))
    ]

    cylinders += [
        [FAR_AWAY, FAR_AWAY, 0.01]
        for _ in range(CAPACITY["cylinder"] - len(cylinders))
    ]

    horizontal_cylinders = [
        [FAR_AWAY, FAR_AWAY, 0.01]
        for _ in range(2)
    ]

    return {
        "scene_id": scene["scene_id"],
        "balls": balls,
        "voxels": voxels,
        "cyl": cylinders,
        "cyl_h": horizontal_cylinders,
        "start": scene["start"],
        "goal": scene["goal"],
        "drone_radius": scene["drone_radius"],
        "counts": counts
    }


def load_and_convert(scene_path):
    with open(scene_path, "r", encoding="utf-8") as f:
        scene = json.load(f)

    return convert_scene(scene)


if __name__ == "__main__":
    for difficulty in ("easy", "medium", "hard"):
        path = (
            Path("scenes") /
            f"{difficulty}_seed_42.json"
        )

        data = load_and_convert(path)

        print(f"\nScene: {data['scene_id']}")
        print("Obstacle counts:", data["counts"])
        print("Balls:", len(data["balls"]))
        print("Voxels:", len(data["voxels"]))
        print("Vertical cylinders:", len(data["cyl"]))
        print("Horizontal cylinders:", len(data["cyl_h"]))
        print("Start:", data["start"])
        print("Goal:", data["goal"])
