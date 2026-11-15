"""Height-change test summary (height-aware training evaluation).

In benchmark_scenes_height the goal is 0.6 m above the start for even scene seeds and
0.6 m below it for odd seeds. Reads benchmark_results/<name>_goal_plane.csv (made by
rescore_goal_plane.py) and prints, per checkpoint and for goal-up / goal-down flights:
goal-sphere success (Wilson 95% CI), safe success, collisions and the height error where
the drone reached the goal plane. Then paired exact McNemar tests on goal-sphere success.

Usage: python lab_tools/height_table.py NAME [NAME ...] [--pair A B ...]
Run from the folder that contains benchmark_results/.
"""
import argparse
import csv
import math
import re
import statistics


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def load(name):
    rows = list(csv.DictReader(open(f"benchmark_results/{name}_goal_plane.csv")))
    for r in rows:
        r["direction"] = "up" if int(re.search(r"_seed_(\d+)", r["scene_id"]).group(1)) % 2 == 0 else "down"
    return rows


def ok(r):
    return r["goal_success"] == "1" or r["plane_success"] == "1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+")
    ap.add_argument("--pair", nargs=2, action="append", default=[])
    args = ap.parse_args()
    data = {}
    for name in dict.fromkeys(args.names + [x for p in args.pair for x in p]):
        try:
            data[name] = load(name)
        except FileNotFoundError:
            print(f"{name}: no results yet (run rescore_goal_plane.py first)")
    print("Goal 0.6 m above (up) or below (down) the start. Height error = z - goal z at the goal plane.")
    print(f"{'checkpoint':<22} {'goal':<5} {'n':>4} | {'goal-sphere success':<22} {'safe':>5} {'coll':>5} | "
          f"{'median height err':>17} {'median |err|':>12}")
    for name, rows in data.items():
        for direction in ("up", "down", "all"):
            g = rows if direction == "all" else [r for r in rows if r["direction"] == direction]
            n = len(g)
            if not n:
                continue
            k = sum(r["goal_success"] == "1" for r in g)
            lo, hi = wilson(k, n)
            err = [float(r["miss_vertical_m"]) for r in g if r["plane_success"] == "1" and r["miss_vertical_m"] != ""]
            med = f"{statistics.median(err):+.2f} m" if err else "n/a"
            mabs = f"{statistics.median(abs(e) for e in err):.2f} m" if err else "n/a"
            coll = sum(r["termination"] == "collision" for r in g)
            print(f"{name:<22} {direction:<5} {n:>4} | {k / n:.2f} [{lo:.2f}, {hi:.2f}]{'':6} "
                  f"{sum(ok(r) for r in g) / n:>5.2f} {coll:>5} | {med:>17} {mabs:>12}")
        print()
    for a_name, b_name in args.pair:
        if a_name not in data or b_name not in data:
            continue
        A = {(r["scene_id"], r["speed_mps"]): r for r in data[a_name]}
        B = {(r["scene_id"], r["speed_mps"]): r for r in data[b_name]}
        keys = sorted(set(A) & set(B))
        print(f"Paired goal-sphere success: A = {a_name}, B = {b_name}")
        for direction in ("up", "down", "all"):
            ks = [k for k in keys if direction == "all" or A[k]["direction"] == direction]
            ga = sum(A[k]["goal_success"] == "1" for k in ks)
            gb = sum(B[k]["goal_success"] == "1" for k in ks)
            only_a = sum(A[k]["goal_success"] == "1" and B[k]["goal_success"] != "1" for k in ks)
            only_b = sum(B[k]["goal_success"] == "1" and A[k]["goal_success"] != "1" for k in ks)
            n = max(1, len(ks))
            print(f"  {direction:<5} n={len(ks):>3}  A {ga / n:.2f}  B {gb / n:.2f}  "
                  f"(A only {only_a}, B only {only_b})  exact McNemar p = {mcnemar(only_a, only_b):.4f}")
        print()


if __name__ == "__main__":
    main()
