import csv, math, sys

def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)

ok = lambda r: r["goal_success"] == "1" or r["plane_success"] == "1"
print("success = reached goal sphere or goal plane with no collision")
print(f"{'checkpoint':<20} {'easy':>6} {'medium':>7} {'hard':>6} | {'all (95% CI)':<22} {'goal sphere':>11} {'collisions':>10}")
for name in sys.argv[1:]:
    try:
        rows = list(csv.DictReader(open(f"benchmark_results/{name}_goal_plane.csv")))
    except FileNotFoundError:
        print(f"{name:<20} (no results yet)")
        continue
    rate = lambda d: sum(ok(r) for r in rows if r["difficulty"] == d) / max(1, sum(r["difficulty"] == d for r in rows))
    k, n = sum(ok(r) for r in rows), len(rows)
    lo, hi = wilson(k, n)
    g = sum(r["goal_success"] == "1" for r in rows) / n
    c = sum(r["termination"] == "collision" for r in rows)
    print(f"{name:<20} {rate('easy'):>6.2f} {rate('medium'):>7.2f} {rate('hard'):>6.2f} | {k/n:.2f} [{lo:.2f}, {hi:.2f}] ({k}/{n}) {g:>8.2f} {c:>10}")
