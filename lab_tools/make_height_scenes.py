import json, re, sys
from pathlib import Path
src, dst, dz = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
dst.mkdir(parents=True, exist_ok=True)
files = sorted(src.glob("*_seed_*.json"))
for f in files:
    s = json.loads(f.read_text())
    seed = int(re.search(r"_seed_(\d+)", f.name).group(1))
    sign = 1.0 if seed % 2 == 0 else -1.0
    s["goal"][2] = s["start"][2] + sign * dz
    s["goal_height_change_m"] = sign * dz
    (dst / f.name).write_text(json.dumps(s, indent=2))
print(f"Wrote {len(files)} scenes to {dst}: even seeds goal +{dz} m, odd seeds goal -{dz} m")
