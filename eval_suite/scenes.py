
import json
import math
import random
from pathlib import Path


DIFFICULTY_SETTINGS = {
    "easy": {
        "trunks": 8,
        "leaves": 6,
        "bushes": 3
    },
    "medium": {
        "trunks": 16,
        "leaves": 12,
        "bushes": 6
    },
    "hard": {
        "trunks": 25,
        "leaves": 20,
        "bushes": 10
    }
}


def generate_scene(difficulty="easy", seed=42):

    if difficulty not in DIFFICULTY_SETTINGS:
        raise ValueError("Invalid difficulty level")

    rng = random.Random(seed)
    settings = DIFFICULTY_SETTINGS[difficulty]

    start = [0.0, 0.0, 1.5]
    goal = [20.0, 0.0, 1.5]
    drone_radius = 0.2

    obstacles = []

    def valid_position(x, y, radius):
        for point in (start, goal):
            distance = math.hypot(
                x - point[0],
                y - point[1]
            )

            if distance < radius + drone_radius + 1.0:
                return False

        return True

    def sample_xy(radius):
        for _ in range(1000):
            x = rng.uniform(1.0, 19.0)
            y = rng.uniform(-6.0, 6.0)

            if valid_position(x, y, radius):
                return x, y

        raise RuntimeError("Unable to place obstacle")

    for _ in range(settings["trunks"]):
        radius = rng.uniform(0.2, 0.5)
        x, y = sample_xy(radius)

        obstacles.append({
            "type": "cylinder",
            "center": [x, y, 0.0],
            "radius": radius
        })

    for _ in range(settings["leaves"]):
        radius = rng.uniform(0.4, 1.0)
        x, y = sample_xy(radius)

        obstacles.append({
            "type": "sphere",
            "center": [x, y, rng.uniform(1.0, 4.0)],
            "radius": radius
        })

    for _ in range(settings["bushes"]):
        hx = rng.uniform(0.3, 0.7)
        hy = rng.uniform(0.3, 0.7)
        hz = rng.uniform(0.2, 0.5)

        x, y = sample_xy(math.hypot(hx, hy))

        obstacles.append({
            "type": "box",
            "center": [x, y, hz],
            "half_extents": [hx, hy, hz]
        })

    return {
        "scene_id": f"{difficulty}_seed_{seed}",
        "difficulty": difficulty,
        "seed": seed,
        "start": start,
        "goal": goal,
        "drone_radius": drone_radius,
        "obstacles": obstacles
    }


def save_scene(scene, output_dir="scenes"):

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / f"{scene['scene_id']}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(scene, file, indent=2)

    return file_path


if __name__ == "__main__":

    for difficulty in DIFFICULTY_SETTINGS:
        scene = generate_scene(difficulty, seed=42)
        path = save_scene(scene)

        print(
            f"{difficulty}: "
            f"{len(scene['obstacles'])} obstacles -> {path}"
        )
