
from validate_scenes import validate_scene


empty_scene = {
    "start": [0.0, 0.0, 1.5],
    "goal": [20.0, 0.0, 1.5],
    "drone_radius": 0.2,
    "obstacles": []
}

result = validate_scene(empty_scene)

assert result["geometry_valid"]
assert result["start_safe"]
assert result["goal_safe"]
assert result["path_exists"]
assert abs(result["path_length"] - 20.0) < 0.01

print("Empty scene validation passed!")


blocked_start_scene = {
    "start": [0.0, 0.0, 1.5],
    "goal": [20.0, 0.0, 1.5],
    "drone_radius": 0.2,
    "obstacles": [
        {
            "type": "sphere",
            "center": [0.0, 0.0, 1.5],
            "radius": 1.0
        }
    ]
}

result = validate_scene(blocked_start_scene)

assert not result["start_safe"]
assert not result["path_exists"]

print("Blocked start validation passed!")
print("All validation tests passed!")
