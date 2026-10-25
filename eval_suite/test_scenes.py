
from scenes import generate_scene


scene1 = generate_scene("easy", seed=42)
scene2 = generate_scene("easy", seed=42)
scene3 = generate_scene("easy", seed=99)

assert scene1 == scene2
print("Same seed reproducibility test passed!")

assert scene1 != scene3
print("Different seed test passed!")

assert len(scene1["obstacles"]) == 17
print("Easy scene obstacle count passed!")

medium = generate_scene("medium", seed=42)
assert len(medium["obstacles"]) == 34
print("Medium scene obstacle count passed!")

hard = generate_scene("hard", seed=42)
assert len(hard["obstacles"]) == 55
print("Hard scene obstacle count passed!")

print("All scene generation tests passed!")
