"""Explicit LDS adaptations, not executions of the authors' missing pipelines.

All state metrics are in the full recorded rate space (dimensionless rates).
No function selects a response using task labels or changes a live trial.
"""
from copy import deepcopy
import numpy as np
from scipy.spatial.distance import cdist


def projection_energy(delta, basis):
    """basis [neuron,component] has orthonormal columns; keep zero energy NA."""
    delta=np.asarray(delta,dtype=float); basis=np.asarray(basis,dtype=float)
    if delta.ndim<1 or basis.ndim!=2 or delta.shape[-1]!=basis.shape[0]:
        raise ValueError('delta/basis dimensions')
    if not np.allclose(basis.T@basis,np.eye(basis.shape[1]),atol=1e-10):
        raise ValueError('projection basis must be orthonormal')
    projected=delta@basis
    residual=delta-projected@basis.T
    full=np.sum(delta**2,axis=-1); plane=np.sum(projected**2,axis=-1)
    off=np.sum(residual**2,axis=-1)
    fraction=np.divide(plane,full,out=np.full_like(full,np.nan),where=full>0)
    return dict(full_squared=full,projected_squared=plane,orthogonal_squared=off,
                projected_fraction=fraction,closure_error=full-plane-off)


def cross_temporal_distance(control, perturbed):
    """D[t_control,t_perturbed]; full-state Euclidean, no averaging/normalizing."""
    c=np.asarray(control); p=np.asarray(perturbed)
    if c.ndim!=2 or p.ndim!=2 or c.shape[1]!=p.shape[1] or not np.isfinite(c).all() or not np.isfinite(p).all():
        raise ValueError('finite [time,neuron] trajectories required')
    return cdist(c,p)


def endpoint_clusters(states,tolerance=.02):
    """Deterministic greedy complete-link max-norm clusters, not an attractor count.

    Every pair within a cluster must be closer than tolerance. State ordering
    is archived; near-boundary cluster counts are descriptive and order-sensitive.
    """
    states=np.asarray(states)
    if states.ndim!=2 or not np.isfinite(states).all() or tolerance<=0:
        raise ValueError('finite states and positive tolerance required')
    labels=np.empty(len(states),dtype=int); clusters=[]
    for i,state in enumerate(states):
        for j,members in enumerate(clusters):
            if np.max(np.abs(states[members]-state))<tolerance:
                members.append(i); labels[i]=j; break
        else:
            labels[i]=len(clusters); clusters.append([i])
    return labels


def phase_drift(coordinate,times_ms):
    """Central difference in coordinate units/ms; no inferred stochastic drift."""
    x=np.asarray(coordinate); t=np.asarray(times_ms)
    if x.ndim!=1 or x.shape!=t.shape or len(t)<3 or np.any(np.diff(t)<=0):
        raise ValueError('ordered one-dimensional coordinates and times required')
    return np.gradient(x,t,edge_order=2)


def piecewise_cascade_certificate(model,state):
    """Sufficient local certificate valid at clip kinks, not a basin estimate.

    Retain every weight row whose activation can vary near state, including
    both sides of each kink. An acyclic union admits one common topological
    order: each coordinate is a stable leak driven only by earlier coordinates.
    A finite feedforward cascade of Lipschitz clips is locally asymptotically
    stable at its equilibrium. Merely sampling Hurwitz matrices would not prove
    this. The regime margin bounds an available neighborhood, not invariance.
    """
    r=np.asarray(state);w=model.signed_weights
    ext=model.tonic+model.stimulus+model.clock-model.theta;drive=w@r+ext
    kink=(abs(drive)<=1e-7)|(abs(drive-1)<=1e-7)
    enabled=((drive>0)&(drive<1))|kink
    edges=enabled[:,None]&(w!=0); indegree=edges.sum(1);queue=list(np.flatnonzero(indegree==0));order=[]
    while queue:
        source=queue.pop();order.append(int(source))
        for target in np.flatnonzero(edges[:,source]):
            indegree[target]-=1
            if indegree[target]==0:queue.append(int(target))
    acyclic=len(order)==len(r)
    norm=np.sum(abs(w),axis=1);fixed=(~kink)&(norm>0)
    margins=np.minimum(abs(drive[fixed]),abs(drive[fixed]-1))/norm[fixed]
    margin=float(margins.min()) if len(margins) else None
    result=dict(acyclic_union=acyclic,regime_neighborhood_maxnorm_margin=margin,
                certificate='local piecewise feedforward cascade' if acyclic else 'not certified')
    if acyclic:
        eq=r.copy()
        for q in order:eq[q]=np.clip(w[q]@eq+ext[q],0,1)
        residual=np.max(abs((-eq+np.clip(w@eq+ext,0,1))/model.tau))
        displacement=float(np.max(abs(eq-r)))
        result.update(exact_equilibrium_residual=float(residual),equilibrium_max_difference=displacement,
                      certified=bool(residual<1e-12 and margin is not None and displacement<margin))
    else:result['certified']=False
    return result


