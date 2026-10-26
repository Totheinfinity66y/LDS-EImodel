"""Independent, fixed-input, whole-state dynamical experiments.

No task labels are used to set neural state or choose perturbation targets.
Archived snapshots provide actual states; only their observed activity selects
an active branch. The vectorized integrator is tested against EINetwork.step.
"""
from __future__ import annotations
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from handcrafted_ei.model.ei_network import EINetwork

AMPLITUDES = (.02, .1, .3, .7)
SEEDS = (7, 11, 19)
TARGETS = ('full', 'response', 'active_branch', 'unselected_branch', 'E', 'I')


def field(model, rates=None):
    r = model.rates if rates is None else np.asarray(rates)
    return (-r + np.clip(model.signed_weights @ r + model.tonic + model.stimulus + model.clock - model.theta, 0, 1)) / model.tau


def jacobian(model, rates=None):
    r = model.rates if rates is None else np.asarray(rates)
    drive = model.signed_weights @ r + model.tonic + model.stimulus + model.clock - model.theta
    slope = ((drive > 0) & (drive < 1)).astype(float)
    slope[np.isclose(drive, 0, atol=1e-10) | np.isclose(drive, 1, atol=1e-10)] = .5
    return (-np.eye(len(r)) + slope[:, None] * model.signed_weights) / model.tau[:, None]


def evolve_batch(model, initial, duration_ms=2000):
    """Euler integration on independent evaluation arrays; model is untouched."""
    state = np.asarray(initial, dtype=float).copy()
    if state.ndim != 2 or state.shape[1] != len(model.rates) or not np.all(np.isfinite(state)) or np.any((state < 0) | (state > 1)):
        raise ValueError('initial state must be [probe,neuron], finite and bounded')
    steps = duration_ms / model.config['dt_ms']
    if steps < 0 or not float(steps).is_integer():
        raise ValueError('duration must be a nonnegative multiple of dt')
    trajectory = np.empty((len(state), int(steps)+1, state.shape[1]))
    trajectory[:, 0] = state
    w = model.signed_weights
    external = model.tonic + model.stimulus + model.clock - model.theta
    dt_tau = model.config['dt_ms'] / model.tau
    for t in range(int(steps)):
        drive = state @ w.T + external
        state += dt_tau * (-state + np.clip(drive, 0, 1))
        trajectory[:, t+1] = state
    return trajectory


def state_identity(model, rates, stage, threshold=.2):
    values = np.asarray(rates)[model.groups[f'R{stage}']].reshape(-1, 6)
    if values.max() < threshold:
        return None
    return tuple(int(x) for x in np.unravel_index(values.argmax(), values.shape))


def recovery(model, final, reference, stage, tolerance=.02):
    identity = state_identity(model, reference, stage)
    return bool(identity is not None and state_identity(model, final, stage) == identity and np.max(abs(final-reference)) < tolerance)


def perturbation_targets(model, stage):
    branch = model.groups[f'R{stage}'].reshape(-1, 6)
    active = int(np.argmax(model.rates[branch].sum(axis=1)))
    return {'full': np.arange(len(model.rates)),
            'response': np.concatenate([model.groups[f'R{s}'] for s in range(1, 5)]),
            'active_branch': branch[active],
            'unselected_branch': branch[np.arange(len(branch)) != active].ravel(),
            'E': np.flatnonzero(model.signs == 1), 'I': np.flatnonzero(model.signs == -1)}


