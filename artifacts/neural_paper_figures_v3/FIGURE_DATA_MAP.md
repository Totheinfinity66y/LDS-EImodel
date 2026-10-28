# Figure data map

Model commit: `971704664740ecad33ea2a8d3ae30fb8ab964ee1`. Full source/array inventory: [data_inventory.json](manifests/data_inventory.json).
Formal raw source: `handcrafted_ei/artifacts/v2/run`; standardized recording: `artifacts/neural_representation_v2/data/<encoding>/recording.npz`; metrics: `artifacts/neural_representation_v2/metrics/<encoding>`. All neural rates are dimensionless. Each output is PNG300dpi/SVG/PDF.

One_hot supplies main figures; ring/topology and other branch/assay panels are supplementary. Figure1/2/3/6/7/10 reuse SHA-verified completed computations and exports; v3 recomputes4/5 and supplements8/9. No baseline is rerun.

## Figure 1

Outputs: [fig01_one_hot](figures/main/fig01_one_hot.png), [fig01_ring](figures/supplementary/fig01_ring.png), [fig01_topology](figures/supplementary/fig01_topology.png)

**Panel A–D — Representative neurons, E/I time courses and grouped population activity.**
- Input: `fig01_population_activity.npz` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figures_early.fig01`; conditions/windows: archived full rates; sample/delay/readout events.
- Reference: Kobak / Churchland population time courses. New simulation: no; recorded/computed data reused or algebraically reprojected.

Detailed original panel caption (scientific definitions retained):
A: single-condition R1–R4 maxima; B: memory/gate/feedback actual peak rates; C: fixed R1 position-0 unit across six L, D=+1 S=1; D: all-condition E/I active fractions (>0.1) and total rates. Vertical markers come from recorded events; dotted readout, green transfer, dashed retire. All rates dimensionless.

## Figure 2

Outputs: [fig02_one_hot](figures/main/fig02_one_hot.png), [fig02_ring](figures/supplementary/fig02_ring.png), [fig02_topology](figures/supplementary/fig02_topology.png)

**Panel A–D — Branch routes, selected vs competitor activity and margins.**
- Input: `fig02_branch_dynamics.npz` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figures_early.fig02`; conditions/windows: all 24 conditions; R1 competitor is NA.
- Reference: Mante Fig2/5 descriptive condition trajectories. New simulation: no; recorded/computed data reused or algebraically reprojected.

Detailed original panel caption (scientific definitions retained):
A: handcrafted branch support, not emergent dimensionality. B: actual branch peak rates for trial 0, correct solid vs competitor dashed; stage offsets labelled. C: four R3 branch small multiples; six actual positional units tuned across six initial L conditions at the readout window, with D/S fixed to the branch rule. No averaging across L. D: paired selected/max-unselected peak rates in each decision window; 24 deterministic task conditions are not repetitions. R1 has no competitor; competitor activity, leakage and margin are undefined (NPZ NaN / CSV NA), and no competitor dot is drawn.

## Figure 3

Outputs: [fig03_one_hot](figures/main/fig03_one_hot.png), [fig03_ring](figures/supplementary/fig03_ring.png), [fig03_topology](figures/supplementary/fig03_topology.png)

