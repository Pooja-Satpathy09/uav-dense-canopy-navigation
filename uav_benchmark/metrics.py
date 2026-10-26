import math
from . import difficulty
from . import flight_metrics
from .geometry import path_clearance
from .registry import REGISTRY
from .types import RunConfig
from .validation import validate_config, validate_samples, validate_scene


def flight_context(samples, scene, config):
    positions = [s.position for s in samples]
    obstacle_clearance = path_clearance(positions, scene["drone_radius"], scene["obstacles"])
    ground_clearance = min(p[2]-scene["drone_radius"]-scene["ground_z_m"] for p in positions)
    collision = any(s.collision for s in samples) or min(obstacle_clearance, ground_clearance) <= config.collision_tolerance_m
    final_distance = math.dist(positions[-1], scene["goal"])
    reached = final_distance <= config.goal_radius_m
    if samples[-1].reached_goal and not reached:
        raise ValueError("Goal flag conflicts with final geometric goal distance")
    out_of_bounds = any(any(v < lo+scene["drone_radius"] or v > hi-scene["drone_radius"]
                            for v, (lo, hi) in zip(p, scene["bounds"])) for p in positions)
    duration = samples[-1].time-samples[0].time
    termination = ("collision" if collision else "out_of_bounds" if out_of_bounds else
                   "goal_reached" if reached else "timeout" if duration >= config.timeout_s-1e-6 else "incomplete")
    return {"samples": samples, "scene": scene, "config": config, "duration": duration,
            "path_length": sum(math.dist(a, b) for a, b in zip(positions, positions[1:])),
            "initial_distance": math.dist(positions[0], scene["goal"]), "final_distance": final_distance,
            "obstacle_clearance": obstacle_clearance, "ground_clearance": ground_clearance,
            "termination": termination}


def evaluate_scene(scene, config=None):
    config = validate_config(config or RunConfig())
    scene = validate_scene(scene, config)
    context = {"scene": scene, "config": config}
    metrics = {name: spec.function(context).to_dict() for name, spec in REGISTRY.items() if spec.scope == "scene"}
    return {"metrics": metrics, "diagnostics": context.get("scene_diagnostics", {})}


def evaluate_run(samples, scene, config=None, *, include_scene_metrics=True, metadata=None):
    config = validate_config(config or RunConfig())
    scene = validate_scene(scene, config)
    samples = validate_samples(list(samples), scene, config)
    context = flight_context(samples, scene, config)
    metrics = {name: spec.function(context).to_dict() for name, spec in REGISTRY.items() if spec.scope == "flight"}
    scene_evaluation = evaluate_scene(scene, config) if include_scene_metrics else None
    if scene_evaluation:
        metrics.update(scene_evaluation["metrics"])
    return {"schema_version": "1.0", "library_version": "0.1.0", "scene_id": scene["scene_id"],
            "difficulty": scene["difficulty"], "termination": context["termination"],
            "complete": context["termination"] != "incomplete", "config": config.to_dict(),
            "metadata": dict(metadata or {}), "metrics": metrics,
            "diagnostics": {"duration_s": context["duration"], "path_length_m": context["path_length"],
                            "initial_goal_distance_m": context["initial_distance"], "final_goal_distance_m": context["final_distance"],
                            "min_ground_clearance_m": context["ground_clearance"], "sample_count": len(samples),
                            "scene": scene_evaluation["diagnostics"] if scene_evaluation else {}}}
