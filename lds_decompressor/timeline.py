"""Join actual retrieval records without altering the circuit or its dynamics.

The time axis counts E/I integration only. Encoding is held throughout;
readout/gate snapshots are held within a transition. Their setup intervals
were not jointly sampled with E/I and are not invented here.
"""

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .neurons import RateRecording


PATHS = ("CW1", "CW2", "CCW1", "CCW2")


@dataclass(frozen=True)
class SequenceTimeline:
    time: np.ndarray
    rates: np.ndarray
    labels: np.ndarray
    groups: np.ndarray
    modes: np.ndarray
    rank_times: np.ndarray
    positions: np.ndarray
    condition: np.ndarray

    def columns(self, group):
        return self.rates[:, self.groups == group]

    def save(self, path):
        np.savez_compressed(path, **vars(self))

    @classmethod
    def load(cls, path):
        """Read recorded values verbatim; no model response or held-rate synthesis."""
        with np.load(path, allow_pickle=False) as data:
            return cls(**{key: data[key].copy() for key in cls.__dataclass_fields__})

    @classmethod
    def from_recording(cls, recording: RateRecording, rank_times, positions, condition):
        """Attach presentation labels to a recording already produced by neurons."""
        return cls(recording.time, recording.rates, recording.labels,
                   recording.groups, recording.modes, np.asarray(rank_times),
                   np.asarray(positions), np.asarray(condition))


def build_sequence_timeline(data: Mapping) -> SequenceTimeline:
    """Legacy importer for activities.npz; new runs export neuron recordings directly.

    The saved example is condition row 1 (L=1,D=+1,S=2). At a rank switch
    E/I continue, relays reset, and readout/gates switch to the next snapshots.
    Keep one sample per time: a boundary belongs to the next transition.
    """
    local = np.asarray(data["example_time"], dtype=float)
    if (local.ndim != 1 or len(local) < 2 or local[0] != 0
            or not np.all(np.diff(local) > 0)):
        raise ValueError("Local times must start at zero and strictly increase")
    e = np.asarray(data["example_e"], dtype=float)
    i = np.asarray(data["example_i"], dtype=float)
    relay = np.asarray(data["example_relays"], dtype=float)
    n = len(local)
    if e.shape != (3, n, 6) or i.shape != (3, n) or relay.shape != (3, n, 4, 6):
        raise ValueError("Unexpected E/I/relay trace shapes")
    if not (np.allclose(e[1:, 0], e[:-1, -1], rtol=0, atol=1e-12)
            and np.allclose(i[1:, 0], i[:-1, -1], rtol=0, atol=1e-12)):
        raise ValueError("Cannot join discontinuous E/I transition boundaries")
    # Reject stale example metadata instead of silently labelling another run.
    positions = np.asarray(data["positions"])[1]
    observed = np.r_[e[0, 0].argmax() + 1, e[:, -1].argmax(axis=1) + 1]
    if not np.array_equal(positions, observed):
        raise ValueError("Saved positions do not match the representative E trace")

    def join(block):
        # Each block is [transition, time, ...]. Last endpoint is retained once.
        return np.concatenate([block[r, :-1] for r in range(3)] + [block[-1, -1:]])

    time = np.concatenate([local[:-1] + r * local[-1] for r in range(3)]
                          + [np.array([3 * local[-1]])])
    count = len(time)
    values, labels, groups, modes = [], [], [], []

    def add(group, names, rates, mode):
        rates = np.asarray(rates, dtype=float)
        if rates.shape != (count, len(names)):
            raise ValueError(f"Unexpected shape for {group}: {rates.shape}")
        values.append(rates)
        labels.extend(names)
        groups.extend([group] * len(names))
        modes.extend([mode] * len(names))

    def held_encoding(key):
        return np.repeat(np.asarray(data[key])[1:2], count, axis=0)

    def held_by_rank(key):
        snapshots = np.asarray(data[key])[1]
        return join(np.repeat(snapshots[:, None, :], n, axis=1))

    add("Position E", [f"E{k}" for k in range(1, 7)], join(e), "integrated")
    add("Direction", ["D_CW", "D_CCW"], held_encoding("direction_rates"), "held")
    add("Step", ["S1", "S2"], held_encoding("step_rates"), "held")
    add("Joint", [f"J_{p}" for p in PATHS], held_encoding("joint_rates"), "held")
    add("Displacement", [f"DISP_{p}" for p in PATHS], held_by_rank("displacement_rates"), "held")
    add("Gate I", [f"I_gate_{p}" for p in PATHS], held_by_rank("gate_i_rates"), "held")
    for path, name in enumerate(PATHS):
        add(f"Relay {name}", [f"R_{name}_E{k}" for k in range(1, 7)],
            join(relay[:, :, path]), "integrated")
    add("Global I", ["I_global"], join(i[:, :, None]), "integrated")
    rates = np.concatenate(values, axis=1)
    if not np.isfinite(rates).all() or np.any(rates < 0):
        raise ValueError("Rates must be finite and nonnegative")
    if len(labels) != 47:
        raise ValueError("Expected all 47 rate units")
    return SequenceTimeline(time, rates, np.asarray(labels), np.asarray(groups),
                            np.asarray(modes), np.arange(4) * local[-1],
                            positions.copy(), np.asarray(data["conditions"])[1].copy())
