import argparse
import csv
import sys
from pathlib import Path
from .aggregate import summarize
from .batch import evaluate_manifest
from .demo import demo
from .io import dump_json, file_hash, fingerprint, load_config, load_json, load_trajectory
from .metrics import evaluate_run, evaluate_scene


def export_csv(path, results):
    names = sorted({name for r in results for name in r["metrics"]})
    fields = ["scene_id", "difficulty", "termination", "complete", "source", "seed", "target_speed_mps", "noise_sigma"]
    fields += [column for name in names for column in (name, name+"__status")]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for result in results:
            row = {k: result[k] for k in ("scene_id", "difficulty", "termination", "complete")}
            row.update({k: result["metadata"].get(k) for k in ("source", "seed", "noise_sigma")})
            row["target_speed_mps"] = result["config"]["target_speed_mps"]
            for name in names:
                metric = result["metrics"].get(name, {})
                row[name], row[name+"__status"] = metric.get("value"), metric.get("status", "not_computed")
            writer.writerow(row)


def parser():
    root = argparse.ArgumentParser(description="UAV benchmark: CPU metrics and optional CUDA flight collection")
    sub = root.add_subparsers(dest="command", required=True)
    p = sub.add_parser("demo", help="Generate and evaluate analytical synthetic trajectories on CPU")
    p.add_argument("--out", required=True)
    p = sub.add_parser("evaluate", help="Evaluate an existing trajectory CSV")
    p.add_argument("--trajectory", required=True)
    p.add_argument("--scene", required=True)
    p.add_argument("--config")
    p.add_argument("--source", default="imported_unverified")
    p.add_argument("--out", required=True)
    p = sub.add_parser("scene", help="Evaluate the two scene metrics")
    p.add_argument("--scene", required=True)
    p.add_argument("--config")
    p.add_argument("--out", required=True)
    p = sub.add_parser("batch", help="Evaluate a manifest of already-recorded trajectories")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("summarize", help="Summarize result files in one directory")
    p.add_argument("--inputs", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--csv")
    p = sub.add_parser(
        "compare",
        help="Compare compatible benchmark groups across difficulties",
    )
    p.add_argument("--inputs", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--csv")
    p = sub.add_parser("generate-scenes", help="Call the team's existing seeded scene generator")
    p.add_argument("--repo", default=".")
    p.add_argument("--out", required=True)
    p.add_argument("--start-seed", type=int, default=0)
    p.add_argument("--count", type=int, default=30)
    p = sub.add_parser("validate-scenes", help="Run the team's existing offline geometry/grid checks on all scene files")
    p.add_argument("--repo", default=".")
    p.add_argument("--inputs", required=True)
    p.add_argument("--config")
    p.add_argument("--out", required=True)
    p = sub.add_parser("run", help="Run one trained-policy flight; requires CUDA and a checkpoint")
    p.add_argument("--repo", default=".")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--scene", required=True)
    p.add_argument("--config")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--noise-sigma", type=float, default=0)
    p.add_argument("--camera-angle-deg", type=float, default=10)
    p.add_argument("--allow-unverified-simulator", action="store_true")
    p.add_argument("--out", required=True)
    p = sub.add_parser("experiment", help="Run a resumable CUDA experiment matrix")
    p.add_argument("--repo", default=".")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--resume", action="store_true")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "demo":
            demo(args.out)
            print(f"Synthetic demonstration saved to {args.out}; these are not trained-policy results.")
        elif args.command == "evaluate":
            scene, config = load_json(args.scene), load_config(args.config)
            metadata = {"source": args.source, "scene_hash": fingerprint(scene),
                        "trajectory_sha256": file_hash(args.trajectory)}
            metadata["run_fingerprint"] = fingerprint({**metadata, "config": config.to_dict()})
            result = evaluate_run(load_trajectory(args.trajectory, scene), scene, config, metadata=metadata)
            dump_json(args.out, result)
            print(f"{result['termination']}: {args.out}")
        elif args.command == "scene":
            dump_json(args.out, evaluate_scene(load_json(args.scene), load_config(args.config)))
            print(args.out)
        elif args.command == "batch":
            results = evaluate_manifest(args.manifest, args.out)
            print(f"Evaluated {len(results)} trajectories: {args.out}")
        elif args.command == "summarize":
            paths = sorted(Path(args.inputs).rglob("*.metrics.json"))
            if not paths:
                raise ValueError("No *.metrics.json result files found")
            results = [load_json(path) for path in paths]
            dump_json(args.out, summarize(results))
            if args.csv:
                export_csv(args.csv, results)
            print(args.out)
        elif args.command == "compare":
            from .comparison import compare_directory, export_comparison_csv

            report = compare_directory(args.inputs)
            dump_json(args.out, report)

            if args.csv:
                export_comparison_csv(args.csv, report)

            print(f"Created {report['comparison_count']} comparison groups: {args.out}")
        elif args.command == "generate-scenes":
            if args.count < 1 or args.start_seed < 0:
                raise ValueError("count must be positive; start-seed must be nonnegative")
            from .diffphys import load_module
            generator = load_module("_uav_team_generator", Path(args.repo).resolve()/"eval_suite/scenes.py")
            cases = [(level, seed) for level in ("easy", "medium", "hard")
                     for seed in range(args.start_seed, args.start_seed+args.count)]
            output = Path(args.out)
            if any((output/f"{level}_seed_{seed}.json").exists() for level, seed in cases):
                raise FileExistsError("A target scene already exists; choose a fresh directory")
            for level, seed in cases:
                dump_json(output/f"{level}_seed_{seed}.json", generator.generate_scene(level, seed))
            print(f"Generated {len(cases)} scenes in {output}; validate before benchmarking.")
        elif args.command == "run":
            from .diffphys import run_diffphys
            from .io import save_trajectory
            output = Path(args.out)
            if output.exists():
                raise FileExistsError("Run output already exists; choose a new directory")
            samples, scene, result = run_diffphys(args.repo, args.checkpoint, args.scene, load_config(args.config),
                seed=args.seed, noise_sigma=args.noise_sigma, camera_angle_deg=args.camera_angle_deg,
                allow_unverified_simulator=args.allow_unverified_simulator)
            output.mkdir(parents=True)
            save_trajectory(output/"trajectory.csv", samples, scene, output.name)
            dump_json(output/"scene.json", scene)
            dump_json(output/"result.metrics.json", result)
            print(f"{result['termination']}: {output}")
            return 1 if result["termination"] == "numerical_failure" else 0
        elif args.command == "validate-scenes":
            from .scene_validation import validate_scene_directory
            report = validate_scene_directory(args.repo, args.inputs, load_config(args.config))
            dump_json(args.out, report)
            print(f"{report['passing']}/{report['total']} scenes passed: {args.out}")
            return 0 if report["passing"] == report["total"] else 1
        elif args.command == "experiment":
            from .experiment import experiment
            report = experiment(args.repo, args.checkpoint, args.plan, args.out, resume=args.resume)
            print(f"Saved {report['completed_result_files']}/{report['planned_runs']} run results")
            return 1 if report["attempt_errors"] or any(g["incomplete_or_numerical"] for g in report["groups"]) else 0
        return 0
    except (ValueError, TypeError, KeyError, OSError, ImportError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
