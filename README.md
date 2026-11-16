# Dense-Canopy UAV Navigation


## 1. Project Overview

This project investigates vision-based UAV navigation in cluttered, GPS-denied or GPS-degraded environments, with dense-canopy scenes as the primary test environment. Such environments contain obstacles at varying positions and heights, making safe and reliable navigation challenging.

We use [DiffPhysDrone](https://github.com/HenryHuYu/DiffPhysDrone) as the upstream simulation and training framework. Rather than replacing its navigation controller, our work builds a reproducible evaluation pipeline around the released policy and investigates a limitation in its vertical goal-following behavior.

The project has two main contributions:

1. **Reproducible baseline evaluation:** We trained a DiffPhysDrone model, compared it with the authors’ released checkpoint, aligned the evaluation setup with training conditions, and added statistical analysis.
2. **Height-aware navigation:** We investigated low-altitude goal-following failures, identified issues in the training loss and target-height distribution, implemented height-aware training, and introduced a vertical-goal evaluation test.

> **Status note:** Baseline reproduction and benchmark analysis are completed and documented. Height-aware training and the vertical-goal benchmark are implemented; their comparative performance should be reported using the latest experiment results and artifacts.

## 2. Motivation

A UAV navigation policy can perform well in the conditions represented during training yet fail when the evaluation environment differs. A fair benchmark therefore needs to:

- Use reproducible scenes and experiment configurations.
- Align camera and simulation settings with the model’s training setup.
- Evaluate goal-reaching and collision safety together.
- Measure performance across scene difficulty and flight speeds.
- Report statistical uncertainty and paired comparisons.
- Examine failure cases, including navigation to goals at different altitudes.

The initial benchmark uses canopy-like scenes with easy, medium, and hard difficulty levels. The height-aware extension specifically tests whether the policy can follow goals above or below its starting altitude.

## 3. Research Contributions

### 3.1 Baseline reproduction and evaluation protocol

- Set up DiffPhysDrone on a laboratory GPU (**NVIDIA Quadro RTX 6000**) with **PyTorch 2.7** and **CUDA 12.8**.
- Fixed a CUDA simulator source incompatibility with the installed PyTorch version.
- Trained a team model for **50,000 iterations**, taking approximately **six hours**.
- Saved checkpoints at 10,000-iteration intervals.
- Obtained the authors’ official released model and verified that it matched their final training checkpoint.
- Evaluated checkpoints and the official model on the team benchmark.
- Identified and corrected five training/evaluation configuration mismatches: timeout, camera pitch, scene height, camera field of view (FOV), and success criterion.
- Added Wilson confidence intervals and exact McNemar paired tests, along with analysis scripts.

### 3.2 Height-aware training

- Investigated failures in which the policy approached goals while flying too low.
- Traced the behavior to a ground-penalty loss-term bug and training targets that remained at the starting altitude.
- Implemented a correction to the loss configuration and height-aware training with targets at varying altitudes.
- Added a vertical-goal test with the target **0.6 m above or below the start height**.

## 4. System Overview

The project uses DiffPhysDrone’s simulator and learned navigation policy, together with the team’s scene and evaluation pipeline.

The benchmark evaluates the policy’s behavior over fixed scenes and records flight outcomes and trajectory information. Height-aware training modifies the training data and loss behavior; it does not replace the simulator or the overall policy architecture.

## 5. Baseline Training and Checkpoints

The team trained DiffPhysDrone on the laboratory GPU for 50,000 iterations. Model checkpoints were saved every 10,000 iterations:

| Checkpoint | Training iterations |
|---|---:|
| Checkpoint 1 | 10,000 |
| Checkpoint 2 | 20,000 |
| Checkpoint 3 | 30,000 |
| Checkpoint 4 | 40,000 |
| Checkpoint 5 | 50,000 |

Checkpoint evaluation showed that performance did not improve further after 10,000 iterations under the corrected benchmark setup. This suggests that the additional training iterations did not provide measurable benefit for the reported safe-success metric.

The authors’ official checkpoint was used as a reference baseline. Since it was verified against the authors’ final training checkpoint, the comparison provides a reproducibility check for the team’s implementation and training procedure.

## 6. Benchmark and Evaluation Protocol

The team benchmark comprises **90 scenes** across three difficulty levels, evaluated at two flight speeds.

| Difficulty | Scenes | Speeds per scene | Flights |
|---|---:|---:|---:|
| Easy | 30 | 2 | 60 |
| Medium | 30 | 2 | 60 |
| Hard | 30 | 2 | 60 |
| **Total** | **90** | | **180** |

The complete evaluation consists of 180 flights per model.

Five evaluation settings were initially found to differ from the training configuration:

1. Timeout duration
2. Camera pitch
3. Scene height
4. Camera field of view (FOV)
5. Success criterion

These settings were corrected to align evaluation with training conditions. This protocol alignment is important for interpreting the results as a fair comparison rather than as a consequence of configuration differences.

## 7. Baseline Results

### 7.1 Effect of evaluation-protocol correction

| Measure | Initial evaluation | Corrected evaluation |
|---|---:|---:|
| Safe success rate | 0.87 | 0.96 |
| Collision count | 22 | 7 |

The safe success rate increased from **0.87 to 0.96** (reported **p = 0.001**). The collision count decreased from **22 to 7**, a reduction of 15 collisions (approximately 68.2%).

These changes reflect the corrected evaluation protocol. They should not be interpreted as a policy update alone improving the model.

### 7.2 Comparison with the authors’ model

| Model | Safe success rate |
|---|---:|
| Team-trained model | 0.96 |
| Authors’ official model | 0.98 |

The paired comparison reported **p = 0.51**, indicating no statistically significant difference at the conventional 0.05 threshold. This supports the conclusion that the team-trained model performs comparably to the authors’ released model on the benchmark; it does not establish formal statistical equivalence.

### 7.3 Statistical analysis

The evaluation analysis includes:

- **Wilson confidence intervals** for success-rate estimates.
- **Exact McNemar paired tests** for comparisons on matched benchmark cases.

The paired test is appropriate when two models are evaluated on the same cases with binary outcomes (for example, safe success or failure). It focuses on cases where the models disagree.

## 8. Height-Aware Training: Motivation and Method

### 8.1 Observed limitation

The baseline policy frequently missed goals by flying too low. Investigation of the training code identified two contributing issues:

- **Ground-penalty loss bug:** A ground penalty that was intended to be disabled remained active due to a loss-term configuration bug.
- **Fixed-height training targets:** Training targets were set at the same altitude as the starting point, limiting the training experience with vertical goal displacement.

Together, these issues could bias the learned behavior toward same-height, low-altitude navigation and reduce generalization to goals requiring ascent or descent.

### 8.2 Proposed modification

Height-aware training varies the goal altitude relative to the starting altitude. In general:

> **z<sub>goal</sub> = z<sub>start</sub> + Δz**

where **Δz** may be positive, negative, or zero.

- **Positive Δz:** the goal is above the starting altitude.
- **Negative Δz:** the goal is below the starting altitude.
- **Zero Δz:** the goal remains at the starting altitude.

The training loss configuration is also corrected so that the unintended ground-penalty behavior is no longer applied when disabled.

### 8.3 Vertical-goal evaluation

A new test places the goal at a vertical offset of **+0.6 m or −0.6 m** from the start:

> **z<sub>goal</sub> = z<sub>start</sub> ± 0.6 m**

This test evaluates the policy’s ability to reach targets that require climbing or descending. The effectiveness of the modification should be established by comparing the original and height-aware policies on the same scenes, conditions, and success criteria.

## 9. Evaluation Metrics

The project’s benchmark includes the following measurements. The precise implementation and reporting units should be taken from the benchmark code and experiment documentation.

| # | Metric | Purpose |
|---:|---|---|
| 1 | Goal success rate / safe success rate | Fraction of flights that reach the goal while satisfying safety criteria |
| 2 | Collision rate / collision count | Measures collision frequency |
| 3 | Path excess factor | Measures extra travel relative to the straight-line start-to-goal distance |
| 4 | Minimum obstacle clearance | Measures the nearest recorded signed clearance along the trajectory |
| 5 | Average traversal speed | Measures average speed during a flight |
| 6 | Relative end distance | Measures remaining goal distance relative to the initial goal distance |
| 7 | Speed tracking error | Measures deviation from commanded speed |
| 8 | Trajectory smoothness | Measures motion smoothness, such as jerk or a related quantity |
| 9 | Traversability | Characterizes geometry-derived difficulty of navigating a scene |
| 10 | Relative gap size | Relates passage width to the size of the UAV |

## 10. Repository Structure

The following is a high-level guide. Check the repository for the current exact paths and files.

```text
uav-dense-canopy-navigation/
├── README.md
├── simulator/
│   └── DiffPhysDrone/              # Upstream simulator and training code
├── eval_suite/                     # Team scene, geometry, and evaluation code
├── scenes/                         # Generated canopy scene definitions
├── results/                        # Benchmark outputs and visualizations
├── benchmark_docs/
│   ├── LAB_EVALUATION.md            # Baseline evaluation details
│   └── HEIGHT_AWARE_TRAINING.md     # Height-aware training investigation
└── docs/
    └── Final_Report_Team03.pdf      # Final project report
