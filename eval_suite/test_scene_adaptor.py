
from scenes import generate_scene
from scene_adapter import convert_scene


expected = {
    "easy": (6, 3, 8),
    "medium": (12, 6, 16),
    "hard": (20, 10, 25)
}

for difficulty, counts in expected.items():
    scene = generate_scene(difficulty, seed=42)
    data = convert_scene(scene)

    assert len(data["balls"]) == 30
    assert len(data["voxels"]) == 30
    assert len(data["cyl"]) == 30
    assert len(data["cyl_h"]) == 2

    assert all(len(row) == 4 for row in data["balls"])
    assert all(len(row) == 6 for row in data["voxels"])
    assert all(len(row) == 3 for row in data["cyl"])
    assert all(len(row) == 3 for row in data["cyl_h"])

    actual_counts = (
        data["counts"]["sphere"],
        data["counts"]["box"],
        data["counts"]["cylinder"]
    )

    assert actual_counts == counts
    assert data["start"] == scene["start"]
    assert data["goal"] == scene["goal"]

    print(f"{difficulty.capitalize()} scene adapter passed!")


too_many = generate_scene("easy", seed=42)
too_many["obstacles"] = [
    {
        "type": "sphere",
        "center": [float(i), 0.0, 1.5],
        "radius": 0.2
    }
    for i in range(31)
]

try:
    convert_scene(too_many)
except ValueError:
    print("Obstacle capacity validation passed!")
else:
    raise AssertionError("Expected capacity error")

print("All scene adapter tests passed!")
