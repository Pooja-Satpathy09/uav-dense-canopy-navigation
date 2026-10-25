
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

import math


def evaluate_flight(records, target_speed):
    """
    Calculate flight-level navigation metrics.

    records: TrajectoryRecorder.records
    target_speed: requested drone speed in m/s
    """

    if not records:
        raise ValueError("Trajectory cannot be empty")

    if not math.isfinite(target_speed) or target_speed <= 0:
        raise ValueError("Target speed must be positive")

    times = [float(r["time"]) for r in records]

    if not all(math.isfinite(t) for t in times):
        raise ValueError("Timestamps must be finite")

    if any(
        times[i] <= times[i - 1]
        for i in range(1, len(times))
    ):
        raise ValueError("Timestamps must increase")

    positions = [
        (float(r["x"]), float(r["y"]), float(r["z"]))
        for r in records
    ]

    velocities = [
        (float(r["vx"]), float(r["vy"]), float(r["vz"]))
        for r in records
    ]

    if not all(
        math.isfinite(v)
        for point in positions + velocities
        for v in point
    ):
        raise ValueError("Position and velocity must be finite")

    if any(
        r["collision"] and r["reached_goal"]
        for r in records
    ):
        raise ValueError("Collision and goal arrival conflict")

    # 1. Flight outcome
    collision = int(any(r["collision"] for r in records))
    reached_goal = bool(records[-1]["reached_goal"])

    success = int(reached_goal and not collision)

    # 2. Duration
    duration = times[-1] - times[0]

    # 3. Total traveled distance
    path_length = sum(
        math.dist(positions[i - 1], positions[i])
        for i in range(1, len(positions))
    )

    # 4. Original straight-line distance
    initial_goal_distance = float(
        records[0]["distance_to_goal"]
    )
    final_goal_distance = float(
        records[-1]["distance_to_goal"]
    )

    if not all(
        math.isfinite(d) and d >= 0
        for d in (initial_goal_distance, final_goal_distance)
    ):
        raise ValueError("Invalid goal distance")

    if initial_goal_distance <= 0:
        path_excess = None
        relative_end_distance = None
        goal_progress = None
    else:
        path_excess = (
            path_length / initial_goal_distance - 1.0
        )

        relative_end_distance = (
            final_goal_distance / initial_goal_distance
        )

        goal_progress = (
            1.0 - relative_end_distance
        )

    # 5. Average traversal speed
    average_speed = (
        path_length / duration
        if duration > 0 else None
    )

    # 6. Time-weighted speed tracking error
    speed_squared_error = 0.0

    accelerations = []
    acceleration_times = []

    for i in range(1, len(records)):
        dt = times[i] - times[i - 1]

        speed = math.sqrt(
            sum(v * v for v in velocities[i])
        )

        speed_squared_error += (
            (speed - target_speed) ** 2 * dt
        )

        acceleration = tuple(
            (velocities[i][axis] -
             velocities[i - 1][axis]) / dt
            for axis in range(3)
        )

        accelerations.append(acceleration)
        acceleration_times.append(
            (times[i - 1] + times[i]) / 2
        )

    speed_rmse = (
        math.sqrt(speed_squared_error / duration)
        if duration > 0 else None
    )

    # 7. RMS jerk (trajectory smoothness)
    jerk_squared_integral = 0.0
    jerk_duration = 0.0

    for i in range(1, len(accelerations)):
        dt = (
            acceleration_times[i] -
            acceleration_times[i - 1]
        )

        jerk = [
            (accelerations[i][axis] -
             accelerations[i - 1][axis]) / dt
            for axis in range(3)
        ]

        jerk_squared_integral += (
            sum(j * j for j in jerk) * dt
        )
        jerk_duration += dt

    jerk_rms = (
        math.sqrt(jerk_squared_integral / jerk_duration)
        if jerk_duration > 0 else None
    )

    return {
        "success": success,
        "collision": collision,
        "duration_s": duration,
        "path_length_m": path_length,
        "path_excess_factor": path_excess,
        "average_speed_mps": average_speed,
        "relative_end_distance": relative_end_distance,
        "goal_progress": goal_progress,
        "speed_rmse_mps": speed_rmse,
        "jerk_rms_mps3": jerk_rms
    }
