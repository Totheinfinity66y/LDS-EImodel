"""All rate states use the same bounded-ReLU Euler equation."""
import numpy as np


def euler(rates, drive, tau_ms, dt_ms):
    if (not np.all(np.isfinite(drive)) or not np.all(np.isfinite(rates))
            or np.any(rates < 0) or np.any(rates > 1)
            or np.any(tau_ms <= 0) or not 0 < dt_ms <= .5 * np.min(tau_ms)):
        raise ValueError('invalid rate, drive, time constant or integration step')
    updated = rates + dt_ms / tau_ms * (-rates + np.clip(drive, 0, 1))
    if not np.all(np.isfinite(updated)) or np.any(updated < 0) or np.any(updated > 1):
        raise ValueError('rate outside [0,1]')
    return updated


class Neuron:
    sign = None
    def __init__(self, tau_ms=40):
        self.tau_ms = tau_ms
        self.rate = 0.

    def step(self, drive, dt_ms):
        self.rate = float(euler(np.array([self.rate]), np.array([drive]),
                                np.array([self.tau_ms]), dt_ms)[0])
        return self.rate


class ExcitatoryNeuron(Neuron):
    sign = 1


class InhibitoryNeuron(Neuron):
    sign = -1
