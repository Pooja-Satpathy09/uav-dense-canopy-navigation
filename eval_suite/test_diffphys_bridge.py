
import math
import tempfile
from pathlib import Path

import torch

from scenes import generate_scene, save_scene
from diffphys_bridge import load_scene_into_env


class MockDiffPhysEnv:
    def __init__(self, batch_size=2):
        self.device = "cpu"
        self.batch_size = batch_size

        B = batch_size

        self.p = torch.zeros(B, 3)
        self.p_target = torch.zeros(B, 3)
        self.p_old = torch.zeros(B, 3)

        self.v = torch.zeros(B, 3)
        self.v_wind = torch.zeros(B, 3)
        self.act = torch.zeros(B, 3)
        self.a = torch.zeros(B, 3)
        self.dg = torch.zeros(B, 3)

        self.R = torch.eye(3).repeat(B, 1, 1)
        self.R_old = self.R.clone()

        self.pitch_ctl_delay = torch.zeros(B, 1)
        self.yaw_ctl_delay = torch.zeros(B, 1)

        self.thr_est_error = torch.ones(B)
        self.margin = torch.zeros(B)

        self.cam_angle = 10
        self.fov_x_half_tan = 0.53

        self.drone_radius = 0.12

        self.balls = torch.zeros(B, 30, 4)
        self.voxels = torch.zeros(B, 30, 6)
        self.cyl = torch.zeros(B, 30, 3)
        self.cyl_h = torch.zeros(B, 2, 3)


def run_tests():
    with tempfile.TemporaryDirectory() as temp_dir:

        scene = generate_scene("easy", seed=42)
        path = save_scene(scene, temp_dir)

        env = MockDiffPhysEnv(batch_size=2)

        loaded = load_scene_into_env(
            env, path, target_speed=2.0
        )

        # Test 1: Obstacle tensor dimensions
        assert env.balls.shape == (2, 30, 4)
        assert env.voxels.shape == (2, 30, 6)
        assert env.cyl.shape == (2, 30, 3)
        assert env.cyl_h.shape == (2, 2, 3)
        print("Test 1 passed: Obstacle tensor shapes")

        # Test 2: Starting position
        start = torch.tensor(scene["start"])

        assert torch.allclose(
            env.p, start.repeat(2, 1)
        )
        print("Test 2 passed: Start position")

        # Test 3: Goal position
        goal = torch.tensor(scene["goal"])

        assert torch.allclose(
            env.p_target, goal.repeat(2, 1)
        )
        print("Test 3 passed: Goal position")

        # Test 4: Target speed
        assert env.max_speed.shape == (2, 1)
        assert torch.allclose(
            env.max_speed,
            torch.full((2, 1), 2.0)
        )
        print("Test 4 passed: Target speed")

        # Test 5: Initial velocity
        assert torch.count_nonzero(env.v).item() == 0
        assert torch.count_nonzero(env.v_wind).item() == 0
        print("Test 5 passed: Initial velocity")

        # Test 6: Initial orientation
        heading = goal - start
        heading = heading[:2] / torch.linalg.norm(heading[:2])

        forward = env.R[0, :2, 0]

        assert torch.allclose(
            forward, heading, atol=1e-6
        )

        assert torch.allclose(
            env.R[0].T @ env.R[0],
            torch.eye(3),
            atol=1e-6
        )
        print("Test 6 passed: Drone orientation")

        # Test 7: Exact original geometry retained
        assert loaded["counts"] == {
            "sphere": 6,
            "box": 3,
            "cylinder": 8
        }

        assert torch.allclose(
            env.balls[0, 0],
            torch.tensor(loaded["balls"][0])
        )

        assert torch.equal(
            env.balls[0], env.balls[1]
        )
        print("Test 7 passed: Scene geometry")

        # Test 8: Speed does not change obstacles
        original_balls = env.balls.clone()
        original_voxels = env.voxels.clone()
        original_cyl = env.cyl.clone()

        load_scene_into_env(
            env, path, target_speed=3.0
        )

        assert torch.equal(env.balls, original_balls)
        assert torch.equal(env.voxels, original_voxels)
        assert torch.equal(env.cyl, original_cyl)
        print("Test 8 passed: Speed-independent scene")

        # Test 9: Repeated loading is consistent
        first_position = env.p.clone()
        first_rotation = env.R.clone()

        load_scene_into_env(
            env, path, target_speed=3.0
        )

        assert torch.equal(env.p, first_position)
        assert torch.equal(env.R, first_rotation)
        print("Test 9 passed: Repeatable initialization")

        # Test 10: Invalid target speed
        try:
            load_scene_into_env(
                env, path, target_speed=0
            )
        except ValueError:
            print("Test 10 passed: Invalid speed rejected")
        else:
            raise AssertionError(
                "Zero target speed should be rejected"
            )

    print("\nAll 10 CPU bridge tests passed!")


if __name__ == "__main__":
    run_tests()
