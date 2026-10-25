
from geometry import (
    sphere_clearance,
    cylinder_clearance,
    box_clearance
)


def minimum_clearance(trajectory, drone_radius, obstacles):

    if not trajectory:
        raise ValueError("Trajectory cannot be empty")

    if not obstacles:
        return float("inf")

    min_distance = float("inf")

    for drone_position in trajectory:

        for obstacle in obstacles:

            obstacle_type = obstacle["type"]

            if obstacle_type == "sphere":
                distance = sphere_clearance(
                    drone_position,
                    drone_radius,
                    obstacle["center"],
                    obstacle["radius"]
                )

            elif obstacle_type == "cylinder":
                distance = cylinder_clearance(
                    drone_position,
                    drone_radius,
                    obstacle["center"],
                    obstacle["radius"]
                )

            elif obstacle_type == "box":
                distance = box_clearance(
                    drone_position,
                    drone_radius,
                    obstacle["center"],
                    obstacle["half_extents"]
                )

            else:
                raise ValueError(
                    f"Unknown obstacle type: {obstacle_type}"
                )

            min_distance = min(min_distance, distance)

    return min_distance
