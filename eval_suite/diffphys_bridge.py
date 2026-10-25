
from scene_adapter import load_and_convert


def load_scene_into_env(env, scene_path):
    """
    Load a fixed forest scene into an already initialized
    DiffPhysDrone environment.

    Call this AFTER env.reset().
    """

    import torch

    scene = load_and_convert(scene_path)

    device = env.device
    batch_size = env.batch_size

    def make_batch(values):
        tensor = torch.as_tensor(
            values,
            dtype=torch.float32,
            device=device
        )

        return tensor.unsqueeze(0).repeat(
            batch_size, 1, 1
        )

    # 1. Replace the randomly generated obstacles.
    env.balls = make_batch(scene["balls"])
    env.voxels = make_batch(scene["voxels"])
    env.cyl = make_batch(scene["cyl"])
    env.cyl_h = make_batch(scene["cyl_h"])

    # 2. Use fixed start and goal positions.
    start = torch.as_tensor(
        scene["start"],
        dtype=torch.float32,
        device=device
    )

    goal = torch.as_tensor(
        scene["goal"],
        dtype=torch.float32,
        device=device
    )

    env.p = start.unsqueeze(0).repeat(batch_size, 1).clone()
    env.p_target = goal.unsqueeze(0).repeat(batch_size, 1).clone()

    # 3. Set the drone's collision radius.
    env.drone_radius = float(scene["drone_radius"])

    # 4. Begin at rest for repeatable evaluation.
    env.v = torch.zeros_like(env.v)
    env.p_old = env.p.clone()

    return scene
