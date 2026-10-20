"""Positive coincidence gating and branch-owned spatial state.

No imports from the old model or evaluator. No targets, branch argmax,
symbolic direction lookup, or symbolic step lookup in state propagation.
Units are nonnegative dimensionless population rates, not individual cells.
"""
from dataclasses import dataclass
from numbers import Integral
import numpy as np

BRANCH_COUNTS = (1, 2, 4, 4)
PREFERENCES = ((1, 1), (1, 2), (-1, 1), (-1, 2))
OFFSETS = (0, 6, 18, 42, 66)


def frozen(value):
    result = np.array(value, dtype=float, copy=True)
    result.setflags(write=False)
    return result


def bounded(value, shape):
    result = frozen(value)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"Require finite array of shape {shape}")
    if np.any(result < 0) or np.any(result > 1 + 1e-12):
        raise ValueError("Rates must lie in [0,1] for the threshold-gate contract")
    return result


@dataclass(frozen=True)
class Code:
    location: int
    direction: int
    step: int

    def __post_init__(self):
        for value, domain in ((self.location, range(1, 7)),
                              (self.direction, (-1, 1)), (self.step, (1, 2))):
            if isinstance(value, bool) or not isinstance(value, Integral) or value not in domain:
                raise ValueError("Require integer L=1..6, D=+/-1, S=1/2")


@dataclass(frozen=True)
class Parameters:
    dt: float = .002
    tau: float = .05
    duration: float = .5

    def __post_init__(self):
        if not all(np.isfinite(x) and x > 0 for x in (self.dt, self.tau, self.duration)):
            raise ValueError("Positive finite timing required")
        if self.dt > .2 * self.tau or self.duration < self.dt:
            raise ValueError("Require dt<=tau/5 and duration>=dt")
        if not np.isclose(self.duration / self.dt, round(self.duration / self.dt)):
            raise ValueError("Duration must be an integer multiple of dt")


@dataclass(frozen=True)
class State:
    rank: int
    response: np.ndarray
    direction_cue: np.ndarray | None = None
    step_cue: np.ndarray | None = None

    def __post_init__(self):
        if isinstance(self.rank, bool) or not isinstance(self.rank, Integral) or self.rank not in range(1, 5):
            raise ValueError("Rank must be 1..4")
        object.__setattr__(self, "response", bounded(self.response, (BRANCH_COUNTS[self.rank-1], 6)))
        for name, required in (("direction_cue", self.rank == 1), ("step_cue", self.rank <= 2)):
            value = getattr(self, name)
            if required:
                if value is None:
                    raise ValueError(f"Pending {name} required at rank {self.rank}")
                object.__setattr__(self, name, bounded(value, (2,)))
            elif value is not None:
                raise ValueError(f"Consumed {name} is forbidden at rank {self.rank}")

    def embedded(self):
        """Current-rank response in the common 66-unit ambient population.

        Old rank blocks are not accumulated: this is an epoch-end embedding.
        Transition traces separately retain the held source and rising target.
        """
        out = np.zeros(66)
        out[OFFSETS[self.rank-1]:OFFSETS[self.rank]] = self.response.ravel()
        return out


@dataclass(frozen=True)
class Trace:
    source_rank: int
    time: np.ndarray
    source: np.ndarray
    content: np.ndarray
    control: np.ndarray
    drive: np.ndarray
    target_rates: np.ndarray

    def __post_init__(self):
        for name in ("time", "source", "content", "control", "drive", "target_rates"):
            object.__setattr__(self, name, frozen(getattr(self, name)))


def decode(state):
    """Output-only decoder. Silence/ties are failures, never valid locations."""
    activity = state.response.sum(axis=0)
    largest = activity.max()
    if largest <= 1e-12 or np.count_nonzero(np.isclose(activity, largest, atol=1e-10, rtol=1e-9)) != 1:
        return None
    return int(np.argmax(activity)) + 1


def shift_matrix(shift):
    return np.roll(np.eye(6), shift, axis=0)


class BranchModel:
    """Externally clocked, hand-wired response hierarchy with no hidden cache.

    Source response is maintained during each external rank pulse (ideal
    unit-gain recurrent hold: tau*dx/dt=-x+x=0). Destination starts at zero,
    tau*dy/dt=-y+drive, integrated using forward Euler. At pulse end the old
    source is released. This is staged dynamics, not a robust attractor or
    a simultaneous autonomous full-population simulation.
    """
    def __init__(self, params=None):
        self.params = params or Parameters()
        # [destination branch, source branch, destination site, source site]
        self.weights = [np.zeros((2, 1, 6, 6)), np.zeros((4, 2, 6, 6)),
                        np.zeros((4, 4, 6, 6))]
        for b, direction in enumerate((1, -1)):
            self.weights[0][b, 0] = shift_matrix(direction)
        for b, (direction, step) in enumerate(PREFERENCES):
            self.weights[1][b, b // 2] = shift_matrix(direction * step)
            self.weights[2][b, b] = shift_matrix(direction)

    def initialize(self, code):
        Code(code.location, code.direction, code.step)
        theta = (code.location - 1) * np.pi / 3
        # Baseline-shifted cosine: centered spatial variance is exactly 2D.
        location = .5 + .5 * np.cos(np.arange(6) * np.pi / 3 - theta)
        direction = np.array([code.direction == 1, code.direction == -1], float)
        step = np.array([code.step == 1, code.step == 2], float)
        return State(1, location[None], direction, step)

    @staticmethod
    def activate(content, control):
        """Excitatory content + excitatory control - fixed intrinsic threshold.

        For content in [0,1], no control => zero; unit control => content;
        control alone => zero. The -1 is a threshold, not an I-neuron drive.
        """
        return np.maximum(content + np.asarray(control)[:, None] - 1., 0.)

    def advance(self, state):
        if state.rank == 4:
            raise ValueError("R4 is terminal")
        index = state.rank - 1
        w = self.weights[index]
        expected = (BRANCH_COUNTS[index+1], BRANCH_COUNTS[index], 6, 6)
        if w.shape != expected or not np.isfinite(w).all() or np.any(w < 0):
            raise ValueError("Require finite nonnegative connection matrices")
        content = np.einsum("bsij,sj->bi", w, state.response)
        if np.any(content > 1 + 1e-12):
            raise ValueError("Intervention violates bounded content contract")
        if state.rank == 1:
            control = state.direction_cue
            drive = self.activate(content, control)
        elif state.rank == 2:
            control = np.tile(state.step_cue, 2)
            drive = self.activate(content, control)
        else:
            # Branch-specific positive wiring carries both D and S implicitly.
            control = np.zeros(4)
            drive = content
        p = self.params
        count = round(p.duration / p.dt)
        rates = np.zeros((count+1, *drive.shape))
        for k in range(count):
            rates[k+1] = rates[k] + p.dt / p.tau * (-rates[k] + drive)
        following = State(state.rank+1, rates[-1], None,
                          state.step_cue if state.rank == 1 else None)
        trace = Trace(state.rank, np.arange(count+1)*p.dt, state.response,
                      content, control, drive, rates)
        return following, trace

    def resume(self, state):
        states, traces = [state], []
        while state.rank < 4:
            state, trace = self.advance(state)
            states.append(state)
            traces.append(trace)
        return tuple(states), tuple(traces)

    def run(self, code):
        return self.resume(self.initialize(code))
