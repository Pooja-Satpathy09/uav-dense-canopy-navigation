import itertools
import re
from pathlib import Path

from .io import load_json


def audit_experiment(output):
    output = Path(output)
    manifest_path = output / "experiment.json"

    if not manifest_path.is_file():
        raise ValueError(f"Missing experiment manifest: {manifest_path}")

    manifest = load_json(manifest_path)
    plan = manifest.get("plan", {})
    scenes = manifest.get("scenes", {})

    for name in ("speeds_mps", "noise_sigmas", "seeds"):
        values = plan.get(name)
        if not isinstance(values, list) or not values:
            raise ValueError(f"Invalid or missing experiment plan field: {name}")

    if not isinstance(scenes, dict) or not scenes:
        raise ValueError("Experiment manifest contains no scene records")

    scene_paths = sorted(scenes)
    conditions = list(itertools.product(
        scene_paths,
        plan["speeds_mps"],
        plan["noise_sigmas"],
        plan["seeds"],
    ))

    runs = []
    counts = {
        "completed": 0,
        "failed": 0,
        "interrupted": 0,
        "missing": 0,
    }

    for index, (scene, speed, noise, seed) in enumerate(conditions):
        run_name = f"run_{index:05d}"
        run_dir = output / run_name
        result_path = run_dir / "result.metrics.json"

        pattern = re.compile(rf"^{re.escape(run_name)}(?:_attempt_(\d+))?$")
        attempt_dirs = []

        for path in output.iterdir():
            match = pattern.fullmatch(path.name)
            if match and path.is_dir():
                attempt_number = int(match.group(1) or 0)
                attempt_dirs.append((attempt_number, path))

        attempt_dirs.sort(key=lambda item: item[0])
        result = load_json(result_path) if result_path.is_file() else None
        completed_attempt = None

        if result is not None:
            raw_dir = result.get("metadata", {}).get("raw_data_directory")
            completed_attempt = raw_dir or run_name

        attempts = []
        for attempt_number, attempt_dir in attempt_dirs:
            relative_dir = str(attempt_dir.relative_to(output))
            error_path = attempt_dir / "error.json"

            if error_path.is_file():
                attempt_status = "failed"
                error = load_json(error_path)
            elif relative_dir == completed_attempt:
                attempt_status = "completed"
                error = None
            else:
                attempt_status = "interrupted"
                error = None

            attempts.append({
                "attempt": attempt_number,
                "directory": relative_dir,
                "status": attempt_status,
                "error": error,
            })

        if result is not None:
            status = "completed"
        elif attempts:
            status = attempts[-1]["status"]
        else:
            status = "missing"

        counts[status] += 1

        runs.append({
            "index": index,
            "scene": scene,
            "speed_mps": speed,
            "noise_sigma": noise,
            "seed": seed,
            "status": status,
            "result_file": (
                str(result_path.relative_to(output))
                if result is not None else None
            ),
            "attempts": attempts,
        })

    planned = len(runs)
    completed = counts["completed"]

    return {
        "experiment_fingerprint": manifest.get("fingerprint"),
        "experiment_directory": str(output),
        "planned_runs": planned,
        "completed_runs": completed,
        "failed_runs": counts["failed"],
        "interrupted_runs": counts["interrupted"],
        "missing_runs": counts["missing"],
        "completion_percentage": (
            round(100 * completed / planned, 2) if planned else 0
        ),
        "status_counts": counts,
        "runs": runs,
    }
