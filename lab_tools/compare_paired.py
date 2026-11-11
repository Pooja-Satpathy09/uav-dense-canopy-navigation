import csv, math, sys, collections

def load(name):
    return {(r["scene_id"], r["speed_mps"]): r for r in csv.DictReader(open(f"benchmark_results/{name}_goal_plane.csv"))}

def ok(r):        # reached the goal sphere or the goal plane without collision
    return r["goal_success"] == "1" or r["plane_success"] == "1"

def mcnemar(b, c):  # exact two-sided test on the discordant pairs
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)

A, B = load(sys.argv[1]), load(sys.argv[2])
keys = sorted(set(A) & set(B))
groups = collections.defaultdict(list)
for k in keys:
    groups[(A[k]["difficulty"], A[k]["speed_mps"])].append((A[k], B[k]))
rows = sorted(groups.items()) + [(("ALL", ""), [(A[k], B[k]) for k in keys])]
print(f"A = {sys.argv[1]}   B = {sys.argv[2]}   (same scenes, paired)")
print(f"{'group':<12} {'n':>4} | {'success A':>9} {'success B':>9} {'p':>7} | {'goal A':>6} {'goal B':>6} | {'collide A':>9} {'collide B':>9}")
for (d, s), pairs in rows:
    n = len(pairs)
    sa, sb = sum(ok(a) for a, _ in pairs), sum(ok(b) for _, b in pairs)
    only_a, only_b = sum(ok(a) and not ok(b) for a, b in pairs), sum(ok(b) and not ok(a) for a, b in pairs)
    ga, gb = sum(a["goal_success"] == "1" for a, _ in pairs), sum(b["goal_success"] == "1" for _, b in pairs)
    ca, cb = sum(a["termination"] == "collision" for a, _ in pairs), sum(b["termination"] == "collision" for _, b in pairs)
    print(f"{d + ' ' + s:<12} {n:>4} | {sa/n:>9.2f} {sb/n:>9.2f} {mcnemar(only_a, only_b):>7.3f} | {ga/n:>6.2f} {gb/n:>6.2f} | {ca:>9} {cb:>9}")
