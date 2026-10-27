# Independent scientific review: local fixed-point portraits

Reviewer: `/root/local_fp_reviewer`, independent from implementation and source expert. Final verdict: **PASS_WITH_LIMITS** for LDS-specific local stability analysis and source-style visual adaptation. This is not original-paper equation/code reproduction.

## Evidence actually examined

Read production equilibrium/classifier/renderer code, original `EINetwork.step`, full fixed-point and perturbation NPZ/CSV for all three encodings, source method contract, and actually opened all six final PNGs (three portraits and three diagnostic figures). Independent program `independent_check.py` imports only the original model, NumPy and SciPy; it does not call production equilibrium, field, Jacobian, batch integrator or classifier functions. Environment verified: analysis Python with NumPy 2.3.5, SciPy 1.16.3, Matplotlib 3.10.7, CPU. Execution log and machine-readable results accompany this report.

## Independently reproduced results

All three encoding modes have 132 states in these archived configurations. The selected response/decay pair is indices 20 and 97. All three roots are genuine full-state equilibria: direct original `model.step` gives maximum continuous-equivalent residuals 0, 1.32e-19 and 0 per ms. Their pair coordinates are (0,0), (.9,.76) and (1,1). These identify rest, a saddle, and held R3 activity respectively.

The off-diagonal union dependency graph is independently checked by strongly connected components. It has no multi-node cycles. Every clip-kink row has zero diagonal recurrence, so generalized derivative slopes cannot change the diagonal spectrum. At both sinks every generalized diagonal is negative; the largest is −.008333333333/ms. The saddle has exactly one positive diagonal +.025/ms. Thus the full-state local sink/saddle classification does not rely on a single arbitrary derivative at clipping folds. This argument applies locally; it does not prove a global basin or an exhaustive count of equilibria.

Independent closed-pair derivatives match all 10,201 grid points to 2.82e-18/ms. All excluded upstream derivatives are zero over this grid; readout outgoing columns are zero. This justifies a closed pair on the specified silent upstream background, while allowing downstream Y to evolve. It does not make an arbitrary constant-130-coordinate plane an invariant full-state manifold.

Original scalar `model.step` reproduces both archived full-state unstable trajectories to maximum error 3.99e-12, including amplified roundoff near the saddle. At 1600 ms the two branches are within 2.94e-5 of rest and 7.14e-6 of held R3 respectively; they approach the sinks, rather than arriving at exactly zero error in finite time. Independent dose/clipping reconstruction and original-step integration reproduce all 18 probes per encoding. Distance traces differ by at most 2.78e-17. Largest final perturbation distance is 2.09e-7. Requested RMS, actual clipped RMS, and clipping fractions are correctly separated.

## Visual review and revision

Initial visual review identified a legend covering the held-state annotation and missing explicit arrows on thick blue/red lines. These were reported to the main agent and corrected. All three final portraits now show filled blue full-state stable equilibria, an open saddle, red closed-pair stable-manifold arrows directed towards the saddle, and blue full-integration branch arrows towards their respective sinks. Main labels and physical rate bounds are legible. Diagnostics show full-state recovery and explicitly separate midpoint spectra from the kink certificate.

## Interpretation limits

- The two displayed sinks are low/high activity of one selected R3 coordinate, not two different locations or an enumeration of all 24 task states.
- The red line is the stable manifold of the closed two-dimensional pair. It is not the entire high-dimensional saddle stable set.
- Fixed external conditions are sample=clock=0 with original tonic drive. No learning or model-parameter changes are implicated.
- State perturbations are finite local probes, not transient input-current perturbations, statistical independent-network repetitions, or global basin measurements.
- Three encodings yield matching portraits here because the selected fixed response/decay mechanism is shared. This does not imply their complete population representations or task trajectories are identical.
- The original-paper visual semantics are adapted to actual LDS equations; the curves and rate axes are not copied from the original illustrative system.

No remaining blocking numerical or scientific-interpretation defect was found within this scope.
