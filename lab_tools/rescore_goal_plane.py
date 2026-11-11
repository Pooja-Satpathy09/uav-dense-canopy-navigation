"""Rescore saved benchmark flights with a goal-plane criterion (no reruns needed).

plane_success  1 if the drone reached the goal plane (x >= goal x) with no
               collision before that point, else 0
miss_lateral_m / miss_vertical_m / miss_3d_m  offsets from the goal where the
               drone crossed the goal plane (vertical < 0 = below the goal)
Usage: python rescore_goal_plane.py benchmark_results/ours_50k [more folders ...]
"""
import csv
import json
import math
import sys
from pathlib import Path


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def rescore(run_dir):
    r = json.loads((run_dir / "result.metrics.json").read_text())
    s = json.loads((run_dir / "scene.json").read_text())
    rows = list(csv.DictReader(open(run_dir / "trajectory.csv")))
    gx, gy, gz = s["goal"]
    out = {"run": run_dir.name, "scene_id": r.get("scene_id"), "difficulty": r.get("difficulty"),
           "speed_mps": r["config"]["target_speed_mps"], "termination": r["termination"],
           "goal_success": r["metrics"]["goal_success"]["value"], "plane_success": 0,
           "miss_lateral_m": "", "miss_vertical_m": "", "miss_3d_m": "", "time_to_plane_s": ""}
    prev = None
    for row in rows:
        t, x, y, z = (float(row[k]) for k in ("time", "x", "y", "z"))
        if row["collision"].strip().lower() == "true":
            break
        if x >= gx:
            if prev is not None and x > prev[1]:
                a = (gx - prev[1]) / (x - prev[1])
                t, y, z = (prev[0] + a * (t - prev[0]), prev[2] + a * (y - prev[2]),
                           prev[3] + a * (z - prev[3]))
            out.update(plane_success=1, miss_lateral_m=round(abs(y - gy), 3),
                       miss_vertical_m=round(z - gz, 3),
                       miss_3d_m=round(math.dist((gx, y, z), (gx, gy, gz)), 3),
                       time_to_plane_s=round(t, 2))
            break
        prev = (t, x, y, z)
    if not out["plane_success"] and int(out["goal_success"]) == 1:
        t, x, y, z = (float(rows[-1][k]) for k in ("time", "x", "y", "z"))
        out.update(plane_success=1, miss_lateral_m=round(abs(y - gy), 3),
                   miss_vertical_m=round(z - gz, 3),
                   miss_3d_m=round(math.dist((x, y, z), (gx, gy, gz)), 3),
                   time_to_plane_s=round(t, 2))
    return out


def main(folders):
    for folder in map(Path, folders):
        dirs = sorted({p.parent for p in folder.rglob("result.metrics.json")
                       if (p.parent / "trajectory.csv").exists()})
        if not dirs:
            print(f"{folder}: no completed flights found")
            continue
        rows = [rescore(d) for d in dirs]
        out_csv = folder.parent / f"{folder.name}_goal_plane.csv"
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\n{folder} ({len(rows)} flights) -> {out_csv}")
        groups = {}
        for row in rows:
            groups.setdefault((row["difficulty"], row["speed_mps"]), []).append(row)
        print(f"{'difficulty':<10} {'speed':>5} {'n':>4}  {'goal-sphere success':<24} "
              f"{'goal reached or plane':<24} {'median vertical miss':>20}")
        for (diff, speed), g in sorted(groups.items()):
            n = len(g)
            k1 = sum(int(x["goal_success"]) for x in g)
            k2 = sum(x["plane_success"] for x in g)
            l1, h1 = wilson(k1, n)
            l2, h2 = wilson(k2, n)
            vm = sorted(x["miss_vertical_m"] for x in g if x["plane_success"])
            med = f"{vm[len(vm) // 2]:+.2f} m" if vm else "n/a"
            print(f"{diff:<10} {speed:>5} {n:>4}  {k1 / n:.2f} [{l1:.2f}, {h1:.2f}]{'':7} "
                  f"{k2 / n:.2f} [{l2:.2f}, {h2:.2f}]{'':7} {med:>20}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
