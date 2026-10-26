"""Descriptive per-run statistics and scene-cluster bootstrap intervals."""
import math
import json
import random
import statistics
from collections import defaultdict


def wilson(values):
    n = len(values)
    if not n:
        return None
    p, z = sum(values)/n, 1.959963984540054
    denominator = 1+z*z/n
    center = (p+z*z/(2*n))/denominator
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return [max(0, center-half), min(1, center+half)]


def percentile(values, fraction):
    values = sorted(values)
    index = (len(values)-1)*fraction
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo]+(values[hi]-values[lo])*(index-lo)


def describe(values):
    if not values:
        return {"n": 0, "mean": None, "std": None, "median": None, "p05": None, "p95": None}
    return {"n": len(values), "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values)>1 else None,
            "median": statistics.median(values), "p05": percentile(values, .05), "p95": percentile(values, .95)}


def cluster_interval(pairs, *, resamples=2000):
    clusters = defaultdict(list)
    for scene_id, value in pairs:
        clusters[scene_id].append(value)
    if len(clusters) < 2:
        return None
    ids, rng = sorted(clusters), random.Random(2026)
    means = []
    for _ in range(resamples):
        picked = [value for _ in ids for value in clusters[rng.choice(ids)]]
        means.append(statistics.mean(picked))
    return [percentile(means, .025), percentile(means, .975)]


def summarize(results):
    seen = set()
    grouped = defaultdict(list)
    for result in results:
        metadata = result.get("metadata", {})
        identity = metadata.get("run_fingerprint")
        if identity and identity in seen:
            raise ValueError("Duplicate run fingerprint; do not aggregate duplicate result files")
        if identity:
            seen.add(identity)
        # No pooling of different policies, origins, simulation settings or noise levels.
        config = result["config"]
        condition = {"difficulty": result["difficulty"], "source": metadata.get("source", "unspecified"),
                     "checkpoint_sha256": metadata.get("checkpoint_sha256"),
                     "noise_sigma": metadata.get("noise_sigma", 0), "config": config,
                     "library_version": result.get("library_version"),
                     "project_commit": metadata.get("project_git", {}).get("commit"),
                     "project_dirty": metadata.get("project_git", {}).get("dirty"),
                     "simulator_commit": metadata.get("simulator_git", {}).get("commit"),
                     "simulator_dirty": metadata.get("simulator_git", {}).get("dirty"),
                     "software_fingerprint": metadata.get("software_fingerprint"),
                     "camera_angle_deg": metadata.get("camera_angle_deg")}
        grouped[json.dumps(condition, sort_keys=True)].append(result)
    groups = []
    for key, runs in grouped.items():
        eligible = [r for r in runs if r.get("complete") and r["termination"] != "numerical_failure"]
        metrics = {}
        for name in sorted({name for r in eligible for name in r["metrics"]}):
            pairs = [(r["metadata"].get("scene_hash", r["scene_id"]), r["metrics"][name]["value"])
                     for r in eligible if name in r["metrics"] and r["metrics"][name]["status"] == "ok"]
            values = [v for _, v in pairs]
            item = describe(values)
            item["scene_cluster_ci95_mean"] = cluster_interval(pairs)
            item["missing_or_non_ok"] = len(eligible)-len(values)
            if name in ("goal_success", "collision"):
                item["wilson_ci95_independent_trials_only"] = wilson(values)
                item["events"] = sum(values)
            if name in ("path_excess_factor", "average_speed_mps", "jerk_rms_mps3"):
                item["successful_flights"] = describe([r["metrics"][name]["value"] for r in eligible
                    if r["termination"] == "goal_reached" and r["metrics"].get(name, {}).get("status") == "ok"])
            metrics[name] = item
        groups.append({"condition": json.loads(key), "runs": len(runs),
                       "eligible_runs": len(eligible), "incomplete_or_numerical": len(runs)-len(eligible),
                       "scene_clusters": len({r["metadata"].get("scene_hash", r["scene_id"]) for r in eligible}),
                       "metrics": metrics})
    return {"schema_version": "1.0", "groups": groups,
            "notes": ["Rates use eligible completed runs; report excluded runs alongside rates.",
                      "Wilson intervals assume independent trials; use scene-cluster bootstrap for repeated scenes.",
                      "Bootstrap is unavailable with fewer than two independent scene clusters.",
                      "No uncertainty estimate establishes sim-to-real performance."]}
