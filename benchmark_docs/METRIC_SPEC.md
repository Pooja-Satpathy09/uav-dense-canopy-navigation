# Metric specification 1.0

This is the project's proposed versioned definition, to be reviewed by the team
before collecting final results. The package version is 0.1.0.

Let p_i, v_i, t_i be recorded positions, velocities, and times. Let g be the fixed
goal, r the spherical drone radius, T=t_last-t_first, L=sum(norm(p_i-p_(i-1))),
d0=norm(g-p_first), and df=norm(g-p_last). Times must increase. All numerical state
must be finite. Coordinates are metres; times are simulation seconds. Body rates
and action smoothness are not used to calculate physical trajectory jerk.

| Identifier | Formula or definition | Unit |
|---|---|---|
| goal_success | 1 for goal_reached termination, otherwise 0 | dimensionless |
| collision | 1 if any logged contact or computed obstacle/ground contact, otherwise 0 | dimensionless |
| path_excess_factor | L/d0 - 1 | dimensionless |
| min_obstacle_clearance_m | Minimum primitive signed distance minus r along recorded piecewise-linear path | m |
| average_speed_mps | L/T | m/s |
| relative_end_distance | df/d0 | dimensionless |
| speed_rmse_mps | sqrt(sum((norm(v_i)-v_command)^2 * (t_i-t_(i-1))) / T) | m/s |
| jerk_rms_mps3 | See midpoint derivative procedure below | m/s^3 |
| traversability | Mean free distance over fixed grid origins/headings divided by 2r | dimensionless |
| relative_gap_size | Minimum declared geometry-verified passage free_width_m divided by 2r | dimensionless |

## Outcomes and applicability

Contact has precedence over bounds violation, then goal arrival, then timeout.
Contact is separation <= collision_tolerance_m (default 1e-8 m). Ground is separate
from obstacles but participates in collision. Bounds apply to the spherical body.
Goal arrival is endpoint distance <= goal_radius_m, default 0.5 m. A goal flag far
from the actual supplied goal is rejected. Both raw terminal flags can be true at
one sample; collision wins. A flag before the last sample is invalid.

Reaching neither a terminal event nor the configured timeout is `incomplete`, not
a demonstrated timeout. Incomplete and numerical failures are excluded from rate
denominators and their counts are reported separately. Out-of-bounds is a valid
navigation failure. Live numerical failures are saved with invalid outcome values
and excluded from ordinary metrics summaries. Infrastructure exceptions get an
error record rather than an invented flight outcome.

The evaluator inspects the entire supplied recorded trajectory; it does not
interpolate and truncate an already recorded flight to first contact. The live
runner stops at the first timestep containing a detected terminal event.

Zero d0 makes normalized distance metrics undefined. Zero T makes average speed
and tracking RMSE undefined. Fewer than three velocity samples makes jerk
undefined. Empty obstacle sets have unbounded clearance, exported as JSON null
with status `unbounded`. No designated passage gives gap status `not_applicable`.
These statuses are not zeros and remain visible in CSV exports and summaries.

Path excess can be negative on an incomplete flight because it stopped early.
Report successful-flight path-excess statistics separately. Speed is travelled
distance/time and can be high while the drone makes poor goal progress.

## Derivative convention

For every consecutive velocity pair compute
a_i=(v_i-v_(i-1))/(t_i-t_(i-1)) at midpoint tau_i=(t_i+t_(i-1))/2.
Compute j_i=(a_i-a_(i-1))/(tau_i-tau_(i-1)). Report
sqrt(sum(norm(j_i)^2 * delta_tau_i)/sum(delta_tau_i)). This uses the available
derivative-support interval, with no fabricated endpoint derivatives or hidden
smoothing. Noise and sample rate affect jerk: keep them comparable. The constant
command-speed reference is explicit; it is not the upstream near-goal tapered
target vector. Add a separately versioned tracking metric if that reference is
required.

