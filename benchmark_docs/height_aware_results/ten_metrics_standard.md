## Ten-metric statistics

Rates: Wilson 95% CI. Means: 95% CI from a scene-cluster bootstrap (2000 resamples).

### released_base_fov82 (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.494 | [0.422, 0.567] | - | - |
| collision | rate | lower | 0.017 | [0.006, 0.048] | - | - |
| min_obstacle_clearance_m | m | higher | 0.390 | [0.338, 0.446] | 0.311 | 0.337 |
| path_excess_factor | 1 | lower | 0.044 | [0.025, 0.061] | 0.129 | 0.063 |
| average_speed_mps | m/s | - | 2.691 | [2.625, 2.748] | 0.726 | 2.273 |
| relative_end_distance | 1 | lower | 0.063 | [0.048, 0.082] | 0.123 | 0.044 |
| speed_rmse_mps | m/s | lower | 1.048 | [1.008, 1.093] | 0.460 | 1.182 |
| jerk_rms_mps3 | m/s^3 | lower | 7.724 | [6.966, 8.717] | 5.198 | 6.967 |

### ft_fix_fov82 (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.500 | [0.428, 0.572] | - | - |
| collision | rate | lower | 0.017 | [0.006, 0.048] | - | - |
| min_obstacle_clearance_m | m | higher | 0.419 | [0.375, 0.470] | 0.259 | 0.404 |
| path_excess_factor | 1 | lower | 0.030 | [0.012, 0.044] | 0.106 | 0.046 |
| average_speed_mps | m/s | - | 2.609 | [2.527, 2.677] | 0.763 | 2.232 |
| relative_end_distance | 1 | lower | 0.062 | [0.048, 0.078] | 0.105 | 0.034 |
| speed_rmse_mps | m/s | lower | 1.073 | [1.021, 1.135] | 0.512 | 1.251 |
| jerk_rms_mps3 | m/s^3 | lower | 5.255 | [5.004, 5.511] | 1.837 | 5.136 |

### ft_height_fov82 (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.517 | [0.444, 0.589] | - | - |
| collision | rate | lower | 0.017 | [0.006, 0.048] | - | - |
| min_obstacle_clearance_m | m | higher | 0.429 | [0.383, 0.480] | 0.271 | 0.405 |
| path_excess_factor | 1 | lower | 0.029 | [0.006, 0.046] | 0.122 | 0.050 |
| average_speed_mps | m/s | - | 2.615 | [2.523, 2.695] | 0.770 | 2.225 |
| relative_end_distance | 1 | lower | 0.063 | [0.046, 0.086] | 0.121 | 0.025 |
| speed_rmse_mps | m/s | lower | 1.098 | [1.044, 1.163] | 0.526 | 1.225 |
| jerk_rms_mps3 | m/s^3 | lower | 5.568 | [5.350, 5.827] | 1.700 | 5.407 |

### ft_hloss2_fov82 (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.556 | [0.483, 0.626] | - | - |
| collision | rate | lower | 0.022 | [0.009, 0.056] | - | - |
| min_obstacle_clearance_m | m | higher | 0.405 | [0.366, 0.444] | 0.200 | 0.387 |
| path_excess_factor | 1 | lower | 0.036 | [0.020, 0.049] | 0.106 | 0.050 |
| average_speed_mps | m/s | - | 2.637 | [2.568, 2.699] | 0.742 | 2.204 |
| relative_end_distance | 1 | lower | 0.057 | [0.044, 0.073] | 0.103 | 0.024 |
| speed_rmse_mps | m/s | lower | 1.059 | [1.016, 1.106] | 0.478 | 1.211 |
| jerk_rms_mps3 | m/s^3 | lower | 5.757 | [5.543, 5.981] | 1.647 | 5.606 |

