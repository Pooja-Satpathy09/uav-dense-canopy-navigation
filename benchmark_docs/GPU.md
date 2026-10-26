# Source ZIP prerequisite

Restore a real Git checkout with the root Restore-GitCheckout.ps1 script before using these live-run commands. The runner verifies the simulator Git revision. The archive includes simulator source but no Git metadata.

# Live DiffPhysDrone commands and required validation

The GPU runner is supplied but has not been run on a CUDA machine in this delivery.
The CPU suite validates metrics, I/O, command-line paths, and mocked experiment
orchestration. It does not validate the CUDA extension, rendered scene padding,
policy control, trained checkpoint, or real flight performance.

Use your friend's existing WORKING DiffPhysDrone CUDA environment first. The
pinned upstream README reports Python 3.11, PyTorch 2.2.2 and CUDA 11.8. The original
CUDA build may be easier on Linux or WSL2 Ubuntu than native Windows. Do not assume
the CPU Python environment has Torch/CUDA or that a CPU model forward pass is a
flight simulation.

## A. Check the working GPU environment

From the team repository root, in the environment your friend uses:

```powershell
python --version
nvidia-smi
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
python -c "import quadsim_cuda; print('DiffPhysDrone CUDA extension imports')"
git -C simulator/DiffPhysDrone rev-parse HEAD
git -C simulator/DiffPhysDrone status --short
```

CUDA availability must print True. The expected simulator commit is
271936190b5c2a5e760230e718fa6b167718a5bf and its working tree should be clean.
If the extension is not yet installed, build it in the working CUDA development
environment, with a compatible CUDA toolkit/compiler available:

```powershell
python -m pip install --no-build-isolation -e simulator/DiffPhysDrone/src
```

This builds GPU code. A driver alone is not the development toolkit. If using
WSL, run its Python and compiler inside WSL, not a Windows virtual environment.
For a completely new GPU setup, reproduce the upstream documented environment
with your GPU teammate before proceeding. This kit intentionally adds no Torch
dependency to CPU installation.

## B. Locate the actual trained checkpoint

Put your friend's compatible checkpoint in checkpoints/baseline.pth. That path is
a chosen local filename, not a claim that weights are included in the repository.
The adapter accepts raw state_dict or a mapping containing model/state_dict.
It infers the 7/10 observation dimensions and requires six action outputs, then
loads strictly. It uses weights_only=True. Serialized custom training objects
need a trusted conversion to a plain state_dict outside this library.

The adapter uses camera angle 10 degrees unless overridden. Confirm it matches
the checkpoint training setup. Model shape does not reveal camera settings.
The 0.2 m evaluation radius also differs from upstream's randomized training
radius range; document that evaluation condition rather than silently changing it.

## C. Opt into the real GPU smoke tests

PowerShell:

```powershell
$env:UAV_RUN_CUDA_TESTS = '1'
$env:UAV_BENCHMARK_REPO = (Resolve-Path .).Path
$env:UAV_BENCHMARK_CHECKPOINT = (Resolve-Path checkpoints/baseline.pth).Path
$env:UAV_BENCHMARK_SCENE = (Resolve-Path benchmark_configs/legacy_demo_scene.json).Path
python -m unittest discover -s benchmark_tests -p test_cuda_opt_in.py -v
if ($LASTEXITCODE -ne 0) { throw 'GPU smoke tests failed; do not collect benchmark results yet.' }
$env:UAV_RUN_CUDA_TESTS = '0'
```

Linux/WSL shell (substitute /absolute/path/to/team-repo with the real Linux path):

```bash
export UAV_RUN_CUDA_TESTS=1
export UAV_BENCHMARK_REPO="$PWD"
export UAV_BENCHMARK_CHECKPOINT="$PWD/checkpoints/baseline.pth"
export UAV_BENCHMARK_SCENE="$PWD/benchmark_configs/legacy_demo_scene.json"
python -m unittest discover -s benchmark_tests -p test_cuda_opt_in.py -v
export UAV_RUN_CUDA_TESTS=0
```

The tests compare an analytically known sphere ray depth against the real CUDA
renderer and check two identically seeded short rollouts. These are necessary
smoke checks, not full simulator certification. Also inspect rendered custom
scenes, known contact/no-contact cases, padding, and representative saved
trajectories before broad experiments.

## D. Run one empty-space trained-policy flight

Commands below work in PowerShell and Linux when run on one line:

```text
python -m uav_benchmark run --repo . --checkpoint checkpoints/baseline.pth --scene benchmark_configs/legacy_demo_scene.json --config benchmark_configs/smoke.json --seed 42 --out benchmark_results/gpu_empty_01
```

