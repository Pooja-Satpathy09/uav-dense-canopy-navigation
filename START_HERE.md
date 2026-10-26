# Start here: complete project source download

This archive already contains the team repository, its pinned DiffPhysDrone
simulator source, the new uav_benchmark library, and the two eval_suite files
provided in the chat. Extract the ZIP completely, then open the extracted
uav-dense-canopy-navigation folder in VS Code. Do not apply another patch.

## 1. Run on your CPU first

Open PowerShell in this folder. Python 3.10+ is required for the CPU library;
no third-party installation or CUDA is needed for these commands:

```powershell
python --version
python -m unittest discover -s benchmark_tests -v
python eval_suite/test_benchmark_metrics.py
python -m uav_benchmark demo --out benchmark_results/demo_01
python -m uav_benchmark summarize --inputs benchmark_results/demo_01 --out benchmark_results/demo_summary_01.json --csv benchmark_results/demo_runs_01.csv
```

The library suite has 47 cases: 45 pass and 2 GPU tests are skipped in a CPU run.
The compatibility check prints 'All combined benchmark checks passed.'
The demo writes analytical synthetic trajectories and metric JSONs; it is not
a trained-policy result. Use a fresh output name for subsequent demos.

You can also run the nine existing/compatibility CPU script checks:

```powershell
$checks = @('test_geometry.py','test_metrics.py','test_flight_metrics.py','test_scenes.py','test_validation.py','test_scene_adaptor.py','test_trajectory_recorder.py','test_difficulty.py','test_benchmark_metrics.py')
foreach ($check in $checks) {
    python (Join-Path 'eval_suite' $check)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $check" }
}
```

## 2. What to use

- uav_benchmark/: main reusable library, CLI, ten metric interfaces, saved-flight
  evaluation, experiment orchestration, and statistical summaries.
- benchmark_docs/METRIC_SPEC.md: formulas, units, thresholds and missing values.
- benchmark_docs/EXTENDING.md: how teammates add metrics and experiments.
- benchmark_configs/: CPU smoke configuration and GPU experiment plans.
- eval_suite/: the team's original scripts plus benchmark_metrics.py and its check.
  This compatibility wrapper reports observed_gap_proxy; use the main library
  for designated passage geometry and the versioned benchmark definitions.
- simulator/DiffPhysDrone/: complete pinned upstream source, including CUDA kernels.
- scenes/: the team's easy, medium and hard seed-42 scenes.
- examples/synthetic_demo/: generated known-answer examples, clearly synthetic.
- PACKAGE_INFO.json and SOURCE_MANIFEST.json: source revisions and file hashes.

The main library does not equate arbitrary pairwise obstacle gaps to a flown
passage. Relative gap size is not_applicable unless a designated passage is
provided and verified. The controlled-gap demo includes such a passage.

## 3. Continue with Git and your teammates

This is a source ZIP; it has no Git history or initialized Git submodule.
CPU commands above work directly after extraction. For contributions and GPU
provenance checks, create a real Git checkout with the supplied script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Restore-GitCheckout.ps1
```

It clones the pinned team revision to a new sibling folder ending in '-git',
initializes the actual simulator submodule, creates codex/ten-metric-benchmark,
and copies only the added project files. It refuses an existing destination.
It does not commit or push. Open the new folder, run the CPU checks, then:

```powershell
git status
# Review the new files before staging them.
git add --pathspec-from-file=ADDED_FILES.txt
git diff --cached --check
git commit -m "Add reusable UAV benchmark library and numerical checks"
git push -u origin codex/ten-metric-benchmark
```

Pushing requires collaborator access to the team repository. If you contribute
through a fork, configure your fork as the push remote first.

## 4. Real GPU flights

Follow benchmark_docs/GPU.md from the restored Git checkout and your teammate's
working CUDA environment. GPU execution was not validated in this delivery.
No trained weights, CUDA runtime, Python packages, or local Drive-only training
changes are included. Your friend's trained checkpoint must be supplied separately.

The new full training checkpoints can include optimizer/RNG state. The runner
expects weights that load with weights_only=True. In your friend's trusted
training environment, export checkpoint['model'] with torch.save to a separate
plain policy state_dict file; retain the original checkpoint and its iteration,
config and hashes as provenance. The existing CPU loader in eval_suite accepts
full trusted training checkpoints, but a CPU forward pass does not run a flight.

Resolve the z=0 versus z=-1 ground convention and identify the actual checkpoint
used for the 8,000-iteration result before claiming a reproduced experiment.
The pinned upstream renderer and default benchmark configuration use ground z=-1.

First reproduce one easy-scene run with trajectory, metrics, scene, config,
checkpoint hash and seed saved together. Then expand to multiple scenes/seeds.
