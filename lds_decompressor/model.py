"""Explicit six-site L/D/S circuit, independent of all previous model packages.

W[post, pre]. Rates are nonnegative, dimensionless model activities; time is
in seconds. Fixed shifts and rank wiring encode the supplied task grammar.
This is a mechanism-sufficiency baseline, not learned geometry or attractor
evidence. No target sequence or evaluation module is available to this module.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from numbers import Integral

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]
PATH_NAMES = ("CW1", "CW2", "CCW1", "CCW2")
SHIFTS = (1, 2, -1, -2)
JOINT_PREFERENCES = ((1, 1), (1, 2), (-1, 1), (-1, 2))


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


def _peak(value) -> int:
    out = _array(value, nonnegative=True)
    largest = float(out.max())
    if largest <= 0 or np.count_nonzero(np.isclose(out, largest, rtol=1e-9, atol=1e-12)) != 1:
        raise ValueError("Activity has no unique positive peak")
    return int(np.argmax(out))


@dataclass(frozen=True)
class CompressedCode:
    """Only allowed symbolic input. L is a label 1..6, D is +/-1, S is 1/2."""

    location: int
    direction: int
    step: int

    def __post_init__(self):
        for value, allowed in ((self.location, range(1, 7)),
                               (self.direction, (-1, 1)), (self.step, (1, 2))):
            if isinstance(value, bool) or not isinstance(value, Integral) or value not in allowed:
                raise ValueError("Require integer L in 1..6, D in {-1,+1}, S in {1,2}")


@dataclass(frozen=True)
class ModelParameters:
    """Instance-local numerical choices; none are fitted to evaluation targets."""

    location_kappa: float = 8.0
    direction_slope: float = 6.0
    step_slope: float = 6.0
    direction_gains: tuple[float, float] = (1.0, 1.0)
    step_gains: tuple[float, float] = (1.0, 1.0)
    joint_gains: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    readout_gains: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    tau_tuning: float = 0.020
    tau_readout: float = 0.020
    tau_gate: float = 0.020
    tau_relay: float = 0.030
    tau_e: float = 0.100
    tau_i: float = 0.050
    encoding_duration: float = 0.200
    readout_duration: float = 0.200
    gate_duration: float = 0.200
    rank_duration: float = 0.800
    dt: float = 0.002
    w_ee: float = 0.15
    w_ei: float = 0.20
    w_ie: float = 0.25
    gate_strength: float = 2.0

    def __post_init__(self):
        nonnegative = {"w_ee", "w_ei", "w_ie", "gate_strength"}
        for item in fields(self):
            value = getattr(self, item.name)
            if item.name.endswith("_gains"):
                size = 2 if item.name in {"direction_gains", "step_gains"} else 4
                arr = _array(value, (size,), nonnegative=True)
                object.__setattr__(self, item.name, tuple(float(x) for x in arr))
            elif not np.isfinite(value) or value < 0 or (value == 0 and item.name not in nonnegative):
                raise ValueError(f"Invalid parameter {item.name}")
        if self.w_ee >= 1:
            raise ValueError("Require w_ee < 1 for this leaky E/I response layer")
        if self.dt > 0.2 * min(self.tau_e, self.tau_i, self.tau_relay):
            raise ValueError("dt must be <= 0.2 times the fastest integrated time constant")
        ratio = self.rank_duration / self.dt
        if round(ratio) < 1 or not np.isclose(ratio, round(ratio)):
            raise ValueError("rank_duration must be an integer multiple of dt")


@dataclass(frozen=True)
class Population:
    """Inspectable raw input, unnormalized rate, and sum-normalized activity."""

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


@dataclass(frozen=True)
class Encoding:
    direction: Population
    step: Population
    joint: Population


@dataclass(frozen=True)
class NeuralState:
    """Sufficient runtime state: activities only; no L/D/S labels or targets."""

    e_rates: Array
    i_rate: float
    encoding: Encoding
    rank: int = 1

    def __post_init__(self):
        object.__setattr__(self, "e_rates", _frozen(_array(self.e_rates, (6,), nonnegative=True)))
        if not np.isfinite(self.i_rate) or self.i_rate < 0:
            raise ValueError("i_rate must be finite and nonnegative")
        if isinstance(self.rank, bool) or not isinstance(self.rank, Integral) or self.rank not in range(1, 5):
            raise ValueError("rank must be 1..4")


@dataclass
class Connections:
    """Editable matrices, independently allocated for each model instance."""

    e_to_relay: Array        # [path, relay_site, source_E], nonnegative
    relay_to_e: Array        # [path, target_E, relay_site], nonnegative
    rank_to_displacement: Array  # [transition, displacement, joint], nonnegative
    winner_to_gate: Array    # [gate_I, winning_displacement], nonnegative
    gate_to_relay: Array     # [path, relay_site, gate_I], nonpositive

    @classmethod
    def build(cls, gate_strength: float):
        paths = np.zeros((4, 6, 6))
        for path, shift in enumerate(SHIFTS):
            for source in range(6):
                paths[path, (source + shift) % 6, source] = 1.0
        rank = np.zeros((3, 4, 4))
        for transition in range(3):
            for joint, (direction, step) in enumerate(JOINT_PREFERENCES):
                displacement = direction * (step if transition == 1 else 1)
                rank[transition, SHIFTS.index(displacement), joint] = 1.0
        return cls(
            paths, np.repeat(np.eye(6)[None], 4, axis=0), rank,
            np.ones((4, 4)) - np.eye(4),
            -gate_strength * np.repeat(np.eye(4)[:, None, :], 6, axis=1),
        )

    def validate(self):
        for name, shape in (("e_to_relay", (4, 6, 6)), ("relay_to_e", (4, 6, 6)),
                            ("rank_to_displacement", (3, 4, 4)),
                            ("winner_to_gate", (4, 4)), ("gate_to_relay", (4, 6, 4))):
            arr = _array(getattr(self, name), shape)
            if (name == "gate_to_relay" and np.any(arr > 0)) or (name != "gate_to_relay" and np.any(arr < 0)):
                raise ValueError(f"Connection sign violation in {name}")


@dataclass(frozen=True)
class Transition:
    from_rank: int
    source_activity: Array
    readout: Population
    selected_path: str
    selected_shift: int
    gate_target: Array
    gate_i_rates: Array
    relay_raw_drive: Array
    relay_inhibitory_drive: Array
    relay_target: Array
    time: Array
    relay_rates: Array
    e_drive: Array
    e_rates: Array
    i_rates: Array

    def __post_init__(self):
        for item in fields(self):
            if isinstance(getattr(self, item.name), np.ndarray):
                object.__setattr__(self, item.name, _frozen(getattr(self, item.name)))


@dataclass(frozen=True)
class Decompression:
    positions: tuple[int, ...]
    position_activity: Array
    initial_state: NeuralState
    final_state: NeuralState
    transitions: tuple[Transition, ...]

    def __post_init__(self):
        object.__setattr__(self, "position_activity", _frozen(self.position_activity))


class RateDecompressor:
    """Six position E groups, four shared relay paths, explicit inhibitory gates.

    External rank pulses select one of three connection slices. The model
    does not claim an autonomous rank clock or persistent symbolic memory.
    """

    def __init__(self, params: ModelParameters | None = None):
        self.params = params or ModelParameters()
        self.connections = Connections.build(self.params.gate_strength)
        # E1=(1,0); labels increase clockwise in Cartesian coordinates.
        self.site_angles = np.arange(6) * np.pi / 3
        self.site_coordinates = np.column_stack((np.cos(self.site_angles), -np.sin(self.site_angles)))
        self.position_names = tuple(f"E{i}" for i in range(1, 7))

    @staticmethod
    def _population(names, raw, target, duration, tau):
        # Exact solution of tau*dr/dt = -r + target, r(0)=0.
        rates = np.asarray(target) * (-np.expm1(-duration / tau))
        return Population(tuple(names), raw, rates, normalize(rates))

    def encode_tuning(self, direction: int, step: int) -> Encoding:
        # Validation uses a local code but no task sequence or start position.
        CompressedCode(1, direction, step)
        p = self.params
        d_raw = p.direction_slope * direction * np.array([1, -1])
        s_raw = p.step_slope * (2 * step - 3) * np.array([-1, 1])
        d = self._population(("D_CW", "D_CCW"), d_raw,
                             np.asarray(p.direction_gains) * np.exp(-np.logaddexp(0, -d_raw)),
                             p.encoding_duration, p.tau_tuning)
        s = self._population(("S1", "S2"), s_raw,
                             np.asarray(p.step_gains) * np.exp(-np.logaddexp(0, -s_raw)),
                             p.encoding_duration, p.tau_tuning)
        joint_raw = np.outer(d.activity, s.activity).reshape(4)
        joint = self._population(tuple(f"J_{name}" for name in PATH_NAMES), joint_raw,
                                 joint_raw * np.asarray(p.joint_gains),
                                 p.encoding_duration, p.tau_tuning)
        return Encoding(d, s, joint)

    def encode_angle(self, clockwise_angle: float) -> Array:
        """Diagnostic position tuning for any angle (radians), not a new L domain."""
        if not np.isfinite(clockwise_angle):
            raise ValueError("Angle must be finite")
        drive = np.exp(self.params.location_kappa * (np.cos(clockwise_angle - self.site_angles) - 1))
        return normalize(drive)

    def initialize(self, code: CompressedCode) -> NeuralState:
        # This is the ONLY reading of symbolic input in the inference path.
        location, direction, step = code.location, code.direction, code.step
        CompressedCode(location, direction, step)
        encoding = self.encode_tuning(direction, step)
        return self.initialize_population(self.encode_angle(self.site_angles[location - 1]), encoding)

    def initialize_population(self, position_activity, encoding: Encoding) -> NeuralState:
        """Initialize from E population for independent spatial/state probes."""
        source = normalize(_array(position_activity, (6,), nonnegative=True))
        self.connections.validate()
        _, e, i, _, _ = self._integrate_ei(source)
        return NeuralState(e[-1], float(i[-1]), encoding)

    def read_displacement(self, state: NeuralState) -> Population:
        if state.rank >= 4:
            raise ValueError("All three transitions have already been executed")
        self.connections.validate()
        p = self.params
        raw = self.connections.rank_to_displacement[state.rank - 1] @ state.encoding.joint.activity
        return self._population(tuple(f"DISP_{name}" for name in PATH_NAMES), raw,
                                raw * np.asarray(p.readout_gains),
                                p.readout_duration, p.tau_readout)

    def _integrate_ei(self, drive, initial_e=None, initial_i=0.0, *, relay_target=None):
        p = self.params
        steps = round(p.rank_duration / p.dt)
        time = np.arange(steps + 1, dtype=float) * p.dt
        es = np.zeros((steps + 1, 6))
        ins = np.zeros(steps + 1)
        relays = np.zeros((steps + 1, 4, 6))
        drives = np.zeros_like(es)
        es[0] = np.zeros(6) if initial_e is None else initial_e
        ins[0] = initial_i
        for k in range(steps):
            if relay_target is not None:
                drives[k] = np.einsum("pij,pj->i", self.connections.relay_to_e, relays[k])
            else:
                drives[k] = drive
            e_target = np.maximum(drives[k] + p.w_ee * es[k] - p.w_ei * ins[k], 0)
            i_target = p.w_ie * float(es[k].sum())
            es[k + 1] = es[k] + p.dt / p.tau_e * (e_target - es[k])
            ins[k + 1] = ins[k] + p.dt / p.tau_i * (i_target - ins[k])
            if relay_target is not None:
                relays[k + 1] = relays[k] + p.dt / p.tau_relay * (relay_target - relays[k])
        drives[-1] = (drive if relay_target is None else
                      np.einsum("pij,pj->i", self.connections.relay_to_e, relays[-1]))
        return time, es, ins, relays, drives

    def advance(self, state: NeuralState) -> tuple[NeuralState, Transition]:
        """One rank pulse; only neural state and instance wiring are available."""
        readout = self.read_displacement(state)
        winner = _peak(readout.activity)
        pulse = np.zeros(4)
        pulse[winner] = 1.0
        gate_target = self.connections.winner_to_gate @ pulse
        p = self.params
        gate_rates = gate_target * (-np.expm1(-p.gate_duration / p.tau_gate))
        source = normalize(state.e_rates)
        raw = np.einsum("pij,j->pi", self.connections.e_to_relay, source)
        inhibition = np.einsum("pjg,g->pj", self.connections.gate_to_relay, gate_rates)
        target = np.maximum(raw + inhibition, 0)
        time, e, i, relay, drive = self._integrate_ei(
            None, state.e_rates, state.i_rate, relay_target=target)
        following = NeuralState(e[-1], float(i[-1]), state.encoding, state.rank + 1)
        trace = Transition(state.rank, source, readout, PATH_NAMES[winner], SHIFTS[winner],
                           gate_target, gate_rates, raw, inhibition, target,
                           time, relay, drive, e, i)
        return following, trace

    def resume(self, state: NeuralState) -> Decompression:
        """Run remaining external rank pulses; accepts no symbolic code/targets."""
        initial = state
        activities = [normalize(state.e_rates)]
        positions = [_peak(activities[0]) + 1]
        transitions = []
        while state.rank < 4:
            state, trace = self.advance(state)
            transitions.append(trace)
            activities.append(normalize(state.e_rates))
            positions.append(_peak(activities[-1]) + 1)
        return Decompression(tuple(positions), np.stack(activities), initial, state, tuple(transitions))

    def decompress(self, code: CompressedCode) -> Decompression:
        return self.resume(self.initialize(code))
