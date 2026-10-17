"""Validation-only independent expanded Euler and high-accuracy ODE equations.

These routines are never imported by the model. No task target is used.
"""

import numpy as np


def expanded_euler(model, initial_state):
    """Integrate R[path,site] explicitly, never integrate aggregate M."""
    p, c = model.params, model.connections
    e, i = initial_state.e_rates.copy(), initial_state.i_rate
    v, g = initial_state.v_rates.copy(), initial_state.g_rates.copy()
    n = round(p.rank_duration / p.dt)
    outputs = []
    for rank in range(initial_state.rank - 1, 3):
        source = e / e.sum()
        branch = np.zeros((4, 6))
        drive = np.asarray(p.readout_gains) * (c.rank_to_readout[rank] @ initial_state.encoding.joint.activity)
        rows, branch_rows = [], []
        for step in range(n + 1):
            summed = sum(c.branch_to_m[k] @ branch[k] for k in range(4))
            rows.append(np.r_[e, i, v, g, summed])
            branch_rows.append(branch.copy())
            if step == n:
                break
            targets = np.stack([np.maximum(c.e_to_branch[k] @ source + c.gate_to_branch[k] @ g, 0)
                                for k in range(4)])
            de = (-e + np.maximum(summed + p.w_ee * e - p.w_ei * i, 0)) / p.tau_e
            di = (-i + p.w_ie * np.sum(e)) / p.tau_i
            dv = (-v + np.maximum(drive + c.gate_to_readout @ g, 0)) / p.tau_v
            dg = (-g + c.readout_to_gate @ v) / p.tau_g
            db = (-branch + targets) / p.tau_m
            e, i, v, g, branch = (e + p.dt * de, i + p.dt * di,
                                  v + p.dt * dv, g + p.dt * dg, branch + p.dt * db)
        outputs.append(dict(rates=np.asarray(rows), branches=np.asarray(branch_rows)))
    return outputs


def ode_reference(model, position_activity, encoding, sample_dt):
    """Solve the continuous equations, including an independent initialization."""
    from scipy.integrate import solve_ivp
    p, c = model.params, model.connections
    source_input = np.array(position_activity, dtype=float)
    source_input /= source_input.sum()

    def initialization(_t, y):
        return np.r_[(-y[:6] + np.maximum(source_input + p.w_ee * y[:6] - p.w_ei * y[6], 0)) / p.tau_e,
                     (-y[6] + p.w_ie * sum(y[:6])) / p.tau_i]

    warm = solve_ivp(initialization, (0, p.initialization_duration), np.zeros(7),
                     rtol=1e-10, atol=1e-12)
    if not warm.success:
        raise RuntimeError(warm.message)
    y = np.r_[warm.y[:, -1], np.zeros(14)]
    local = np.linspace(0, p.rank_duration, round(p.rank_duration / sample_dt) + 1)
    outputs = []
    for rank in range(3):
        source = y[:6] / sum(y[:6])
        b = np.asarray(p.readout_gains) * (c.rank_to_readout[rank] @ encoding.joint.activity)
        y[15:] = 0

        def rhs(_t, z):
            e, i, v, g, m = z[:6], z[6], z[7:11], z[11:15], z[15:]
            excitation = np.stack([c.e_to_branch[k] @ source for k in range(4)])
            branch = np.stack([np.maximum(excitation[k] + c.gate_to_branch[k] @ g, 0)
                               for k in range(4)])
            pooled = sum(c.branch_to_m[k] @ branch[k] for k in range(4))
            return np.r_[(-e + np.maximum(m + p.w_ee * e - p.w_ei * i, 0)) / p.tau_e,
                         (-i + p.w_ie * sum(e)) / p.tau_i,
                         (-v + np.maximum(b + c.gate_to_readout @ g, 0)) / p.tau_v,
                         (-g + c.readout_to_gate @ v) / p.tau_g,
                         (-m + pooled) / p.tau_m]

        solved = solve_ivp(rhs, (0, p.rank_duration), y, t_eval=local,
                           rtol=1e-10, atol=1e-12, max_step=0.002)
        if not solved.success:
            raise RuntimeError(solved.message)
        outputs.append(solved.y.T)
        y = solved.y[:, -1].copy()
    return outputs
