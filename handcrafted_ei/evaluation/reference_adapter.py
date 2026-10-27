"""Lossless, explicit interfaces from archived LDS states to reference methods.

No paper preprocessing, inferred repeats, state generation, or model modification.
Currents are reconstructed from verified code/configuration/events, not measured.
"""
import numpy as np
from .population_data import load_dataset, validate_dataset, source_identity
from ..model.ei_network import EINetwork


def _validate(d):
    validate_dataset(d)
    mode = d['encoding_type']
    expected_dim = {'one_hot': 6, 'ring': 1, 'topology': 2}.get(mode)
    if expected_dim is None or d['config']['location_encoding'] != mode:
        raise ValueError('encoding/config identity mismatch')
    conditions = []
    for task in d['tasks']:
        if task['encoding'] != mode or len(task['encoded']['x_L']) != expected_dim:
            raise ValueError('encoded input identity mismatch')
        conditions.append((task['L'], task['D'], task['S']))
    expected = {(l, dr, s) for l in range(6) for dr in (-1, 1) for s in (1, 2)}
    if len(conditions) != 24 or set(conditions) != expected:
        raise ValueError('requires exactly one recorded trial per 24 LDS conditions')
    if np.asarray(d['times_ms'])[0] != 0:
        raise ValueError('recording must include initial t=0 state')
    if len(np.unique(d['trial_id'])) != 24:
        raise ValueError('trial identifiers must be unique')
    return np.asarray(conditions, dtype=int)


def load_audited_dataset(input_dir, mode, experiment='baseline'):
    """Verify protected source and archive checksum before returning raw rates."""
    protected = source_identity(input_dir)
    d = load_dataset(input_dir, mode, experiment)
    _validate(d)
    d['protected_source_identity'] = protected
    return d


def reference_axes(d):
    """Explicit [trial,time,neuron] -> [time,condition,neuron], without averaging."""
    conditions = _validate(d)
    return {'rates': np.transpose(d['rates'], (1, 0, 2)).copy(),
            'times_ms': np.asarray(d['times_ms']).copy(), 'conditions': conditions,
            'trial_id': np.asarray(d['trial_id']).copy(),
            'axis_semantics': ['time', 'condition', 'neuron'],
            'repetitions_per_condition': 1, 'averaging': 'none',
            'normalization': 'none; dimensionless rates',
            'population': 'whole LDS network; no assumed biological equivalence',
            'encoding_type': d['encoding_type'], 'archive_sha256': d['archive_sha256']}


def reconstruct_currents(d):
    """Current row t is that used to integrate into the recorded state at t.

    Clock events act on the step *after* their timestamp. All t=0 rows are zero
    placeholders (no integration into initial state), including tonic.
    """
    _validate(d)
    m = EINetwork(overrides=d['config'])
    shape = np.asarray(d['rates']).shape
    stimulus = np.zeros(shape); clock = np.zeros(shape); tonic = np.zeros(shape)
    t = np.asarray(d['times_ms'])
    tonic[:, 1:] = m.tonic
    for trial, (task, events) in enumerate(zip(d['tasks'], d['events'])):
        m.apply_input(**{k: np.asarray(v) for k, v in task['encoded'].items()})
        stimulus[trial, (t > events['sample_start']) & (t <= events['sample_end'])] = m.stimulus
        for event, group, amplitude in (
                ('to_R2', 'E_gate_D', 'clock_activation'),
                ('to_R3', 'E_gate_S', 'clock_activation'),
                ('to_R4', 'E_gate_34', 'clock_activation3')):
            if event not in events: raise ValueError('missing clock event: ' + event)
            clock[trial][np.ix_(t > events[event], m.groups[group])] = m.config[amplitude]
        for stage in (1, 2, 3):
            event = f'retire{stage}'
            if event not in events: raise ValueError('missing retire event: ' + event)
            clock[trial, t > events[event], m.groups['retire'][stage - 1]] = m.config['clock_retire']
    return {'stimulus': stimulus, 'clock': clock, 'tonic': tonic,
            'origin': 'reconstructed from verified model configuration, encoded input, and recorded events',
            'row_semantics': 'current integrated into state at this timestamp; t=0 zero placeholder',
            'measured': False}


def extract_snapshots(d, stage=3):
    """Gather actual per-condition readout states; never synthesize from labels.

    Snapshot clock is the current acting immediately after the readout event;
    the present archived protocol has no simultaneous phase/retire event.
    """
    conditions = _validate(d)
    if stage not in (1, 2, 3, 4): raise ValueError('stage must be 1..4')
    currents = reconstruct_currents(d)
    t = np.asarray(d['times_ms']); indices = []
    for events in d['events']:
        event = f'readout{stage}'
        if event not in events: raise ValueError('missing readout event')
        matches = np.flatnonzero(t == events[event])
        if len(matches) != 1: raise ValueError('snapshot event absent from exact recording grid')
        if any(events.get(k) == events[event] for k in ('to_R2', 'to_R3', 'to_R4', 'retire1', 'retire2', 'retire3')):
            raise ValueError('ambiguous simultaneous readout and clock event')
        indices.append(matches[0])
    trial = np.arange(len(indices)); index = np.asarray(indices)
    return {'rates': np.asarray(d['rates'])[trial, index].copy(),
            'clock': currents['clock'][trial, index].copy(),
            'tonic': currents['tonic'][trial, index].copy(),
            'stimulus': currents['stimulus'][trial, index].copy(),
            'times_ms': t[index].copy(), 'recording_indices': index,
            'trial_id': np.asarray(d['trial_id']).copy(), 'conditions': conditions,
            'labels': np.asarray(d['labels']).copy(), 'neuron_types': np.asarray(d['neuron_types']).copy(),
            'population_indices': {k: np.asarray(v).copy() for k, v in d['groups'].items()},
            'branch_indices': {k: np.asarray(v).copy() for k, v in d['branch_indices'].items()},
            'encoding_type': d['encoding_type'], 'stage': stage,
            'archive_sha256': d['archive_sha256'], 'archive_path': d['archive_path'],
            'current_origin': currents['origin'], 'rate_origin': 'exact archived readout state'}
