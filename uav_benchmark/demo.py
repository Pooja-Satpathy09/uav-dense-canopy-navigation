from dataclasses import replace
from pathlib import Path
from .io import dump_json, save_trajectory, fingerprint
from .metrics import evaluate_run
from .types import RunConfig, Sample


def demo(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    scene = {"scene_id": "synthetic_known_gap", "difficulty": "synthetic",
             "start": [0, 0, 1.5], "goal": [10, 0, 1.5], "drone_radius": .2,
             "ground_z_m": -1, "bounds": [[-1, 11], [-3, 3], [-1, 5]],
             "obstacles": [{"type": "box", "center": [5, -1.25, 1.5], "half_extents": [.1, .75, 2]},
                           {"type": "box", "center": [5, 1.25, 1.5], "half_extents": [.1, .75, 2]}],
             "passages": [{"id": "gap_x5", "free_width_m": 1.0, "geometry_verified": True,
                           "description": "Between y=-0.5 and y=0.5 faces of the two boxes"}]}
    config = RunConfig()
    dump_json(output/"scene.json", scene)
    dump_json(output/"config.json", config.to_dict())
    cases = {
        "success": [Sample(i, (2*i, 0, 1.5), (2, 0, 0), reached_goal=i==5) for i in range(6)],
        "timeout": [Sample(i, (0, 0, 1.5), (0, 0, 0)) for i in range(13)],
        "partial": [Sample(i, (i, 0, 1.5), (1, 0, 0)) for i in range(6)],
        "collision": [Sample(0, (0, 0, 1.5), (0, 0, 0)), Sample(1, (5, 1.25, 1.5), (5, 1.25, 0), collision=True)]}
    for name, samples in cases.items():
        save_trajectory(output/f"{name}.csv", samples, scene, name)
        result = evaluate_run(samples, scene, config, metadata={"source": "synthetic",
            "run_id": name, "scene_hash": fingerprint(scene), "run_fingerprint": fingerprint([scene, name])})
        dump_json(output/f"{name}.metrics.json", result)
    dump_json(output/"manifest.json", {"runs": [{"trajectory": f"{name}.csv", "scene": "scene.json",
                  "config": "config.json", "source": "synthetic"} for name in cases]})
    return output
