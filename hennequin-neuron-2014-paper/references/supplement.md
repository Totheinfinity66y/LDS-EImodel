# Supplementary information

**Neuron, Volume** **_82_**

# **Supplemental Information**

**Optimal Control of Transient Dynamics in Balanced Networks Supports Generation of Complex Movements**

**Guillaume Hennequin, Tim P. Vogels, and Wulfram Gerstner**

Optimal control of transient dynamics in balanced networks supports generation of complex movements

# **Supplemental Information**

Guillaume Hennequin, Tim P. Vogels and Wulfram Gerstner

## **Contents**

1 Supplemental Figures — 2
2 Supplementary Movie caption — 4
3 Supplemental Experimental Procedures — 5
  3.1 Preferred initial states — 5
  3.2 Construction of the SOC architecture — 6
  3.3 Generation of SOC matrices for spiking networks — 8
4 References — 10

## **1 Supplemental Figures**

[Figure S1](../assets/supp_figs/supplementary-figure-s1.jpg)

**Figure S1, related to Figure 7 of the main text** – **Diversity of single-cell transient responses in the spiking SOC.** Shown here are trial-averaged responses (1’000 trials) of the first cell for each of the first 18 subgroups (one panel per subgroup). The preparatory period drives the network in one of 27 random combinations (color coded) of its top 2 preferred initial conditions. The color code is meaningless and not consistent across panels, but only intended to ease visualization. Rate traces were smoothed using a Gaussian kernel of width 20 ms.

[Figure S2](../assets/supp_figs/supplementary-figure-s2.jpg)

**Figure S2, related to Figure 8 of the main text** – **Control random spiking network. (a)** Top: raster plot of spiking activity in the control network. Middle: average momentary network activity (black), and activities of the two colored subgroups. Note that the concept of subgroups is absent from the connectivity; subgroups are completely arbitrary here, and only meant to provide a comparison with Figure 8 of the main manuscript. Bottom: voltage traces for two randomly chosen cells. **(b)** Distribution of average firing rates in the random network (black) and in the SOC (gray). Averate rates were computed from a 1’000 second-long simulation. **(c)** Same as in (b), for the CVs of the ISI distributions.

## **2 Supplementary Movie caption**

**Supplementary Movie** The eigenvalues of the original random balanced network are shown as fixed gray dots in the complex plane. Roughly 50% of them lie to the right of the critical line defined by Re( _λ_ ) = 1 (purple line), thus corresponding to unstable eigenmodes. The moving dots show the evolution of the eigenvalues as the inhibitory connectivity is being refined to produce a SOC. Each frame corresponds to one step of the gradient descent (cf. Experimental Procedures). Purple dots indicate unstable eigenmodes.

## **3 Supplemental Experimental Procedures**

We present here additional information regarding both the theoretical underpinnings of the stabilization algorithm we have used to build Stability-Optimized Circuits (SOCs), and all details of its implementation. We also give a complete description of our spiking network model.

### **3.1 Preferred initial states**

Given a network with connectivity matrix **W** and network dynamics of the form

[Formula on PDF page 6 (5)](../assets/supp_figs/formula-p0006-004.jpg)

(cf. Equation (1) in the main text), we ask: what initial condition **a** _≡_ ∆ **r** ( _t_ = 0) will give rise to the strongest transient response? How “strong” a transient response is is quantified by the energy _E_ ( **a** ), defined in Equation (4) of the main text, which we repeat here for convenience:

[Formula on PDF page 6 (7)](../assets/supp_figs/formula-p0006-006.jpg)

We restrict the analysis to the linear regime in which ∆ _ri ≃ xi_ , and we assume that the network dynamics run freely without noise ( **_ξ_** ( _t_ ) = 0) from _t_ = 0 on. In Equation (2), 2 _/τ_ is a normalizing factor such that _E_ ( **a** ) = 1 for an unconnected network ( **W** = 0), irrespective of the (unit-norm) initial condition **a** (in which case _∥_ ∆ **r** ( _t_ ) _∥_<sup>2</sup> = exp(−2t/τ)). Since the SOC is linearly stable, _E_ is finite, in the sense that any initial condition is bound to decay (exponentially) after sufficiently long periods of time.

