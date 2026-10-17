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

from .core import (
    Array, PATH_NAMES, SHIFTS, JOINT_PREFERENCES, UNIT_GROUPS,
    CompressedCode, ModelParameters, Connections, Population,
    _array, _frozen, normalize,
)
from .neurons import (
    Neurons, ENeurons, INeurons, DNeurons, SNeurons, JNeurons, VNeurons, RelayNeurons,
)
from .timeline import RateRecording


def _peak(value) -> int:
    out = _array(value, nonnegative=True)
    largest = float(out.max())
    if largest <= 0 or np.count_nonzero(np.isclose(out, largest, rtol=1e-9, atol=1e-12)) != 1:
        raise ValueError("Activity has no unique positive peak")
    return int(np.argmax(out))


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
        object.__setattr__(self, "e_rates", _frozen(self.e_rates, (6,), nonnegative=True))
        if not np.isfinite(self.i_rate) or self.i_rate < 0:
            raise ValueError("i_rate must be finite and nonnegative")
        if isinstance(self.rank, bool) or not isinstance(self.rank, Integral) or self.rank not in range(1, 5):
            raise ValueError("rank must be 1..4")


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
    relay_path_targets: Array  # [4, 6] static gated inputs, not dynamic rates
    relay_target: Array
    time: Array
    relay_rates: Array
    e_drive: Array
    e_rates: Array
    i_rates: Array
    recording: RateRecording

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

    @property
    def recording(self) -> RateRecording:
        return RateRecording.concatenate(tuple(t.recording for t in self.transitions))


class RateDecompressor:
    """Six position E groups, six summed relay states, four gated input paths.

    External rank pulses select one of three connection slices. The model
    does not claim an autonomous rank clock or persistent symbolic memory.
    """

    def __init__(self, params: ModelParameters | None = None):
        self.params = params or ModelParameters()
        self.connections = Connections.build(self.params.gate_strength)
        p = self.params
        self.e, self.i = ENeurons(p), INeurons(p)
        self.d, self.s, self.j = DNeurons(p), SNeurons(p), JNeurons(p)
        self.v, self.gate_i, self.relay = VNeurons(p), INeurons(p, gate=True), RelayNeurons(p)
        self.neurons: dict[str, Neurons] = {
            group.name: getattr(self, group.attribute) for group in UNIT_GROUPS
        }
        self.site_angles = self.e.site_angles
        self.site_coordinates = self.e.site_coordinates
        self.position_names = self.e.names

    @property
    def rate_potentials(self) -> Array:
        """All 29 current raw rates, in ``unit_names`` order; safe to print."""
        return _frozen(np.concatenate([n.rate_potentials for n in self.neurons.values()]))

    @property
    def unit_names(self):
        return tuple(name for n in self.neurons.values() for name in n.names)

    def _restore_encoding(self, encoding):
        self.d.restore(encoding.direction)
        self.s.restore(encoding.step)
        self.j.restore(encoding.joint)

    def encode_tuning(self, direction: int, step: int) -> Encoding:
        # Validation uses a local code but no task sequence or start position.
        CompressedCode(1, direction, step)
        d = self.d.encode(direction)
        s = self.s.encode(step)
        joint = self.j.encode(d.activity, s.activity)
        return Encoding(d, s, joint)

    def encode_angle(self, clockwise_angle: float) -> Array:
        """Diagnostic position tuning for any angle (radians), not a new L domain."""
        return self.e.encode_angle(clockwise_angle)

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
        self._restore_encoding(encoding)
        self.v.initialize()
        self.gate_i.initialize()
        _, e, i, _, _ = self._integrate_ei(source)
        return NeuralState(e[-1], float(i[-1]), encoding)

    def read_displacement(self, state: NeuralState) -> Population:
        if state.rank >= 4:
            raise ValueError("All three transitions have already been executed")
        self.connections.validate()
        return self.v.read(self.connections.rank_to_displacement[state.rank - 1],
                           state.encoding.joint.activity)

    def _integrate_ei(self, drive, initial_e=None, initial_i=0.0, *, relay_target=None):
        p = self.params
        steps = round(p.rank_duration / p.dt)
        time = np.arange(steps + 1, dtype=float) * p.dt
        self.e.initialize(initial_e)
        self.i.initialize([initial_i])
        self.relay.initialize()
        drives = np.zeros((steps + 1, 6))
        for k in range(steps):
            if relay_target is not None:
                drives[k] = self.relay.rates
            else:
                drives[k] = drive
            # Compute both targets before either step: synchronous Euler.
            e_target = self.e.target(drives[k], float(self.i.rates[0]))
            i_target = self.i.feedback_target(self.e.rates)
            self.e.step(e_target, p.dt)
            self.i.step(i_target, p.dt)
            if relay_target is not None:
                self.relay.step(relay_target, p.dt)
            else:
                # During initialization these unused paths remain exactly zero.
                self.relay.hold()
        es = self.e.history
        ins = self.i.history[:, 0]
        relays = self.relay.history
        drives[-1] = drive if relay_target is None else relays[-1]
        return time, es, ins, relays, drives

    def _record_rates(self, time, e, i, relay):
        """Record all current neuron values; plotting never constructs rates."""
        samples = {name: neurons.rates for name, neurons in self.neurons.items()}
        samples.update({"Position E": e, "Relay": relay,
                        "Global I": i[:, None]})
        return RateRecording.from_groups(time, samples)

    def advance(self, state: NeuralState) -> tuple[NeuralState, Transition]:
        """One rank pulse; only neural state and instance wiring are available."""
        self._restore_encoding(state.encoding)
        readout = self.read_displacement(state)
        winner = _peak(readout.activity)
        pulse = np.zeros(4)
        pulse[winner] = 1.0
        gate_target = self.connections.winner_to_gate @ pulse
        gate_rates = self.gate_i.gate(gate_target)
        source = normalize(state.e_rates)
        raw, inhibition, path_targets, target = self.relay.target(
            source, self.connections.e_to_relay, gate_rates, self.connections.gate_to_relay,
            self.connections.relay_to_e)
        time, e, i, relay, drive = self._integrate_ei(
            None, state.e_rates, state.i_rate, relay_target=target)
        following = NeuralState(e[-1], float(i[-1]), state.encoding, state.rank + 1)
        trace = Transition(state.rank, source, readout, PATH_NAMES[winner], SHIFTS[winner],
                           gate_target, gate_rates, raw, inhibition, path_targets, target,
                           time, relay, drive, e, i, self._record_rates(time, e, i, relay))
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
