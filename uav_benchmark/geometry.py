"""Spherical drone; spheres, infinite vertical cylinders, axis-aligned boxes."""
import math


def clearance(position, radius, obstacle):
    center = obstacle["center"]
    kind = obstacle["type"]
    if kind == "sphere":
        return math.dist(position, center) - obstacle["radius"] - radius
    if kind == "cylinder":
        return math.dist(position[:2], center[:2]) - obstacle["radius"] - radius
    if kind == "box":
        q = [abs(position[i] - center[i]) - obstacle["half_extents"][i] for i in range(3)]
        return math.sqrt(sum(max(x, 0)**2 for x in q)) + min(max(q), 0) - radius
    raise ValueError(f"Unsupported obstacle: {kind}")


def point_clearance(position, radius, obstacles):
    return min((clearance(position, radius, o) for o in obstacles), default=math.inf)


def interpolate(a, b, t):
    return tuple(x + t * (y - x) for x, y in zip(a, b))


def segment_clearance(a, b, radius, obstacle):
    """Minimum signed clearance on a straight segment (box uses convex minimization)."""
    kind = obstacle["type"]
    if kind in ("sphere", "cylinder"):
        dimensions = 3 if kind == "sphere" else 2
        delta = [b[i] - a[i] for i in range(dimensions)]
        norm2 = sum(v * v for v in delta)
        t = 0.0 if norm2 == 0 else sum(
            (obstacle["center"][i] - a[i]) * delta[i] for i in range(dimensions)
        ) / norm2
        return clearance(interpolate(a, b, min(1.0, max(0.0, t))), radius, obstacle)
    if kind != "box":
        raise ValueError(f"Unsupported obstacle: {kind}")
    # Signed distance to a convex box is convex along a line. Include endpoints.
    lo, hi = 0.0, 1.0
    for _ in range(80):
        u, v = (2 * lo + hi) / 3, (lo + 2 * hi) / 3
        if clearance(interpolate(a, b, u), radius, obstacle) <= clearance(interpolate(a, b, v), radius, obstacle):
            hi = v
        else:
            lo = u
    return min(clearance(a, radius, obstacle), clearance(b, radius, obstacle),
               clearance(interpolate(a, b, (lo + hi) / 2), radius, obstacle))


def path_clearance(positions, radius, obstacles):
    if not positions:
        raise ValueError("Empty path")
    result = min((point_clearance(p, radius, obstacles) for p in positions), default=math.inf)
    for a, b in zip(positions, positions[1:]):
        for obstacle in obstacles:
            result = min(result, segment_clearance(a, b, radius, obstacle))
    return result
