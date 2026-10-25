
from geometry import sphere_clearance

drone_position = (3, 0, 0)
drone_radius = 0.2

sphere_center = (0, 0, 0)
sphere_radius = 1.0

clearance = sphere_clearance(
    drone_position,
    drone_radius,
    sphere_center,
    sphere_radius
)

print("Obstacle clearance:", round(clearance, 2), "meters")

assert abs(clearance - 1.8) < 1e-9
print("Test passed!")

from geometry import cylinder_clearance, box_clearance

cylinder_distance = cylinder_clearance(
    (3, 0, 0),
    0.2,
    (0, 0, 0),
    1.0
)

assert abs(cylinder_distance - 1.8) < 1e-9
print("Cylinder test passed!")

box_distance = box_clearance(
    (3, 0, 0),
    0.2,
    (0, 0, 0),
    (1, 1, 1)
)

assert abs(box_distance - 1.8) < 1e-9
print("Box test passed!")
