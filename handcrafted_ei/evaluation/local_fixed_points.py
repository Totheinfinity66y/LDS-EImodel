"""Closed response/decay pair and full-state equilibria; evaluation copies only."""
import numpy as np
from scipy.optimize import root
from .population_dynamics import field,jacobian


def closed_pair(model,q,z,xy):
    xy=np.asarray(xy);r=np.repeat(model.rates[None],len(xy),axis=0);r[:,[q,z]]=xy
    f=(-r+np.clip(r@model.signed_weights.T+model.tonic+model.stimulus+model.clock-model.theta,0,1))/model.tau
    nuisance=np.ones(len(model.rates),bool);nuisance[[q,z]]=False;nuisance[model.groups['Y']]=False
    if np.any(model.signed_weights[:,model.groups['Y']]):raise ValueError('readout feeds back')
    return dict(velocity=f[:,[q,z]],nuisance_field_max=float(abs(f[:,nuisance]).max()))


def triangular_classification(model,r):
    w=model.signed_weights;drive=w@r+model.tonic+model.stimulus+model.clock-model.theta
    kink=(abs(drive)<1e-8)|(abs(drive-1)<1e-8);inside=(drive>0)&(drive<1)
    enabled=inside|kink;edges=enabled[:,None]&(w!=0);np.fill_diagonal(edges,False)
    degree=edges.sum(1);queue=list(np.flatnonzero(degree==0));order=[]
    while queue:
        source=queue.pop();order.append(int(source))
        for target in np.flatnonzero(edges[:,source]):
            degree[target]-=1
            if degree[target]==0:queue.append(int(target))
    lo=inside.astype(float);hi=lo.copy();lo[kink]=0;hi[kink]=1
    a=(-1+lo*np.diag(w))/model.tau;b=(-1+hi*np.diag(w))/model.tau
    lower=np.minimum(a,b);upper=np.maximum(a,b);dag=len(order)==len(r)
    positive=int(np.count_nonzero(lower>0));negative=int(np.count_nonzero(upper<0))
    kind='stable' if dag and negative==len(r) else ('saddle' if dag and positive>0 and positive+negative==len(r) else 'uncertified')
    return dict(offdiagonal_union_acyclic=dag,classification=kind,positive_eigenvalue_count=positive,
        max_real_eigenvalue_per_ms=float(upper.max()),diagonal_lower=lower.tolist(),diagonal_upper=upper.tolist(),
        kink_count=int(kink.sum()),euler_spectral_radius_bound=float(np.maximum(abs(1+model.config['dt_ms']*lower),abs(1+model.config['dt_ms']*upper)).max()))


def find_nodes(model,q,z,high):
    guesses=[model.rates.copy(),model.rates.copy(),high.copy()]
    guesses[1][q]=.9;guesses[1][z]=.76;guesses[1][model.groups['Y'][0]]=.42
    nodes=[];rows=[]
    for guess in guesses:
        sol=root(lambda r:field(model,r),guess,jac=lambda r:jacobian(model,r),tol=1e-11)
        r=sol.x.copy();raw=float(abs(field(model,r)).max())
        if np.any(r < -1e-12) or np.any(r>1+1e-12):raise ValueError('root outside rate cube')
        r=np.clip(r,0,1);res=float(abs(field(model,r)).max())
        if res>1e-11:raise ValueError('root residual failed')
        row=triangular_classification(model,r);row.update(full_residual_max_per_ms=res,raw_residual_max_per_ms=raw,
            boundary_roundoff_max=float(abs(r-sol.x).max()),solver_success=bool(sol.success),solver_message=str(sol.message))
        nodes.append(r);rows.append(row)
    return np.array(nodes),rows