**Panel A–E — Memory/Response handoff, fixed rule axes, feedback cut and matched controls.**
- Input: `fig03_handoff_axes.npz; fig03_temporal_ablation.csv; archived lesion traces` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figures_early.fig03`; conditions/windows: D handoff R2, S handoff R3; axes fixed at recorded anchors.
- Reference: Inagaki Fig5 adapted persistence/control contrast. New simulation: no; recorded/computed data reused or algebraically reprojected.

Detailed original panel caption (scientific definitions retained):
A/B: actual (not amplitude-renormalized) condition-mean peak rates in 360 ms windows after recorded transfer. C: fixed normalized rule contrast axes fitted to balanced condition means at delay end (memory) or readout (Response); projection axes and centers saved. D: feedback removed versus baseline and three matched random controls. E: existing disjoint-task-condition nearest-centroid cross-validation, fractional tie credit. Chance 0.5; activity decay does not establish information erasure. Companion temporal-ablation CSV reuses pre/post handoff edge cuts and all matched random seed controls. No noise-repeat and condition-held-out results are pooled.

## Figure 4

Outputs: [fig04_one_hot_decompression_trajectories](figures/main/fig04_one_hot_decompression_trajectories.png), [fig04_one_hot_global3d](figures/supplementary/fig04_one_hot_global3d.png), [fig04_one_hot_transition_speed_zooms](figures/supplementary/fig04_one_hot_transition_speed_zooms.png), [fig04_ring_decompression_trajectories](figures/supplementary/fig04_ring_decompression_trajectories.png), [fig04_ring_global3d](figures/supplementary/fig04_ring_global3d.png), [fig04_ring_transition_speed_zooms](figures/supplementary/fig04_ring_transition_speed_zooms.png), [fig04_topology_decompression_trajectories](figures/supplementary/fig04_topology_decompression_trajectories.png), [fig04_topology_global3d](figures/supplementary/fig04_topology_global3d.png), [fig04_topology_transition_speed_zooms](figures/supplementary/fig04_topology_transition_speed_zooms.png)

**Panel A — 24 full trajectories in one global PCA.**
- Input: `fig04_trajectories.npz: global_scores/global_mean/global_components` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig4`; conditions/windows: all 24; stride4 fit inherited and verified.
- Reference: Mante Fig2/5 shared neural-state projection. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel B — Fixed-L branch discrimination.**
- Input: `fig04_trajectories.npz: branch_scores/branch_basis/R2_D_centroids/R3_branch_centroids` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figure_v3_geometry.build`; conditions/windows: L=0; balanced S at R2; four D/S at R3 decision window.
- Reference: Mante-inspired descriptive contrast, not dPCA. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel C — Three transition windows on the same branch axes.**
- Input: `fig04_trajectories.npz: branch_scores/times_ms` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig4`; conditions/windows: to_R2/3/4 through respective readout; fixed limits.
- Reference: Mante shared coordinates. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel D — Full-state velocity and centroid separation.**
- Input: `fig04_trajectories.npz: speed/speed_times_ms/R3_centroid_distances` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figure_v3_geometry.build`; conditions/windows: finite differences divided by actual 5ms; all132 neurons.
- Reference: method adapted. New simulation: no; recorded/computed data reused or algebraically reprojected.

## Figure 5

Outputs: [fig05_one_hot_branch_subspaces](figures/main/fig05_one_hot_branch_subspaces.png), [fig05_one_hot_structural_controls](figures/supplementary/fig05_one_hot_structural_controls.png), [fig05_ring_branch_subspaces](figures/supplementary/fig05_ring_branch_subspaces.png), [fig05_ring_structural_controls](figures/supplementary/fig05_ring_structural_controls.png), [fig05_topology_branch_subspaces](figures/supplementary/fig05_topology_branch_subspaces.png), [fig05_topology_structural_controls](figures/supplementary/fig05_topology_structural_controls.png)

**Panel A — Four branch trajectories and six endpoints in shared global axes.**
- Input: `fig04_trajectories.npz: global_scores` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig5`; conditions/windows: R3 formation to readout3; overlap disclosed.
- Reference: Gallego Fig1/3 shared projection. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel B — Six complete dimensional angle spectra.**
- Input: `fig05_principal_angle_spectra.csv: angles_degrees` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figure_v3_geometry.build`; conditions/windows: R3; exact archived semicolon angle lists.
- Reference: Gallego Fig3b. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel C — Bidirectional variance capture.**
- Input: `fig05_principal_angle_spectra.csv: cross_vaf_a_to_b/cross_vaf_b_to_a` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig5`; conditions/windows: full retained centered rank; target variance fraction.
- Reference: Gallego Fig3c ADAPTED; original across/within ratio differs. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel D — Time-resolved full/Response/support-folded geometry.**
- Input: `fig05_time_resolved_geometry.npz: *_angles_degrees/*_centroid_distance/*_ranks/*_singular_values` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figure_v3_geometry.temporal_geometry`; conditions/windows: each recorded time; six L samples per branch; centered rank<=5; abs/rel tol1e-8.
- Reference: Gallego geometry; fixed supports are structural. New simulation: no; recorded/computed data reused or algebraically reprojected.

## Figure 6

Outputs: [fig06_one_hot](figures/main/fig06_one_hot.png), [fig06_ring](figures/supplementary/fig06_ring.png), [fig06_topology](figures/supplementary/fig06_topology.png)

**Panel A–D — Six actual discrete states, whole/Response RDM and persistence margin.**
- Input: `fig06_position_stability.npz` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figures_geometry.fig6`; conditions/windows: D=+1,S=1; six L; R3 decision window and stage.
- Reference: Kriegeskorte RDM; discrete points without ring. New simulation: no; recorded/computed data reused or algebraically reprojected.

Detailed original panel caption (scientific definitions retained):
D=+1/S=1 is held fixed; the six initial locations yield six represented R3 positions. A fits PCA to six actual 132-D decision-window states and saves the mean and basis; no regular polygon or connecting loop is imposed. B/C use exact Euclidean distances in full and Response-only coordinates, with matched color limits. D shows selected-position rates (solid), maximum competitor (dotted), and selection margins during the R3 interval. The archive also contains argmax identity and full-state drift relative to readout3. This finite time interval tests maintained task states; it does not establish an autonomous attractor or a continuous ring manifold.

