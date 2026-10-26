import itertools
from dataclasses import replace
from pathlib import Path
from .aggregate import summarize
from .diffphys import run_diffphys
from .io import dump_json, file_hash, fingerprint, git_info, load_config, load_json, save_trajectory, software_fingerprint


def experiment(repo, checkpoint, plan_path, output, *, resume=False):
    repo, plan_path, output = Path(repo).resolve(), Path(plan_path).resolve(), Path(output)
    plan = load_json(plan_path)
    config = load_config(plan_path.parent/plan["config"])
    if any(not plan.get(name) for name in ("speeds_mps", "noise_sigmas", "seeds")):
        raise ValueError("Experiment speeds_mps, noise_sigmas and seeds must be nonempty")
    for name in ("speeds_mps", "noise_sigmas", "seeds"):
        if len(set(plan[name])) != len(plan[name]):
            raise ValueError(f"Duplicate experiment condition in {name}")
    scenes = sorted(repo.glob(plan["scene_glob"]))
    if not scenes:
        raise ValueError("No scenes matched scene_glob")
    conditions = list(itertools.product(scenes, plan["speeds_mps"], plan["noise_sigmas"], plan["seeds"]))
    manifest = {"plan": plan, "config": config.to_dict(), "checkpoint_sha256": file_hash(checkpoint),
                "software_fingerprint": software_fingerprint(repo),
                "project_git": git_info(repo), "simulator_git": git_info(repo/"simulator/DiffPhysDrone"),
                "scenes": {str(s.relative_to(repo)): file_hash(s) for s in scenes}}
    identity = fingerprint(manifest)
    if output.exists():
        if not resume:
            raise FileExistsError("Experiment output exists; use --resume or a new output directory")
        if load_json(output/"experiment.json")["fingerprint"] != identity:
            raise ValueError("Cannot resume: code/config/checkpoint/scenes changed")
    else:
        output.mkdir(parents=True)
        dump_json(output/"experiment.json", {"fingerprint": identity, **manifest})
    results = []
    errors = []
    for i, (scene, speed, noise, seed) in enumerate(conditions):
        run_dir = output/f"run_{i:05d}"
        result_path = run_dir/"result.metrics.json"
        if result_path.exists():
            results.append(load_json(result_path))
            continue
        # Retain interrupted/error output and create a fresh attempt directory.
        attempt = run_dir
        n = 1
        while attempt.exists():
            attempt = output/f"run_{i:05d}_attempt_{n}"
            n += 1
        attempt.mkdir()
        try:
            samples, normalized_scene, result = run_diffphys(repo, checkpoint, scene,
                replace(config, target_speed_mps=speed), seed=seed, noise_sigma=noise,
                camera_angle_deg=plan.get("camera_angle_deg", 10))
            save_trajectory(attempt/"trajectory.csv", samples, normalized_scene, f"run_{i:05d}")
            dump_json(attempt/"scene.json", normalized_scene)
            result["metadata"]["raw_data_directory"] = str(attempt.relative_to(output))
            # Canonical completion marker is written only after raw data is safe.
            dump_json(result_path, result)
            results.append(result)
            print(f"{i+1}/{len(conditions)} {scene.stem}: {result['termination']}", flush=True)
        except Exception as error:
            failure = {"index": i, "scene": str(scene), "speed_mps": speed, "noise_sigma": noise,
                       "seed": seed, "exception_type": type(error).__name__, "message": str(error)}
            dump_json(attempt/"error.json", failure)
            errors.append(failure)
            print(f"{i+1}/{len(conditions)} ERROR: {error}", flush=True)
    report = summarize(results)
    report["attempt_errors"] = errors
    report["planned_runs"] = len(conditions)
    report["completed_result_files"] = len(results)
    # Summaries are immutable snapshots; resuming produces a new numbered summary.
    index = 0
    summary = output/"summary.json"
    while summary.exists():
        index += 1
        summary = output/f"summary_{index}.json"
    dump_json(summary, report)
    return report
