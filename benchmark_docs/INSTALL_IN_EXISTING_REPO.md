# Exact implementation and command sequence

All commands in this file are Windows PowerShell commands. Run them from the
team repository root unless explicitly stated. Source code is supplied as an
additive Git patch and as a ZIP. Use ONE installation method; applying both
would attempt to add the same files twice.

The reviewed baseline is a09299e5525b8098d378d402e8ef3f20ca290e26 on main.
The code adds a new `uav_benchmark` package, so existing eval_suite scripts are
preserved. This is a small architecture adjustment from the earlier proposal:
it avoids an immediate import migration for your friends.

## 1. Get the repository and make your branch

If you do not already have a checkout, run this from the parent folder in which
you want to keep the project:

```powershell
git clone --recurse-submodules https://github.com/Pooja-Satpathy09/uav-dense-canopy-navigation.git
cd uav-dense-canopy-navigation
git switch -c codex/ten-metric-benchmark
```

If you ALREADY have the checkout, open PowerShell in its root and use this
instead. Preserve any uncommitted work before switching branches:

```powershell
git status --short
git switch main
git pull --ff-only origin main
git submodule update --init --recursive
git switch -c codex/ten-metric-benchmark
```

If the branch already exists, use `git switch codex/ten-metric-benchmark` rather
than creating it again. Do not reset or overwrite your friends' changes.

## 2. Apply the exact supplied code

Save uav-benchmark.patch in Downloads. If you saved elsewhere, change only the
`$benchmarkPatch` path below:

```powershell
$benchmarkPatch = Join-Path $env:USERPROFILE 'Downloads\uav-benchmark.patch'
git apply --check $benchmarkPatch
if ($LASTEXITCODE -ne 0) { throw 'Patch check failed; do not apply until conflicts are reviewed.' }
git apply $benchmarkPatch
if ($LASTEXITCODE -ne 0) { throw 'Patch application failed.' }
git status --short
```

The patch adds source files; it does not edit eval_suite or the simulator.
Alternatively, extract the ZIP CONTENTS into the repository root. Afterward,
`uav_benchmark` and `eval_suite` must be side-by-side. Do not create an extra
`uav-benchmark-kit` directory inside the repository.

## 3. Run CPU tests first

Python 3.10+ is sufficient for CPU metrics. Python 3.11 is recommended if this
environment will later run the pinned simulator. No third-party package is
needed for CPU tests or the demonstration:

```powershell
python --version
python -m unittest discover -s benchmark_tests -v
if ($LASTEXITCODE -ne 0) { throw 'Fix failed tests before running experiments.' }
```

Ordinary execution skips the two opt-in CUDA tests. A skipped CUDA test does not
mean the GPU runner passed.

To run your friends' existing CPU checks as well:

```powershell
$existingTests = @('test_geometry.py','test_metrics.py','test_flight_metrics.py','test_scenes.py','test_validation.py','test_scene_adaptor.py','test_trajectory_recorder.py','test_difficulty.py')
foreach ($testFile in $existingTests) {
    python (Join-Path 'eval_suite' $testFile)
    if ($LASTEXITCODE -ne 0) { throw "Existing test failed: $testFile" }
}
```

The existing test_diffphys_bridge.py additionally needs Torch, even though its
environment is mocked. Run it in your friend's working Torch environment:

```powershell
python eval_suite/test_diffphys_bridge.py
```

## 4. Run the known-answer demonstration

```powershell
python -m uav_benchmark demo --out benchmark_results/demo_01
Get-Content benchmark_results/demo_01/success.metrics.json
python -m uav_benchmark summarize --inputs benchmark_results/demo_01 --out benchmark_results/demo_summary_01.json --csv benchmark_results/demo_runs_01.csv
```

The demo creates a real geometric 1 m gap between two boxes, then evaluates
hand-authored trajectories. It is an analytical test, not a drone-policy result.
The success case should contain:

```text
goal_success             1
collision                0
path_excess_factor       0
min_obstacle_clearance_m  approximately 0.3
average_speed_mps        2
relative_end_distance    0
speed_rmse_mps           0
jerk_rms_mps3            0
relative_gap_size        2.5
```

Traversability depends on the declared grid/domain and is calculated separately.
The demo also saves timeout, partial, and collision cases. Summary counts exclude
the partial case from completed-trial rates and report that exclusion.

Output files are not overwritten. For a second demo use demo_02 and new summary
filenames rather than deleting the earlier results.

## 5. Evaluate the trajectory already committed by your friends

Its scene is empty with a 10 m goal; do not evaluate it against the 20 m canopy
scene. The matching scene description is included:

```powershell
python -m uav_benchmark evaluate --trajectory results/trajectories/empty_demo_scene_synthetic_run_01.csv --scene benchmark_configs/legacy_demo_scene.json --config benchmark_configs/smoke.json --source synthetic --out benchmark_results/existing_demo.metrics.json
```

For a real saved flight, replace the CSV and scene paths with the exact ones used
in that run and supply its actual configuration. In particular, if the old flight
used ground z=0, make a separate configuration with `ground_z_m: 0.0` and preserve
that fact. Do not relabel an analytical/demo trajectory as a policy flight.

To use the library from your friend's Python flight script:

