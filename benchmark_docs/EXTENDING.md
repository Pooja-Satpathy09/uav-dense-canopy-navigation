# Teammate extension guide

## Suggested ownership

| Person | Files and responsibility |
|---|---|
| You | types.py, validation.py, registry.py, flight_metrics/, METRIC_SPEC.md |
| Scene teammate | geometry.py, difficulty.py, scene_validation.py, controlled gap fixtures |
| GPU teammate | diffphys.py, real GPU validation, checkpoint/config provenance |
| Experiment teammate | experiment.py, aggregate.py, plans, plots and failure analysis |

Keep shared types and metric identifiers stable. One person changing a metric
definition should update its tests and versioned specification in the same PR.
Coordinate edits to shared schemas before writing multiple implementations.

## Add a metric without changing the simulator

Create a new evaluator module, register a unique identifier, and import that
module in flight_metrics/__init__.py. The evaluator receives the validated
context produced by metrics.flight_context(). Example optional altitude output:

```python
from ..registry import metric
from ..types import MetricResult

@metric('minimum_altitude_m', 'flight', 'm')
def minimum_altitude(context):
    return MetricResult(min(s.position[2] for s in context['samples']), 'm')
```

This would be an eleventh optional output. Keep the agreed ten in the core report.
If adding it to the default registry, update test_exactly_ten_core_metrics and
document the expanded default set intentionally, rather than silently changing
what 'the ten metrics' means. For scene metrics register scope='scene'.

Every new metric needs: definition/source, units, required inputs, deterministic
known-answer test, undefined-case test, clear status, and schema/version review.
If it needs acceleration or commands, extend Sample/I/O deliberately; do not
guess quantities from a missing field or add controller dependencies to geometry.

## Preserve the existing project

The current eval_suite modules stay available. The optional GPU adapter loads the
existing bridge and scene adapter without editing them or permanently changing
sys.path. It temporarily supplies their script-style sibling import during load.
Future migration of old modules to package-relative imports should be a separate
PR with existing-script compatibility tests.

Avoid committing generated bulk results or weights. The patch creates ignored
benchmark_results/, benchmark_scenes/ and checkpoints/ directories. Store final
datasets with manifests/checksums in the team's chosen artifact store. For a
report, archive exact scene snapshots, configuration, code commits, checkpoint
hashes, validation evidence, and raw result rows together.

## Suggested next PRs after this delivery

1. GPU validation evidence and any fixes exposed by the opt-in real tests.
2. Controlled passage generation with geometry-derived width metadata, plus
   sphere/box/vertical-cylinder edge-case fixtures and manual scene inspection.
3. Explicit feasible/stress-set manifests based on published scene-selection
   rules; keep impossible scenes labeled rather than silently dropping them.
4. Paired policy comparisons and plots with scene-level uncertainty.
5. New metric plugins or a shortest-free-path reference, with new names/versions
   rather than changing the straight-line path-excess meaning silently.

Do not train a new policy merely to finish this library. A compatible existing
checkpoint and validated simulator are enough to begin the benchmark pilot.
