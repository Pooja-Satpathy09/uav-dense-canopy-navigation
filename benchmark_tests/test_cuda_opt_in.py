"""Run explicitly with UAV_RUN_CUDA_TESTS=1; skipped on ordinary CPU checks."""
import os
import math
import tempfile
import unittest
from pathlib import Path
from uav_benchmark.types import RunConfig


@unittest.skipUnless(os.environ.get("UAV_RUN_CUDA_TESTS") == "1", "Real CUDA test requires explicit opt-in and checkpoint")
class CudaSmokeTests(unittest.TestCase):
    def test_rendered_sphere_matches_analytic_camera_ray(self):
        import torch
        from uav_benchmark.diffphys import load_module, load_bridge
        from uav_benchmark.io import dump_json
        repo = Path(os.environ["UAV_BENCHMARK_REPO"]).resolve()
        Env = load_module("_uav_render_test_env", repo/"simulator/DiffPhysDrone/env_cuda.py").Env
        env = Env(1, 64, 48, .4, torch.device("cuda"), single=True)
        geometry = {"scene_id": "render_oracle", "start": [0, 0, 1.5], "goal": [10, 0, 1.5],
                    "drone_radius": .2, "obstacles": [{"type": "sphere", "center": [5, 0, 1.5], "radius": 1}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = dump_json(Path(tmp)/"scene.json", geometry)
            load_bridge(repo).load_scene_into_env(env, path)
        env.R = torch.eye(3, device="cuda")[None]
        env.R_cam = env.R.clone()
        depth, _ = env.render(1/15)
        u, v = 24, 32
        fu = (2*(u+.5)/48-1)*(.53/64*48)-1e-5
        fv = (2*(v+.5)/64-1)*.53-1e-5
        a, b, c = 1+fu*fu+fv*fv, -10, 24
        expected = (-b-math.sqrt(b*b-4*a*c))/(2*a)
        self.assertAlmostEqual(float(depth[0, u, v]), expected, places=4)

    def test_repeated_seed_and_finite_trajectory(self):
        from uav_benchmark.diffphys import run_diffphys
        repo = Path(os.environ["UAV_BENCHMARK_REPO"]).resolve()
        checkpoint = Path(os.environ["UAV_BENCHMARK_CHECKPOINT"]).resolve()
        scene = Path(os.environ["UAV_BENCHMARK_SCENE"]).resolve()
        config = RunConfig(timeout_s=3)
        a, _, ar = run_diffphys(repo, checkpoint, scene, config, seed=42)
        b, _, br = run_diffphys(repo, checkpoint, scene, config, seed=42)
        self.assertNotEqual(ar["termination"], "numerical_failure")
        self.assertEqual(ar["termination"], br["termination"])
        self.assertEqual(len(a), len(b))
        self.assertGreater(len(a), 1)
        for first, second in zip(a, b):
            for x, y in zip((*first.position, *first.velocity), (*second.position, *second.velocity)):
                self.assertAlmostEqual(x, y, places=5)


if __name__ == "__main__":
    unittest.main()
