# Lab GPU evaluation of trained DiffPhysDrone checkpoints

All numbers below come from the `uav_benchmark` runner on a Quadro RTX 6000 (lab machine),
180 flights per condition: 90 scenes (30 easy, 30 medium, 30 hard; generator seeds 0-29)
flown at 2 m/s and 4 m/s, one flight per scene and speed, simulator seed 42, no depth noise.

## 1. Training

| Item | Value |
|---|---|
| Code | DiffPhysDrone `main_cuda.py`, commit 2719361, `configs/single_agent.args` |
| Iterations / batch | 50,000 / 64 (checkpoints every 10,000) |
| Hardware / time | Quadro RTX 6000, about 6 h |
| Software | PyTorch 2.7.1+cu128, CUDA 12.8, gcc 11.4 |
| Source change | `.type()` replaced by `.scalar_type()` in the 6 `AT_DISPATCH_FLOATING_TYPES` calls of `src/quadsim_kernel.cu` and `src/dynamics_kernel.cu` (needed to compile with PyTorch 2.7) |

## 2. Evaluation setup corrections

The first evaluations did not match how DiffPhysDrone is trained. These changes were made, in order:

| # | Setting | Before | Now | Why |
|---|---|---|---|---|
| 1 | Timeout | 12 s | 24 s | 20 m at 2 m/s needs about 11-12 s with detours |
| 2 | Camera pitch | 10 deg | 20 deg | `single_agent.args` uses `--cam_angle 20` |
| 3 | Scene heights | as generated | all z shifted by -1 m (`lab_tools/shift_scenes.py`) | scene generator assumes ground at z = 0, DiffPhysDrone renders ground at z = -1 |
| 4 | Field of view | `fov_x_half_tan` 0.53 (about 56 deg, DiffPhysDrone default) | 0.82 (about 79 deg) | `single_agent.args` uses `--fov_x_half_tan 0.82`; the runner never passed it |
| 5 | Success metric | goal sphere only (0.5 m) | goal sphere **and** "goal reached or goal plane" | the run stops at the goal sphere; flights that cross x = goal x without any collision are also reported (`lab_tools/rescore_goal_plane.py`) |

Code changes to `uav_benchmark` (all opt-in; defaults reproduce the original runner):
`fov_x_half_tan` option, `altitude_hold_kp/kd` option, and `allow_unverified_simulator` passed
through `experiment` (needed because the simulator carries the compile fix above).

## 3. Results

"Safe success" = reached the goal sphere or the goal plane with no collision before it.
95% confidence intervals are Wilson intervals; p-values are exact McNemar tests on the same 180 scenes.

### 3.1 Effect of the field-of-view correction (50k checkpoint, paired)

| | FOV 56 deg (mismatched) | FOV 79 deg (matches training) | p |
|---|---|---|---|
| Safe success | 0.87 | **0.96** | 0.001 |
| Hard, 2 m/s | 0.73 | 0.93 | 0.031 |
| Goal-sphere success | 0.01 | **0.40** | |
| Collisions (of 180) | 22 | **7** | |
| Median height miss at goal | about -0.8 m | about -0.25 m | |

With the narrow camera the policy sank to about 0.5 m above ground and passed under the goal.
With the training field of view it holds height much better. **All results obtained with
FOV 56 deg should be treated as invalid.**

### 3.2 Learning curve (FOV 79 deg, no altitude hold)

| Checkpoint | Easy | Medium | Hard | Safe success (95% CI) | Goal sphere | Collisions |
|---|---|---|---|---|---|---|
| 10k | 1.00 | 0.97 | 0.92 | 0.96 [0.92, 0.98] (173/180) | 0.28 | 7 |
| 20k | 1.00 | 0.93 | 0.95 | 0.96 [0.92, 0.98] (173/180) | 0.34 | 6 |
| 30k | 1.00 | 0.95 | 0.87 | 0.94 [0.89, 0.97] (169/180) | 0.50 | 11 |
| 40k | 1.00 | 1.00 | 0.93 | 0.98 [0.94, 0.99] (176/180) | 0.26 | 4 |
| 50k | 1.00 | 0.97 | 0.92 | 0.96 [0.92, 0.98] (173/180) | 0.40 | 7 |
| Released (authors) | 0.98 | 0.98 | 0.97 | 0.98 [0.94, 0.99] (176/180) | 0.50 | 3 |