The “best” input direction is then defined as the initial condition **a** 1 that maximizes _E_ ( **a** ). In the linear regime, this maximization can be performed analytically. Indeed, Equation (2) can be rewritten as

[Formula on PDF page 6 (10)](../assets/supp_figs/formula-p0006-009.jpg)

where ( _·_ )<sup>_⊤_</sup> denotes the matrix transpose. The last equality defines **Q** as the matrix integral inside square brackets. **Q** is a symmetric, positive-definite matrix, so its principal eigenvector is precisely the initial condition **a** 1 that maximizes the evoked energy, which is then given by the corresponding principal eigenvalue of **Q** . In fact, the full eigenbasis of **Q** , ranked in decreasing order of the associated eigenvalues, defines a collection ( **a** 1 _,_ **a** 2 _, . . . ,_ **a** _N_ ) of _N_ orthogonal input states that each maximize the evoked energy within the subspace orthogonal to all previous best input directions (cf. Figure 3a in the main manuscript). Again, the eigenvalues are the corresponding evoked energies. We use this energy formalism again below to explain the optimal inhibitory stabilization algorithm. Note that in the linear regime, **a** _k_ and _−_ **a** _k_ evoke the exact same energy. In the non-linear network, this needs not be the case, and we resolve this sign ambiguity by picking the condition that evoked most energy. Note also that **Q** is the solution to the Lyapunov equation

[Formula on PDF page 6 (12)](../assets/supp_figs/formula-p0006-011.jpg)

which is easily solved numerically (Bartels and Stewart, 1972), e.g. using the Matlab function `lyap` .

### **3.2 Construction of the SOC architecture**

Random connectivity matrices of size $N = 2M$, with $M$ positive (excitatory) columns and $M$ negative (inhibitory) columns, were generated as in Hennequin et al. (2012) with connectivity density $p = 0.1$. Non-zero excitatory (resp. inhibitory) weights were set to $w_0/√N$ (resp. $−γw_0/√N$), where $w_0 = R/√[p(1−p)(1+γ^2)/2]$ and $R$ is the desired spectral radius (before stability optimization, Rajan and Abbott (2006)).

To generate a SOC, we generated such a random connectivity matrix with _R_ = 10, producing unstable, chaotic network behavior. After the creation of the initial **W** , all excitatory connections remained fixed. To achieve robust linear stability of the dynamics (i.e. quench chaos), we refined the inhibitory synapses to minimize the “smoothed spectral abscissa” _α_ ˜ _ϵ_ ( **W** ), a relaxation of the spectral abscissa (the largest real part in the eigenvalues of **W** ) that – among other advantages – leads to tractable optimization (Vanbiervliet et al., 2009). We describe it in more details below, but in short, the inhibitory weights followed a gradient descent on _α_ ˜ _ϵ_ ( **W** ), subject to three constraints. First, we constrained the inhibitory weights to remain inhibitory, i.e. negative. Second, we enforced a constant ratio between the average magnitude of the inhibitory weights, and its excitatory counterpart ( _γ_ = 3). Third, the density of inhibitory connections was restricted to less than 40%. This constrained gradient descent usually converged within a few hundred iterations (cf. also our online Supplemental Movie).

In more technical terms, the smoothed spectral abscissa can be introduced by way of considering, as above, the energy evoked through linear network dynamics by some initial condition **a** :

[Formula on PDF page 7 (5)](../assets/supp_figs/formula-p0007-004.jpg)

where **Q** ( _s_ ) is defined more generally as

[Formula on PDF page 7 (7)](../assets/supp_figs/formula-p0007-006.jpg)

