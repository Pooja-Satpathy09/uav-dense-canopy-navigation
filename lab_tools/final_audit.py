
"""Final evaluation audit for the UAV navigation project.

Run from the repository root:
    python lab_tools/final_audit.py

Reads committed goal-plane CSV results, validates paired trials,
and reports safe traversal separately from precise goal arrival.
"""

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAB = ROOT / "benchmark_docs" / "lab_results"
HEIGHT = ROOT / "benchmark_docs" / "height_aware_results"
OUT = ROOT / "benchmark_docs" / "final_audit"

MODELS = {
    "Our 50k": LAB / "ours_50k_fov82_goal_plane.csv",
    "Authors": LAB / "released_base_fov82_goal_plane.csv",
    "FT loss fix": HEIGHT / "ft_fix_fov82_goal_plane.csv",
    "FT height targets": HEIGHT / "ft_height_fov82_goal_plane.csv",
    "FT height loss 2": HEIGHT / "ft_hloss2_fov82_goal_plane.csv",
    "FT height loss 5": HEIGHT / "ft_hloss5_fov82_goal_plane.csv",
}

HEIGHT_MODELS = {
    "Authors": HEIGHT / "released_base_height_goal_plane.csv",
    "FT loss fix": HEIGHT / "ft_fix_height_goal_plane.csv",
    "FT height targets": HEIGHT / "ft_height_height_goal_plane.csv",
    "FT height loss 2": HEIGHT / "ft_hloss2_height_goal_plane.csv",
    "FT height loss 5": HEIGHT / "ft_hloss5_height_goal_plane.csv",
}

EXPECTED_KEYS = {
    (f"{difficulty}_seed_{seed}", float(speed))
    for difficulty in ("easy", "medium", "hard")
    for seed in range(30)
    for speed in (2, 4)
}


def wilson(k, n):
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (
        z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
        / d
    )
    return max(0, c-h), min(1, c+h)


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    data = {}

    for row in rows:
        key = (
            row["scene_id"],
            float(row["speed_mps"])
        )

        if key in data:
            raise ValueError(f"Duplicate trial in {path}: {key}")

        if row["goal_success"] not in ("0", "1"):
            raise ValueError(f"Invalid goal flag: {key}")

        if row["plane_success"] not in ("0", "1"):
            raise ValueError(f"Invalid plane flag: {key}")

        row["goal"] = int(row["goal_success"])
        row["plane"] = int(row["plane_success"])

        row["safe"] = int(
            row["goal"] == 1 or row["plane"] == 1
        )

        row["collision"] = int(
            row["termination"] == "collision"
        )

        row["miss"] = (
            float(row["miss_3d_m"])
            if row["miss_3d_m"].strip()
            else None
        )

        if row["goal"] and not row["plane"]:
            raise ValueError(
                f"Goal reached but not safely recorded: {key}"
            )

        if row["collision"] and row["safe"]:
            raise ValueError(
                f"Collision marked safe: {key}"
            )

        data[key] = row

    actual_keys = set(data)
    if actual_keys != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - actual_keys)
        extra = sorted(actual_keys - EXPECTED_KEYS)
        raise ValueError(
            f"{path.name}: expected 180 paired flights; "
            f"missing={missing[:5]}, extra={extra[:5]}"
        )

    return data


def summary(name, data, dataset):
    rows = list(data.values())
    n = len(rows)

    safe = sum(r["safe"] for r in rows)
    goal = sum(r["goal"] for r in rows)
    collision = sum(r["collision"] for r in rows)

    plane_only = [
        r for r in rows
        if r["plane"] and not r["goal"]
    ]

    misses = [
        r["miss"] for r in plane_only
        if r["miss"] is not None
    ]

    if len(misses) != len(plane_only):
        raise ValueError(
            f"{name}: missing plane-crossing distances"
        )

    ci_low, ci_high = wilson(safe, n)

    return {
        "dataset": dataset,
        "model": name,
        "flights": n,
        "safe_count": safe,
        "safe_rate": round(safe/n, 4),
        "safe_ci_low": round(ci_low, 4),
        "safe_ci_high": round(ci_high, 4),
        "exact_goal_count": goal,
        "exact_goal_rate": round(goal/n, 4),
        "collision_count": collision,
        "plane_only_count": len(plane_only),
        "plane_only_median_miss_m": (
            round(statistics.median(misses), 3)
            if misses else None
        ),
        "plane_only_max_miss_m": (
            round(max(misses), 3)
            if misses else None
        ),
        "plane_only_over_1m": sum(
            miss > 1.0 for miss in misses
        ),
    }


def exact_mcnemar(a, b, field):
    keys = sorted(set(a) & set(b))

    a_only = sum(
        a[k][field] == 1 and b[k][field] == 0
        for k in keys
    )
    b_only = sum(
        a[k][field] == 0 and b[k][field] == 1
        for k in keys
    )

    n = a_only + b_only
    if n == 0:
        return 1.0

    p = sum(
        math.comb(n, i) for i in
        range(min(a_only, b_only) + 1)
    ) / (2 ** n)

    return min(1.0, 2*p)


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    standard = {
        name: load_csv(path)
        for name, path in MODELS.items()
    }

    height = {
        name: load_csv(path)
        for name, path in HEIGHT_MODELS.items()
    }

    summaries = []

    for name, data in standard.items():
        summaries.append(
            summary(name, data, "standard")
        )

    for name, data in height.items():
        summaries.append(
            summary(name, data, "height_change")
        )

    write_csv(
        OUT / "model_summary.csv",
        summaries
    )

    baseline = standard["Authors"]
    ours = standard["Our 50k"]

    paired = [
        {
            "comparison": "Our 50k vs authors",
            "outcome": field,
            "exact_mcnemar_p": round(
                exact_mcnemar(ours, baseline, field), 6
            )
        }
        for field in ("safe", "goal", "collision")
    ]

    write_csv(
        OUT / "paired_tests.csv",
        paired
    )

    groups = defaultdict(list)
    for row in ours.values():
        groups[
            (row["difficulty"], float(row["speed_mps"]))
        ].append(row)

    by_condition = []

    for (difficulty, speed), rows in sorted(groups.items()):
        n = len(rows)
        by_condition.append({
            "difficulty": difficulty,
            "speed_mps": speed,
            "flights": n,
            "safe": sum(r["safe"] for r in rows),
            "exact_goal": sum(r["goal"] for r in rows),
            "collisions": sum(
                r["collision"] for r in rows
            ),
            "plane_only": sum(
                r["plane"] and not r["goal"]
                for r in rows
            )
        })

    write_csv(
        OUT / "ours_by_difficulty_and_speed.csv",
        by_condition
    )

    print("\nFINAL UAV EVALUATION AUDIT")
    print("=" * 68)

    for r in summaries:
        print(
            f"{r['dataset']:<14} "
            f"{r['model']:<20} "
            f"safe={r['safe_count']:>3}/180 "
            f"goal={r['exact_goal_count']:>3}/180 "
            f"collisions={r['collision_count']:>2}"
        )

    print("\nPAIRED TESTS")
    for r in paired:
        print(
            r["outcome"],
            "p =", r["exact_mcnemar_p"]
        )

    print("\nOUTPUT FILES")
    for path in sorted(OUT.glob("*.csv")):
        print(path.relative_to(ROOT))

    print("\nAUDIT PASSED: every input contains the")
    print("expected 90 scenes at 2 and 4 m/s.")


if __name__ == "__main__":
    main()
