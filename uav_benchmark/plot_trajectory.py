import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


def main():
    parser = argparse.ArgumentParser(
        description="Plot a UAV benchmark trajectory and scene obstacles."
    )
    parser.add_argument("--trajectory", type=Path, required=True)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.trajectory.open(newline="") as f:
        rows = list(csv.DictReader(f))
    with args.scene.open() as f:
        scene = json.load(f)

    x = [float(r["x"]) for r in rows]
    y = [float(r["y"]) for r in rows]
    start = scene["start"]
    goal = scene["goal"]
    drone_radius = float(scene.get("drone_radius", 0.0))

    fig, ax = plt.subplots(figsize=(12, 6))

    for obs in scene.get("obstacles", []):
        cx, cy, cz = obs["center"]
        if obs["type"] == "cylinder":
            patch = Circle(
                (cx, cy), float(obs["radius"]) + drone_radius,
                color="gray", alpha=0.55
            )
            ax.add_patch(patch)
        elif obs["type"] == "sphere":
            # XY projection of a sphere; circle includes drone radius.
            patch = Circle(
                (cx, cy), float(obs["radius"]) + drone_radius,
                color="orange", alpha=0.35
            )
            ax.add_patch(patch)
        elif obs["type"] == "box":
            hx, hy, hz = obs["half_extents"]
            patch = Rectangle(
                (cx - hx - drone_radius, cy - hy - drone_radius),
                2 * (hx + drone_radius), 2 * (hy + drone_radius),
                color="gray", alpha=0.45
            )
            ax.add_patch(patch)

    ax.plot(x, y, linewidth=2, label="UAV trajectory")
    ax.scatter(start[0], start[1], marker="o", s=90, label="Start")
    ax.scatter(goal[0], goal[1], marker="*", s=180, label="Goal")
    ax.scatter(x[-1], y[-1], marker="X", s=90, label="Final position")

    ax.set(
        xlabel="X position (m)",
        ylabel="Y position (m)",
        title=f"UAV trajectory — {scene.get('scene_id', 'scene')}",
        aspect="equal",
    )
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(f"Saved trajectory plot: {args.output}")


if __name__ == "__main__":
    main()
