import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from .types import RunConfig, Sample
from .validation import number, validate_config


def load_json(path):
    def invalid_constant(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid_constant)


def dump_json(path, data):
    path = Path(path)
    content = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as file:
        file.write(content)
    return path


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_info(path):
    def run(*args):
        try:
            return subprocess.check_output(["git", "-C", str(path), *args], stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    status = run("status", "--porcelain")
    return {"commit": run("rev-parse", "HEAD"), "dirty": None if status is None else bool(status)}


def software_fingerprint(repo=None):
    """Detect source changes even when the Git commit and dirty flag are unchanged."""
    package = Path(__file__).resolve().parent
    sources = {"uav_benchmark/"+str(p.relative_to(package)).replace("\\", "/"): file_hash(p)
               for p in sorted(package.rglob("*.py"))}
    if repo:
        root = Path(repo)
        for relative in ("eval_suite/scene_adapter.py", "eval_suite/diffphys_bridge.py",
                         "simulator/DiffPhysDrone/env_cuda.py", "simulator/DiffPhysDrone/model.py"):
            path = root/relative
            if path.exists():
                sources[relative] = file_hash(path)
    return fingerprint(sources)


def load_config(path=None):
    return validate_config(RunConfig(**(load_json(path) if path else {})))


def parse_bool(value):
    if type(value) is bool:
        return value
    normalized = str(value).strip().lower()
    if normalized in ("true", "1"):
        return True
    if normalized in ("false", "0"):
        return False
    raise ValueError(f"Invalid boolean: {value!r}")


def load_trajectory(path, scene):
    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"time", "x", "y", "z", "vx", "vy", "vz"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Trajectory CSV needs {sorted(required)}")
        result, ids = [], set()
        for row in reader:
            if row.get("scene_id"):
                if row["scene_id"] != scene.get("scene_id", "unnamed"):
                    raise ValueError("CSV scene_id differs from supplied scene")
            if row.get("run_id"):
                ids.add(row["run_id"])
            position = tuple(number(row[k], k) for k in ("x", "y", "z"))
            velocity = tuple(number(row[k], k) for k in ("vx", "vy", "vz"))
            if row.get("distance_to_goal"):
                recorded = number(row["distance_to_goal"], "distance_to_goal", nonnegative=True)
                if not math.isclose(recorded, math.dist(position, scene["goal"]), abs_tol=1e-4, rel_tol=1e-5):
                    raise ValueError("CSV distance_to_goal conflicts with scene goal")
            result.append(Sample(number(row["time"], "time", nonnegative=True), position, velocity,
                                 parse_bool(row.get("collision", "False")),
                                 parse_bool(row.get("reached_goal", "False"))))
    if len(ids) > 1:
        raise ValueError("A trajectory file must contain only one run")
    return result


def save_trajectory(path, samples, scene, run_id):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["scene_id", "run_id", "time", "x", "y", "z", "vx", "vy", "vz",
              "distance_to_goal", "collision", "reached_goal"]
    with path.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for sample in samples:
            row = dict(zip(("x", "y", "z", "vx", "vy", "vz"), (*sample.position, *sample.velocity)))
            row.update(scene_id=scene["scene_id"], run_id=run_id, time=sample.time,
                       distance_to_goal=math.dist(sample.position, scene["goal"]),
                       collision=sample.collision, reached_goal=sample.reached_goal)
            writer.writerow(row)
    return path
