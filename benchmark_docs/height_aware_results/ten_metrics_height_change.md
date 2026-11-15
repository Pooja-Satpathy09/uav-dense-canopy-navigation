## Ten-metric statistics

Rates: Wilson 95% CI. Means: 95% CI from a scene-cluster bootstrap (2000 resamples).

### released_base_height (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.272 | [0.212, 0.341] | - | - |
| collision | rate | lower | 0.044 | [0.023, 0.085] | - | - |
| min_obstacle_clearance_m | m | higher | 0.414 | [0.351, 0.486] | 0.366 | 0.351 |
| path_excess_factor | 1 | lower | 0.042 | [0.011, 0.066] | 0.167 | 0.070 |
| average_speed_mps | m/s | - | 2.648 | [2.573, 2.716] | 0.744 | 2.261 |
| relative_end_distance | 1 | lower | 0.085 | [0.062, 0.114] | 0.153 | 0.057 |
| speed_rmse_mps | m/s | lower | 1.071 | [1.024, 1.126] | 0.500 | 1.199 |
| jerk_rms_mps3 | m/s^3 | lower | 8.231 | [6.989, 9.887] | 7.970 | 6.876 |

### ft_fix_height (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.250 | [0.192, 0.318] | - | - |
| collision | rate | lower | 0.011 | [0.003, 0.040] | - | - |
| min_obstacle_clearance_m | m | higher | 0.427 | [0.384, 0.478] | 0.254 | 0.400 |
| path_excess_factor | 1 | lower | 0.045 | [0.021, 0.063] | 0.126 | 0.060 |
| average_speed_mps | m/s | - | 2.580 | [2.496, 2.649] | 0.763 | 2.215 |
| relative_end_distance | 1 | lower | 0.073 | [0.056, 0.096] | 0.119 | 0.054 |
| speed_rmse_mps | m/s | lower | 1.084 | [1.033, 1.147] | 0.524 | 1.242 |
| jerk_rms_mps3 | m/s^3 | lower | 5.234 | [4.983, 5.490] | 1.850 | 5.054 |

### ft_height_height (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.089 | [0.055, 0.140] | - | - |
| collision | rate | lower | 0.017 | [0.006, 0.048] | - | - |
| min_obstacle_clearance_m | m | higher | 0.418 | [0.379, 0.460] | 0.212 | 0.393 |
| path_excess_factor | 1 | lower | 0.066 | [0.047, 0.078] | 0.082 | 0.068 |
| average_speed_mps | m/s | - | 2.608 | [2.522, 2.681] | 0.754 | 2.193 |
| relative_end_distance | 1 | lower | 0.069 | [0.058, 0.087] | 0.080 | 0.055 |
| speed_rmse_mps | m/s | lower | 1.084 | [1.035, 1.146] | 0.512 | 1.215 |
| jerk_rms_mps3 | m/s^3 | lower | 5.448 | [5.258, 5.654] | 1.488 | 5.332 |

### ft_hloss2_height (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.294 | [0.233, 0.365] | - | - |
| collision | rate | lower | 0.022 | [0.009, 0.056] | - | - |
| min_obstacle_clearance_m | m | higher | 0.409 | [0.371, 0.449] | 0.206 | 0.383 |
| path_excess_factor | 1 | lower | 0.052 | [0.036, 0.065] | 0.110 | 0.064 |
| average_speed_mps | m/s | - | 2.616 | [2.543, 2.682] | 0.748 | 2.182 |
| relative_end_distance | 1 | lower | 0.067 | [0.054, 0.083] | 0.103 | 0.054 |
| speed_rmse_mps | m/s | lower | 1.067 | [1.021, 1.118] | 0.496 | 1.203 |
| jerk_rms_mps3 | m/s^3 | lower | 5.741 | [5.515, 5.975] | 1.690 | 5.594 |

### ft_hloss5_height (180 flights)

| Metric | Unit | Better | Estimate | 95% CI | SD | Median |
|---|---|---|---|---|---|---|
| goal_success | rate | higher | 0.294 | [0.233, 0.365] | - | - |
| collision | rate | lower | 0.039 | [0.019, 0.078] | - | - |
| min_obstacle_clearance_m | m | higher | 0.378 | [0.340, 0.417] | 0.195 | 0.361 |
| path_excess_factor | 1 | lower | 0.045 | [0.027, 0.061] | 0.094 | 0.060 |
| average_speed_mps | m/s | - | 2.588 | [2.494, 2.669] | 0.765 | 2.221 |
| relative_end_distance | 1 | lower | 0.065 | [0.053, 0.081] | 0.086 | 0.051 |
| speed_rmse_mps | m/s | lower | 1.082 | [1.022, 1.151] | 0.534 | 1.214 |
| jerk_rms_mps3 | m/s^3 | lower | 5.791 | [5.573, 6.028] | 1.675 | 5.586 |

### Scene metrics (properties of the test scenes, same for every checkpoint)

| Difficulty | Scenes | traversability (mean) | relative_gap_size (mean) |
|---|---|---|---|
| easy | 30 | 14.514 | n/a |
| hard | 30 | 8.136 | n/a |
| medium | 30 | 10.762 | n/a |