For the network to be stable, the energy in Equation (6) must remain finite for any initial condition **a** . Since **Q** (1) is positive definite, its maximum eigenvalue is smaller than the sum of its eigenvalues. Thus, for any **a** , _E_ ( **W** _,_ **a** ) is upper-bounded by the trace of **Q** (1). Consequently, if trace [ **Q** (1)] _< ϵ_<sup>_−_1</sup> for some given _ϵ >_ 0, then the energy evoked by any **a** is less than _ϵ_<sup>_−_1</sup> , so the network dynamics of Equation (1) are guaranteed to be stable<sup>1</sup> . In a network that is not (yet) linearly stable, we ask: how far must the system be “shifted”, **W** → **W** _− s_ **I** (cf. Equation (7)), for trace [ **Q** ( _s_ )] to become smaller than _ϵ_<sup>_−_1</sup> ? The _ϵ_ -smoothed spectral abscissa answers this question. Mathematically, _α_ ˜ _ϵ_ ( **W** ) is the unique root of $s \mapsto$ trace [ **Q** ( _s_ )] _− ϵ_<sup>_−_1</sup> , which is a monotonically decreasing function of _s_ . If the shift _s_ is smaller than the spectral abscissa _α_ ( **W** ), some of the eigenvalues of **W** _− s_ **I** will have positive real parts, causing trace [ **Q** ( _s_ )] to diverge. The smoothed spectral abscissa _α_ ˜ _ϵ_ ( **W** ) is therefore necessarily greater than _α_ ( **W** ), which means that stability can be achieved by minimizing _α_ ˜ _ϵ_ ( **W** ) instead of _α_ ( **W** ). This is an advantageous replacement as, unlike _α_ , _α_ ˜ _ϵ_ is a smooth function of the synaptic weights (Vanbiervliet et al., 2009).

The tractability of the approach stems from the computability of _α_ ˜ _ϵ_ ( **W** ) and its derivatives w.r.t **W** . For any _s > α_ ( **W** ), the matrix **Q** ( _s_ ) defined in Equation (7) is known to be the solution to the following Lyapunov equation

[Formula on PDF page 7 (10)](../assets/supp_figs/formula-p0007-009.jpg)

Solving this equation numerically can be done efficiently (Bartels and Stewart, 1972). Knowing that trace [ **Q** ( _s_ )] _−ϵ_<sup>_−_1</sup> is a decreasing function of _s_ , one can apply standard root-finding methods

1 Globally stable in the linear case, locally stable around background state otherwise. to identify _α_ ˜ _ϵ_ ( **W** ). Finally, Vanbiervliet et al. (2009) also provide its derivatives w.r.t the synaptic weights, needed to perform our gradient-based minimization of _α_ ˜ _ϵ_ :

[Formula on PDF page 8 (2)](../assets/supp_figs/formula-p0008-001.jpg)

where

[Formula on PDF page 8 (4)](../assets/supp_figs/formula-p0008-003.jpg)

solves a Lyapunov equation analogous to Equation (8):

[Formula on PDF page 8 (6)](../assets/supp_figs/formula-p0008-005.jpg)

The iterative constrained gradient descent on _α_ ˜ _ϵ_ ( **W** ) entails the following steps:

1. Compute the current value of the smoothed spectral abscissa _α_ ˜ _ϵ_ ( **W** ). This implies multiple iterations of a numerical root-finding method (e.g. bisection) on $s \mapsto$ trace[ **Q** ( _s_ )] _− ϵ_<sup>_−_1</sup> . The main cost here is to solve Equation (8) for **Q** ( _s_ ) numerically, but we show below that the present step can in fact be bypassed.

2. Solve Equation (8) and Equation (11) with _s_ = _α_ ˜ _ϵ_ found in step 1. This gives matrices **Q** (˜ _αϵ_ ) and **P** (˜ _αϵ_ ), which must be multiplied to form the desired gradient (Equation (9)).

3. Move the inhibitory weights by a small amount in the direction of the negative gradient. That is, for every _existing_ inhibitory synapse _Wij_ (only 40% of all possible inhibitory connections exist at any given time, see step 6), set _Wij ← Wij − η_ [ _∂α_ ˜ _ϵ/∂_ **W** ] _ij_ . Here _η_ = 10 is a learning rate.

