# V3 numerical experiments

All dynamics use the existing full 132-dimensional Euler integrator, original model parameters and independent evaluation arrays. Archived baseline is only replayed for paired controls. Historical data is read-only.

## Protocol

- Basin: sample=0, clock=0, original tonic; 2,000 ms integration; 21×21 grid; four R3 branches and triples (0,1,2), (0,2,4), (1,3,5). Full-state endpoint affine differences; illegal rate-cube states masked without clipping. Integer barycentric numerators remove cancellation at simplex edges. 32 states per integration chunk; only endpoints and 48 representative complete paths retained per encoding.
- Classification: full-field max residual <1e-7 rate/ms precedes all R3-unit activity classification; active threshold 0.2 dimensionless. Classes retain single position, multiple position, outside branch, R3-inactive, and unconverged. R3-inactive does not mean every neural unit is silent: tonic inhibition persists. Cross-branch/multiple-position counts are retained.
- Finite inputs: 24 conditions × four stages × direction seeds 7/11/19; full132 seeded Gaussian current normalized to RMS 0.25, duration 50 ms, integrated RMS 12.5 rate-current·ms, identical controls/history/current schedules. Preselection pulses end at the corresponding gate onset. Postformation pulses start at readout2_start/readout3_start; timing is explicit in manifests. These are fixed random directions, not independent animals/networks.
- Source-time recovery: terminal shared readout and all-stage activity patterns; original unique branch/position plus max absolute state error <0.02 defines full-state recovery. Source-time convergence/residual is not applicable and never inferred from a different fixed field. Fixed-clock input and tonic-only state kicks are separately classified.
- Existing state kicks: reconstruct seeded preclip state, verify archived clipped initial state, record actual postclip target/whole RMS and clipping fraction; endpoints come directly from archived full-system integration.

## Verified results

Each encoding has 2,772 legal mixed initial states: 216 single-position endpoints and 2,556 R3-inactive endpoints. No sampled multi-position, outside-branch, or unconverged endpoint occurred. This does not establish an exhaustive attractor count or a global basin. No mixed stable attractor was found in these slices.

Each encoding has 288 paired stage-input trials: 196 full-state recoveries, 56 outside-branch outcomes, 33 R4-inactive outcomes and three preserved readouts/original locations without full-state recovery. Stage-specific counts follow below. All control replays agree with baseline within 1e-12; prehistory is bitwise identical.

The representative fixed-clock input assay preserves a full-state error plateau: seeds 7/11 lose R3 activity; seed 19 preserves the R3 position while full-state Euclidean error remains approximately 1.118 and PC1/2 error is approximately 1.22e-9. Projection alone would conceal this error. Source-time controls can recover under the normal clock; that is a different protocol.

- one_hot, post_R2_formed: {'full_state_recovered': 53, 'rest': 6, 'outside_branch': 13}
- one_hot, post_R3_formed: {'rest': 21, 'full_state_recovered': 48, 'readout_correct_state_not_recovered': 3}
- one_hot, pre_R2_selection: {'full_state_recovered': 42, 'outside_branch': 30}
- one_hot, pre_R3_selection: {'full_state_recovered': 53, 'rest': 6, 'outside_branch': 13}
- ring, post_R2_formed: {'full_state_recovered': 53, 'rest': 6, 'outside_branch': 13}
- ring, post_R3_formed: {'rest': 21, 'full_state_recovered': 48, 'readout_correct_state_not_recovered': 3}
- ring, pre_R2_selection: {'full_state_recovered': 42, 'outside_branch': 30}
- ring, pre_R3_selection: {'full_state_recovered': 53, 'rest': 6, 'outside_branch': 13}
- topology, post_R2_formed: {'full_state_recovered': 53, 'rest': 6, 'outside_branch': 13}
- topology, post_R3_formed: {'rest': 21, 'full_state_recovered': 48, 'readout_correct_state_not_recovered': 3}
- topology, pre_R2_selection: {'full_state_recovered': 42, 'outside_branch': 30}
- topology, pre_R3_selection: {'full_state_recovered': 53, 'rest': 6, 'outside_branch': 13}

## Validation and reproducibility

Seven dedicated numerical tests cover five-category competition, the multi-branch/same-position edge case, source-time convergence isolation, full Euler step and Jacobian finite differences, zero pulse and paired history, orthogonal projection energy closure, and actual pre/postclip archived kick dose. reports/numerics_red.txt records the two semantic regression failures before correction; reports/numerics_green.txt records the passing suite. No main-model changes occurred.

Use analysis Python 3.12.12 / NumPy 2.3.5 / SciPy 1.16.3. On Windows prepend analysis, analysis/Library/bin and analysis/Scripts to the process PATH; bare invocation can fail during NumPy BLAS DLL loading. OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 were used. No packages were installed.

Rebuild: python -m handcrafted_ei.evaluation.paper_v3_dynamics
Tests: python -m unittest handcrafted_ei.tests.test_paper_v3_numerics -v

Numerical receipts contain source and input SHA256, full original configuration, thresholds, time windows and environment. derived/numerical_summary.csv is recomputed from the output files. The 21×21 slices describe selected 2D initial-state sections of full-state dynamics; no global/exhaustive six-attractor claim is made.
