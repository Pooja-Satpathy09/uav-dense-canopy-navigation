import sys
from pathlib import Path
from .diffphys import load_module
from .io import load_json
from .validation import validate_scene


def validate_scene_directory(repo, inputs, config):
    repo = Path(repo).resolve()
    geometry = load_module("_uav_team_geometry", repo/"eval_suite/geometry.py")
    previous = sys.modules.get("geometry")
    sys.modules["geometry"] = geometry
    try:
        validator = load_module("_uav_team_validation", repo/"eval_suite/validate_scenes.py")
    finally:
        if previous is None:
            sys.modules.pop("geometry", None)
        else:
            sys.modules["geometry"] = previous
    files = sorted(Path(inputs).glob("*.json"))
    if not files:
        raise ValueError("No scene JSON files found")
    rows = []
    for path in files:
        try:
            scene = validate_scene(load_json(path), config)
            row = validator.validate_scene(scene)
            row.update(file=str(path), scene_id=scene["scene_id"],
                       ground_start_safe=scene["start"][2]-scene["drone_radius"]>scene["ground_z_m"])
            row["passes"] = all(row.get(key, False) for key in
                                ("geometry_valid", "start_safe", "goal_safe", "path_exists", "ground_start_safe"))
        except (ValueError, KeyError, TypeError) as error:
            row = {"file": str(path), "passes": False, "error": str(error)}
        rows.append(row)
    return {"scenes": rows, "passing": sum(r["passes"] for r in rows), "total": len(rows),
            "limitation": "Existing fixed-altitude 2D grid feasibility check; no dynamic or full-3D guarantee"}
