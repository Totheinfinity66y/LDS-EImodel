"""Observation-only metrics with thresholds fixed before default runs."""

import numpy as np

TAIL_SECONDS = 0.100
BLOCKED_TOLERANCE = 1e-6
EQUILIBRIUM_TOLERANCE = 1e-4
SETTLING_LIMIT = 0.600
AGGREGATION_TOLERANCE = 1e-10
DT_DIFFERENCE_LIMIT = 0.025
ODE_COARSE_LIMIT = 0.040
ODE_REFINEMENT_RATIO = 0.70


def transition_metrics(trace):
    """Compare measured control with its theoretical default equilibrium."""
    winner = int(np.argmax(trace.readout_drive))
    v_star = np.zeros(4)
    v_star[winner] = trace.readout_drive[winner]
    g_star = v_star.sum() - v_star
    errors = np.maximum(np.abs(trace.v_rates - v_star).max(axis=1),
                        np.abs(trace.g_rates - g_star).max(axis=1))
    inactive = np.arange(4) != winner
    blocked = trace.branch_target[:, inactive]
    blocked_max = blocked.max(axis=(1, 2))
    good = (errors <= EQUILIBRIUM_TOLERANCE) & (blocked_max <= BLOCKED_TOLERANCE)
    suffix_good = np.logical_and.accumulate(good[::-1])[::-1]
    indices = np.flatnonzero(suffix_good)
    settle = float(trace.time[indices[0]]) if len(indices) else None
    tail = trace.time >= trace.time[-1] - TAIL_SECONDS - 1e-12
    leakage_sum = blocked.sum(axis=(1, 2))
    leakage_area = np.sum(0.5 * (leakage_sum[:-1] + leakage_sum[1:]) * np.diff(trace.time))
    sorted_e = np.sort(trace.e_rates[-1])
    return dict(
        transition=int(trace.from_rank), drive_winner=winner,
        observed_readout_peak=int(np.argmax(trace.v_rates[-1])),
        terminal_vg_error=float(errors[tail].max()),
        terminal_blocked_drive=float(blocked_max[tail].max()),
        settling_time=settle, leakage_peak=float(blocked_max.max()),
        leakage_integral=float(leakage_area),
        position_peak_margin=float(sorted_e[-1] - sorted_e[-2]),
        control_pass=bool(errors[tail].max() <= EQUILIBRIUM_TOLERANCE
                          and blocked_max[tail].max() <= BLOCKED_TOLERANCE
                          and settle is not None and settle <= SETTLING_LIMIT + 1e-12),
    )


def packed_trace(trace):
    """21 integrated variables: E6, I1, V4, G4, M6."""
    return np.column_stack((trace.e_rates, trace.i_rates, trace.v_rates, trace.g_rates, trace.m_rates))
