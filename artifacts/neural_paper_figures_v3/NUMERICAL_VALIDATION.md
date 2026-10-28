# Numerical validation

Status: PASS_WITH_LIMITS for LDS methods adaptation; source-exact paper reproduction is BLOCKED.

Base model commit: `971704664740ecad33ea2a8d3ae30fb8ab964ee1`. CPU environment: Python 3.12.12, NumPy 2.3.5; exact packages in [runtime preflight](reports/runtime_preflight.json). Process-local Conda Library/bin is required on this Windows host; no dependency installed.

91 regression tests passed; [full log](reports/tests_full.txt). New geometry and numerical tests cover common neural coordinates, principal-angle invariance, VAF matrix projection, rank<=5/NA, energy closure, classifier categories, real Euler/field/Jacobian conventions, zero pulse, paired history and preclip/postclip dose. Red/green development evidence is preserved under reports; missing-module red verifies new API absence, numerical classifier defect regression supplies behavior checks.

Independent full-array audit: [report](reports/INDEPENDENT_AUDIT.md), [machine record](manifests/independent_audit.json). Input hashes and exact shape/key inventory: [inventory](manifests/data_inventory.json).

## Thresholds and protocols

- Singular value threshold max(1e-8,largest×1e-8); six centered location samples imply rank≤5. Low variance angles are NA, not zero.
- Full fixed-field max residual <1e-7 rate/ms; clip-kink stability uses piecewise cascade certificate separately from representative Jacobian eigenvalues.
- Active position threshold 0.2; classify all six position units in every branch. Outside/multibranch takes precedence over within-branch multiple positions; counts retain simultaneous-activity flags.
- Full-state recovery additionally requires original unique branch/position and max-norm state error<0.02. Same final Y/readout alone does not establish recovery.
- Source-time final classification is R4, intermediate R2/R3 checked; residual/converged is NA under a changing clock. R3_fixed_clock retains archived fixed clock and uses R3 at its actual fixed field.
- Mixed initial states are full endpoint-affine states in the legal [0,1]^132 cube; invalid grids masked, never clipped. 21×21×3 slices×4 branches; 2000ms, dt5ms, batch32. No claim that this exhausts the six-position basin geometry.
- Four task-time pulse windows, 50ms, RMS0.25, seeds7/11/19, dose12.5 current-RMS ms. Conditions/directions are descriptive, not independent networks/animals.

## one_hot
- New mixed-state scan: {'legal': 2772, 'invalid': 2520, 'classes': {'single_position': 216, 'multiple_positions': 0, 'outside_branch': 0, 'rest': 2556, 'unconverged': 0}, 'max_residual': 4.1480625081171164e-10}.
- Paired stage outcomes (288): {'full_state_recovered': 196, 'outside_branch': 56, 'rest': 33, 'readout_correct_state_not_recovered': 3}.
- Maximum control replay error: 2.22e-16; certified reference endpoints: 24/24; max endpoint residual 4.28e-11/ms.
- Correct final R4 readouts: 228/288; complete sequences: 213/288. Two branch display axes capture 36.6688% of fixed-L R3 centroid variance; projection loses information.

## ring
- New mixed-state scan: {'legal': 2772, 'invalid': 2520, 'classes': {'single_position': 216, 'multiple_positions': 0, 'outside_branch': 0, 'rest': 2556, 'unconverged': 0}, 'max_residual': 4.1480625081171164e-10}.
- Paired stage outcomes (288): {'full_state_recovered': 196, 'outside_branch': 56, 'rest': 33, 'readout_correct_state_not_recovered': 3}.
- Maximum control replay error: 2.22e-16; certified reference endpoints: 24/24; max endpoint residual 4.28e-11/ms.
- Correct final R4 readouts: 228/288; complete sequences: 213/288. Two branch display axes capture 36.6688% of fixed-L R3 centroid variance; projection loses information.

## topology
- New mixed-state scan: {'legal': 2772, 'invalid': 2520, 'classes': {'single_position': 216, 'multiple_positions': 0, 'outside_branch': 0, 'rest': 2556, 'unconverged': 0}, 'max_residual': 4.1480625081171164e-10}.
- Paired stage outcomes (288): {'full_state_recovered': 196, 'outside_branch': 56, 'rest': 33, 'readout_correct_state_not_recovered': 3}.
- Maximum control replay error: 2.22e-16; certified reference endpoints: 24/24; max endpoint residual 4.28e-11/ms.
- Correct final R4 readouts: 228/288; complete sequences: 213/288. Two branch display axes capture 36.6688% of fixed-L R3 centroid variance; projection loses information.