## Figure 7

Outputs: [fig07_one_hot](figures/main/fig07_one_hot.png), [fig07_ring](figures/supplementary/fig07_ring.png), [fig07_topology](figures/supplementary/fig07_topology.png)

**Panel A–D — Condition-held-out readout, cross-temporal decoding, handoff and held-noise-seed probes.**
- Input: `fig07_branch_decoding.npz; decoding.npz; decoding_noise_seed.npz` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figures_geometry.fig7`; conditions/windows: disjoint LDS folds vs separate noise seeds7/11/19.
- Reference: King & Dehaene time-generalization METHOD ADAPTED. New simulation: no; recorded/computed data reused or algebraically reprojected.

Detailed original panel caption (scientific definitions retained):
A–C reuse nearest-centroid probes with stratified disjoint LDS-condition folds, fractional tie credit, and archived split identities. A plots whole, memory, and Response populations; B shows D/S cross-temporal accuracy; C zooms on memory-to-Response availability. The extra branch probe predicts four D/S branch labels from Response with disjoint condition folds, masked before R3 transfer. D separately reports each held-out noise seed (7/11/19) with all task tuples present in training; these are noise realizations, not independent networks or biological repeats. Chance is 1/6 (L), 1/2 (D/S), 1/4 (branch). Low rates may remain decodable; activity decay is not information erasure. No decoder feeds back to the network.

## Figure 8

Outputs: [fig08_one_hot_six_point_attractors_branch0](figures/main/fig08_one_hot_six_point_attractors_branch0.png), [fig08_one_hot_multiple_slices](figures/supplementary/fig08_one_hot_multiple_slices.png), [fig08_one_hot_six_endpoints_3d](figures/supplementary/fig08_one_hot_six_endpoints_3d.png), [fig08_one_hot_six_point_attractors_branch1](figures/supplementary/fig08_one_hot_six_point_attractors_branch1.png), [fig08_one_hot_six_point_attractors_branch2](figures/supplementary/fig08_one_hot_six_point_attractors_branch2.png), [fig08_one_hot_six_point_attractors_branch3](figures/supplementary/fig08_one_hot_six_point_attractors_branch3.png), [fig08_ring_multiple_slices](figures/supplementary/fig08_ring_multiple_slices.png), [fig08_ring_six_endpoints_3d](figures/supplementary/fig08_ring_six_endpoints_3d.png), [fig08_ring_six_point_attractors_branch0](figures/supplementary/fig08_ring_six_point_attractors_branch0.png), [fig08_ring_six_point_attractors_branch1](figures/supplementary/fig08_ring_six_point_attractors_branch1.png), [fig08_ring_six_point_attractors_branch2](figures/supplementary/fig08_ring_six_point_attractors_branch2.png), [fig08_ring_six_point_attractors_branch3](figures/supplementary/fig08_ring_six_point_attractors_branch3.png), [fig08_topology_multiple_slices](figures/supplementary/fig08_topology_multiple_slices.png), [fig08_topology_six_endpoints_3d](figures/supplementary/fig08_topology_six_endpoints_3d.png), [fig08_topology_six_point_attractors_branch0](figures/supplementary/fig08_topology_six_point_attractors_branch0.png), [fig08_topology_six_point_attractors_branch1](figures/supplementary/fig08_topology_six_point_attractors_branch1.png), [fig08_topology_six_point_attractors_branch2](figures/supplementary/fig08_topology_six_point_attractors_branch2.png), [fig08_topology_six_point_attractors_branch3](figures/supplementary/fig08_topology_six_point_attractors_branch3.png)

**Panel A — Six endpoints within one R3 branch.**
- Input: `fig08_six_position_fixed_points_branch0.npz` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig8`; conditions/windows: D=+1,S=1; six L; other branches supplement.
- Reference: Sussillo & Barak Fig3; Inagaki Fig5 adapted. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel B — Actual state-kick relaxation paths, including failed recovery.**
- Input: `external lds_results/<encoding>/basin_full.npz: rates/initial_reference_index/amplitude` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig8`; conditions/windows: three seed directions; preclip amplitude0.1; start/end shown.
- Reference: Inagaki Fig5 perturbation semantics adapted. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel C — Mixed complete-state initial-condition sections.**
- Input: `fig08_basin_slices_v3.npz: initial_rates/endpoints/legal_mask/class_code` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3_dynamics.basin_slices`; conditions/windows: 4 branches×3 triples012/024/135×21x21; 2000ms; sample=clock0/tonic retained.
- Reference: Sussillo fixed-field analysis adapted. New simulation: yes, independent complete-state initializations.