Unlike the synthetic CSV demonstration, this command actually executes the
checkpoint through the simulator. It saves trajectory.csv, normalized scene.json,
and result.metrics.json. Success is not guaranteed just because the code runs.
Metadata retains integration_validation=requires_user_gpu_validation to avoid
implying a validation history this delivery does not have. Keep your completed
GPU validation evidence alongside final results.

For the known geometric gap, create the CPU demo once, then use its scene:

```text
python -m uav_benchmark demo --out benchmark_results/gpu_gap_fixture
python -m uav_benchmark run --repo . --checkpoint checkpoints/baseline.pth --scene benchmark_results/gpu_gap_fixture/scene.json --config benchmark_configs/smoke.json --seed 42 --out benchmark_results/gpu_gap_01
```

For the repository's three scenes:

```text
python -m uav_benchmark run --repo . --checkpoint checkpoints/baseline.pth --scene scenes/easy_seed_42.json --config benchmark_configs/smoke.json --seed 42 --out benchmark_results/gpu_easy_42
python -m uav_benchmark run --repo . --checkpoint checkpoints/baseline.pth --scene scenes/medium_seed_42.json --config benchmark_configs/smoke.json --seed 42 --out benchmark_results/gpu_medium_42
python -m uav_benchmark run --repo . --checkpoint checkpoints/baseline.pth --scene scenes/hard_seed_42.json --config benchmark_configs/smoke.json --seed 42 --out benchmark_results/gpu_hard_42
```

Report failure cases honestly. For a numerical failure the last valid trajectory
and an explicit failure record are saved; the command exits nonzero. A geometric
collision or timeout is a valid navigation outcome, not an infrastructure error.

## E. Run the 90-flight pilot after generating/validating scenes

First commit the implementation/configuration so provenance is stable. From root:

```text
python -m uav_benchmark experiment --repo . --checkpoint checkpoints/baseline.pth --plan benchmark_configs/pilot.json --out benchmark_results/pilot_01
```

To resume the same experiment after interruption:

```text
python -m uav_benchmark experiment --repo . --checkpoint checkpoints/baseline.pth --plan benchmark_configs/pilot.json --out benchmark_results/pilot_01 --resume
```

Completed result files are skipped. Error/interrupted attempts are retained, and
retries save raw data into a fresh attempt directory. Resume rejects changed
scene/config/checkpoint/source identities. A changed codebase requires a new
experiment directory. Summary JSON is versioned on each resume. A per-run error
does not silently become success or disappear from the error report.

Export all finished pilot rows:

```text
python -m uav_benchmark summarize --inputs benchmark_results/pilot_01 --out benchmark_results/pilot_01_summary.json --csv benchmark_results/pilot_01_runs.csv
```

Only after the pilot is inspected, run the larger condition matrix:

```text
python -m uav_benchmark experiment --repo . --checkpoint checkpoints/baseline.pth --plan benchmark_configs/full.json --out benchmark_results/full_01
```

## Integration choices to understand

- The runner calls the existing fixed-scene bridge after env.reset(). It leaves
  upstream source unchanged and defaults to its pinned commit. The optional
  --allow-unverified-simulator flag exists only for an intentional new-version
  validation, not to hide an unexplained mismatch.
- It preserves the upstream render-before-step ordering, horizontal rotation
  frame, inverse-depth normalization, pooling, 7/10 state fields, six-output
  action transform, and two-slot initial action buffer.
- Simulation timestep is fixed for reproducible evaluation; training jitters it.
  Record this evaluation adaptation. Timestamps use simulation time, not wall time.
- Reset drag is fixed at [0,0.375]; pitch/yaw delay, camera rotation and thrust
  estimate follow the bridge's deterministic values. The upstream dg disturbance
  process remains active with a recorded seed. Fixed seed is not a promise of
  bitwise reproducibility across different GPU/toolchain combinations.
- Observation noise uses a separate seeded generator and is added in normalized
  inverse-depth space BEFORE pooling. sigma=0.02 is dimensionless; it does not
  mean 2 cm of depth noise.
- Collision/clearance uses the library's primitive geometry and recorded segments,
  not the upstream training loss's nearest-point vector as a signed oracle.
- Ground must be z=-1 for this pinned renderer. Bounds are a declared termination
  region, not newly rendered walls. An XY/altitude bound crossing is out_of_bounds.
- Inference runs without gradients and resets recurrent state for each flight.
  The library does not train a policy or manufacture missing checkpoints.
