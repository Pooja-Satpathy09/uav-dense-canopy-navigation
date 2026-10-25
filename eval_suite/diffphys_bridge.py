
import math
import torch

from scene_adapter import load_and_convert


def load_scene_into_env(env, scene_path, target_speed=2.0):
    """
    Load a fixed scene into an initialized DiffPhysDrone Env.

    Must be called after env.reset().
    Intended for evaluation, not training.
    """

    if target_speed <= 0:
        raise ValueError("Target speed must be positive")

    scene = load_and_convert(scene_path)

    device = env.device
    B = env.batch_size
    dtype = env.p.dtype

    def make_batch(values):
        tensor = torch.as_tensor(
            values, dtype=dtype, device=device
        )
        return tensor.unsqueeze(0).expand(
            B, -1, -1
        ).contiguous().clone()

    # 1. Load fixed obstacle geometry
    env.balls = make_batch(scene["balls"])
    env.voxels = make_batch(scene["voxels"])
    env.cyl = make_batch(scene["cyl"])
    env.cyl_h = make_batch(scene["cyl_h"])

    # 2. Set start and goal
    start = torch.as_tensor(
        scene["start"], dtype=dtype, device=device
    )
    goal = torch.as_tensor(
        scene["goal"], dtype=dtype, device=device
    )

    env.p = start.unsqueeze(0).repeat(B, 1).clone()
    env.p_target = goal.unsqueeze(0).repeat(B, 1).clone()
    env.p_old = env.p.clone()

    # 3. Set drone size and target speed
    env.drone_radius = float(scene["drone_radius"])

    env.max_speed = torch.full(
        (B, 1), float(target_speed),
        dtype=dtype, device=device
    )

    # 4. Initialize motion state consistently
    env.v = torch.zeros_like(env.v)
    env.v_wind = torch.zeros_like(env.v_wind)
    env.act = torch.zeros_like(env.act)
    env.a = torch.zeros_like(env.a)
    env.dg = torch.zeros_like(env.dg)

    # 5. Deterministic initial control parameters
    env.pitch_ctl_delay = torch.full_like(
        env.pitch_ctl_delay, 12.0
    )
    env.yaw_ctl_delay = torch.full_like(
        env.yaw_ctl_delay, 6.0
    )
    env.thr_est_error = torch.ones_like(
        env.thr_est_error
    )

    # 6. Align the drone's forward axis with the goal
    direction = goal - start

    yaw = math.atan2(
        float(direction[1]),
        float(direction[0])
    )

    c = math.cos(yaw)
    s = math.sin(yaw)

    rotation = torch.tensor(
        [
            [c, -s, 0.0],
            [s,  c, 0.0],
            [0.0, 0.0, 1.0]
        ],
        dtype=dtype,
        device=device
    )

    env.R = rotation.unsqueeze(0).repeat(B, 1, 1).clone()
    env.R_old = env.R.clone()

    # 7. Fix camera orientation
    cam_angle = math.radians(float(env.cam_angle))

    ca = math.cos(cam_angle)
    sa = math.sin(cam_angle)

    camera_rotation = torch.tensor(
        [
            [ca, 0.0, -sa],
            [0.0, 1.0, 0.0],
            [sa, 0.0, ca]
        ],
        dtype=dtype,
        device=device
    )

    env.R_cam = (
        camera_rotation.unsqueeze(0)
        .repeat(B, 1, 1)
        .clone()
    )

    env._fov_x_half_tan = env.fov_x_half_tan

    # 8. Use independent drone groups for evaluation
    env.n_drones_per_group = 1

    # Keep deterministic evaluation margin
    env.margin = torch.full_like(env.margin, 0.2)

    return scene
