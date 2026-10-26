# UAV navigation benchmark implementation

This is an additive implementation for Pooja-Satpathy09/uav-dense-canopy-navigation,
reviewed at a09299e5525b8098d378d402e8ef3f20ca290e26. It preserves existing
eval_suite files and the pinned upstream simulator. The new import is
`uav_benchmark`; it is separate so teammates can continue using existing scripts.

Start with benchmark_docs/START_HERE.md. It contains the exact Windows PowerShell
commands for applying the patch, testing, running examples, committing, pushing,
and updating teammates' checkouts. GPU setup and live-run commands are in
benchmark_docs/GPU.md.

## What works on a CPU

- Eight flight metrics and two scene metric interfaces.
- Analytical synthetic examples, existing trajectory CSV evaluation, offline
  batches, JSON/CSV exports, and statistical summaries.
- Geometry checks between recorded samples, typed CSV booleans, input validation,
  units, explicit missing-value statuses, and extensible metric registration.
- Adapters calling the team's existing scene generator and grid validator.

## GPU integration status

The optional DiffPhysDrone runner implements the pinned upstream observation,
state, action transforms and initial action buffer. It has NOT been executed on
CUDA or with a real checkpoint in the authoring environment. It must pass the
opt-in GPU tests and manual smoke checks before final policy experiments.
CPU/mock tests do not establish GPU compatibility or navigation performance.

## Important definitions

The ten metrics are this project's set, not an exact reproduction of one paper.
Relative gap size needs a designated, geometry-verified passage. On the existing
random canopy scenes it is `not_applicable`; it is never fabricated from arbitrary
obstacle pairs. The provided controlled-gap demo evaluates all ten.

Ground defaults to z=-1 to agree with the pinned upstream renderer. Override it
only for offline trajectories known to use another ground convention. Correct
scene/config metadata is required to interpret a trajectory.

## Quick CPU commands, from repository root

```powershell
python -m unittest discover -s benchmark_tests -v
python -m uav_benchmark demo --out benchmark_results/demo_01
python -m uav_benchmark summarize --inputs benchmark_results/demo_01 --out benchmark_results/demo_summary.json --csv benchmark_results/demo_runs.csv
```

Output paths are created exclusively to protect earlier results. Choose a new
output name if rerunning a command. CUDA experiments additionally support
`--resume`, which verifies configuration, source, checkpoint and scene identities.

See benchmark_docs/METRIC_SPEC.md for formulas and limitations, and
benchmark_docs/EXTENDING.md for teammate responsibilities and extension examples.
