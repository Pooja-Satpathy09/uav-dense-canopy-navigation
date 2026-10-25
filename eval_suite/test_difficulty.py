
from difficulty import traversability, observed_gap_proxy


empty_scene = {
    "scene_id": "empty",
    "difficulty": "test",
    "start": [0.0, 0.0, 1.5],
    "goal": [20.0, 0.0, 1.5],
    "drone_radius": 0.2,
    "obstacles": []
}

blocked_scene = {
    **empty_scene,
    "scene_id": "blocked",
    "obstacles": [
        {
            "type": "cylinder",
            "center": [10.0, 0.0, 0.0],
            "radius": 2.0
        }
    ]
}

empty_result = traversability(empty_scene)
blocked_result = traversability(blocked_scene)

assert empty_result["traversability"] is not None
assert blocked_result["traversability"] is not None

assert (
    empty_result["traversability"]
    > blocked_result["traversability"]
)

print("Traversability test passed!")


gap_scene = {
    **empty_scene,
    "scene_id": "gap_test",
    "obstacles": [
        {
            "type": "cylinder",
            "center": [5.0, 0.0, 0.0],
            "radius": 1.0
        },
        {
            "type": "cylinder",
            "center": [8.0, 0.0, 0.0],
            "radius": 1.0
        }
    ]
}

gap = observed_gap_proxy(gap_scene)

# Center spacing = 3 m
# Surface gap = 3 - 1 - 1 = 1 m
# Drone diameter = 0.4 m
# Normalized gap = 1 / 0.4 = 2.5

assert abs(gap - 2.5) < 1e-9

print("Gap proxy test passed!")
print("All difficulty tests passed!")
