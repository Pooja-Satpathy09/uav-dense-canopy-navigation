import copy
import math
from .types import RunConfig, Sample


def number(value, label, *, positive=False, nonnegative=False):
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number, not a boolean")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    if positive and value <= 0 or nonnegative and value < 0:
        raise ValueError(f"Invalid {label}: {value}")
    return value


def vector(value, label):
    if len(value) != 3:
        raise ValueError(f"{label} must contain three coordinates")
    return tuple(number(v, label) for v in value)


def validate_config(config):
    for name in ("target_speed_mps", "timeout_s", "dt_s", "goal_radius_m",
                 "traversability_step_m"):
        number(getattr(config, name), name, positive=True)
    number(config.ground_z_m, "ground_z_m")
    number(config.collision_tolerance_m, "collision tolerance", nonnegative=True)
    if config.dt_s > config.timeout_s:
        raise ValueError("dt_s must not exceed timeout_s")
    for name in ("traversability_grid", "traversability_headings"):
        value = getattr(config, name)
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    return config


def validate_scene(scene, config=None):
    config = validate_config(config or RunConfig())
    result = copy.deepcopy(scene)
    result["start"] = vector(scene["start"], "start")
    result["goal"] = vector(scene["goal"], "goal")
    result["drone_radius"] = number(scene["drone_radius"], "drone radius", positive=True)
    result["scene_id"] = str(scene.get("scene_id", "unnamed"))
    result["difficulty"] = str(scene.get("difficulty", "unspecified"))
    result["ground_z_m"] = number(scene.get("ground_z_m", config.ground_z_m), "ground")
    bounds = scene.get("bounds", [[-1, 21], [-7, 7], [-1, 8]])
    if len(bounds) != 3 or any(len(pair) != 2 for pair in bounds):
        raise ValueError("bounds must contain x/y/z [minimum, maximum] pairs")
    result["bounds"] = [tuple(number(v, "bound") for v in pair) for pair in bounds]
    if any(lo >= hi for lo, hi in result["bounds"]):
        raise ValueError("Bounds must increase")
    r = result["drone_radius"]
    if any(hi - lo <= 2 * r for lo, hi in result["bounds"]):
        raise ValueError("Drone does not fit inside bounds")
    for label in ("start", "goal"):
        if any(not lo + r <= v <= hi - r for v, (lo, hi) in zip(result[label], result["bounds"])):
            raise ValueError(f"{label} must be inside body-inset bounds")
    obstacles = result["obstacles"]
    if not isinstance(obstacles, list):
        raise ValueError("obstacles must be a list")
    for obstacle in obstacles:
        obstacle["center"] = vector(obstacle["center"], "obstacle center")
        kind = obstacle["type"]
        if kind in ("sphere", "cylinder"):
            obstacle["radius"] = number(obstacle["radius"], "obstacle radius", positive=True)
        elif kind == "box":
            obstacle["half_extents"] = vector(obstacle["half_extents"], "half extents")
            if min(obstacle["half_extents"]) <= 0:
                raise ValueError("Box half extents must be positive")
        else:
            raise ValueError(f"Unsupported primitive: {kind}")
    for passage in result.get("passages", []):
        number(passage["free_width_m"], "passage width", positive=True)
        if not passage.get("id") or passage.get("geometry_verified") is not True:
            raise ValueError("Passages need an id and geometry_verified=true")
    return result


def validate_samples(samples, scene, config):
    if not samples:
        raise ValueError("Trajectory cannot be empty")
    for i, sample in enumerate(samples):
        if not isinstance(sample, Sample):
            raise TypeError("Use Sample objects or load_trajectory()")
        number(sample.time, "time", nonnegative=True)
        vector(sample.position, "position")
        vector(sample.velocity, "velocity")
        if type(sample.collision) is not bool or type(sample.reached_goal) is not bool:
            raise ValueError("Terminal flags must be booleans")
        if i and sample.time <= samples[i - 1].time:
            raise ValueError("Timestamps must strictly increase")
        if i < len(samples) - 1 and (sample.collision or sample.reached_goal):
            raise ValueError("Trajectory continues after a terminal flag")
    if math.dist(samples[0].position, scene["start"]) > 1e-4:
        raise ValueError("First trajectory position differs from scene start")
    duration = samples[-1].time - samples[0].time
    if duration > config.timeout_s + 1e-6:
        raise ValueError("Trajectory exceeds configured timeout; correct its configuration")
    return samples
