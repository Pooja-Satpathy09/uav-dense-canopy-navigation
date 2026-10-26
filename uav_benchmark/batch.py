from pathlib import Path
from .aggregate import summarize
from .io import dump_json, load_config, load_json, load_trajectory, fingerprint, file_hash
from .metrics import evaluate_run


def evaluate_manifest(manifest_path, output):
    manifest_path, output = Path(manifest_path).resolve(), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = load_json(manifest_path)
    results = []
    for i, run in enumerate(manifest["runs"]):
        scene_path = manifest_path.parent/run["scene"]
        trajectory_path = manifest_path.parent/run["trajectory"]
        scene = load_json(scene_path)
        config = load_config(manifest_path.parent/run["config"] if run.get("config") else None)
        identity = fingerprint({"trajectory": file_hash(trajectory_path), "scene": fingerprint(scene), "config": config.to_dict()})
        result = evaluate_run(load_trajectory(trajectory_path, scene), scene, config,
            metadata={**run.get("metadata", {}), "source": run.get("source", "imported_unverified"), "scene_hash": fingerprint(scene),
                      "trajectory_sha256": file_hash(trajectory_path), "run_fingerprint": identity,
                      })
        dump_json(output/f"run_{i:05d}.metrics.json", result)
        results.append(result)
    dump_json(output/"summary.json", summarize(results))
    return results
