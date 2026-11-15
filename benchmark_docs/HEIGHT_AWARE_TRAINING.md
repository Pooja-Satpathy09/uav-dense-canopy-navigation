# Height-aware training for DiffPhysDrone

This continues `LAB_EVALUATION.md`. With a training-matched evaluation, DiffPhysDrone is safe
(0.96–0.98 safe success) but often misses the 0.5 m goal sphere, typically by flying **low**
(median height error at the goal about −0.25 to −0.29 m). This page explains why, what we changed,
how to reproduce it and what it achieved.

## 1. Diagnosis

1. **Ground-affinity bug** (`main_cuda.py`, upstream commit `2719361`). The total loss ends with
   `... + args.coef_ground_affinity + loss_ground_affinity`, while every other term is a product
   `coef * loss`. `coef_ground_affinity` defaults to 0 and is documented as legacy, so the term is meant
   to be off; because of the `+` it is always on with weight 1.
   `loss_ground_affinity = mean(relu(p_z)^2)` penalises any height above z = 0, i.e. more than 1 m above
   the ground (ground at z = −1), which pulls the policy down.
2. **Same-height targets** (`env_cuda.py`). Each episode samples start and target with the same height
   factor, so the policy never has to change altitude to reach a target.

## 2. What we changed

`patches/diffphysdrone_height_aware.patch` (apply after `diffphysdrone_pytorch27_scalar_type.patch`)
adds three training options. All are **off by default**, so training without them is unchanged.

| Option | Effect |
|---|---|
| `--ground_affinity_fix` | multiplies instead of adds: `coef_ground_affinity * loss_ground_affinity` (0 with the default) |
| `--target_dz D` | offsets each training target's height by U(−D, D) m, clamped to z ∈ [−0.6, 1.5] |
| `--coef_height W` | adds `W * mean_t( t/T * smoothL1(p_z(t) − z_target) )`: a height error that matters more as the flight goes on, so early vertical dodging stays cheap |

The same edits as scripts (safe to re-run): `lab_tools/training/add_height_aware.py`, then
`lab_tools/training/add_height_loss.py`, run inside `simulator/DiffPhysDrone`.

## 3. Height-change test

`lab_tools/make_height_scenes.py benchmark_scenes_ground benchmark_scenes_height 0.6` takes the 90
standard scenes and moves each goal 0.6 m **above** the start (even seeds) or **below** it (odd seeds).
Plan: `benchmark_configs/lab_plan_height_fov82.json` (same settings as `lab_plan_fov82.json`).

## 4. Reproduce

**Colab (no lab machine needed):** `colab/UAV_finetune_eval_colab.ipynb` and
`colab/UAV_height_loss_colab.ipynb`. Each clones this repository at `91d186a`, applies both patches,
builds the simulator, regenerates the 90 scenes and checks them byte-for-byte against the lab scene
hashes, fine-tunes, evaluates (resumable, results on Google Drive) and writes all tables. They need the
authors' released checkpoint as `MyDrive/uav_eval/checkpoints/released_base.pth` (from the authors'
v1.0 release; it is not redistributed here).

**Training commands** (inside `simulator/DiffPhysDrone`, both patches applied):

```bash
# fine-tuning, as evaluated below (1,200 iterations from the authors' weights)
python main_cuda.py $(cat configs/single_agent.args) --num_iters 1200 --lr 3e-4 \
    --resume released_base.pth --ground_affinity_fix                       # FT: loss fix
#   ... --ground_affinity_fix --target_dz 1.0                               # FT: + height targets
#   ... --ground_affinity_fix --target_dz 1.0 --coef_height 2.0             # FT: + height loss, w = 2
#   ... --ground_affinity_fix --target_dz 1.0 --coef_height 5.0             # FT: + height loss, w = 5

# from scratch (trained on the lab GPU, not yet evaluated: the lab machine failed)
python main_cuda.py $(cat configs/single_agent.args) --num_iters 20000 --ground_affinity_fix
python main_cuda.py $(cat configs/single_agent.args) --num_iters 20000 --ground_affinity_fix --target_dz 1.0
```

**Analysis** (from the folder that holds `benchmark_results/`):

```bash
python lab_tools/rescore_goal_plane.py benchmark_results/<run>
python lab_tools/height_table.py released_base_height ft_fix_height ft_height_height --pair ft_fix_height ft_height_height
python lab_tools/ten_metrics.py benchmark_results released_base_fov82 ft_fix_fov82 --pair released_base_fov82 ft_fix_fov82
```

## 5. Results

All runs on a Colab Tesla T4, 180 flights per model (90 scenes × 2 and 4 m/s). Colab reproduced the
lab results for the authors' model exactly (0.98 safe success, 3 collisions, median height error
−0.25 m); 19 of 20 check flights on hard scenes ended the same way as on the lab GPU.
FT = fine-tuned from the authors' model. ẽz = median height error at the goal plane.
"Follows" = change of the drone's median height between goal-above and goal-below scenes, as a share
of the goal's 1.2 m change.

| Model | Standard: safe | goal | coll. | ẽz | Height test: goal above | goal below | all | follows | coll. |
|---|---|---|---|---|---|---|---|---|---|
| Authors' model | 0.98 | 0.49 | 3 | −0.25 m | 0.00 | 0.54 | 0.27 | 17% | 8 |
| FT: loss fix | 0.96 | 0.50 | 3 | +0.10 m | 0.39 | 0.11 | 0.25 | 27% | 2 |
| FT: + height targets | 0.96 | 0.52 | 3 | +0.04 m | 0.11 | 0.07 | 0.09 | 19% | 3 |
| FT: + height loss, w = 2 | 0.96 | 0.56 | 4 | −0.21 m | 0.00 | 0.59 | 0.29 | 29% | 4 |
| FT: + height loss, w = 5 | 0.97 | 0.52 | 5 | −0.17 m | 0.02 | 0.57 | 0.29 | 41% | 7 |

Findings (paired tests on the same 180 flights):

- **Loss fix** removes the low-flying bias on the standard scenes (median absolute height error 0.25 →
  0.11 m, Wilcoxon p < 1e-8) with safety unchanged (0.96 vs 0.98, exact McNemar p = 0.45).
- **Height-aware targets** reduce the error further (0.06 m, p < 1e-12) but do not teach height
  following: 19%, and goal-sphere success on the height test drops to 0.09 (p < 0.001).
- **Explicit height loss** gives the first measurable height following (29% at w = 2, 41% at w = 5,
  vs 17%) and recovers goal-sphere success (0.29 vs 0.09, p < 0.001), not yet significantly above the
  authors' model (0.27, p = 0.42). w = 5 lowers obstacle clearance (p < 0.001). On standard scenes
  w = 2 has the highest goal-sphere success (0.56 vs 0.49, p = 0.06, not significant).
- Every fine-tuned model flies more smoothly than the authors' (jerk 5.3–5.8 vs 7.7 m/s³, p < 0.001).
- **Limit:** the policy perceives the goal only through the target-velocity direction; at 20 m, a 0.6 m
  height difference tilts it by under 2°. Next step: give the policy the relative goal height as an input.

Full tables: `height_aware_results/` (goal-plane CSVs per run, ten-metric tables and paired tests, the
notebooks' printed results, and SHA-256 of the fine-tuned models).

## 6. Models

Model files are not in the repository. The fine-tuned models are derived from the authors' released
weights, which carry no licence, so they are shared within the team only. Their SHA-256 fingerprints
are in `height_aware_results/checkpoint_sha256.txt`.
