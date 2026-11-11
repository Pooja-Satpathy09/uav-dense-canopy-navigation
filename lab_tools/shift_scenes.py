"""Lower every height in the team's scenes by 1 m.

The scene generator (eval_suite/scenes.py) puts the ground at z = 0, but the
DiffPhysDrone renderer draws the ground at z = -1. Shifting everything down by
1 m lines the two up and puts the drone 1.5 m above the ground, inside the
height range DiffPhysDrone was trained on (about 0.5-1.5 m above ground).
"""
import json, sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dz = float(sys.argv[3]) if len(sys.argv) > 3 else -1.0
dst.mkdir(parents=True, exist_ok=True)
files = sorted(src.glob("*_seed_*.json"))
for f in files:
    s = json.loads(f.read_text())
    for key in ("start", "goal"):
        s[key][2] += dz
    for o in s["obstacles"]:
        o["center"][2] += dz
    s["height_shift_m"] = dz
    (dst / f.name).write_text(json.dumps(s, indent=2))
print(f"Shifted {len(files)} scenes by {dz} m into {dst}")
