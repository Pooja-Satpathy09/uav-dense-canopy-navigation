
import json
import math
from pathlib import Path

from validate_scenes import point_clearance


def traversability(scene, grid_size=5, headings=8, step=0.1):
    obstacles = scene["obstacles"]
    radius = scene["drone_radius"]
    z = scene["start"][2]

    xmin, xmax = 0.0, 20.0
    ymin, ymax = -6.0, 6.0

    free_distances = []
    skipped = 0

    for i in range(grid_size):
        x = xmin + (i + 0.5) * (xmax - xmin) / grid_size

        for j in range(grid_size):
            y = ymin + (j + 0.5) * (ymax - ymin) / grid_size
            start = (x, y, z)

            if point_clearance(start, radius, obstacles) <= 0:
                skipped += 1
                continue

            for h in range(headings):
                angle = 2 * math.pi * h / headings
                dx = math.cos(angle)
                dy = math.sin(angle)

                distance = 0.0

                while True:
                    next_distance = distance + step
                    px = x + next_distance * dx
                    py = y + next_distance * dy

                    if not (
                        xmin + radius <= px <= xmax - radius
                        and ymin + radius <= py <= ymax - radius
                    ):
                        break

                    if point_clearance(
                        (px, py, z), radius, obstacles
                    ) <= 0:
                        break

                    distance = next_distance

                free_distances.append(distance)

    if not free_distances:
        return {
            "traversability": None,
            "valid_rays": 0,
            "skipped_positions": skipped
        }

    mean_free_distance = sum(free_distances) / len(free_distances)

    return {
        "traversability": round(
            mean_free_distance / (2 * radius), 4
        ),
        "valid_rays": len(free_distances),
        "skipped_positions": skipped
    }


def horizontal_footprint(obstacle, altitude):
    kind = obstacle["type"]
    x, y, z = obstacle["center"]

    if kind == "cylinder":
        return x, y, obstacle["radius"]

    if kind == "sphere":
        r = obstacle["radius"]
        dz = abs(altitude - z)

        if dz >= r:
            return None

        cross_section = math.sqrt(r * r - dz * dz)
        return x, y, cross_section

    if kind == "box":
        hx, hy, hz = obstacle["half_extents"]

        if abs(altitude - z) >= hz:
            return None

        # Conservative enclosing circle for the box footprint
        return x, y, math.hypot(hx, hy)

    raise ValueError(f"Unknown obstacle type: {kind}")


def observed_gap_proxy(scene):
    altitude = scene["start"][2]
    drone_diameter = 2 * scene["drone_radius"]

    footprints = []

    for obstacle in scene["obstacles"]:
        footprint = horizontal_footprint(obstacle, altitude)

        if footprint is not None:
            footprints.append(footprint)

    if len(footprints) < 2:
        return None

    smallest_gap = float("inf")

    for i in range(len(footprints)):
        x1, y1, r1 = footprints[i]

        for j in range(i + 1, len(footprints)):
            x2, y2, r2 = footprints[j]

            center_distance = math.hypot(x2 - x1, y2 - y1)
            gap = center_distance - r1 - r2

            smallest_gap = min(smallest_gap, gap)

    return round(smallest_gap / drone_diameter, 4)


def calculate_difficulty(scene):
    result = traversability(scene)

    return {
        "scene_id": scene["scene_id"],
        "difficulty_label": scene["difficulty"],
        "traversability": result["traversability"],
        "valid_rays": result["valid_rays"],
        "skipped_positions": result["skipped_positions"],
        "observed_gap_proxy": observed_gap_proxy(scene)
    }


if __name__ == "__main__":
    for level in ("easy", "medium", "hard"):
        path = Path("scenes") / f"{level}_seed_42.json"

        with open(path, "r", encoding="utf-8") as f:
            scene = json.load(f)

        result = calculate_difficulty(scene)

        print(f"\n{level.upper()} SCENE")

        for key, value in result.items():
            print(f"{key}: {value}")
