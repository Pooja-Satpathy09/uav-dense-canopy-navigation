import json, csv, sys
d = sys.argv[1]
r = json.load(open(f"{d}/result.metrics.json"))
s = json.load(open(f"{d}/scene.json"))
print("termination:", r["termination"])
print({k: v.get("value") for k, v in r["metrics"].items() if k != "traversability"})
rows = list(csv.DictReader(open(f"{d}/trajectory.csv")))
P = [(float(t["time"]), float(t["x"]), float(t["y"]), float(t["z"])) for t in rows]
rad = s["drone_radius"]
print("bounds:", s["bounds"], "| radius:", rad, "| start:", s["start"], "| goal:", s["goal"])
for t, x, y, z in P:
    bad = [a for a, v, (lo, hi) in zip("xyz", (x, y, z), s["bounds"]) if v < lo + rad or v > hi - rad]
    if bad:
        print(f"FIRST OUT OF BOUNDS at t={t:.2f}s, axis {bad}: x={x:.2f} y={y:.2f} z={z:.2f}")
        break
for t, x, y, z in P[::max(1, len(P) // 10)] + [P[-1]]:
    print(f"t={t:5.2f}  x={x:6.2f}  y={y:6.2f}  z={z:6.2f}")
