
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle


def visualize_scene(scene_path, output_dir="results/scene_plots"):
    with open(scene_path, "r", encoding="utf-8") as file:
        scene = json.load(file)

    fig, ax = plt.subplots(figsize=(11, 7))

    for obstacle in scene["obstacles"]:
        kind = obstacle["type"]
        x, y = obstacle["center"][:2]

        if kind == "cylinder":
            shape = Circle(
                (x, y),
                obstacle["radius"],
                facecolor="saddlebrown",
                edgecolor="black",
                alpha=0.8
            )

        elif kind == "sphere":
            shape = Circle(
                (x, y),
                obstacle["radius"],
                facecolor="forestgreen",
                edgecolor="darkgreen",
                alpha=0.5
            )

        elif kind == "box":
            hx, hy, _ = obstacle["half_extents"]

            shape = Rectangle(
                (x - hx, y - hy),
                2 * hx,
                2 * hy,
                facecolor="olivedrab",
                edgecolor="black",
                alpha=0.6
            )

        else:
            raise ValueError(f"Unknown obstacle type: {kind}")

        ax.add_patch(shape)

    start = scene["start"]
    goal = scene["goal"]

    ax.plot(
        [start[0], goal[0]],
        [start[1], goal[1]],
        "k--",
        linewidth=1.5,
        label="Straight-line reference"
    )

    ax.scatter(
        start[0], start[1],
        color="blue", s=120,
        label="Start", zorder=5
    )

    ax.scatter(
        goal[0], goal[1],
        color="red", marker="*",
        s=180, label="Goal", zorder=5
    )

    ax.set_title(
        f"{scene['difficulty'].upper()} Canopy Scene "
        f"(Seed {scene['seed']})"
    )

    ax.set_xlabel("X position (meters)")
    ax.set_ylabel("Y position (meters)")
    ax.set_xlim(-2, 22)
    ax.set_ylim(-8, 8)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = output_path / f"{scene['scene_id']}.png"

    fig.savefig(filename, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved visualization: {filename}")


if __name__ == "__main__":
    for difficulty in ("easy", "medium", "hard"):
        scene_path = Path("scenes") / f"{difficulty}_seed_42.json"
        visualize_scene(scene_path)
