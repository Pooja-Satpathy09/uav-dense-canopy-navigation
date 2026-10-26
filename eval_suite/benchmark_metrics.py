"""Compatibility evaluator for the existing eval_suite recorder."""
import math
from metrics import evaluate_flight, minimum_clearance
from difficulty import calculate_difficulty


def evaluate_benchmark_run(records, scene, target_speed):
    """Evaluate recorded positions; the gap output remains a scene proxy.

    Use uav_benchmark for the versioned library and segment collision checks.
    """
    if len(records) < 2:
        raise ValueError("At least two trajectory records are required")
    radius = float(scene["drone_radius"])
    if not math.isfinite(radius) or radius <= 0:
        raise ValueError("Drone radius must be finite and positive")
    positions = [tuple(float(row[a]) for a in ("x", "y", "z")) for row in records]
    goal = tuple(float(value) for value in scene["goal"])
    for row, position in zip(records, positions):
        if not math.isclose(float(row["distance_to_goal"]), math.dist(position, goal),
                            rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError("Trajectory goal does not match scene goal")
    flight = evaluate_flight(records, target_speed)
    clearance = minimum_clearance(positions, radius, scene["obstacles"])
    collision = int(bool(flight["collision"]) or clearance <= 0)
    difficulty = calculate_difficulty(scene)
    return {
        "scene_id": scene["scene_id"],
        "metric_version": "0.1",
        "success": int(bool(flight["success"]) and not collision),
        "collision": collision,
        "path_excess_factor": flight["path_excess_factor"],
        "minimum_obstacle_clearance_m": clearance if math.isfinite(clearance) else None,
        "average_speed_mps": flight["average_speed_mps"],
        "relative_end_distance": flight["relative_end_distance"],
        "speed_rmse_mps": flight["speed_rmse_mps"],
        "jerk_rms_mps3": flight["jerk_rms_mps3"],
        "traversability": difficulty["traversability"],
        "observed_gap_proxy": difficulty["observed_gap_proxy"],
        "duration_s": flight["duration_s"],
        "path_length_m": flight["path_length_m"],
        "collision_check": "recorded_positions",
    }