4. Enforce the negativity constraint (inhibitory weights remain inhibitory), by clipping all positive inhibitory weights to zero

5. Enforce the constraint that inhibition must be _γ_ = 3 times stronger than excitation on average. This is done by writing the connectivity matrix **W** block-wise as

[Formula on PDF page 8 (13)](../assets/supp_figs/formula-p0008-012.jpg)

and multiplicatively rescaling both inhibitory blocks by $−γ\overline{W}^{E→E}/\overline{W}^{I→E}$ and $−γ\overline{W}^{E→I}/\overline{W}^{I→I}$ respectively, where $\overline{W}^{X→Y}$ denotes the average over all matrix elements. This step is not necessary for stability optimization, but is essential to make sure that the high correlation of excitatory and inhibitory input currents that emerges from optimization is not overwhelmed by the baseline correlation contributed by shared population fluctuations (see Discussion in the main text, and Renart et al. (2010); Hennequin et al. (2012)).

6. Enforce the maximum density of inhibitory connections, by removing any existing _Wij_ that step 4 may have set to zero, and replacing it by a new connection _Wik_ (which does not exist yet) where the presynaptic inhibitory neuron _k_ is chosen randomly. Set the strength of these new connections to zero initially. Again, this constraint is not strictly required, but adds to the biological plausibility of the resulting connectivity. Note that this step ensures that the number of “existing” inhibitory synapses per neuron is left unchanged. The desired number of allowed synapses must therefore be decided before starting this iterative procedure; here we “tag” 40% of all inhibitory synapses as “existing”, picking the 10% of non-zero synapses that are already present in the initial chaotic network and completing the remaining 30% with randomly chosen synapses, whose weights are initially set to zero.

Steps 1 through 6 are then repeated until convergence of the spectral abscissa (Supplemental Movie).

**Choice of ε.** In this procedure, _ϵ_ modulates the distance between the spectral abscissa _α_ and its upper bound _α_ ˜ _ϵ_ : if _ϵ_ is decreased, _α_ ˜ _ϵ_ becomes a tighter upper bound to the spectral abscissa. In pilot studies, we realized that stability could be reached much faster if _ϵ_ was set to decrease progressively during the course of the gradient descent. Empirically, it seemed a good idea to keep the ratio _α_ ˜ _ϵ/α_ constant, and to adjust _ϵ_ in every iteration to meet this need. Mathematically, this means that the cost function ( **W** → α_ ˜ _ϵ_ ( **W** )) keeps moving, but it becomes a progressively tighter upper bound on _α_ , and crucially, we no longer need to compute _α_ ˜ _ϵ_ in step 1! We thus capitalized on this observation and set _α_ ˜ _ϵ_ ( **W** ) = _Cα_ ( **W** ) in every iteration, with _C_ = 1.5, empirically found to be a good choice. Note that this automatically constrains _ϵ_ to a value of 1 _/_ trace[ **Q** ( _Cα_ )], where **Q** ( _·_ ) is defined in Equation (7). Steps 2 to 6 are then performed as prescribed above. Note that computationally, the cost is still of order _N_<sup>3</sup> , but the large multiplicative constant implied by the iterative root-finding method of Step 1 is eliminated. Note also that Step 2 requires solving Equation (8) and Equation (11), for which we need to compute a Schur decomposition of **W** only once (Bartels and Stewart, 1972). As a byproduct, the Schur decomposition also returns the spectral abscissa at no further cost, so _α_ needs not be computed separately. The above simplified procedure is very effective, except for one small detail. As _α_ ˜ _ϵ_ gets closer to _α_ (which is bound to happen as learning progresses, since _α_ ˜ _ϵ_ = _Cα_ and _α_ ˜ _ϵ_ decreases), it also becomes increasingly non-smooth as a function of **W** . For its gradient to remain well-behaved, we therefore kept _α_ ˜ _ϵ_ some safe margin away from _α_ , by setting _α_ ˜ _ϵ_ to _Cα_ or _α_ + _B_ in every iteration, whichever was the greatest. We used _B_ = 0.2.

