"""Independent L/D/S rate equations; W[post, pre], seconds, dimensionless rates.

No targets, symbolic routing, old model imports, or hidden instance history.
Shared M is an effective aggregate: four rectified spatial branches remain.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from numbers import Integral
import numpy as np

PATH_NAMES = ("CW1", "CW2", "CCW1", "CCW2")
SHIFTS = (1, 2, -1, -2)
JOINT_PREFERENCES = ((1, 1), (1, 2), (-1, 1), (-1, 2))


def _array(value, shape=None, *, nonnegative=False):
    out = np.array(value, dtype=float, copy=True)
    if shape is not None and out.shape != shape:
        raise ValueError(f"Expected {shape}, got {out.shape}")
    if not np.isfinite(out).all() or (nonnegative and np.any(out < 0)):
        raise ValueError("Require finite activity with the specified sign")
    return out


def frozen(value):
    out = _array(value)
    out.setflags(write=False)
    return out


def normalize(value):
    out = _array(value, nonnegative=True)
    if out.sum() <= 0:
        raise ValueError("Cannot normalize silent activity")
    return out / out.sum()


def require_unique_drive(value):
    """Validate the single-choice task; does not select or command a path."""
    value = _array(value, nonnegative=True)
    largest = value.max()
    if largest <= 0 or np.count_nonzero(np.isclose(value, largest, rtol=1e-9, atol=1e-12)) != 1:
        raise ValueError("Require a unique positive maximum drive")


def observed_peak(value):
    """Observation only: this function is never used to form a gate or input."""
    require_unique_drive(value)
    return int(np.argmax(value))


@dataclass(frozen=True)
class CompressedCode:
    location: int
    direction: int
    step: int

    def __post_init__(self):
        for v, allowed in ((self.location, range(1, 7)),
                           (self.direction, (-1, 1)), (self.step, (1, 2))):
            if isinstance(v, bool) or not isinstance(v, Integral) or v not in allowed:
                raise ValueError("Require L=1..6, D=+/-1, S=1/2, all integers")


@dataclass(frozen=True)
class ModelParameters:
    location_kappa: float = 8.0
    direction_slope: float = 6.0
    step_slope: float = 6.0
    direction_gains: tuple = (1.0, 1.0)
    step_gains: tuple = (1.0, 1.0)
    joint_gains: tuple = (1.0, 1.0, 1.0, 1.0)
    readout_gains: tuple = (1.0, 1.0, 1.0, 1.0)
    tau_tuning: float = 0.020
    encoding_duration: float = 0.200
    tau_v: float = 0.020
    tau_g: float = 0.020
    tau_m: float = 0.030
    tau_e: float = 0.100
    tau_i: float = 0.050
    initialization_duration: float = 0.800
    rank_duration: float = 0.800
    dt: float = 0.002
    w_ee: float = 0.15
    w_ei: float = 0.20
    w_ie: float = 0.25
    gate_strength: float = 2.0

    def __post_init__(self):
        allow_zero = {"w_ee", "w_ei", "w_ie", "gate_strength"}
        for item in fields(self):
            v = getattr(self, item.name)
            if item.name.endswith("_gains"):
                n = 2 if item.name in ("direction_gains", "step_gains") else 4
                a = _array(v, (n,), nonnegative=True)
                object.__setattr__(self, item.name, tuple(float(x) for x in a))
            elif not np.isfinite(v) or v < 0 or (v == 0 and item.name not in allow_zero):
                raise ValueError(f"Invalid {item.name}")
        if self.w_ee >= 1:
            raise ValueError("Require w_ee < 1")
        if self.dt > 0.2 * min(self.tau_v, self.tau_g, self.tau_m, self.tau_e, self.tau_i):
            raise ValueError("Time step exceeds 0.2 times the fastest time constant")
        for duration in (self.initialization_duration, self.rank_duration):
            n = duration / self.dt
            if round(n) < 1 or not np.isclose(n, round(n), rtol=0, atol=1e-9):
                raise ValueError("Durations must be integer multiples of dt")


@dataclass(frozen=True)
class Population:
    names: tuple
    raw_drive: np.ndarray
    rates: np.ndarray
    activity: np.ndarray

    def __post_init__(self):
        for name in ("raw_drive", "rates", "activity"):
            a = _array(getattr(self, name), (len(self.names),), nonnegative=name != "raw_drive")
            object.__setattr__(self, name, frozen(a))
        if not np.isclose(self.activity.sum(), 1):
            raise ValueError("Population activity must sum to one")


@dataclass(frozen=True)
class Encoding:
    direction: Population
    step: Population
    joint: Population


@dataclass(frozen=True)
class NeuralState:
    e_rates: np.ndarray
    i_rate: float
    v_rates: np.ndarray
    g_rates: np.ndarray
    m_rates: np.ndarray
    encoding: Encoding
    rank: int = 1

    def __post_init__(self):
        for name, n in (("e_rates", 6), ("v_rates", 4), ("g_rates", 4), ("m_rates", 6)):
            object.__setattr__(self, name, frozen(_array(getattr(self, name), (n,), nonnegative=True)))
        if not np.isfinite(self.i_rate) or self.i_rate < 0:
            raise ValueError("Invalid I rate")
        if isinstance(self.rank, bool) or not isinstance(self.rank, Integral) or self.rank not in range(1, 5):
            raise ValueError("Require rank 1..4")


@dataclass
class Connections:
    e_to_branch: np.ndarray
    branch_to_m: np.ndarray
    rank_to_readout: np.ndarray
    readout_to_gate: np.ndarray
    gate_to_readout: np.ndarray
    gate_to_branch: np.ndarray

    @classmethod
    def build(cls, strength):
        a = np.zeros((4, 6, 6))
        for p, shift in enumerate(SHIFTS):
            for j in range(6):
                a[p, (j + shift) % 6, j] = 1
        w = np.zeros((3, 4, 4))
        for r in range(3):
            for j, (d, s) in enumerate(JOINT_PREFERENCES):
                shift = d * (s if r == 1 else 1)
                w[r, SHIFTS.index(shift), j] = 1
        return cls(a, np.repeat(np.eye(6)[None], 4, axis=0), w,
                   np.ones((4, 4)) - np.eye(4), -np.eye(4),
                   -strength * np.repeat(np.eye(4)[:, None, :], 6, axis=1))

    def validate(self):
        specs = (("e_to_branch", (4, 6, 6), 1), ("branch_to_m", (4, 6, 6), 1),
                 ("rank_to_readout", (3, 4, 4), 1), ("readout_to_gate", (4, 4), 1),
                 ("gate_to_readout", (4, 4), -1), ("gate_to_branch", (4, 6, 4), -1))
        for name, shape, sign in specs:
            a = _array(getattr(self, name), shape)
            if np.any(sign * a < 0):
                raise ValueError(f"Connection sign violation: {name}")


@dataclass(frozen=True)
class Transition:
    from_rank: int
    source_activity: np.ndarray
    readout_raw_drive: np.ndarray
    readout_drive: np.ndarray
    time: np.ndarray
    e_rates: np.ndarray
    i_rates: np.ndarray
    v_rates: np.ndarray
    g_rates: np.ndarray
    m_rates: np.ndarray
    readout_net_drive: np.ndarray
    gate_drive: np.ndarray
    branch_excitation: np.ndarray
    branch_inhibition: np.ndarray
    branch_target: np.ndarray
    pooled_drive: np.ndarray

    def __post_init__(self):
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, np.ndarray):
                object.__setattr__(self, item.name, frozen(value))


@dataclass(frozen=True)
class Decompression:
    positions: tuple
    position_activity: np.ndarray
    initial_state: NeuralState
    final_state: NeuralState
    transitions: tuple

    def __post_init__(self):
        object.__setattr__(self, "position_activity", frozen(self.position_activity))


class RateDecompressor:
    def __init__(self, params=None):
        self.params = params or ModelParameters()
        self.connections = Connections.build(self.params.gate_strength)
        self.site_angles = np.arange(6) * np.pi / 3
        self.site_coordinates = np.column_stack((np.cos(self.site_angles), -np.sin(self.site_angles)))
        self.position_names = tuple(f"E{k}" for k in range(1, 7))

    def _population(self, names, raw, target):
        p = self.params
        rates = np.asarray(target) * (-np.expm1(-p.encoding_duration / p.tau_tuning))
        return Population(tuple(names), raw, rates, normalize(rates))

    def encode_tuning(self, direction, step):
        CompressedCode(1, direction, step)
        p = self.params
        dr = p.direction_slope * direction * np.array([1, -1])
        sr = p.step_slope * (2 * step - 3) * np.array([-1, 1])
        d = self._population(("D_CW", "D_CCW"), dr,
                             np.asarray(p.direction_gains) * np.exp(-np.logaddexp(0, -dr)))
        s = self._population(("S1", "S2"), sr,
                             np.asarray(p.step_gains) * np.exp(-np.logaddexp(0, -sr)))
        jr = np.outer(d.activity, s.activity).reshape(4)
        j = self._population(tuple(f"J_{x}" for x in PATH_NAMES), jr,
                             np.asarray(p.joint_gains) * jr)
        return Encoding(d, s, j)

    def encode_angle(self, angle):
        if not np.isfinite(angle):
            raise ValueError("Angle must be finite")
        return normalize(np.exp(self.params.location_kappa * (np.cos(angle - self.site_angles) - 1)))

    def initialize(self, code):
        location, direction, step = code.location, code.direction, code.step
        CompressedCode(location, direction, step)
        return self.initialize_population(self.encode_angle(self.site_angles[location - 1]),
                                          self.encode_tuning(direction, step))

    def initialize_population(self, position_activity, encoding):
        self.connections.validate()
        drive = normalize(_array(position_activity, (6,), nonnegative=True))
        p = self.params
        e, i = np.zeros(6), 0.0
        for _ in range(round(p.initialization_duration / p.dt)):
            de = (-e + np.maximum(drive + p.w_ee * e - p.w_ei * i, 0)) / p.tau_e
            di = (-i + p.w_ie * e.sum()) / p.tau_i
            e, i = e + p.dt * de, i + p.dt * di
        return NeuralState(e, float(i), np.zeros(4), np.zeros(4), np.zeros(6), encoding)

    def readout_drive(self, state):
        if state.rank >= 4:
            raise ValueError("All three transitions are complete")
        raw = self.connections.rank_to_readout[state.rank - 1] @ state.encoding.joint.activity
        drive = np.asarray(self.params.readout_gains) * raw
        require_unique_drive(drive)
        return raw, drive

    def advance(self, state):
        """One external rank pulse. V/G/E/I carry; only M resets to zero."""
        self.connections.validate()
        raw, drive = self.readout_drive(state)
        p, c = self.params, self.connections
        h = normalize(state.e_rates)
        n = round(p.rank_duration / p.dt)
        e, i = np.empty((n + 1, 6)), np.empty(n + 1)
        v, g, m = np.empty((n + 1, 4)), np.empty((n + 1, 4)), np.empty((n + 1, 6))
        e[0], i[0], v[0], g[0], m[0] = state.e_rates, state.i_rate, state.v_rates, state.g_rates, 0
        net, gd, pooled = np.empty_like(v), np.empty_like(g), np.empty_like(m)
        excitation = np.einsum("pij,j->pi", c.e_to_branch, h)
        inhibition, target = np.empty((n + 1, 4, 6)), np.empty((n + 1, 4, 6))
        for k in range(n + 1):
            net[k] = drive + c.gate_to_readout @ g[k]
            gd[k] = c.readout_to_gate @ v[k]
            inhibition[k] = np.einsum("pjg,g->pj", c.gate_to_branch, g[k])
            target[k] = np.maximum(excitation + inhibition[k], 0)
            pooled[k] = np.einsum("pij,pj->i", c.branch_to_m, target[k])
            if k == n:
                break
            de = (-e[k] + np.maximum(m[k] + p.w_ee * e[k] - p.w_ei * i[k], 0)) / p.tau_e
            di = (-i[k] + p.w_ie * e[k].sum()) / p.tau_i
            dv = (-v[k] + np.maximum(net[k], 0)) / p.tau_v
            dg = (-g[k] + gd[k]) / p.tau_g
            dm = (-m[k] + pooled[k]) / p.tau_m
            e[k + 1] = e[k] + p.dt * de
            i[k + 1] = i[k] + p.dt * di
            v[k + 1] = v[k] + p.dt * dv
            g[k + 1] = g[k] + p.dt * dg
            m[k + 1] = m[k] + p.dt * dm
        following = NeuralState(e[-1], float(i[-1]), v[-1], g[-1], m[-1], state.encoding, state.rank + 1)
        trace = Transition(state.rank, h, raw, drive, np.arange(n + 1) * p.dt,
                           e, i, v, g, m, net, gd, excitation, inhibition, target, pooled)
        return following, trace

    def resume(self, state):
        initial, traces = state, []
        activity = [normalize(state.e_rates)]
        positions = [observed_peak(activity[0]) + 1]
        while state.rank < 4:
            state, trace = self.advance(state)
            traces.append(trace)
            activity.append(normalize(state.e_rates))
            positions.append(observed_peak(activity[-1]) + 1)
        return Decompression(tuple(positions), np.stack(activity), initial, state, tuple(traces))

    def decompress(self, code):
        return self.resume(self.initialize(code))