def stability(model):
    f = field(model); j = jacobian(model)
    eigenvalues = np.linalg.eigvals(j)
    discrete = 1 + model.config['dt_ms'] * eigenvalues
    return {'residual_l2_per_ms': float(np.linalg.norm(f)),
            'residual_max_per_ms': float(np.max(abs(f))),
            'euler_residual_l2': float(np.linalg.norm(f) * model.config['dt_ms']),
            'max_real_eigenvalue_per_ms': float(eigenvalues.real.max()),
            'euler_spectral_radius': float(np.max(abs(discrete))),
            'jacobian_kink_units': int(np.count_nonzero(np.isclose(model.signed_weights@model.rates+model.tonic+model.clock-model.theta, 0, atol=1e-10) | np.isclose(model.signed_weights@model.rates+model.tonic+model.clock-model.theta, 1, atol=1e-10)))}


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, columns); writer.writeheader(); writer.writerows(rows)


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(input_dir, output_dir):
    """Reuse audited v2 trajectories and extend independent perturbation probes.

    Output metrics use fixed 2 s horizons, seeds 7/11/19 and targeted RMS
    amplitudes .02/.1/.3/.7 before clipping. R1 has no unselected branch: its
    corresponding target is explicitly NA rather than a fabricated lesion.
    """
    source = Path(input_dir); root = Path(output_dir)
    data_dir = root/'data'/'dynamics'; data_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir = root/'metrics'; metrics_dir.mkdir(exist_ok=True)
    input_paths = sorted((source/'attractor_trajectories').glob('*.npz'))
    source_index=json.loads((source/'attractor_trajectories/index.json').read_text(encoding='utf-8'))
    if {p.name for p in input_paths}!=set(source_index):
        raise ValueError('source snapshot inventory differs from its archived index')
    for path in input_paths:
        if _hash(path)!=source_index[path.name]['sha256']:
            raise ValueError('source snapshot checksum mismatch: '+path.name)
    signature = {'analysis_sha256': _hash(Path(__file__)), 'inputs': {str(p): _hash(p) for p in input_paths}, 'config_sha256': _hash(source/'config.json'),
                 'model_source_hashes': {str(p): _hash(p) for p in sorted((Path(__file__).parents[1]/'model').glob('*.py'))}}
    summary_path = data_dir/'summary.json'
    if summary_path.exists():
        cached = json.loads(summary_path.read_text(encoding='utf-8'))
        outputs=cached.get('output_sha256',{})
        if cached.get('signature') == signature and outputs and all((root/name).exists() and _hash(root/name)==expected for name,expected in outputs.items()):
            return cached
    config = json.loads((source/'config.json').read_text(encoding='utf-8'))
    snapshots = {}
    for path in input_paths:
        key = path.stem
        with np.load(path, allow_pickle=False) as archive:
            snapshots[key] = {name[len(key)+1:]: archive[name] for name in archive.files}
    fixed_rows = []; perturb_rows = []; endpoint_rows = []
    for key, archive in snapshots.items():
        mode = key.split('_L')[0]; stage = int(key.rsplit('_R', 1)[1])
        cfg = dict(config); cfg['location_encoding'] = mode
        model = EINetwork(overrides=cfg)
        model.rates = archive['initial_rates'].copy(); model.clock = archive['initial_clock'].copy(); model.remove_stimulus()
        times = np.arange(len(archive['autonomous'])) * model.config['dt_ms']
        output = {'times_ms': times, 'initial_rates': model.rates.copy(), 'initial_clock': model.clock.copy(),
                  'control_forced': archive['forced'], 'control_tonic_only': archive['autonomous'],
                  'control_autonomous': archive['autonomous'], 'neuron_labels': np.asarray(model.labels), 'neuron_signs': model.signs}
        for condition, array in [('forced', archive['forced']), ('tonic_only', archive['autonomous']), ('autonomous', archive['autonomous'])]:
            probe = deepcopy(model); probe.rates = array[-1].copy()
            if condition != 'forced': probe.clock[:] = 0
            metrics = stability(probe)
            eig = np.linalg.eigvals(jacobian(probe))
            output[f'{condition}_jacobian_eigenvalues_real_per_ms'] = eig.real
            output[f'{condition}_jacobian_eigenvalues_imag_per_ms'] = eig.imag
            output[f'{condition}_euler_eigenvalues_real'] = (1+model.config['dt_ms']*eig).real
            output[f'{condition}_euler_eigenvalues_imag'] = (1+model.config['dt_ms']*eig).imag
            identity = state_identity(probe, probe.rates, stage)
            persistent = identity is not None and identity == state_identity(model, model.rates, stage)
            fixed_rows.append({'snapshot': key, 'encoding': mode, 'stage': stage, 'condition': condition,
                               'condition_equivalent_to': 'tonic_only' if condition == 'autonomous' else '',
                               'sample_off': True, 'clock_fixed': True, 'tonic_retained': True,
                               'duration_ms': float(times[-1]), 'state_drift_l2': float(np.linalg.norm(array[-1]-array[0])),
                               'tail_change_l2_100ms': float(np.linalg.norm(array[-1]-array[-21])),
                               'response_identity_preserved': persistent, **metrics,
                               'classification': 'stable_fixed_point_candidate' if metrics['residual_max_per_ms'] < 1e-8 and metrics['euler_spectral_radius'] < 1 and persistent else 'rest_fixed_point' if identity is None and metrics['residual_max_per_ms'] < 1e-8 else 'persistent_or_transient_state'})
            output[f'{condition}_drift_l2'] = np.linalg.norm(array-array[0], axis=1)
            output[f'{condition}_velocity_l2_per_ms'] = np.asarray([np.linalg.norm(field(probe, r)) for r in array])
        model.rates = archive['autonomous'][-1].copy(); model.clock[:] = 0
        targets = perturbation_targets(model, stage)
        initial = []; descriptors = []
        for name in TARGETS:
            indices = targets[name]
            for amplitude in AMPLITUDES:
                for seed in SEEDS:
                    eps = np.zeros(len(model.rates))
                    if len(indices):
                        random = np.random.default_rng(seed).normal(size=len(indices))
                        eps[indices] = amplitude * random / np.sqrt(np.mean(random**2))
                    initial.append(np.clip(model.rates+eps, 0, 1))
                    descriptors.append((name, amplitude, seed, len(indices)))
        paths = evolve_batch(model, np.asarray(initial), duration_ms=2000)
        # Exact existing whole-network probes were generated by EINetwork.step;
        # use them as the authoritative full perturbation trajectories.
        for index, (name, amplitude, seed, count) in enumerate(descriptors):
            if name == 'full':
                old = archive[f'basin_{amplitude}_{seed}']
                np.testing.assert_allclose(paths[index], old, atol=2e-12)
                paths[index] = old
        reference = evolve_batch(model, model.rates[None], 2000)[0]
        output['perturbation_control'] = reference
        output['perturbation_rates'] = paths.reshape(6, 4, 3, len(times), -1)
        distances = np.linalg.norm(paths-reference[None], axis=2)
        output['distances_l2'] = distances.reshape(6, 4, 3, len(times))
        output['target_names'] = np.asarray(TARGETS); output['amplitudes'] = np.asarray(AMPLITUDES); output['seeds'] = np.asarray(SEEDS)
        output['control_identity'] = np.array(state_identity(model, reference[-1], stage) or (-1, -1))
        for index, (name, amplitude, seed, count) in enumerate(descriptors):
            trace = paths[index]; final = trace[-1]
            error = np.max(abs(trace-reference), axis=1)
            identity_preserved = state_identity(model, final, stage) == state_identity(model, reference[-1], stage) and state_identity(model, final, stage) is not None
            good = (error < .02)
            persistent_good = np.logical_and.accumulate(good[::-1])[::-1]
            recovered = recovery(model, final, reference[-1], stage) if count else None
            eligible = np.flatnonzero(persistent_good) if recovered else np.array([], dtype=int)
            switch = state_identity(model, final, stage) is not None and not identity_preserved
            perturb_rows.append({'snapshot': key, 'encoding': mode, 'stage': stage, 'target': name, 'target_unit_count': count,
                                 'amplitude_target_rms_before_clipping': amplitude, 'seed': seed,
                                 'actual_rms_all_neurons': float(np.sqrt(np.mean((trace[0]-reference[0])**2))),
                                 'initial_distance_l2': float(distances[index, 0]), 'final_distance_l2': float(distances[index, -1]),
                                 'final_max_distance': float(error[-1]), 'identity_preserved': identity_preserved if count else 'NA',
                                 'recovered': recovered if count else 'NA', 'state_switched': switch if count else 'NA',
                                 'recovery_time_ms': float(times[eligible[0]]) if len(eligible) else 'NA',
                                 'final_branch': state_identity(model, final, stage)[0] if state_identity(model, final, stage) else 'NA',
                                 'final_position': state_identity(model, final, stage)[1] if state_identity(model, final, stage) else 'NA',
                                 'status': 'OK' if count else 'NA_NO_UNSELECTED_BRANCH'})
        selected = paths[6]  # full-network amplitude .3, seed 7, declared in metadata
        output['cross_temporal_times_ms'] = times[::4]
        output['cross_temporal_distance'] = cdist(selected[::4], reference[::4])
        family = [item['autonomous'][-1] for name, item in snapshots.items() if name.split('_L')[0] == mode and name.endswith(f'_R{stage}')]
        family = np.asarray(family); _, singular, basis_t = np.linalg.svd(family-family.mean(axis=0), full_matrices=False)
        basis = basis_t[:2].T
        xy = np.asarray([(x, y) for y in np.linspace(-.6, .6, 13) for x in np.linspace(-.6, .6, 13)])
        plane_states = np.clip(model.rates + xy@basis.T, 0, 1)
        vectors = np.asarray([field(model, r) for r in plane_states]); projected = vectors@basis
        output.update({'vector_grid_xy': (plane_states-model.rates)@basis, 'vector_xy_per_ms': projected,
                       'vector_offplane_norm_per_ms': np.linalg.norm(vectors-projected@basis.T, axis=1),
                       'vector_basis': basis, 'vector_origin': model.rates, 'vector_family_singular_values': singular})
        for seed in SEEDS:
            trajectory = archive[f'initial_{seed}']
            endpoint_model = deepcopy(model); endpoint_model.rates = trajectory[-1].copy()
            endpoint_rows.append({'snapshot': key, 'encoding': mode, 'stage': stage, 'initial_seed': seed,
                                  'source': 'reused_archived_random_uniform_initial_state',
                                  'endpoint_state': json.dumps(trajectory[-1].tolist()),
                                  'tail_change_l2_100ms': float(np.linalg.norm(trajectory[-1]-trajectory[-21])), **stability(endpoint_model)})
            output[f'random_initial_{seed}'] = trajectory
        np.savez_compressed(data_dir/f'{key}.npz', **output)
        print(f'dynamics {key}: saved {paths.shape[0]} probe trajectories', flush=True)
    _write_csv(metrics_dir/'dynamics_fixed_points.csv', fixed_rows)
    _write_csv(metrics_dir/'dynamics_perturbation.csv', perturb_rows)
    _write_csv(metrics_dir/'dynamics_endpoints.csv', endpoint_rows)
    endpoint_counts = {}
    for mode in sorted({name.split('_L')[0] for name in snapshots}):
        states = [item['autonomous'][-1] for name, item in snapshots.items() if name.split('_L')[0] == mode]
        observed = []
        for state in states:
            if all(np.max(abs(state-other)) >= .02 for other in observed): observed.append(state)
        random_states = [np.asarray(json.loads(row['endpoint_state'])) for row in endpoint_rows if row['encoding'] == mode]
        all_observed = list(observed)
        for state in random_states:
            if all(np.max(abs(state-other)) >= .02 for other in all_observed): all_observed.append(state)
        endpoint_counts[mode] = {'distinct_task_endpoint_states': len(observed), 'distinct_including_random_initial_states': len(all_observed)}
    summary = {'signature': signature, 'snapshot_count': len(snapshots), 'new_targeted_probe_count': len(snapshots)*5*4*3,
               'reused_full_probe_count': len(snapshots)*4*3, 'duration_ms': 2000, 'targets': list(TARGETS),
               'amplitudes': list(AMPLITUDES), 'seeds': list(SEEDS), 'raw_directory': str(data_dir),
               'fixed_points_csv': str(metrics_dir/'dynamics_fixed_points.csv'),
               'perturbation_csv': str(metrics_dir/'dynamics_perturbation.csv'),
               'conditions': {'forced': 'sample off; snapshot clock fixed; tonic retained',
                              'tonic_only': 'sample off; all clock zero; model tonic retained',
                              'autonomous': 'identical to tonic_only: no other task-related input exists'},
               'perturbation_origin': 'archived autonomous endpoint after 2000 ms; copied independent states',
               'perturbation_amplitude_definition': 'RMS over targeted units before [0,1] clipping; report actual whole-state RMS separately',
               'recovery_definition': 'full-state max error <.02 AND original active Response branch/location identity retained; rest is never recovery',
               'cross_temporal_selection': 'full target amplitude .3 seed 7; every fourth integration step',
               'vector_field_definition': 'clipped 13x13 slice in top two PCs of six same-stage autonomous endpoints; full field evaluated before projection; off-plane norm retained',
               'jacobian_definition': 'continuous piecewise-linear analytic Jacobian; symmetric derivative at clip kinks; Euler map I+dt*J; not a global stability proof',
               'scope': 'finite, local, fixed-input basin probes; random perturbation seeds are directions, not independent networks; six discrete locations do not establish a continuous attractor'}
    summary['distinct_endpoint_counts_maxnorm_tolerance_0.02'] = endpoint_counts
    summary['snapshot_coverage'] = 'six L conditions, historical fixed D=+1,S=1 (evaluate.py capture predicate), all four stages, all three encodings; does not enumerate all branch basins'
    summary['output_sha256']={str(path.relative_to(root)).replace('\\','/'):_hash(path) for path in [*sorted(data_dir.glob('*.npz')),*sorted(metrics_dir.glob('dynamics_*.csv'))]}
    summary_path.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.input, args.output)