### **3.3 Generation of SOC matrices for spiking networks**

SOC matrices for spiking networks were generated in a similar manner as described above for rate-based networks, except for a few simple variations to account for the effective gains of the excitatory and inhibitory synaptic pathways between subgroups. To calculate these gains, we isolated two subgroups of spiking neurons, _n_ (sender) and _m_ (receiver), and assumed (selfconsistently) that the rest of the network fired with Poisson statistics at 5 Hz. We then numerically estimated the effect of small firing rate deviations in group _n_ , ∆ _n_ , on the firing rate response ∆ _m_ of the receiver (thus linearizing the joint dynamics of subgroups around the background state). Due do the E/I balance, this is a roughly linear function of the connection probability $\widehat{W}_{mn}$ from group _n_ to group _m_ :

[Formula on PDF page 9 (4)](../assets/supp_figs/formula-p0009-003.jpg)

Using a simple least-squares fit, we extracted the coefficients of proportionality $β_{exc} ≃ 5.2$ and $β_{inh} ≃ −21.9$. These constants were then used to rescale the excitatory and inhibitory parts of the normalized matrix of connection probabilities,  $\widehat{\mathbf W}$  , yielding an effective connectivity matrix **W** such that linear dynamics of the form

[Formula on PDF page 9 (6)](../assets/supp_figs/formula-p0009-005.jpg)

approximated the joint dynamics of our spiking subgroups (which is shown in Figure 8b of the main manuscript). This suggests that the threshold process of spiking in combination with the finite size of the randomly connected subgroups leads to apparent stochasticity that can, to a high degree of accuracy, be treated as noise around an effective population rate of each subgroup (see also Brunel (2000)).

We used the smoothed spectral abscissa method described above to modify the connections probabilities $\widehat{W}_{mn}$ (200 _< n ≤_ 400) that involved inhibitory presynaptic subgroups to achieve stability in an initially unstable, random sparse matrix. In each gradient step, the inhibitory part of each row of  $\widehat{\mathbf W}$  was re-normalized to sum to 1, to preserve the probabilistic interpretation of  $\widehat{\mathbf W}$  . Second, we used a straightforward application of the chain rule to propagate the gradient of the smoothed spectral abscissa of **W** to  $\widehat{\mathbf W}$  given the value of _β_ inh _._ .

We used the effective weight matrix **W** to compute the preferred initial states of the spiking SOC, akin to the rate-based case with ∆ _ri ∝ xi_ (i.e. assuming linear dynamics among subgroups given by Equation (14)). During the preparatory period, each LIF neuron received a ramping input current that depended only on the subgroup it belonged to.

## **4 References**

- Bartels, R. H. and Stewart, G. W. (1972). Solution of the matrix equation AX+XB=C. _Communications of the ACM_ , 15:820–826.

- Brunel, N. (2000). Dynamics of sparsely connected networks of excitatory and inhibitory spiking neurons. _J. Comput. Neurosci._ , 8:183âĂŞ–208.

- Hennequin, G., Vogels, T. P., and Gerstner, W. (2012). Non-normal amplification in random balanced neuronal networks. _Phys. Rev. E_ , 86:011909.

- Rajan, K. and Abbott, L. F. (2006). Eigenvalue spectra of random matrices for neural networks. _Phys. Rev. Lett._ , 97:188104.

- Renart, A., de la Rocha, J., Bartho, P., Hollender, L., Parga, N., Reyes, A., and Harris, K. (2010). The asynchronous state in cortical circuits. _Science_ , 327:587.

- Vanbiervliet, J., Vandereycken, B., Michiels, W., Vandewalle, S., and Diehl, M. (2009). The smoothed spectral abscissa for robust stability optimization. _SIAM Journal on Optimization_ , 20:156–171.

## Conversion notes

- The supplied supplemental PDF contains a Supplementary Movie caption, but the movie file was not supplied.
- Displayed equations and plot labels are retained as source images where text extraction cannot preserve their layout reliably.
