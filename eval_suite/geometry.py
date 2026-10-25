
import math


def sphere_clearance(drone_position, drone_radius,
                     sphere_center, sphere_radius):
    dx = drone_position[0] - sphere_center[0]
    dy = drone_position[1] - sphere_center[1]
    dz = drone_position[2] - sphere_center[2]

    center_distance = math.sqrt(dx**2 + dy**2 + dz**2)

    clearance = center_distance - sphere_radius - drone_radius

    return clearance

def cylinder_clearance(drone_position, drone_radius,
                       cylinder_center, cylinder_radius):

    dx = drone_position[0] - cylinder_center[0]
    dy = drone_position[1] - cylinder_center[1]

    horizontal_distance = math.sqrt(dx**2 + dy**2)

    clearance = horizontal_distance - cylinder_radius - drone_radius

    return clearance

def box_clearance(drone_position, drone_radius,
                  box_center, half_extents):

    dx = abs(drone_position[0] - box_center[0]) - half_extents[0]
    dy = abs(drone_position[1] - box_center[1]) - half_extents[1]
    dz = abs(drone_position[2] - box_center[2]) - half_extents[2]

    outside_distance = math.sqrt(
        max(dx, 0)**2 +
        max(dy, 0)**2 +
        max(dz, 0)**2
    )

    inside_distance = min(max(dx, dy, dz), 0)

    return outside_distance + inside_distance - drone_radius