## Geometry and scene scope

The supported primitives are spheres, infinite vertical cylinders, and axis-aligned
boxes; the drone is spherical. Sphere/cylinder segment minima are analytic. Box
segment minima use 80 iterations of convex one-dimensional minimization. Contacts
are numerical, with the declared tolerance; this is not exact real-body collision
or a guarantee about curved motion between simulation steps. Test dt/2 on a subset.

Absent scene bounds default to x=[-1,21], y=[-7,7], z=[-1,8]. Absent ground defaults
to config.ground_z_m=-1. Normalized live scene snapshots save these conventions.
Changing bounds changes both the allowed flight domain and traversability.

Traversability samples a grid inside radius-inset XY bounds at scene.start.z.
Headings are uniformly spaced on a circle. Blocked origins contribute zero for
all headings. Sphere tracing advances no farther than signed obstacle clearance
or the declared maximum step until a surface/boundary is reached, within 1e-7 m.
It includes ground and reports blocked-origin counts. This fixed-altitude score
is not a full-3D dynamic traversability guarantee. It intentionally differs from
the old difficulty.py, which skips blocked origins and hard-codes other bounds.

For controlled passage experiments, scene.passages is a list such as:

```json
[{"id":"gap_x5","free_width_m":1.0,"geometry_verified":true}]
```

The author must verify each width against actual obstacle faces/aperture geometry
and record why that passage is part of the test. The library checks metadata but
does not prove it geometrically. The demo's gap is between box faces y=-0.5 and
y=0.5. With diameter 0.4 m, relative gap size is 2.5. Existing canopy scenes have
no passage metadata, so no equivalent gap value is claimed for them. Small gaps
elsewhere in a forest do not establish that every start-goal route is blocked.

## Literature traceability and adaptations

The repository README defines this ten-metric project set. AvoidBench distinguishes
environment difficulty from flight performance; its path excess uses a shortest
collision-free reference and its goal-speed measure differs from L/T. Its gap
measure is related to procedural obstacle spacing. Our straight-line path excess,
travel speed, and designated passage ratio are explicit project variants. Its
definitions also vary between published/manuscript versions, so cite an exact
version if claiming replication.

- Project metric list: https://github.com/Pooja-Satpathy09/uav-dense-canopy-navigation/blob/a09299e5525b8098d378d402e8ef3f20ca290e26/README.md
- AvoidBench: https://arxiv.org/abs/2301.07430
- Published AvoidBench PDF: https://pure.tudelft.nl/ws/portalfiles/portal/158955507/AvoidBench_A_high_fidelity_vision_based_obstacle_avoidance_benchmarking_suite_for_multi_rotors.pdf
- Gap-traversal paper: https://arxiv.org/html/2604.02779v1 (Section V's learned
  traversability predictor and Eq. 17's action regularization are different from
  this library's geometric traversability and physical jerk.)

No metric is presented here as electrical energy consumption or a guarantee of
real-world flight safety.

## Statistical reporting

Each eligible flight contributes success/collision indicators. Keep partial logs
and numerical/infrastructure failures visible rather than quietly dropping them.
Reports contain means, sample standard deviations, medians, fifth/ninety-fifth
percentiles, counts and missing-status counts. Success-only statistics accompany
efficiency/smoothness metrics. Wilson 95% intervals assume independent trials.
For repeated flights on the same scene, use the scene-cluster bootstrap mean
interval (2000 deterministic resamples), available with at least two scene clusters.
The bootstrap resamples complete scene clusters and retains within-scene repeats.
Scene scores are repeated on per-flight rows; do not interpret those repetitions
as new independent maps. Use balanced experimental matrices for aggregate means.

Summaries separate difficulty, source, checkpoint, noise, configuration, software,
camera setting and simulator identity. Compare checkpoints on paired scene sets;
the code provides descriptive summaries, not a paired significance-test claim.