### 3.3 Our 50k model vs the authors' released checkpoint (FOV 79 deg, paired)

| | Released | Ours 50k | p |
|---|---|---|---|
| Safe success | 0.98 | 0.96 | 0.51 |
| Goal-sphere success | 0.50 | 0.40 | |
| Collisions | 3 | 7 | |

The released checkpoint is `base.pth` from DiffPhysDrone's GitHub release v1.0 (`validation_code.zip`,
`high_speed_flight/src/e2e_planner_v2/base.pth`), with two layer names renamed to match `model.py`.
Its training configuration is not published; we assume `single_agent.args`.

### 3.4 Altitude-hold add-on (measured with FOV 56 deg, superseded by 3.1)

A PD term on the vertical command (kp = 10, kd = 5, capped at 8 m/s^2) raised goal-sphere success
from 0.01 to 0.43 with unchanged safe success (0.87 vs 0.86, p = 0.71), but collisions rose from
22 to 26 (hard 4 m/s: 5 to 10) and RMS jerk roughly doubled in a test flight. With the correct
field of view the add-on is not needed.

## 4. Conclusions

1. The main cause of the early poor results was evaluation mismatch (field of view, scene height,
   timeout), not insufficient training.
2. With a training-matched setup the trained policy completes 94-98% of flights without collision,
   including hard scenes, and is statistically indistinguishable from the authors' checkpoint.
3. Safe navigation plateaus by 10k iterations; training longer does not improve it.
4. Goal-sphere success (26-50%) varies between checkpoints without a trend and tracks each
   checkpoint's cruising-height bias: the median height miss is about -0.2 to -0.3 m against a
   0.5 m goal radius. DiffPhysDrone's objective rewards flying towards the goal direction safely, not
   arriving at an exact point, so precise arrival is not something more training would add.

## 5. Limitations

- Simulation only, one flight per scene and speed, a single simulator seed, no depth noise.
- Goal-plane success is our addition; the benchmark's own metric is the 0.5 m goal sphere.
- The scene-height shift and field-of-view value are our corrections to the team's scene generator
  and runner, based on DiffPhysDrone's code; they are documented above so they can be reviewed.

## 6. Evidence in this repository

`benchmark_docs/lab_results/` holds the per-flight CSVs (`*_goal_plane.csv`), the printed comparison
tables (`*.txt`), each 79 deg run's `experiment.json` manifest (including the checkpoint SHA-256),
`checkpoint_sha256.txt`, and the compressed training log (`train_50k.log.gz`). Checkpoints are not
committed; they are shared separately.

## 7. Reproduce

```bash
python -m uav_benchmark generate-scenes --repo . --out benchmark_scenes --start-seed 0 --count 30
python lab_tools/shift_scenes.py benchmark_scenes benchmark_scenes_ground -1.0
python -m uav_benchmark validate-scenes --repo . --inputs benchmark_scenes_ground \
    --config benchmark_configs/eval_24s.json --out benchmark_results/scene_validation_ground.json
python -m uav_benchmark experiment --repo . --checkpoint checkpoints/ours_50k.pth \
    --plan benchmark_configs/lab_plan_fov82.json --out benchmark_results/ours_50k_fov82
python lab_tools/rescore_goal_plane.py benchmark_results/ours_50k_fov82
python lab_tools/learning_curve.py ours_50k_fov82
python lab_tools/compare_paired.py released_base_fov82 ours_50k_fov82
```