### Paired: A = ft_height_height vs B = ft_hloss2_height (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.089 | 0.294 | 180 | McNemar (A only 10, B only 47) | 0.0000 | 0.0000 * |
| collision | lower | 0.017 | 0.022 | 180 | McNemar (A only 2, B only 3) | 1.0000 | 1.0000 |
| min_obstacle_clearance_m | higher | 0.418 | 0.409 | 180 | Wilcoxon signed-rank | 0.3961 | 1.0000 |
| path_excess_factor | lower | 0.066 | 0.052 | 180 | Wilcoxon signed-rank | 0.0694 | 0.2777 |
| average_speed_mps | - | 2.608 | 2.616 | 180 | Wilcoxon signed-rank | 0.7577 | 1.0000 |
| relative_end_distance | lower | 0.069 | 0.067 | 180 | Wilcoxon signed-rank | 0.0114 | 0.0610 |
| speed_rmse_mps | lower | 1.084 | 1.067 | 180 | Wilcoxon signed-rank | 0.0102 | 0.0610 |
| jerk_rms_mps3 | lower | 5.448 | 5.741 | 180 | Wilcoxon signed-rank | 0.0001 | 0.0010 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

### Paired: A = ft_height_height vs B = ft_hloss5_height (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.089 | 0.294 | 180 | McNemar (A only 10, B only 47) | 0.0000 | 0.0000 * |
| collision | lower | 0.017 | 0.039 | 180 | McNemar (A only 1, B only 5) | 0.2188 | 0.4375 |
| min_obstacle_clearance_m | higher | 0.418 | 0.378 | 180 | Wilcoxon signed-rank | 0.0001 | 0.0004 * |
| path_excess_factor | lower | 0.066 | 0.045 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0001 * |
| average_speed_mps | - | 2.608 | 2.588 | 180 | Wilcoxon signed-rank | 0.7828 | 0.7828 |
| relative_end_distance | lower | 0.069 | 0.065 | 180 | Wilcoxon signed-rank | 0.0002 | 0.0007 * |
| speed_rmse_mps | lower | 1.084 | 1.082 | 180 | Wilcoxon signed-rank | 0.0006 | 0.0019 * |
| jerk_rms_mps3 | lower | 5.448 | 5.791 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

### Paired: A = ft_fix_height vs B = ft_hloss2_height (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.250 | 0.294 | 180 | McNemar (A only 36, B only 44) | 0.4340 | 1.0000 |
| collision | lower | 0.011 | 0.022 | 180 | McNemar (A only 2, B only 4) | 0.6875 | 1.0000 |
| min_obstacle_clearance_m | higher | 0.427 | 0.409 | 180 | Wilcoxon signed-rank | 0.3166 | 1.0000 |
| path_excess_factor | lower | 0.045 | 0.052 | 180 | Wilcoxon signed-rank | 0.2872 | 1.0000 |
| average_speed_mps | - | 2.580 | 2.616 | 180 | Wilcoxon signed-rank | 0.0046 | 0.0323 * |
| relative_end_distance | lower | 0.073 | 0.067 | 180 | Wilcoxon signed-rank | 0.4396 | 1.0000 |
| speed_rmse_mps | lower | 1.084 | 1.067 | 180 | Wilcoxon signed-rank | 0.6435 | 1.0000 |
| jerk_rms_mps3 | lower | 5.234 | 5.741 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

### Paired: A = released_base_height vs B = ft_hloss2_height (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.272 | 0.294 | 180 | McNemar (A only 5, B only 9) | 0.4240 | 0.7287 |
| collision | lower | 0.044 | 0.022 | 180 | McNemar (A only 5, B only 1) | 0.2188 | 0.6562 |
| min_obstacle_clearance_m | higher | 0.414 | 0.409 | 180 | Wilcoxon signed-rank | 0.0002 | 0.0010 * |
| path_excess_factor | lower | 0.042 | 0.052 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| average_speed_mps | - | 2.648 | 2.616 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| relative_end_distance | lower | 0.085 | 0.067 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| speed_rmse_mps | lower | 1.071 | 1.067 | 180 | Wilcoxon signed-rank | 0.3644 | 0.7287 |
| jerk_rms_mps3 | lower | 8.231 | 5.741 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

### Paired: A = ft_hloss2_height vs B = ft_hloss5_height (same scene and speed)

| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |
|---|---|---|---|---|---|---|---|
| goal_success | higher | 0.294 | 0.294 | 180 | McNemar (A only 6, B only 6) | 1.0000 | 1.0000 |
| collision | lower | 0.022 | 0.039 | 180 | McNemar (A only 2, B only 5) | 0.4531 | 1.0000 |
| min_obstacle_clearance_m | higher | 0.409 | 0.378 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0001 * |
| path_excess_factor | lower | 0.052 | 0.045 | 180 | Wilcoxon signed-rank | 0.0000 | 0.0000 * |
| average_speed_mps | - | 2.616 | 2.588 | 180 | Wilcoxon signed-rank | 0.8393 | 1.0000 |
| relative_end_distance | lower | 0.067 | 0.065 | 180 | Wilcoxon signed-rank | 0.0005 | 0.0031 * |
| speed_rmse_mps | lower | 1.067 | 1.082 | 180 | Wilcoxon signed-rank | 0.6976 | 1.0000 |
| jerk_rms_mps3 | lower | 5.741 | 5.791 | 180 | Wilcoxon signed-rank | 0.0816 | 0.4081 |

* = significant at 0.05 after Holm correction over the 8 flight metrics.

