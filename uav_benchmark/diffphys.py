"""Optional CUDA integration for the repository's pinned DiffPhysDrone revision.

CPU-tested helpers are in other modules. Real CUDA execution needs validation on
the user's NVIDIA machine and a compatible checkpoint; see benchmark_docs/GPU.md.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path
from .geometry import path_clearance
from .io import file_hash, fingerprint, git_info, software_fingerprint
from .metrics import evaluate_run
from .types import Sample
from .validation import validate_config, validate_scene

PINNED_SIMULATOR = "271936190b5c2a5e760230e718fa6b167718a5bf"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bridge(repo):
    # Existing bridge uses a script-style sibling import. Adapt it locally.
    adapter = load_module("_uav_scene_adapter", repo/"eval_suite/scene_adapter.py")
    previous = sys.modules.get("scene_adapter")
    sys.modules["scene_adapter"] = adapter
    try:
        return load_module("_uav_diffphys_bridge", repo/"eval_suite/diffphys_bridge.py")
    finally:
        if previous is None:
            sys.modules.pop("scene_adapter", None)
        else:
            sys.modules["scene_adapter"] = previous


def run_diffphys(repo, checkpoint, scene_path, config, *, seed=42, noise_sigma=0.0,
                 camera_angle_deg=10, allow_unverified_simulator=False):
    import torch
    import numpy as np
    import torch.nn.functional as F

    config = validate_config(config)
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("seed must be an integer in [0, 2**32)")
    if not math.isfinite(noise_sigma) or noise_sigma < 0:
        raise ValueError("noise_sigma must be finite and nonnegative")
    if not math.isfinite(camera_angle_deg):
        raise ValueError("Camera angle must be finite")
    if not torch.cuda.is_available():
        raise RuntimeError("Live DiffPhysDrone rollouts require NVIDIA CUDA; use demo/evaluate on CPU")
    repo, checkpoint, scene_path = Path(repo).resolve(), Path(checkpoint).resolve(), Path(scene_path).resolve()
    simulator = repo/"simulator/DiffPhysDrone"
    simulator_info = git_info(simulator)
    if simulator_info["commit"] != PINNED_SIMULATOR or simulator_info["dirty"]:
        if not allow_unverified_simulator:
            raise ValueError("Simulator revision differs or is dirty. Restore the pinned submodule or explicitly use --allow-unverified-simulator")
    from .io import load_json
    scene = validate_scene(load_json(scene_path), config)
    if scene["ground_z_m"] != -1.0:
        raise ValueError("Pinned renderer uses ground z=-1; align scene/config before a live run")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    device = torch.device("cuda")

    Env = load_module("_uav_upstream_env", simulator/"env_cuda.py").Env
    Model = load_module("_uav_upstream_model", simulator/"model.py").Model
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    checkpoint_config = {}
    if isinstance(state, dict) and "model" in state:
        checkpoint_config = state.get("config", {})
        state = state["model"]
    elif isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    if not isinstance(state, dict) or "v_proj.weight" not in state or "fc.weight" not in state:
        raise ValueError("Expected a DiffPhysDrone state_dict with v_proj.weight and fc.weight")
    dim_obs, dim_action = state["v_proj.weight"].shape[1], state["fc.weight"].shape[0]
    if dim_obs not in (7, 10) or dim_action != 6:
        raise ValueError(f"Unsupported checkpoint dimensions: state={dim_obs}, action={dim_action}")
    model = Model(dim_obs, dim_action).to(device)
    model.load_state_dict(state, strict=True)
    model.eval()
    # batch_size=1 and single=True avoid inter-drone rendering/collision effects.
    env = Env(1, 64, 48, .4, device, single=True, cam_angle=camera_angle_deg)
    env.reset()
    load_bridge(repo).load_scene_into_env(env, scene_path, target_speed=config.target_speed_mps)
    # Freeze the reset-time drag distribution; ongoing dg noise remains seeded.
    env.drag_2 = torch.tensor([[0.0, .375]], dtype=env.p.dtype, device=device)
    env.z_drag_coef = torch.ones_like(env.z_drag_coef)
    sensor_rng = torch.Generator(device=device)
    sensor_rng.manual_seed((seed+1) % 2**32)

    def sample(time, collision=False, reached=False):
        return Sample(time, tuple(float(v) for v in env.p[0].detach().cpu()),
                      tuple(float(v) for v in env.v[0].detach().cpu()), collision, reached)

    records, numerical_failure = [sample(0.0)], None
    hidden, time = None, 0.0
    # Preserve upstream ordering and the two-slot initial action buffer.
    action_buffer = [env.act.clone(), env.act.clone()]
    radius = scene["drone_radius"]

    def event(previous, current):
        path = [previous.position, current.position] if previous else [current.position]
        contact = min(path_clearance(path, radius, scene["obstacles"]),
                      min(p[2]-radius-scene["ground_z_m"] for p in path)) <= config.collision_tolerance_m
        outside = any(v < lo+radius or v > hi-radius for v, (lo, hi) in zip(current.position, scene["bounds"]))
        reached = math.dist(current.position, scene["goal"]) <= config.goal_radius_m
        return contact, outside, reached

    initial_contact, initial_outside, initial_reached = event(None, records[0])
    if initial_contact or initial_reached:
        records[0] = sample(0.0, initial_contact, initial_reached and not initial_contact)
    with torch.inference_mode():
        while time < config.timeout_s-1e-9 and not (initial_contact or initial_outside or initial_reached):
            dt = min(config.dt_s, config.timeout_s-time)
            depth, _ = env.render(dt)
            target_raw = env.p_target-env.p
            env.run(action_buffer.pop(0), dt, target_raw)
            next_time = min(config.timeout_s, time+dt)
            if not all(torch.isfinite(x).all().item() for x in (depth, env.p, env.v, env.R)):
                numerical_failure = {"time_s": next_time, "stage": "simulation_or_depth"}
                break
            current = sample(next_time)
            contact, outside, reached = event(records[-1], current)
            records.append(sample(next_time, contact, reached and not contact and not outside))
            time = next_time
            if contact or outside or reached or time >= config.timeout_s-1e-9:
                break
            forward = env.R[:, :, 0].clone()
            forward[:, 2] = 0
            forward = F.normalize(forward, dim=-1)
            up = torch.zeros_like(forward)
            up[:, 2] = 1
            rotation = torch.stack([forward, torch.cross(up, forward, dim=-1), up], -1)
            norm = target_raw.norm(dim=-1, keepdim=True).clamp_min(1e-8)
            target = target_raw/norm*torch.minimum(norm, env.max_speed)
            fields = [torch.squeeze(target[:, None]@rotation, 1), env.R[:, 2], env.margin[:, None]]
            if dim_obs == 10:
                fields.insert(0, torch.squeeze(env.v[:, None]@rotation, 1))
            observation = 3/depth.clamp(.3, 24)-.6
            if noise_sigma:
                observation = observation+torch.randn(observation.shape, device=device, generator=sensor_rng)*noise_sigma
            observation = F.max_pool2d(observation[:, None], 4, 4)
            action, _, hidden = model(observation, torch.cat(fields, -1), hidden)
            if not torch.isfinite(action).all().item():
                numerical_failure = {"time_s": time, "stage": "policy"}
                break
            a_pred, v_pred = (rotation@action.reshape(1, 3, 2)).unbind(-1)
            control = (a_pred-v_pred-env.g_std)*env.thr_est_error[:, None]+env.g_std
            action_buffer.append(control)
    metadata = {"source": "diffphys_cuda", "integration_validation": "requires_user_gpu_validation",
                "checkpoint_sha256": file_hash(checkpoint), "scene_hash": fingerprint(scene),
                "seed": seed, "noise_seed": (seed+1) % 2**32, "noise_sigma": noise_sigma,
                "noise_space": "normalized_inverse_depth_before_pooling", "camera_angle_deg": camera_angle_deg,
                "model_state_dimension": dim_obs, "model_action_dimension": dim_action,
                "checkpoint_embedded_config_present": bool(checkpoint_config),
                "project_git": git_info(repo), "simulator_git": simulator_info,
                "software_fingerprint": software_fingerprint(repo),
                "python": sys.version, "torch": str(torch.__version__), "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(0), "drag_2": [0, .375], "margin_m": .2,
                "ongoing_disturbance": "seeded upstream dg process; not disabled"}
    metadata["run_fingerprint"] = fingerprint({"metadata": metadata, "config": config.to_dict()})
    result = evaluate_run(records, scene, config, metadata=metadata)
    if numerical_failure:
        result["termination"] = "numerical_failure"
        result["complete"] = False
        result["diagnostics"]["numerical_failure"] = numerical_failure
        for name in ("goal_success", "collision"):
            result["metrics"][name].update(value=None, status="invalid_run", note="Numerical failure")
    return records, scene, result
