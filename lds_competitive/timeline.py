"""Right-continuous retrieval timeline; only actual raw rates, never targets."""

from dataclasses import dataclass
import numpy as np
from .model import PATH_NAMES, observed_peak


@dataclass(frozen=True)
class RateTimeline:
    time: np.ndarray
    rates: np.ndarray
    labels: np.ndarray
    groups: np.ndarray
    modes: np.ndarray
    rank_times: np.ndarray
    positions: np.ndarray

    def __post_init__(self):
        for key, value in vars(self).items():
            copy = np.array(value, copy=True)
            copy.setflags(write=False)
            object.__setattr__(self, key, copy)
        if self.rates.shape != (len(self.time), 29) or not np.isfinite(self.rates).all():
            raise ValueError("Expected finite samples x 29 raw rates")
        if np.any(self.rates < 0) or not np.all(np.diff(self.time) > 0):
            raise ValueError("Require nonnegative rates and strictly increasing times")

    def columns(self, group):
        return self.rates[:, self.groups == group]

    def save(self, path):
        np.savez_compressed(path, **vars(self))


def build_timeline(result):
    traces = result.transitions
    if len(traces) != 3 or len(result.positions) != 4:
        raise ValueError("A full three-transition result is required")
    local = traces[0].time
    for k, trace in enumerate(traces):
        if not np.array_equal(trace.time, local):
            raise ValueError("Inconsistent sample times")
        if np.any(trace.m_rates[0] != 0):
            raise ValueError("Shared relay must reset at each rank")
        if k:
            for name in ("e_rates", "v_rates", "g_rates", "i_rates"):
                if not np.array_equal(getattr(trace, name)[0], getattr(traces[k - 1], name)[-1]):
                    raise ValueError(f"Discontinuous {name}")
    observed = (observed_peak(traces[0].e_rates[0]) + 1,
                *(observed_peak(t.e_rates[-1]) + 1 for t in traces))
    if observed != tuple(result.positions):
        raise ValueError("Output labels disagree with actual E records")

    def join(values):
        return np.concatenate([v[:-1] for v in values[:-1]] + [values[-1]])

    time = join([t.time + k * local[-1] for k, t in enumerate(traces)])
    values, labels, groups, modes = [], [], [], []

    def add(group, names, rate, mode):
        values.append(rate)
        labels.extend(names)
        groups.extend([group] * len(names))
        modes.extend([mode] * len(names))

    add("Position E", [f"E{k}" for k in range(1, 7)], join([t.e_rates for t in traces]), "integrated")
    enc = result.initial_state.encoding
    for group, pop in (("Direction", enc.direction), ("Step", enc.step), ("Joint", enc.joint)):
        add(group, pop.names, np.repeat(pop.rates[None], len(time), axis=0), "held")
    add("Readout V", [f"V_{x}" for x in PATH_NAMES], join([t.v_rates for t in traces]), "integrated")
    add("Gate G", [f"G_{x}" for x in PATH_NAMES], join([t.g_rates for t in traces]), "integrated")
    add("Shared M", [f"M{k}" for k in range(1, 7)], join([t.m_rates for t in traces]), "integrated")
    add("Global I", ["I_global"], join([t.i_rates[:, None] for t in traces]), "integrated")
    return RateTimeline(time, np.column_stack(values), np.asarray(labels), np.asarray(groups),
                        np.asarray(modes), np.arange(4) * local[-1], np.asarray(result.positions))
