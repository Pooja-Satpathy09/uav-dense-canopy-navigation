# UAV Navigation in Dense Canopy / Indoor Environments

**Foundations of Robotics — Direction A: Reproducible Evaluation Suite**

## 1. Project overview

This course project investigates UAV navigation in cluttered, GPS-denied or GPS-degraded environments such as dense forests and indoor spaces. Our chosen **Direction A** focuses on evaluating an existing UAV navigation policy fairly and reproducibly, with **canopy-like scenes as the main test environment**.

We use [DiffPhysDrone](https://github.com/HenryHuYu/DiffPhysDrone) as the upstream simulation/training codebase. Our own code lives in `eval_suite/`; we aim to preserve the released baseline and add a separate evaluation pipeline rather than rewrite its navigation controller.

**Current stage:** CPU-side geometry, preliminary minimum-clearance metric, scene generation, visualization and basic scene validation. **The custom scenes and metrics are not yet integrated with DiffPhysDrone, and no trained-policy benchmark results are reported here.**

## 2. Team

| Member | Student ID |
|---|---|
| Isha | IIT2023202 |
| Kavya Mitruka | IIT2023199 |
| Shree Kruthi | IIT2023188 |
| Amulya | IIT2023068 |
| Aditi Satpathy | MRM2025005 |

Contributions and file ownership will be recorded as development proceeds. The project may add one further member, subject to course approval.

## 3. Why Direction A?

The aim is to build a benchmark that tests **fixed scenes**, checks **goal arrival as well as collisions**, measures **navigation quality and scene difficulty**, and produces repeatable data with statistical uncertainty. Initial experiments will vary canopy-scene difficulty, target speed and depth-sensor noise. The scope is evaluation, not training an entirely new canopy-specific controller.

## 4. Repository layout (current / planned)

```text
uav-dense-canopy-navigation/
├── README.md
├── .gitignore
├── simulator/
│   └── DiffPhysDrone/          # Upstream Git submodule; requires CUDA to run original system
├── eval_suite/
│   ├── geometry.py             # Sphere, infinite vertical cylinder, axis-aligned box clearances
│   ├── test_geometry.py        # Small numerical tests of obstacle clearances
│   ├── metrics.py              # Minimum clearance over sampled trajectory points
│   ├── test_metrics.py         # Small trajectory-clearance test
│   ├── scenes.py               # Seeded canopy-like scene JSON generator
│   ├── test_scenes.py          # Scene counts and seeded reproducibility tests
│   ├── visualize_scenes.py     # Top-down obstacle plots (XY projection)
│   ├── validate_scenes.py      # Geometry, start/goal safety and offline grid-path validation
│   └── test_validation.py      # Empty-scene and blocked-start sanity tests
├── scenes/                     # Generated JSON scene definitions
│   ├── easy_seed_42.json
│   ├── medium_seed_42.json
│   └── hard_seed_42.json
└── results/
    └── scene_plots/           # Generated PNG visualizations
```

> Files and folders above describe our **planned Step 1–8 working layout**, not a verified snapshot of everyone's local checkout. Create or run a file only after it has been added to the repository. Additional evaluation modules, policies, reports and experiment outputs will be introduced later.

## 5. Step-by-step progress

| Step | What we did | Key output | Status |
|---|---|---|---|
| 1 | Created GitHub project; configured Git in VS Code | Repository and clean `main` branch | Confirmed locally |
| 2 | Added upstream DiffPhysDrone as a Git submodule and pushed | `simulator/DiffPhysDrone/` and `.gitmodules` | Confirmed locally |
| 3 | Implemented sphere-to-drone clearance | `geometry.py` and initial test | Initial test confirmed |
| 4 | Added vertical-cylinder and box clearance | Expanded `geometry.py` | Code provided; verify locally |
| 5 | Implemented minimum obstacle clearance over sampled trajectory positions | `metrics.py`, `test_metrics.py` | Code provided; verify locally |
| 6 | Generated deterministic easy/medium/hard canopy-like scenes | `scenes.py`, JSON files, `test_scenes.py` | Code provided; verify locally |
| 7 | Added top-down scene visualization | `visualize_scenes.py`, PNGs | Code provided; verify locally |
| 8 | Added geometry and grid-based route feasibility checks | `validate_scenes.py`, `test_validation.py` | Code provided; verify locally |

### File explanations

- **`geometry.py`**: Returns signed surface clearance between a spherical drone approximation and one obstacle. Supports spheres, infinitely tall vertical cylinders and axis-aligned boxes. Positive means separated; zero means touching; negative means geometric overlap. The box uses a signed-distance formula.
- **`test_geometry.py`**: Checks known numerical examples for those distance formulas. These are starter tests, not full edge-case coverage.
- **`metrics.py`**: Iterates through sampled drone positions and all scene obstacles to return the **minimum recorded clearance**. It does not yet check collisions continuously between sampled positions.
- **`test_metrics.py`**: Validates the minimum-clearance function on a small hand-written trajectory and obstacle set.
- **`scenes.py`**: Uses a local random generator and a user-defined seed to create JSON scenes. Current presets contain **17 / 34 / 55** obstacles for easy / medium / hard respectively: vertical cylinders (trunks), spheres (foliage), and boxes (bushes). Each JSON file stores the start, goal, drone radius, seed, difficulty and obstacle geometry.
- **`test_scenes.py`**: Checks that repeated calls with the same seed produce the same scene, different seeds change the scene, and obstacle counts match presets.
- **`visualize_scenes.py`**: Produces top-down PNG plots of scene geometry, start and goal. **XY overlap in the plot does not automatically mean a 3D collision**, since obstacle altitude matters.
- **`validate_scenes.py`**: Checks basic obstacle dimensions and calculates start/goal clearance. Also uses a bounded, fixed-altitude 2D A* grid search as an **offline feasibility check only**; it is **not** the UAV's autonomous flight planner and does **not** demonstrate dynamic flyability.
- **`test_validation.py`**: Sanity-checks an empty scene and an example where the starting point is obstructed.
- **`simulator/DiffPhysDrone/`**: Upstream simulator/training code maintained separately as a Git submodule. We have not yet connected our custom JSON scenes or metric code to its flight loop.

## 6. Local setup and run commands (Windows PowerShell)

From the repository root:

```powershell
python --version
python -m pip install matplotlib
```

Standard-library Python is sufficient for the preliminary geometry, scene generation and validation code. `matplotlib` is needed for visualization.

If obtaining a fresh copy of our repository, initialize the simulator submodule:

```powershell
git clone --recurse-submodules <YOUR_TEAM_REPOSITORY_URL>
```

If you have already cloned the main project:

```powershell
git submodule update --init --recursive
```

Run the individual development checks and generators:

```powershell
python eval_suite/test_geometry.py
python eval_suite/test_metrics.py
python eval_suite/scenes.py
python eval_suite/test_scenes.py
python eval_suite/visualize_scenes.py
python eval_suite/validate_scenes.py
python eval_suite/test_validation.py
```

Run from the **repository root**, because scene paths are relative to it. Generated JSON files are written to `scenes/`; visualizations are written to `results/scene_plots/`.

### About CPU vs GPU

The modules listed above can run on a CPU. **Original DiffPhysDrone training and GPU-based simulation depend on CUDA and a compatible NVIDIA GPU**; cloning the code does not make the original simulator CPU-compatible. Our custom evaluation scripts have not yet been connected to a live drone policy.

## 7. Evaluation metrics (proposed; definitions to be finalized)

Our target benchmark has ten measurements. This is a **project-defined metric set**, informed by the papers below; it is **not a claim that all ten appear as one list in the gap-traversal paper**.

| # | Metric | Intended use | Status |
|---|---|---|---|
| 1 | Goal success rate | Fraction of trials reaching goal without collision | Planned |
| 2 | Collision rate | Fraction of trials with a collision | Planned |
| 3 | Path excess factor | Extra travel relative to start–goal straight-line distance | Planned |
| 4 | Minimum obstacle clearance | Nearest signed clearance along a sampled flight | Preliminary CPU implementation |
| 5 | Average traversal speed | Travelled path length divided by flight duration | Planned |
| 6 | Relative end distance | Remaining goal distance normalized by initial goal distance | Planned |
| 7 | Speed tracking error | Deviation from commanded speed | Planned |
| 8 | Trajectory smoothness | Motion jerk or related control-smoothness measure | Planned |
| 9 | Traversability | Geometry-derived difficulty of free flight | Planned |
| 10 | Relative gap size | Available passage width relative to drone size | Planned |

**Before collecting final results**, freeze the exact formulas, units, success/timeout thresholds, collision model, obstacle difficulty calculations and denominators. Additional logged fields should include seed, scene ID, policy checkpoint, speed, noise condition, altitude, termination reason and flight duration.

## 8. Known limitations and checks still needed

1. Obstacles are simplified geometric primitives, not photorealistic trees.
2. The drone is approximated as a sphere for CPU clearance calculations.
3. Vertical cylinders are currently treated as infinitely tall.
4. The minimum-clearance code checks recorded samples, not continuous flight segments.
5. Scene labels are based on obstacle counts, **not yet validated difficulty scores**.
6. The generator protects the start/goal but does not guarantee obstacles don't overlap or that every scene is safely navigable.
7. The path checker operates at one altitude and cannot establish quadrotor dynamic feasibility.
8. The top-down visualizer ignores height in the rendered footprint.
9. The original simulator is not yet running on our CPU machine.
10. No final policy evaluation, confidence intervals or benchmark conclusions have been generated.

## 9. Next development milestones

1. **Review and test Step 8 outputs**, especially invalid or obstructed scenes; improve scene generation/validation as necessary.
2. Define and implement geometry-based traversability and relative gap size; check that difficulty meaningfully increases.
3. Inspect the upstream simulator interfaces and implement a minimally invasive fixed-scene loader.
4. Train or obtain a baseline checkpoint on a compatible CUDA system; save complete reproducibility metadata.
5. Implement the rollout collector and remaining metrics; record a CSV row per flight.
6. Run controlled tests across scene difficulty, drone speed and depth noise with at least three independent training seeds where feasible.
7. Calculate uncertainty measures, compare policies/checkpoints and produce failure analyses.
8. Submit documented source code, scene-generation procedures, result CSVs, reproducible commands, literature review and final report/presentation as required by the instructor.

## 10. References

- [Vision-Based End-to-End Learning for UAV Traversal of Irregular Gaps via Differentiable Simulation](https://arxiv.org/pdf/2604.02779) — professor's reference paper.
- [DiffPhysDrone](https://github.com/HenryHuYu/DiffPhysDrone) — upstream codebase.
- [Learning Vision-Based Agile Flight via Differentiable Physics](https://www.nature.com/articles/s42256-025-01048-0) — related differentiable-physics flight research.
- [AvoidBench: A High-Fidelity Vision-Based Obstacle Avoidance Benchmarking Suite for Multi-Rotors](https://pure.tudelft.nl/ws/portalfiles/portal/158955507/AvoidBench_A_high_fidelity_vision_based_obstacle_avoidance_benchmarking_suite_for_multi_rotors.pdf) — benchmark and environment difficulty reference.

## 11. Working agreement

Work in small commits, test code before pushing, avoid edits to upstream submodule history, record experiment seeds/configurations and never label synthetic numerical tests as real trained-policy results.
