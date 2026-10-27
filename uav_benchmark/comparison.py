"""Compare compatible benchmark summaries across scene difficulties."""

import csv
import json
from pathlib import Path

from .aggregate import summarize
from .io import load_json, dump_json


def compare_results(results):
    """Compare existing run results without pooling incompatible conditions."""
    summary = summarize(results)
    comparisons = {}

    for group in summary["groups"]:
        condition = dict(group["condition"])
        difficulty = condition.pop("difficulty", "unknown")
        key = json.dumps(condition, sort_keys=True)

        entry = comparisons.setdefault(
            key,
            {
                "condition": condition,
                "by_difficulty": {},
            },
        )

        if difficulty in entry["by_difficulty"]:
            raise ValueError(
                f"Duplicate summary group for difficulty {difficulty!r}"
            )

        entry["by_difficulty"][difficulty] = {
            "runs": group["runs"],
            "eligible_runs": group["eligible_runs"],
            "incomplete_or_numerical": group["incomplete_or_numerical"],
            "scene_clusters": group["scene_clusters"],
            "metrics": group["metrics"],
        }

    return {
        "schema_version": "1.0",
        "comparison_count": len(comparisons),
        "comparisons": list(comparisons.values()),
        "notes": [
            "Only groups with matching non-difficulty conditions are compared.",
            "Missing difficulty levels are omitted, not filled with invented values.",
            "Synthetic results are not trained-policy results.",
        ],
    }


def compare_directory(inputs):
    """Load all metric result files under a directory and compare them."""
    paths = sorted(Path(inputs).rglob("*.metrics.json"))
    if not paths:
        raise ValueError("No *.metrics.json result files found")

    results = [load_json(path) for path in paths]
    return compare_results(results)


def export_comparison_csv(path, report):
    """Export one row per condition, difficulty, and metric."""
    fields = [
        "condition",
        "difficulty",
        "runs",
        "eligible_runs",
        "incomplete_or_numerical",
        "scene_clusters",
        "metric",
        "n",
        "mean",
        "std",
        "median",
        "p05",
        "p95",
        "scene_cluster_ci95_mean",
        "missing_or_non_ok",
    ]

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for comparison in report["comparisons"]:
            condition = json.dumps(
                comparison["condition"], sort_keys=True
            )

            for difficulty, group in sorted(
                comparison["by_difficulty"].items()
            ):
                for metric, stats in sorted(group["metrics"].items()):
                    writer.writerow({
                        "condition": condition,
                        "difficulty": difficulty,
                        "runs": group["runs"],
                        "eligible_runs": group["eligible_runs"],
                        "incomplete_or_numerical":
                            group["incomplete_or_numerical"],
                        "scene_clusters": group["scene_clusters"],
                        "metric": metric,
                        "n": stats["n"],
                        "mean": stats["mean"],
                        "std": stats["std"],
                        "median": stats["median"],
                        "p05": stats["p05"],
                        "p95": stats["p95"],
                        "scene_cluster_ci95_mean":
                            json.dumps(stats["scene_cluster_ci95_mean"]),
                        "missing_or_non_ok":
                            stats["missing_or_non_ok"],
                    })
