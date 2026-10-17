"""Join actual retrieval records without altering the circuit or its dynamics.

The time axis counts E/I integration only. Encoding is held throughout;
readout/gate snapshots are held within a transition. Their setup intervals
were not jointly sampled with E/I and are not invented here.
"""

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .core import Array, PATH_NAMES, UNIT_GROUPS, _frozen


PATHS = PATH_NAMES


@dataclass(frozen=True)
class RateRecording:
    """Owned raw rates for every unit, recorded by the model before plotting."""

    time: Array
    rates: Array
    labels: np.ndarray
    groups: np.ndarray
    modes: np.ndarray

    def __post_init__(self):
        time = _frozen(self.time)
        rates = _frozen(self.rates, nonnegative=True)
        if time.ndim != 1 or len(time) == 0 or not np.all(np.diff(time) > 0):
            raise ValueError("Recording times must be nonempty and strictly increasing")
        if rates.shape != (len(time), len(self.labels)):
            raise ValueError("Recording must have one rate per time and unit")
        if np.shape(self.labels) != (len(self.labels),):
            raise ValueError("Recording labels must be one-dimensional")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("Recording labels must be unique")
        for name in ("groups", "modes"):
            if np.shape(getattr(self, name)) != (len(self.labels),):
                raise ValueError("Recording metadata must have one entry per unit")
        object.__setattr__(self, "time", time)
        object.__setattr__(self, "rates", rates)
        for name in ("labels", "groups", "modes"):
            value = np.array(getattr(self, name), dtype=str, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)

    @property
    def rate_potentials(self):
        return self.rates

    @classmethod
    def from_groups(cls, time, samples: Mapping):
        """Assemble the circuit's canonical columns from actual group rates.

        Integrated groups provide time-by-unit arrays. Held controls provide
        one vector; only this explicit mode allows broadcasting over time.
        """
        expected = {group.name for group in UNIT_GROUPS}
        if set(samples) != expected:
            raise ValueError("Samples must contain exactly the circuit's unit groups")
        values, labels, groups, modes = [], [], [], []
        for group in UNIT_GROUPS:
            width = len(group.labels)
            rates = np.asarray(samples[group.name], dtype=float)
            if group.mode == "held":
                if rates.shape != (width,):
                    raise ValueError(f"Unexpected held rate shape for {group.name}")
                rates = np.repeat(rates[None], len(time), axis=0)
            elif rates.shape != (len(time), width):
                raise ValueError(f"Unexpected integrated rate shape for {group.name}")
            values.append(rates)
            labels.extend(group.labels)
            groups.extend(group.groups)
            modes.extend([group.mode] * width)
        return cls(time, np.concatenate(values, axis=1), labels, groups, modes)

    @classmethod
    def concatenate(cls, recordings):
        """Retain the next transition's sample at a shared boundary."""
        if not recordings:
            raise ValueError("No retrieval transitions were recorded")
        first = recordings[0]
        continuous = np.isin(first.groups, ("Position E", "Global I"))
        previous = None
        times, values, offset = [], [], 0.0
        for record in recordings:
            if len(record.time) < 2 or record.time[0] != 0:
                raise ValueError("Transition times must start at zero and include an endpoint")
            for name in ("labels", "groups", "modes"):
                if not np.array_equal(getattr(record, name), getattr(first, name)):
                    raise ValueError("Recording unit metadata changed between transitions")
            if previous is not None and not np.allclose(
                    previous.rates[-1, continuous], record.rates[0, continuous],
                    rtol=0, atol=1e-12):
                raise ValueError("Cannot join discontinuous E/I transition boundaries")
            previous = record
            times.append(record.time[:-1] + offset)
            values.append(record.rates[:-1])
            offset += record.time[-1]
        return cls(np.r_[np.concatenate(times), offset],
                   np.concatenate(values + [recordings[-1].rates[-1:]]),
                   first.labels, first.groups, first.modes)


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
    # Reject stale example metadata instead of silently labelling another run.
    positions = np.asarray(data["positions"])[1]
    observed = np.r_[e[0, 0].argmax() + 1, e[:, -1].argmax(axis=1) + 1]
    if not np.array_equal(positions, observed):
        raise ValueError("Saved positions do not match the representative E trace")

    records = []
    for rank in range(3):
        records.append(RateRecording.from_groups(local, {
            "Position E": e[rank],
            "Direction": np.asarray(data["direction_rates"])[1],
            "Step": np.asarray(data["step_rates"])[1],
            "Joint": np.asarray(data["joint_rates"])[1],
            "Displacement": np.asarray(data["displacement_rates"])[1, rank],
            "Gate I": np.asarray(data["gate_i_rates"])[1, rank],
            "Relay": relay[rank].reshape(n, 24),
            "Global I": i[rank, :, None],
        }))
    recording = RateRecording.concatenate(records)
    return SequenceTimeline.from_recording(
        recording, np.arange(4) * local[-1], positions.copy(),
        np.asarray(data["conditions"])[1].copy())
