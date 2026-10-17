"""Static circuit specification and shared immutable value contracts.

No neuron dynamics, runtime state, evaluation targets or plotting dependencies.
Connection matrices remain editable and are allocated separately per instance.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from numbers import Integral

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]
# Each path binds its name, ring displacement and joint preference together.
PATH_DEFINITIONS = (("CW1", 1, (1, 1)), ("CW2", 2, (1, 2)),
                    ("CCW1", -1, (-1, 1)), ("CCW2", -2, (-1, 2)))
PATH_NAMES = tuple(path[0] for path in PATH_DEFINITIONS)
SHIFTS = tuple(path[1] for path in PATH_DEFINITIONS)
JOINT_PREFERENCES = tuple(path[2] for path in PATH_DEFINITIONS)


@dataclass(frozen=True)
class UnitGroup:
    """Canonical column order shared by neurons, recordings and legacy import."""

    name: str
    attribute: str
    labels: tuple[str, ...]
    mode: str = "held"

    @property
    def groups(self):
        return (self.name,) * len(self.labels)


UNIT_GROUPS = (
    UnitGroup("Position E", "e", tuple(f"E{k}" for k in range(1, 7)), "integrated"),
    UnitGroup("Direction", "d", ("D_CW", "D_CCW")),
    UnitGroup("Step", "s", ("S1", "S2")),
    UnitGroup("Joint", "j", tuple(f"J_{p}" for p in PATH_NAMES)),
    UnitGroup("Displacement", "v", tuple(f"DISP_{p}" for p in PATH_NAMES)),
    UnitGroup("Gate I", "gate_i", tuple(f"I_gate_{p}" for p in PATH_NAMES)),
    UnitGroup("Relay", "relay", tuple(f"M{k}" for k in range(1, 7)), "integrated"),
    UnitGroup("Global I", "i", ("I_global",), "integrated"),
)


def unit_names(attribute):
    return next(group.labels for group in UNIT_GROUPS if group.attribute == attribute)


def _array(value, shape=None, *, nonnegative=False) -> Array:
    out = np.array(value, dtype=float, copy=True)
    if shape is not None and out.shape != shape:
        raise ValueError(f"Expected shape {shape}, got {out.shape}")
    if not np.isfinite(out).all() or (nonnegative and np.any(out < 0)):
        raise ValueError("Activity must be finite and, where required, nonnegative")
    return out


def _frozen(value, shape=None, *, nonnegative=False) -> Array:
    out = _array(value, shape, nonnegative=nonnegative)
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
            object.__setattr__(self, name, _frozen(
                getattr(self, name), (n,), nonnegative=name != "raw_drive"))
        if not np.isclose(self.activity.sum(), 1):
            raise ValueError("Population activity must sum to one")


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


@dataclass
class Connections:
    """Editable matrices, independently allocated for each model instance."""

    e_to_relay: Array        # [path, relay_site, source_E], nonnegative
    relay_to_e: Array        # [path, target_E, relay_site]; projects input before aggregation
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
