"""Neuron-owned rate state and the circuit's original response equations.

``rate_potentials`` means the nonnegative rate variable r, in model units.
The model has no separately simulated membrane voltage.
"""

from __future__ import annotations

import numpy as np

from .core import Array, PATH_NAMES, Population, _array, _frozen, normalize, unit_names
from .timeline import RateRecording  # Compatibility with the original import path.


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
        self.rate_potentials = _frozen(
            np.zeros(shape) if rates is None else rates, shape, nonnegative=True)
        self.raw_drive = _frozen(
            np.zeros(shape) if raw_drive is None else raw_drive, shape)
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
        self.rate_potentials = _frozen(rates, (len(self.names),), nonnegative=True)
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
        super().__init__(unit_names("e"), params.tau_e)
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
        names = unit_names("gate_i" if gate else "i")
        super().__init__(names, params.tau_gate if gate else params.tau_i)
        self.params = params

    def feedback_target(self, e_rates):
        return self.params.w_ie * float(e_rates.sum())

    def gate(self, target):
        return self.respond(target, target, self.params.gate_duration)


class DNeurons(Neurons):
    def __init__(self, params):
        super().__init__(unit_names("d"), params.tau_tuning)
        self.params = params

    def encode(self, direction):
        p = self.params
        raw = p.direction_slope * direction * np.array([1, -1])
        self.respond(raw, np.asarray(p.direction_gains) * np.exp(-np.logaddexp(0, -raw)),
                     p.encoding_duration)
        return self.population()


class SNeurons(Neurons):
    def __init__(self, params):
        super().__init__(unit_names("s"), params.tau_tuning)
        self.params = params

    def encode(self, step):
        p = self.params
        raw = p.step_slope * (2 * step - 3) * np.array([-1, 1])
        self.respond(raw, np.asarray(p.step_gains) * np.exp(-np.logaddexp(0, -raw)),
                     p.encoding_duration)
        return self.population()


class JNeurons(Neurons):
    def __init__(self, params):
        super().__init__(unit_names("j"), params.tau_tuning)
        self.params = params

    def encode(self, direction_activity, step_activity):
        raw = np.outer(direction_activity, step_activity).reshape(4)
        self.respond(raw, raw * np.asarray(self.params.joint_gains), self.params.encoding_duration)
        return self.population()


class VNeurons(Neurons):
    """Four displacement readout units, retaining their DISP_* names."""

    def __init__(self, params):
        super().__init__(unit_names("v"), params.tau_readout)
        self.params = params

    def read(self, connection_slice, joint_activity):
        raw = connection_slice @ joint_activity
        self.respond(raw, raw * np.asarray(self.params.readout_gains), self.params.readout_duration)
        return self.population()


class RelayNeurons(Neurons):
    def __init__(self, params):
        super().__init__(unit_names("relay"),
                         params.tau_relay)

    def target(self, source, e_to_relay, gate_rates, gate_to_relay):
        raw = np.einsum("pij,j->pi", e_to_relay, source)
        inhibition = np.einsum("pjg,g->pj", gate_to_relay, gate_rates)
        return raw, inhibition, np.maximum(raw + inhibition, 0)