### ft_hloss5_fov82 (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.522 | [0.450, 0.594] | - | - |
| collision | rate | lower | 0.028 | [0.012, 0.063] | - | - |
| min_obstacle_clearance_m | m | higher | 0.369 | [0.331, 0.408] | 0.190 | 0.351 |
| path_excess_factor | 1 | lower | 0.034 | [0.017, 0.047] | 0.098 | 0.052 |
| average_speed_mps | m/s | - | 2.623 | [2.539, 2.700] | 0.734 | 2.233 |
| relative_end_distance | 1 | lower | 0.055 | [0.043, 0.069] | 0.090 | 0.025 |
| speed_rmse_mps | m/s | lower | 1.065 | [1.011, 1.128] | 0.515 | 1.204 |
| jerk_rms_mps3 | m/s^3 | lower | 5.843 | [5.634, 6.087] | 1.643 | 5.777 |

### Scene metrics (properties of the test scenes, same for every checkpoint)

| Difficulty | Scenes | traversability (mean) | relative_gap_size (mean) |
|---|---|---|---|
| easy | 30 | 14.514 | n/a |
| hard | 30 | 8.136 | n/a |
| medium | 30 | 10.762 | n/a |

### Paired: A = ft_height_fov82 vs B = ft_hloss2_fov82 (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.517 | 0.556 | 180 | McNemar (A only 8, B only 15) | 0.2100 | 0.6301 |
| collision | lower | 0.017 | 0.022 | 180 | McNemar (A only 2, B only 3) | 1.0000 | 1.0000 |
| min_obstacle_clearance_m | higher | 0.429 | 0.405 | 180 | Wilcoxon signed-rank | 0.1435 | 0.5741 |
| path_excess_factor | lower | 0.029 | 0.036 | 180 | Wilcoxon signed-rank | 0.0009 | 0.0063 * |
| average_speed_mps | - | 2.615 | 2.637 | 180 | Wilcoxon signed-rank | 0.1025 | 0.5126 |
| relative_end_distance | lower | 0.063 | 0.057 | 180 | Wilcoxon signed-rank | 0.9249 | 1.0000 |
| speed_rmse_mps | lower | 1.098 | 1.059 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0003 * |
| jerk_rms_mps3 | lower | 5.568 | 5.757 | 180 | Wilcoxon signed-rank | 0.0033 | 0.0199 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

### Paired: A = ft_height_fov82 vs B = ft_hloss5_fov82 (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.517 | 0.522 | 180 | McNemar (A only 16, B only 17) | 1.0000 | 1.0000 |
| collision | lower | 0.017 | 0.028 | 180 | McNemar (A only 2, B only 4) | 0.6875 | 1.0000 |
| min_obstacle_clearance_m | higher | 0.429 | 0.369 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0001 * |
| path_excess_factor | lower | 0.029 | 0.034 | 180 | Wilcoxon signed-rank | 0.5353 | 1.0000 |
| average_speed_mps | - | 2.615 | 2.623 | 180 | Wilcoxon signed-rank | 0.6997 | 1.0000 |
| relative_end_distance | lower | 0.063 | 0.055 | 180 | Wilcoxon signed-rank | 0.9294 | 1.0000 |
| speed_rmse_mps | lower | 1.098 | 1.065 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| jerk_rms_mps3 | lower | 5.568 | 5.843 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

### Paired: A = released_base_fov82 vs B = ft_hloss2_fov82 (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.494 | 0.556 | 180 | McNemar (A only 9, B only 20) | 0.0614 | 0.1843 |
| collision | lower | 0.017 | 0.022 | 180 | McNemar (A only 3, B only 4) | 1.0000 | 1.0000 |
| min_obstacle_clearance_m | higher | 0.390 | 0.405 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0001 * |
| path_excess_factor | lower | 0.044 | 0.036 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| average_speed_mps | - | 2.691 | 2.637 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| relative_end_distance | lower | 0.063 | 0.057 | 180 | Wilcoxon signed-rank | 0.0012 | 0.0047 * |
| speed_rmse_mps | lower | 1.048 | 1.059 | 180 | Wilcoxon signed-rank | 0.0746 | 0.1843 |
| jerk_rms_mps3 | lower | 7.724 | 5.757 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

