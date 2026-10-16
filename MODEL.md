# Hennequin et al. (Neuron, 2014): rate-unit model

This implementation follows the rate-network definitions in the supplied
[paper, “SOCs” and “Network Setup and Dynamics”](hennequin-neuron-2014-paper/references/paper.md)
and [supplement, §3.1–3.2](hennequin-neuron-2014-paper/references/supplement.md).
The source equations are preserved as images in that paper skill; the formulas
below transcribe those images. The [Python implementation](hennequin_rate_model.py)
uses seconds for time, Hz for potentials and firing-rate deviations, and
`W[i, j]` for the synapse from neuron `j` to neuron `i`.

## State and firing rate

For the paper's `N = 200` units (`100 E + 100 I`), Equation 1 is

\[
\tau\frac{d\mathbf{x}}{dt}
=-\mathbf{x}(t)+\mathbf{I}(t)+\mathbf{W}\,\Delta\mathbf{r}(\mathbf{x},t),
\qquad \mathbf{I}(t)=\boldsymbol\xi(t)+\mathbf{S}(t),
\qquad \tau=0.200\;\mathrm{s}.
\]

Here `x_i` is a potential, `Δr_i = g(x_i)` is the deviation from the
spontaneous firing rate, and the absolute firing rate is `r_i = r₀ + Δr_i`.
Equation 2 defines the piecewise saturating gain:

\[
g(x)=\begin{cases}
r_0\tanh(x/r_0),&x<0,\\
(r_{\max}-r_0)\tanh[x/(r_{\max}-r_0)],&x\geq0,
\end{cases}
\qquad r_0=5\;\mathrm{Hz},\quad r_{\max}=100\;\mathrm{Hz}.
\]

For linear analysis only, `Δr = x`. The default simulation uses the nonlinear
gain and fourth-order Runge–Kutta, as stated in Experimental Procedures.

Each `ξ_i` is an independent Ornstein–Uhlenbeck input with correlation time
`τξ = 0.050 s` and stationary variance
`Var(ξ_i) = σ₀²(τ + τξ)/τξ`, with `σ₀ = 0.2 Hz`.
The paper gives the correlation time and stationary variance, but does not
specify the discrete noise update. Here an exact OU transition is taken each
`dt` and its current value is held fixed during that step's RK4 stages.
Noise is optional, so autonomous transients can be studied without it.

## Connectivity and SOC construction

The first `N/2` columns of `W` are excitatory and nonnegative; the last
`N/2` are inhibitory and nonpositive (Dale's principle). The initial random
network has independent connection probability `p = 0.1` and nonzero weights

\[
W_{ij}^{E}=\frac{w_0}{\sqrt N},\qquad
W_{ij}^{I}=-\frac{\gamma w_0}{\sqrt N},\qquad
w_0=\frac{R}{\sqrt{p(1-p)(1+\gamma^2)/2}},
\]

with `γ = 3`, `R = 10`. `R` is the target *random-bulk* spectral radius,
not a guarantee that any finite sample has exactly that measured radius.

The SOC procedure in supplement §3.2 freezes the excitatory columns and
minimizes a smoothed spectral abscissa by changing only inhibitory synapses.
Let `α(W) = max Re eig(W)` and choose the shifted value used by the authors'
simplified algorithm, `s = max(1.5 α(W), α(W) + 0.2)`. For `A = W − sI`,
the supplement's Equations 8, 9 and 11 are

\[
A^\top Q+QA=-2I,\qquad AP+PA^\top=-2I,\qquad
\frac{\partial\widetilde\alpha_\epsilon}{\partial W}
=\frac{QP}{\operatorname{tr}(QP)}.
\]

The implementation updates tagged inhibitory sites with learning rate `η=10`,
clips any positive inhibitory weight to zero, rescales `I→E` and `I→I`
blocks separately so that their all-entry mean magnitude is `γ` times the
corresponding excitatory block mean, and replaces clipped tagged connections
with randomly selected empty sites. There are `40%` tagged inhibitory sites
per postsynaptic row; some tagged weights can be zero. A reported
`converged=True` means a plateau in `α(W)` at the selected tolerance, **not**
proof that `α(W)<1` or that the published SOC matrix was recovered. The
paper's original random seed, optimized weight matrix, and exact stopping
criterion are not supplied.

## Preferred initial states

In the linear, noise-free system, free dynamics obey
`τ dΔr/dt = (W − I)Δr`. For a unit-norm initial condition `a`, the
paper's evoked energy is

\[
\mathcal E(a)=\frac{2}{\tau}\int_0^\infty
\|\Delta r(t)\|^2dt=a^\top Q(1)a,
\qquad (W-I)^\top Q(1)+Q(1)(W-I)=-2I.
\]

The eigenvectors of `Q(1)` are the preferred initial states, ranked by
decreasing eigenvalue/energy. This requires `α(W)<1`. For `W=0`, `Q=I`,
so all unit-norm states have energy exactly `1`. The nonlinear signs of
these states can evoke different energies; the paper resolves that ambiguity
by selecting the more energetic sign. This module leaves that later
experimental selection to the caller.

## Minimal use

```python
from hennequin_rate_model import (
    optimize_inhibition, preferred_initial_states,
    random_balanced_weights, simulate,
)

w0 = random_balanced_weights(seed=7)  # paper's N=200, p=.1, gamma=3, R=10
soc = optimize_inhibition(w0, seed=8)
if soc.spectral_abscissa[-1] < 1:
    states, energies = preferred_initial_states(soc.weights)
    response = simulate(soc.weights, duration=1.0,
                        initial_potential=states[:, 0] * 1.5 * (200 ** .5))
```

The example initializes a potential with population RMS `1.5 Hz`; for a
strict nonlinear firing-rate initialization, invert `g` at the desired
`Δr` first. The SOC optimization is cubic in `N` per iteration and may be
slow at the paper's `N=200`.
