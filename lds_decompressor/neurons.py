"""Neuron-owned rate state and the circuit's original response equations.

``rate_potentials`` means the nonnegative rate variable r, in model units.
The model has no separately simulated membrane voltage.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]
PATH_NAMES = ("CW1", "CW2", "CCW1", "CCW2")


def _array(value, shape=None, *, nonnegative=False) -> Array:
    out = np.array(value, dtype=float, copy=True)
    if shape is not None and out.shape != shape:
        raise ValueError(f"Expected shape {shape}, got {out.shape}")
    if not np.isfinite(out).all() or (nonnegative and np.any(out < 0)):
        raise ValueError("Activity must be finite and, where required, nonnegative")
    return out


def _frozen(value) -> Array:
    out = _array(value)
    out.setflags(write=False)
    return out


def normalize(value) -> Array:
    out = _array(value, nonnegative=True)
    total = float(out.sum())
    if total <= 0:
        raise ValueError("Cannot normalize silent activity")
    return out / total


@dataclass(frozen=True)
class Population:
    """Immutable raw input, unnormalized rate and normalized activity."""

    names: tuple[str, ...]
    raw_drive: Array
    rates: Array
    activity: Array

    def __post_init__(self):
        n = len(self.names)
        for name in ("raw_drive", "rates", "activity"):
            arr = _array(getattr(self, name), (n,), nonnegative=name != "raw_drive")
            object.__setattr__(self, name, _frozen(arr))
        if not np.isclose(self.activity.sum(), 1):
            raise ValueError("Population activity must sum to one")


class Neurons:
    """A named group; each column is one scalar rate unit.

    All subclasses initialize and update their own ``rate_potentials``.
    ``history`` stores the latest response/integration, including its start.
    """

    def __init__(self, names, tau):
        self.names = tuple(names)
        self.tau = tau
        self.initialize()

    def initialize(self, rates=None, *, raw_drive=None):
        shape = (len(self.names),)
        self.rate_potentials = _frozen(_array(
            np.zeros(shape) if rates is None else rates, shape, nonnegative=True))
        self.raw_drive = _frozen(_array(
            np.zeros(shape) if raw_drive is None else raw_drive, shape))
        self._history = [self.rate_potentials]

    @property
    def rates(self):
        return self.rate_potentials

    @property
    def history(self):
        return _frozen(np.stack(self._history))

    def restore(self, population: Population):
        self.initialize(population.rates, raw_drive=population.raw_drive)

    def respond(self, raw, target, duration):
        """Original exact solution: tau*dr/dt=-r+target, r(0)=0."""
        self.initialize(raw_drive=raw)
        rates = np.asarray(target) * (-np.expm1(-duration / self.tau))
        self.rate_potentials = _frozen(_array(rates, (len(self.names),), nonnegative=True))
        self._history.append(self.rate_potentials)
        return self.rate_potentials

    def population(self):
        return Population(self.names, self.raw_drive, self.rates, normalize(self.rates))

    def step(self, target, dt):
        """Original forward Euler update; callers compute synchronous targets."""
        self.raw_drive = _frozen(target)
        self.rate_potentials = _frozen(
            self.rates + dt / self.tau * (target - self.rates))
        self._history.append(self.rate_potentials)

    def hold(self):
        """Record an unchanged sample without introducing new dynamics."""
        self._history.append(self.rate_potentials)


class ENeurons(Neurons):
    def __init__(self, params):
        super().__init__((f"E{k}" for k in range(1, 7)), params.tau_e)
        self.params = params
        self.site_angles = np.arange(6) * np.pi / 3
        self.site_coordinates = np.column_stack((np.cos(self.site_angles), -np.sin(self.site_angles)))

    def encode_angle(self, clockwise_angle):
        if not np.isfinite(clockwise_angle):
            raise ValueError("Angle must be finite")
        drive = np.exp(self.params.location_kappa * (np.cos(clockwise_angle - self.site_angles) - 1))
        return normalize(drive)

    def target(self, drive, i_rate):
        p = self.params
        return np.maximum(drive + p.w_ee * self.rates - p.w_ei * i_rate, 0)


class INeurons(Neurons):
    """Global feedback I or path-gating I, with their original time constants."""

    def __init__(self, params, *, gate=False):
        names = tuple(f"I_gate_{name}" for name in PATH_NAMES) if gate else ("I_global",)
        super().__init__(names, params.tau_gate if gate else params.tau_i)
        self.params = params

    def feedback_target(self, e_rates):
        return self.params.w_ie * float(e_rates.sum())

    def gate(self, target):
        return self.respond(target, target, self.params.gate_duration)


class DNeurons(Neurons):
    def __init__(self, params):
        super().__init__(("D_CW", "D_CCW"), params.tau_tuning)
        self.params = params

    def encode(self, direction):
        p = self.params
        raw = p.direction_slope * direction * np.array([1, -1])
        self.respond(raw, np.asarray(p.direction_gains) * np.exp(-np.logaddexp(0, -raw)),
                     p.encoding_duration)
        return self.population()


class SNeurons(Neurons):
    def __init__(self, params):
        super().__init__(("S1", "S2"), params.tau_tuning)
        self.params = params

    def encode(self, step):
        p = self.params
        raw = p.step_slope * (2 * step - 3) * np.array([-1, 1])
        self.respond(raw, np.asarray(p.step_gains) * np.exp(-np.logaddexp(0, -raw)),
                     p.encoding_duration)
        return self.population()


class JNeurons(Neurons):
    def __init__(self, params):
        super().__init__((f"J_{name}" for name in PATH_NAMES), params.tau_tuning)
        self.params = params

    def encode(self, direction_activity, step_activity):
        raw = np.outer(direction_activity, step_activity).reshape(4)
        self.respond(raw, raw * np.asarray(self.params.joint_gains), self.params.encoding_duration)
        return self.population()


class VNeurons(Neurons):
    """Four displacement readout units, retaining their DISP_* names."""

    def __init__(self, params):
        super().__init__((f"DISP_{name}" for name in PATH_NAMES), params.tau_readout)
        self.params = params

    def read(self, connection_slice, joint_activity):
        raw = connection_slice @ joint_activity
        self.respond(raw, raw * np.asarray(self.params.readout_gains), self.params.readout_duration)
        return self.population()


class RelayNeurons(Neurons):
    def __init__(self, params):
        super().__init__((f"R_{path}_E{k}" for path in PATH_NAMES for k in range(1, 7)),
                         params.tau_relay)

    def target(self, source, e_to_relay, gate_rates, gate_to_relay):
        raw = np.einsum("pij,j->pi", e_to_relay, source)
        inhibition = np.einsum("pjg,g->pj", gate_to_relay, gate_rates)
        return raw, inhibition, np.maximum(raw + inhibition, 0)


@dataclass(frozen=True)
class RateRecording:
    """Owned raw rates for every unit, recorded by the model before plotting."""

    time: Array
    rates: Array
    labels: np.ndarray
    groups: np.ndarray
    modes: np.ndarray

    def __post_init__(self):
        time = _array(self.time)
        rates = _array(self.rates, nonnegative=True)
        if time.ndim != 1 or len(time) == 0 or not np.all(np.diff(time) > 0):
            raise ValueError("Recording times must be nonempty and strictly increasing")
        if rates.shape != (len(time), len(self.labels)):
            raise ValueError("Recording must have one rate per time and unit")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("Recording labels must be unique")
        for name in ("groups", "modes"):
            if np.shape(getattr(self, name)) != (len(self.labels),):
                raise ValueError("Recording metadata must have one entry per unit")
        object.__setattr__(self, "time", _frozen(time))
        object.__setattr__(self, "rates", _frozen(rates))
        for name in ("labels", "groups", "modes"):
            value = np.array(getattr(self, name), dtype=str, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)

    @property
    def rate_potentials(self):
        return self.rates

    @classmethod
    def concatenate(cls, recordings):
        """Retain the next transition's sample at a shared boundary."""
        if not recordings:
            raise ValueError("No retrieval transitions were recorded")
        first = recordings[0]
        times, values, offset = [], [], 0.0
        for record in recordings:
            for name in ("labels", "groups", "modes"):
                if not np.array_equal(getattr(record, name), getattr(first, name)):
                    raise ValueError("Recording unit metadata changed between transitions")
            times.append(record.time[:-1] + offset)
            values.append(record.rates[:-1])
            offset += record.time[-1]
        return cls(np.r_[np.concatenate(times), offset],
                   np.concatenate(values + [recordings[-1].rates[-1:]]),
                   first.labels, first.groups, first.modes)