```python
from uav_benchmark import Sample, RunConfig, evaluate_run
from uav_benchmark.io import dump_json

samples = [
    Sample(float(r['time']), (r['x'], r['y'], r['z']),
           (r['vx'], r['vy'], r['vz']),
           collision=r['collision'], reached_goal=r['reached_goal'])
    for r in recorder.records
]
result = evaluate_run(samples, original_scene, RunConfig(target_speed_mps=2.0),
                      metadata={'source': 'trained_policy', 'run_id': 'flight_001'})
dump_json('benchmark_results/flight_001.metrics.json', result)
```

Here recorder and original_scene are the existing in-memory objects in that
script. For CSVs use `load_trajectory()` instead; it safely decodes boolean text.
The initial sample must equal the supplied scene start. Add checkpoint/seed
metadata for real comparisons; the supplied live runner records it automatically.

## 6. Evaluate easy, medium and hard scene geometry

```powershell
python -m uav_benchmark validate-scenes --repo . --inputs scenes --config benchmark_configs/smoke.json --out benchmark_results/seed42_validation.json
foreach ($level in @('easy','medium','hard')) {
    python -m uav_benchmark scene --scene "scenes/${level}_seed_42.json" --config benchmark_configs/smoke.json --out "benchmark_results/${level}_seed42_scene.json"
    if ($LASTEXITCODE -ne 0) { throw "Scene metric failed: $level" }
}
```

These commands measure scenes, not policy performance. The existing canopy scenes
have no verified passage metadata, so relative_gap_size is not_applicable.
Traversability is a fixed-altitude geometric score, not predicted goal success.

## 7. Commit and push your implementation

Review before committing. All commands below are for YOUR local terminal; nothing
has been committed or pushed automatically:

```powershell
git add uav_benchmark benchmark_tests benchmark_configs benchmark_docs benchmark_results/.gitignore benchmark_scenes/.gitignore checkpoints/.gitignore README_BENCHMARK.md pyproject.toml .github/workflows/benchmark-tests.yml
git diff --cached --stat
git diff --cached
git diff --cached --check
python -m unittest discover -s benchmark_tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; do not commit this version.' }
git commit -m "Add modular ten-metric UAV benchmark library and validation"
git push -u origin codex/ten-metric-benchmark
```

Then open this compare page and create a pull request targeting main:
https://github.com/Pooja-Satpathy09/uav-dense-canopy-navigation/compare/main...codex/ten-metric-benchmark

Ask one friend to review definitions and one to review simulator integration.
The CPU implementation can merge after review, but final experiment results must
wait for the GPU checks in GPU.md. If you lack push access, push the branch to your
fork and open a PR from that fork instead.

## 8. Run real policy flights and statistical experiments

Follow benchmark_docs/GPU.md on the NVIDIA machine already used by your friend.
First run one empty-space/known-gap flight, then one easy/medium/hard flight.
Only then generate the 90-scene pilot set:

```powershell
python -m uav_benchmark generate-scenes --repo . --out benchmark_scenes --start-seed 0 --count 30
python -m uav_benchmark validate-scenes --repo . --inputs benchmark_scenes --config benchmark_configs/smoke.json --out benchmark_results/pilot_scene_validation.json
```

Review validation failures before benchmarking; do not silently cherry-pick seeds.
The grid checker establishes only fixed-altitude route feasibility, not a full
dynamic flight guarantee. Retain infeasible cases as a labeled stress set or
publish a fixed documented selection rule for the feasible benchmark.

The pilot plan gives 3 difficulties x 30 scenes x 1 speed x 1 noise condition x
1 dynamics seed = 90 flights/checkpoint. The full plan gives 1620 flights/checkpoint
with 3 speeds x 2 noise settings x 3 dynamics seeds. Repeated seeds on the same
scene are not independent maps. Never start the full matrix before the pilot.

## 9. Your friends' exact Git update commands

While your PR is still under review, friends can inspect and extend your branch:

```powershell
git status --short
git fetch origin
git switch --track origin/codex/ten-metric-benchmark
python -m unittest discover -s benchmark_tests -v
git switch -c codex/scene-metrics
```

If they already have that local branch, use `git switch codex/ten-metric-benchmark`
and `git pull --ff-only` instead of creating a tracking branch again. Each friend
should choose their own feature branch name before editing.

After your PR merges:

```powershell
git switch main
git pull --ff-only origin main
git submodule update --init --recursive
python -m unittest discover -s benchmark_tests -v
git switch -c codex/next-benchmark-extension
```

## 10. Build the reusable Python library

The package can be used directly from the repository without installation. To
install it into a virtual environment or produce a wheel:

```powershell
python -m pip install --upgrade setuptools wheel
python -m pip install --no-build-isolation -e .
python -m pip wheel --no-deps --no-build-isolation . --wheel-dir dist
```

The wheel appears in dist/. Friends can install that .whl with `python -m pip
install` followed by its exact filename. It contains the CPU library and optional
adapter, not upstream simulator sources, Torch, CUDA, checkpoints, or experiment
data. The live adapter requires the team repository path in `--repo`.

If tests fail only because the computer's temporary directory is inaccessible,
choose a writable temporary folder for this PowerShell session:

```powershell
New-Item -ItemType Directory -Path benchmark_results/test_temp -Force | Out-Null
$env:TEMP = (Resolve-Path benchmark_results/test_temp).Path
$env:TMP = $env:TEMP
python -m unittest discover -s benchmark_tests -v
```
