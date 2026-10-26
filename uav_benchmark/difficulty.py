import math
from .geometry import point_clearance, interpolate
from .registry import metric
from .types import MetricResult


def ray_free_distance(start, direction, scene, config):
    radius = scene["drone_radius"]
    bounds = scene["bounds"]
    maximum = math.inf
    for coordinate, velocity, (lo, hi) in zip(start[:2], direction[:2], bounds[:2]):
        if velocity > 1e-15:
            maximum = min(maximum, (hi-radius-coordinate)/velocity)
        elif velocity < -1e-15:
            maximum = min(maximum, (lo+radius-coordinate)/velocity)
    distance = 0.0
    # Sphere tracing never steps farther than the signed clearance to a surface.
    for _ in range(20000):
        p = tuple(start[i] + distance * direction[i] for i in range(3))
        separation = min(point_clearance(p, radius, scene["obstacles"]),
                         p[2]-radius-scene["ground_z_m"])
        if separation <= 1e-7 or maximum-distance <= 1e-7:
            return max(0.0, distance)
        distance += min(separation, config.traversability_step_m, maximum-distance)
    raise RuntimeError("Ray did not converge; adjust scene scale or ray step")


@metric("traversability", "scene", "1")
def traversability(context):
    scene, config = context["scene"], context["config"]
    radius, n = scene["drone_radius"], config.traversability_grid
    (xmin, xmax), (ymin, ymax) = scene["bounds"][:2]
    rays = []
    blocked = 0
    for i in range(n):
        for j in range(n):
            p = (xmin+radius+(i+.5)*(xmax-xmin-2*radius)/n,
                 ymin+radius+(j+.5)*(ymax-ymin-2*radius)/n, scene["start"][2])
            blocked_here = min(point_clearance(p, radius, scene["obstacles"]),
                               p[2]-radius-scene["ground_z_m"]) <= 0
            blocked += int(blocked_here)
            for heading in range(config.traversability_headings):
                angle = 2*math.pi*heading/config.traversability_headings
                rays.append(0.0 if blocked_here else ray_free_distance(p, (math.cos(angle), math.sin(angle), 0), scene, config))
    context["scene_diagnostics"] = {"ray_count": len(rays), "blocked_grid_positions": blocked,
                                    "grid_positions": n*n, "altitude_m": scene["start"][2]}
    return MetricResult(sum(rays)/len(rays)/(2*radius), "1",
                        note="Fixed-altitude XY grid/rays; blocked origins contribute zero")


@metric("relative_gap_size", "scene", "1")
def relative_gap_size(context):
    passages = context["scene"].get("passages", [])
    if not passages:
        return MetricResult(None, "1", "not_applicable", "No geometry-verified designated passage")
    return MetricResult(min(float(p["free_width_m"]) for p in passages)/(2*context["scene"]["drone_radius"]), "1",
                        note="Minimum declared passage width / drone diameter; project definition")
