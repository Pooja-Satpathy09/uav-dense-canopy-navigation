
import json
import math
import heapq
from pathlib import Path

from geometry import (
    sphere_clearance,
    cylinder_clearance,
    box_clearance
)


def point_clearance(position, drone_radius, obstacles):
    if not obstacles:
        return float("inf")

    minimum = float("inf")

    for obstacle in obstacles:
        kind = obstacle["type"]

        if kind == "sphere":
            distance = sphere_clearance(
                position,
                drone_radius,
                obstacle["center"],
                obstacle["radius"]
            )

        elif kind == "cylinder":
            distance = cylinder_clearance(
                position,
                drone_radius,
                obstacle["center"],
                obstacle["radius"]
            )

        elif kind == "box":
            distance = box_clearance(
                position,
                drone_radius,
                obstacle["center"],
                obstacle["half_extents"]
            )

        else:
            raise ValueError(f"Unknown obstacle: {kind}")

        minimum = min(minimum, distance)

    return minimum


def check_geometry(scene):
    for obstacle in scene["obstacles"]:
        kind = obstacle["type"]
        center = obstacle["center"]

        if len(center) != 3:
            return False

        if not all(math.isfinite(v) for v in center):
            return False

        if kind in ("sphere", "cylinder"):
            radius = obstacle["radius"]
            if not math.isfinite(radius) or radius <= 0:
                return False

        elif kind == "box":
            extents = obstacle["half_extents"]
            if len(extents) != 3:
                return False
            if not all(
                math.isfinite(v) and v > 0 for v in extents
            ):
                return False

        else:
            return False

    return True


def check_path(scene, resolution=0.25):
    start = scene["start"]
    goal = scene["goal"]
    radius = scene["drone_radius"]
    obstacles = scene["obstacles"]

    # Bounded, constant-altitude XY path validation
    xmin, xmax = -1.0, 21.0
    ymin, ymax = -7.0, 7.0

    nx = round((xmax - xmin) / resolution) + 1
    ny = round((ymax - ymin) / resolution) + 1

    def grid_to_world(node):
        i, j = node
        return (
            xmin + i * resolution,
            ymin + j * resolution,
            start[2]
        )

    def world_to_grid(point):
        return (
            round((point[0] - xmin) / resolution),
            round((point[1] - ymin) / resolution)
        )

    start_node = world_to_grid(start)
    goal_node = world_to_grid(goal)

    safety_cache = {}

    def is_safe(node):
        i, j = node

        if not (0 <= i < nx and 0 <= j < ny):
            return False

        if node not in safety_cache:
            position = grid_to_world(node)
            safety_cache[node] = (
                point_clearance(position, radius, obstacles) > 0
            )

        return safety_cache[node]

    def edge_safe(a, b):
        p = grid_to_world(a)
        q = grid_to_world(b)

        length = math.dist(p, q)
        samples = max(1, math.ceil(length / (resolution / 4)))

        for k in range(samples + 1):
            t = k / samples
            position = tuple(
                p[d] + t * (q[d] - p[d])
                for d in range(3)
            )

            if point_clearance(position, radius, obstacles) <= 0:
                return False

        return True

    if not is_safe(start_node) or not is_safe(goal_node):
        return False, float("inf")

    movements = [
        (-1, 0), (1, 0),
        (0, -1), (0, 1),
        (-1, -1), (-1, 1),
        (1, -1), (1, 1)
    ]

    def heuristic(node):
        return math.dist(node, goal_node) * resolution

    queue = [(heuristic(start_node), 0.0, start_node)]
    best_cost = {start_node: 0.0}

    while queue:
        _, cost, current = heapq.heappop(queue)

        if cost > best_cost[current] + 1e-9:
            continue

        if current == goal_node:
            return True, cost

        for dx, dy in movements:
            neighbor = (
                current[0] + dx,
                current[1] + dy
            )

            if not is_safe(neighbor):
                continue

            if not edge_safe(current, neighbor):
                continue

            step_cost = math.hypot(dx, dy) * resolution
            new_cost = cost + step_cost

            if new_cost < best_cost.get(
                neighbor, float("inf")
            ):
                best_cost[neighbor] = new_cost

                heapq.heappush(
                    queue,
                    (
                        new_cost + heuristic(neighbor),
                        new_cost,
                        neighbor
                    )
                )

    return False, float("inf")


def validate_scene(scene):
    if not check_geometry(scene):
        return {
            "geometry_valid": False,
            "start_safe": False,
            "goal_safe": False,
            "path_exists": False,
            "path_length": None
        }

    radius = scene["drone_radius"]
    obstacles = scene["obstacles"]

    start_safe = point_clearance(
        scene["start"], radius, obstacles
    ) > 0

    goal_safe = point_clearance(
        scene["goal"], radius, obstacles
    ) > 0

    path_exists, path_length = check_path(scene)

    return {
        "geometry_valid": True,
        "start_safe": start_safe,
        "goal_safe": goal_safe,
        "path_exists": path_exists,
        "path_length": (
            round(path_length, 3)
            if path_exists else None
        )
    }


if __name__ == "__main__":
    for difficulty in ("easy", "medium", "hard"):
        path = Path("scenes") / f"{difficulty}_seed_42.json"

        with open(path, "r", encoding="utf-8") as file:
            scene = json.load(file)

        results = validate_scene(scene)

        print(f"\n{difficulty.upper()} SCENE")
        print("--------------------------")

        for name, value in results.items():
            print(f"{name}: {value}")