**Panel D–E — Full residual, continuous/Euler spectra and kink certificate.**
- Input: `fig08_v3_fixed_point_certificates.csv` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `reference_dynamics.exact_local_stability/piecewise_cascade_certificate`; conditions/windows: 24 endpoints; residual<1e-7/ms; kink certificate required.
- Reference: Sussillo local stability. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel F — Actual-dose state-kick outcomes.**
- Input: `fig09_state_kick_classification.csv` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.kick_panel`; conditions/windows: full target; six branch positions×three directions; postclip RMS grouped by preclip dose.
- Reference: Inagaki recovery vs state identity; adapted. New simulation: no; recorded/computed data reused or algebraically reprojected.

## Figure 9

Outputs: [fig09_one_hot_perturbation_dynamics_source_time](figures/main/fig09_one_hot_perturbation_dynamics_source_time.png), [fig09_one_hot_perturbation_dynamics_R3_fixed_clock](figures/supplementary/fig09_one_hot_perturbation_dynamics_R3_fixed_clock.png), [fig09_ring_perturbation_dynamics_R3_fixed_clock](figures/supplementary/fig09_ring_perturbation_dynamics_R3_fixed_clock.png), [fig09_ring_perturbation_dynamics_source_time](figures/supplementary/fig09_ring_perturbation_dynamics_source_time.png), [fig09_topology_perturbation_dynamics_R3_fixed_clock](figures/supplementary/fig09_topology_perturbation_dynamics_R3_fixed_clock.png), [fig09_topology_perturbation_dynamics_source_time](figures/supplementary/fig09_topology_perturbation_dynamics_source_time.png)

**Panel A–D — Control/pulse rates, shared control-only PCA, full cross-temporal distance and projection error.**
- Input: `external lds_results/<encoding>/input_source_time_7.npz: control/perturbed/basis/pca_center/cross_temporal_distance/full_squared/projected_squared/orthogonal_squared` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.fig9`; conditions/windows: 50ms finite input pulse; seed7 representative; fixed-clock separate supplement.
- Reference: Zhou Fig7 METHOD ADAPTED; control-only PCA fit is LDS choice. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel E — Independent state-kick classifications.**
- Input: `fig09_state_kick_classification.csv` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3.kick_panel`; conditions/windows: never pooled with finite input recovery.
- Reference: Inagaki Fig5 adapted. New simulation: no; recorded/computed data reused or algebraically reprojected.

**Panel F — Four-stage finite input outcomes.**
- Input: `fig09_stage_perturbation_v3.npz; fig09_perturbation_classification.csv` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_v3_dynamics.stage_perturbations`; conditions/windows: 24×4×3 seeded directions; 50ms,RMS0.25; final R4 + intermediate R2/R3.
- Reference: Zhou perturbation method adapted to scheduled LDS. New simulation: yes, independent paired task-time pulse replay.

## Figure 10

Outputs: [fig10_encoding_comparison](figures/main/fig10_encoding_comparison.png)

**Panel A–F — Joint/fixed PCA, branch geometry and current-dose-matched encoding comparison.**
- Input: `derived/comparison/fig10_common_basis.npz; fig10_encoding_comparison.csv; fig10_raw_noise_doses.csv` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.
- Function: `paper_figures_comparison.run`; conditions/windows: all3 encodings; same neuron identities; raw coordinate noise separated.
- Reference: Gallego Fig3 adapted comparison. New simulation: no; recorded/computed data reused or algebraically reprojected.

Detailed original panel caption (scientific definitions retained):
Figure 10. Six external L inputs map to the same internal six-position population (A). All 24 conditions and all 132 neurons enter an equal-weight, stride-4 joint PCA (B); one-hot-only fit is a sensitivity comparison. Certified endpoints (C) retain source clip-kink certificates. D uses identical full132 external-current directions at RMS .05/.2/.5 for 50 ms, starting 100 ms after to_R3, seeds7/11/19 and 24 conditions per encoding. This is not raw-input-coordinate noise. Recovery requires final R4 branch/position identity and full-state Linf<.02 relative to the paired control. Dots summarize deterministic condition/direction samples, without biological confidence intervals. Rates are dimensionless. Sample/clock are reconstructed from verified events. Trajectories in coincident coordinates can overlap and are distinguished by line style. C separately shows six R3 branch-pair angles, four branch RDM distances and certified endpoints; different dots are branch comparisons, not biological repeats. Counts are not exhaustive attractor counts. No geometry superiority is asserted.

## Exact derived array keys
Every derived NPZ is indexed by file/key/shape in [derived_array_keys.json](manifests/derived_array_keys.json). Data are never implicitly reshaped into repeats. Per-panel output captions and source code define each plotted reduction; missing plotted inputs fail explicitly.
