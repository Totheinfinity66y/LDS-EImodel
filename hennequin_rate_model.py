"""Rate-unit network from Hennequin et al., Neuron 2014.

W[i, j] is the connection from presynaptic unit j to postsynaptic unit i.
The first half of columns are excitatory; the second half inhibitory.
Time is expressed in seconds and rates in Hz. See MODEL.md for the source
equations and the distinctions between paper settings and numerical choices.
"""

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import solve_continuous_lyapunov


Array = NDArray[np.float64]


@dataclass(frozen=True)
class RateParameters:
    tau: float = 0.200
    r0: float = 5.0
    r_max: float = 100.0
    tau_noise: float = 0.050
    sigma0: float = 0.2

    def __post_init__(self) -> None:
        if self.tau <= 0 or self.tau_noise <= 0:
            raise ValueError("Time constants must be positive")
        if self.r0 <= 0 or self.r_max <= self.r0 or self.sigma0 < 0:
            raise ValueError("Require 0 < r0 < r_max and sigma0 >= 0")

    @property
    def noise_variance(self) -> float:
        # Paper: Var[xi] = sigma0^2 (tau + tau_noise) / tau_noise.
        return self.sigma0**2 * (self.tau + self.tau_noise) / self.tau_noise


@dataclass(frozen=True)
class Simulation:
    time: Array
    potential: Array
    rate_deviation: Array
    firing_rate: Array
    noise: Array


@dataclass(frozen=True)
class SOCResult:
    weights: Array
    spectral_abscissa: Array
    converged: bool


def gain(x: Array, params: RateParameters = RateParameters()) -> Array:
    """Equation 2: firing-rate deviation from the baseline r0."""
    x = np.asarray(x, dtype=float)
    return np.where(
        x < 0,
        params.r0 * np.tanh(x / params.r0),
        (params.r_max - params.r0) * np.tanh(x / (params.r_max - params.r0)),
    )


def _check_weights(weights: Array) -> Array:
    w = np.asarray(weights, dtype=float)
    if w.ndim != 2 or w.shape[0] != w.shape[1] or w.shape[0] % 2:
        raise ValueError("W must be an even-sized square matrix")
    if not np.all(np.isfinite(w)):
        raise ValueError("W must contain finite values")
    return w


def rate_rhs(
    x: Array,
    weights: Array,
    external: Array | float = 0.0,
    params: RateParameters = RateParameters(),
    *,
    linear: bool = False,
) -> Array:
    """Equation 1: dx/dt = (-x + I + W @ Delta_r) / tau."""
    w = _check_weights(weights)
    x = np.asarray(x, dtype=float)
    external = np.asarray(external, dtype=float)
    if x.shape != (w.shape[0],) or external.shape not in [(), x.shape]:
        raise ValueError("x and external must match W's unit count")
    delta_r = x if linear else gain(x, params)
    return (-x + external + w @ delta_r) / params.tau


