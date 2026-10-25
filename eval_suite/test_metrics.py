
from metrics import minimum_clearance


trajectory = [
    (0, 0, 0),
    (1, 0, 0),
    (2, 0, 0),
    (3, 0, 0)
]

obstacles = [
    {
        "type": "sphere",
        "center": (5, 0, 0),
        "radius": 1.0
    },
    {
        "type": "cylinder",
        "center": (0, 5, 0),
        "radius": 1.0
    },
    {
        "type": "box",
        "center": (0, -5, 0),
        "half_extents": (1, 1, 1)
    }
]

drone_radius = 0.2

result = minimum_clearance(
    trajectory,
    drone_radius,
    obstacles
)

print("Minimum obstacle clearance:", round(result, 2), "m")

assert abs(result - 0.8) < 1e-9

print("Minimum clearance test passed!")