def paired_input_probe(model,initial,times_ms,stimulus,clock,direction,onset_ms,duration_ms,amplitude,noise=None):
    """Replay archived currents in independent arrays with a finite input pulse.

    Row k is current used to integrate INTO time k. Pulse acts on transitions
    [onset,onset+duration), so recorded samples satisfy onset<t<=offset.
    Random signed projection is external current, never a Dale synapse.
    LDS has no process noise: explicit zero arrays are paired by default.
    """
    t=np.asarray(times_ms); initial=np.asarray(initial); u=np.asarray(stimulus); c=np.asarray(clock)
    direction=np.asarray(direction); n=len(model.rates); dt=model.config['dt_ms']
    if t.ndim!=1 or len(t)<2 or not np.allclose(np.diff(t),dt) or u.shape!=(len(t),n) or c.shape!=u.shape or initial.shape!=(n,) or direction.shape!=(n,):
        raise ValueError('replay shape/time mismatch')
    if duration_ms<=0 or not float(duration_ms/dt).is_integer() or not np.any(t==onset_ms) or onset_ms+duration_ms>t[-1]:
        raise ValueError('pulse must fit recorded integer-step time grid')
    if not all(np.isfinite(x).all() for x in (initial,u,c,direction)) or np.any((initial<0)|(initial>1)):
        raise ValueError('invalid replay input')
    noise=np.zeros_like(u) if noise is None else np.asarray(noise)
    if noise.shape!=u.shape or not np.isfinite(noise).all(): raise ValueError('invalid paired noise')
    pulse=(t>onset_ms)&(t<=onset_ms+duration_ms)
    states=np.repeat(initial[None],2,axis=0); paths=np.empty((2,len(t),n)); paths[:,0]=states
    w=model.signed_weights; fixed=model.tonic-model.theta
    for k in range(1,len(t)):
        drive=states@w.T+fixed+u[k]+c[k]+noise[k]
        if pulse[k]: drive[1]+=amplitude*direction
        states=states+(dt/model.tau)*(-states+np.clip(drive,0,1))
        paths[:,k]=states
    return dict(control=paths[0],perturbed=paths[1],pulse_mask=pulse,
                noise_control=noise,noise_perturbed=noise.copy(),direction=direction)


def exact_local_stability(model,state):
    """Analytic Jacobian plus independent finite differences and Euler check."""
    from .population_dynamics import field,jacobian
    probe=deepcopy(model); probe.rates=np.asarray(state).copy()
    j=jacobian(probe); h=1e-7; numeric=np.empty_like(j)
    for q in range(len(state)):
        eps=np.zeros(len(state)); eps[q]=h
        numeric[:,q]=(field(probe,state+eps)-field(probe,state-eps))/(2*h)
    eigen=np.linalg.eigvals(j); residual=field(probe)
    copied=deepcopy(probe); copied.step()
    drive=probe.signed_weights@state+probe.tonic+probe.stimulus+probe.clock-probe.theta
    kink=np.isclose(drive,0,atol=1e-7)|np.isclose(drive,1,atol=1e-7)
    stable=bool(eigen.real.max()<0 and np.max(abs(1+probe.config['dt_ms']*eigen))<1 and not kink.any())
    return dict(residual_l2_per_ms=float(np.linalg.norm(residual)),
        residual_max_per_ms=float(np.max(abs(residual))),
        max_real_eigenvalue_per_ms=float(eigen.real.max()),
        euler_spectral_radius=float(np.max(abs(1+probe.config['dt_ms']*eigen))),
        jacobian_fd_max_error=float(np.max(abs(j-numeric))),
        euler_consistency_max_error=float(np.max(abs(copied.rates-state-probe.config['dt_ms']*residual))),
        kink_count=int(kink.sum()),strict_local_stability=stable),eigen
