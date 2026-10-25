# Archived E/I activity analysis

The figures use checksum-verified `handcrafted_ei/artifacts/v1` rates. Its receipt records **PASS** for 39 experiments and 936 trials. Four archives used here (`baseline.zip` and the three recurrence scans) also passed SHA256 and ZIP CRC checks. All 24 baseline trials contain finite 663 × 104 rate arrays with matched timestamps, labels, and rates bounded to [0, 1].

## Figures

1. [Information flow and event timing](information-flow-timing.png) — archived phase events, four readout windows, and when D/S/branch information is carried forward.
2. [Disinhibitory gating](disinhibitory-gating.png) — recorded activity in baseline trial 00. `I_release` rises after the stage clock, suppresses the selected `I_gate` through I→I inhibition, and the selected E branch becomes active while the competing branch stays suppressed.
3. [All-neuron subspace](all-neuron-subspace.png) — common PCA basis from all 104 neuron coordinates, using 24 archived four-readout trajectories (96 population-state vectors).
4. [Delay fixed-point probe](delay-state-attractor-probe.png) — local Euler-map stability and zero-input/zero-clock perturbation return from 24 saved delay states.
5. [Local Jacobian](delay-state-jacobian.png) — full 104 × 104 continuous-time piecewise Jacobian at baseline condition 00, organized by population, plus its eigenvalue spectrum.
6. [Projected vector field](delay-state-vector-field.png) — zero-input dynamics projected onto the PC1–PC2 plane of 24 observed delay states, with the other 102 coordinates fixed at condition 00.
7. [Delay-state count map](delay-state-condition-map.png) — the R1 rate pattern for six L values and pairwise distances among all 24 full 104-neuron delay states, grouped by L and D/S.

## Population-state result

Each point is a 104-dimensional activity vector, one coordinate per recorded neuron. The common centered endpoint matrix has numerical rank 67 and participation ratio 6.98. Stage-local rank / participation ratio are R1: 7 / 5.55, R2: 12 / 3.70, R3: 23 / 3.59, R4: 23 / 3.59. These are sample summaries of the saved endpoint states, not a claim that the network was designed to have a particular PCA rank.

## Attractor evidence and limits

In the 1,400–1,750 ms delay window, the 24 mean saved states have maximum fixed-point residual 2.22e-16; the local discrete Euler Jacobian has spectral radius 0.875 for every condition. With per-coordinate perturbation SD 0.005, 100% of 96 probes returned within 0.1% of their initial deviation from the saved state after 1000 ms. At SD 0.05, 93.8% returned to the same saved state; the remaining probes did not return within the observation window.

The archived recurrence scan is consistent with recurrence-dependent holding: at `w_rec=0`, full-sequence accuracy is 0/24 and median late maximum activity is 8.4e-15 in R1 and both memory groups; at `w_rec=1.6`, `2.0`, and `2.2`, accuracy is 24/24, 24/24, and 24/24, with late active-group rates near 1.0.

This supports **locally stable fixed points for the delay states** in the zero-stimulus, zero-clock dynamics. The larger perturbations show that return is not guaranteed for the broader perturbation scale. These analyses do not establish global basins, a continuous attractor, or autonomous stage switching. They test archived v1 dynamics and do not imply learned or biological dynamics.

The new Jacobian is the derivative of the implemented clipped rate field in the active linear region at condition 00; units at either clip boundary are assigned zero slope, so the derivative is piecewise and boundary states have one-sided alternatives. Its continuous-time eigenvalues and Euler-map spectrum are stored in `analysis.json`. The vector-field arrows show the field component in a two-dimensional activity slice. This projection aids intuition but cannot establish full-space flow topology or attractor basins.

The delay-state count map makes the distinction visible: the same one-of-six R1 rate pattern repeats across the four D/S combinations for each L, while every full 104-neuron state differs from the others. These are 24 observed condition-specific delay states, not proof that the network has exactly 24 attractors.

## Reproduction

Run from the repository root with the project's verified `analysis` environment:

```powershell
$envRoot='C:\Users\Totheinfinity\.conda\envs\analysis'
$env:PATH="$envRoot\Library\bin;$envRoot\Scripts;$envRoot;$env:PATH"
& (Join-Path $envRoot 'python.exe') 'handcrafted_ei\artifacts\activity-analysis-2026-10-25\plot_activity.py'
```

`analysis.json` stores input archive checksums, source hashes, configuration, environment versions, Jacobian/eigenvalue and vector-field summaries, and the exact analysis scope.