def random_balanced_weights(
    n: int = 200,
    *,
    density: float = 0.1,
    gamma: float = 3.0,
    radius: float = 10.0,
    seed: int | None = None,
) -> Array:
    """Paper's sparse E/I reference network before inhibitory optimization.

    The paper calls `radius` the desired random-bulk spectral radius; this
    formula does not force the measured spectral radius of a finite sample.
    """
    if n < 2 or n % 2 or not 0 < density < 1 or gamma <= 0 or radius <= 0:
        raise ValueError("Require even n >= 2, 0 < density < 1, gamma, radius > 0")
    rng = np.random.default_rng(seed)
    w0 = radius / np.sqrt(density * (1 - density) * (1 + gamma**2) / 2)
    present = rng.random((n, n)) < density
    w = np.empty((n, n), dtype=float)
    w[:, : n // 2] = present[:, : n // 2] * w0 / np.sqrt(n)
    w[:, n // 2 :] = present[:, n // 2 :] * (-gamma * w0 / np.sqrt(n))
    return w


def spectral_abscissa(weights: Array) -> float:
    return float(np.max(np.linalg.eigvals(_check_weights(weights)).real))


def _lyapunov_pair(weights: Array, shift: float) -> tuple[Array, Array]:
    """Supplement Equations 8 and 11 for Q(s) and P(s)."""
    a = weights - shift * np.eye(weights.shape[0])
    rhs = -2 * np.eye(weights.shape[0])
    q = solve_continuous_lyapunov(a.T, rhs)
    p = solve_continuous_lyapunov(a, rhs)
    return q, p


def preferred_initial_states(weights: Array) -> tuple[Array, Array]:
    """Unit-norm initial states and energies, ordered by decreasing energy.

    Only defined for linearly stable free dynamics: max Re eig(W) < 1.
    The returned columns are the preferred states a_k; Q eigenvalues are E(a_k).
    """
    w = _check_weights(weights)
    if spectral_abscissa(w) >= 1:
        raise ValueError("Preferred-state energy requires max Re eig(W) < 1")
    q, _ = _lyapunov_pair(w, 1.0)
    energies, states = np.linalg.eigh((q + q.T) / 2)
    order = np.argsort(energies)[::-1]
    return states[:, order], energies[order]


def optimize_inhibition(
    initial_weights: Array,
    *,
    gamma: float = 3.0,
    inhibitory_density: float = 0.4,
    learning_rate: float = 10.0,
    c: float = 1.5,
    margin: float = 0.2,
    max_iterations: int = 400,
    tolerance: float = 1e-4,
    patience: int = 5,
    seed: int | None = None,
) -> SOCResult:
    """Supplement 3.2: constrained inhibitory SSA gradient descent.

    Fixed excitatory weights; inhibitory sign, block means and number of
    tagged inhibitory connections per row are enforced after each update.
    `converged` reports spectral-abscissa plateau, not a guarantee of stability.
    """
    w = _check_weights(initial_weights).copy()
    n = w.shape[0]
    half = n // 2
    if np.any(w[:, :half] < 0) or np.any(w[:, half:] > 0):
        raise ValueError("W violates Dale's column signs")
    if not 0 < inhibitory_density <= 1 or gamma <= 0 or learning_rate <= 0:
        raise ValueError("Invalid density, gamma or learning rate")
    if c <= 1 or margin <= 0 or max_iterations < 1 or tolerance < 0 or patience < 1:
        raise ValueError("Invalid optimization controls")

    rng = np.random.default_rng(seed)
    target = round(inhibitory_density * half)
    if target < 1:
        raise ValueError("Inhibitory density tags fewer than one synapse per row")
    tagged = np.zeros((n, half), dtype=bool)
    for row in range(n):
        existing = np.flatnonzero(w[row, half:] < 0)
        if len(existing) > target:
            raise ValueError("Initial inhibitory row exceeds requested density")
        tagged[row, existing] = True
        absent = np.flatnonzero(~tagged[row])
        tagged[row, rng.choice(absent, size=target - len(existing), replace=False)] = True

    history = [spectral_abscissa(w)]
    stable_count = 0
    for _ in range(max_iterations):
        alpha = history[-1]
        shift = max(c * alpha, alpha + margin)
        q, p = _lyapunov_pair(w, shift)
        product = q @ p
        gradient = product / np.trace(product)
        inhibitory = w[:, half:]
        inhibitory[tagged] -= learning_rate * gradient[:, half:][tagged]
        np.minimum(inhibitory, 0, out=inhibitory)

        # Equation 12: normalize I->E and I->I blocks separately. Means
        # include absent synapses, exactly as the source's block averages do.
        for rows in (slice(0, half), slice(half, n)):
            e_mean = w[rows, :half].mean()
            i_mean = inhibitory[rows].mean()
            if e_mean <= 0 or i_mean >= 0:
                raise ValueError("Cannot preserve E/I block-mean ratio")
            inhibitory[rows] *= -gamma * e_mean / i_mean

        # Replace tagged synapses clipped to zero with random empty sites.
        for row in range(n):
            lost = np.flatnonzero(tagged[row] & (inhibitory[row] == 0))
            if len(lost):
                tagged[row, lost] = False
                candidates = np.flatnonzero(~tagged[row] & ~np.isin(np.arange(half), lost))
                fresh = rng.choice(candidates, size=min(len(lost), len(candidates)), replace=False)
                tagged[row, fresh] = True
                if len(fresh) < len(lost):
                    # At unusually high requested densities there may be too
                    # few new sites; keep the remaining zero-valued old tags.
                    retained = rng.choice(lost, size=len(lost) - len(fresh), replace=False)
                    tagged[row, retained] = True

        next_alpha = spectral_abscissa(w)
        history.append(next_alpha)
        stable_count = stable_count + 1 if abs(next_alpha - alpha) <= tolerance else 0
        if stable_count >= patience:
            break
    return SOCResult(w, np.asarray(history), stable_count >= patience)


def simulate(
    weights: Array,
    duration: float,
    *,
    dt: float = 0.001,
    initial_potential: Array | None = None,
    stimulus: Callable[[float], Array] | None = None,
    noise: bool = False,
    seed: int | None = None,
    params: RateParameters = RateParameters(),
    linear: bool = False,
) -> Simulation:
    """RK4 for Equation 1; exact-in-time OU updates at each fixed step.

    The noise value is held constant within a step's RK4 stages. This is an
    explicit numerical convention; the paper does not specify the OU stepper.
    """
    w = _check_weights(weights)
    n = w.shape[0]
    if duration <= 0 or dt <= 0:
        raise ValueError("duration and dt must be positive")
    steps = round(duration / dt)
    if steps < 1 or not np.isclose(steps * dt, duration):
        raise ValueError("duration must be an integer multiple of dt")
    x = np.zeros(n) if initial_potential is None else np.asarray(initial_potential, dtype=float).copy()
    if x.shape != (n,):
        raise ValueError("initial_potential must have one value per unit")
    rng = np.random.default_rng(seed)
    variance = params.noise_variance
    xi = rng.normal(scale=np.sqrt(variance), size=n) if noise else np.zeros(n)
    time = np.arange(steps + 1, dtype=float) * dt
    potentials = np.empty((steps + 1, n))
    deviations = np.empty_like(potentials)
    noises = np.empty_like(potentials)
    decay = np.exp(-dt / params.tau_noise)
    innovation_sd = np.sqrt(variance * (1 - decay**2))

    def drive(t: float) -> Array:
        if stimulus is None:
            return xi
        s = np.asarray(stimulus(t), dtype=float)
        if s.shape != (n,):
            raise ValueError("stimulus must return one value per unit")
        return xi + s

    for step, t in enumerate(time):
        potentials[step] = x
        deviations[step] = x if linear else gain(x, params)
        noises[step] = xi
        if step == steps:
            break
        k1 = rate_rhs(x, w, drive(t), params, linear=linear)
        k2 = rate_rhs(x + dt * k1 / 2, w, drive(t + dt / 2), params, linear=linear)
        k3 = rate_rhs(x + dt * k2 / 2, w, drive(t + dt / 2), params, linear=linear)
        k4 = rate_rhs(x + dt * k3, w, drive(t + dt), params, linear=linear)
        x += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        if noise:
            xi = decay * xi + innovation_sd * rng.standard_normal(n)
    return Simulation(time, potentials, deviations, params.r0 + deviations, noises)
