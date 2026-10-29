import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--trajectory", type=Path, required=True)
    p.add_argument("--scene", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    with args.trajectory.open(newline="") as f:
        rows = list(csv.DictReader(f))
    with args.scene.open() as f:
        scene = json.load(f)

    x = np.array([float(r["x"]) for r in rows])
    y = np.array([float(r["y"]) for r in rows])
    z = np.array([float(r["z"]) for r in rows])

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    for obs in scene.get("obstacles", []):
        cx, cy, cz = obs["center"]
        if obs["type"] == "sphere":
            radius = float(obs["radius"])
            u = np.linspace(0, 2*np.pi, 18)
            v = np.linspace(0, np.pi, 12)
            sx = cx + radius*np.outer(np.cos(u), np.sin(v))
            sy = cy + radius*np.outer(np.sin(u), np.sin(v))
            sz = cz + radius*np.outer(np.ones_like(u), np.cos(v))
            ax.plot_surface(sx, sy, sz, color="orange", alpha=0.18,
                            linewidth=0)
        elif obs["type"] == "cylinder":
            radius = float(obs["radius"])
            zmin = scene.get("bounds", [[-1, 21], [-7, 7], [-1, 8]])[2][0]
            zmax = scene.get("bounds", [[-1, 21], [-7, 7], [-1, 8]])[2][1]
            theta = np.linspace(0, 2*np.pi, 24)
            zz = np.linspace(zmin, zmax, 2)
            tt, zgrid = np.meshgrid(theta, zz)
            ax.plot_surface(cx + radius*np.cos(tt),
                            cy + radius*np.sin(tt), zgrid,
                            color="gray", alpha=0.12, linewidth=0)
        elif obs["type"] == "box":
            hx, hy, hz = obs["half_extents"]
            corners = np.array([
                [cx+sx*hx, cy+sy*hy, cz+sz*hz]
                for sx in (-1, 1)
                for sy in (-1, 1)
                for sz in (-1, 1)
            ])
            faces_idx = [
                [0, 1, 3, 2], [4, 5, 7, 6],
                [0, 1, 5, 4], [2, 3, 7, 6],
                [0, 2, 6, 4], [1, 3, 7, 5]
            ]
            ax.add_collection3d(Poly3DCollection(
                [[corners[i] for i in face] for face in faces_idx],
                facecolor="gray", edgecolor="gray", alpha=0.12
            ))

    start = scene["start"]
    goal = scene["goal"]
    ax.plot(x, y, z, linewidth=2.2, label="UAV trajectory")
    ax.scatter(*start, marker="o", s=70, label="Start")
    ax.scatter(*goal, marker="*", s=150, label="Goal")
    ax.scatter(x[-1], y[-1], z[-1], marker="X", s=80,
               label="Final position")

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title(f"3D UAV trajectory — {scene.get('scene_id', 'scene')}")
    ax.legend()
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
