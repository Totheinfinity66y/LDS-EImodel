"""Independent audit: use original model.step, never production analysis helpers."""
from pathlib import Path
import json,csv,sys
import numpy as np
from scipy.sparse.csgraph import connected_components
from handcrafted_ei.model.ei_network import EINetwork

ROOT=Path(__file__).resolve().parents[3]
results=[]
for mode in ('one_hot','ring','topology'):
    folder=ROOT/'artifacts/local_fixed_points_v2'/mode
    config=json.loads((folder/'config.json').read_text())
    m=EINetwork(overrides=config); data=np.load(folder/'analysis.npz')
    nodes=data['nodes'];q,z=data['pair_indices'];w=m.signed_weights.copy()
    external=m.tonic-m.theta; n=len(m.rates);dt=m.config['dt_ms']
    row={'mode':mode,'state_dimension':n,'pair_indices':[int(q),int(z)]}
    residuals=[];bounds=[];positive=[];cycles=[]
    for r in nodes:
        m.rates=r.copy();m.step();residuals.append(float(np.max(abs(m.rates-r))/dt))
        drive=w@r+external
        inside=(drive>1e-8)&(drive<1-1e-8)
        kink=(abs(drive)<1e-8)|(abs(drive-1)<1e-8)
        graph=(w!=0)&(inside|kink)[:,None];np.fill_diagonal(graph,False)
        count,labels=connected_components(graph,directed=True,connection='strong')
        cycles.append(bool(count<n))
        diag=(-1+inside*np.diag(w))/m.tau
        # At these equilibria all kink rows have no recurrence; hence diag unique.
        assert not np.any(np.diag(w)[kink])
        bounds.append(float(diag.max()));positive.append(int(np.sum(diag>0)))
        assert count==n
    assert max(residuals)<1e-11
    assert positive==[0,1,0] and bounds[0]<0 and bounds[2]<0
    row.update(full_model_step_residual_max_per_ms=residuals,positive_modes=positive,max_generalized_real_eigenvalue_per_ms=bounds)
    # Compare independently reconstructed closed pair derivatives to entire grid.
    initial=EINetwork(overrides=config).rates
    baseline=external+w@initial
    xy=data['grid'];vel=np.c_[(-xy[:,0]+np.clip(w[q,q]*xy[:,0]+baseline[q],0,1))/m.tau[q],(-xy[:,1]+np.clip(w[z,q]*xy[:,0]+baseline[z],0,1))/m.tau[z]]
    assert np.max(abs(vel-data['velocity']))<1e-14
    allr=np.repeat(initial[None],len(xy),axis=0);allr[:,[q,z]]=xy
    fullf=(-allr+np.clip(allr@w.T+external,0,1))/m.tau
    mask=np.ones(n,bool);mask[[q,z]]=False;mask[m.groups['Y']]=False
    assert np.max(abs(fullf[:,mask]))<1e-14
    assert not np.any(w[:,m.groups['Y']])
    row.update(closed_pair_grid_max_error=float(np.max(abs(vel-data['velocity']))),nuisance_derivative_max=float(np.max(abs(fullf[:,mask]))))
    # Original step must reproduce every archived unstable trajectory, unmodified.
    errors=[];ends=[]
    for path in data['unstable_paths']:
        m.rates=path[0].copy();err=0
        for state in path[1:]:m.step();err=max(err,float(np.max(abs(m.rates-state))))
        errors.append(err);ends.append([float(np.linalg.norm(path[-1]-r)) for r in nodes[[0,2]]])
    print(mode,'unstable path maximum independent cumulative differences',errors,flush=True)
    assert max(errors)<1e-10
    print(mode,'endpoint distances',ends,flush=True)
    assert ends[0][0]<1e-4 and ends[1][1]<1e-4
    row.update(full_unstable_model_step_errors=errors,unstable_endpoint_distance_to_rest_held=ends)
    # Recreate every finite perturbation with original full step and verify dose/clipping.
    doses=list(csv.DictReader((folder/'perturbations.csv').open()))
    errdose=errdist=0.;maxfinal=0.
    for i,dose in enumerate(doses):
        node=int(dose['node']);amp=float(dose['requested_rms']);seed=int(dose['seed'])
        delta=np.random.default_rng(seed).normal(size=n);delta*=amp/np.sqrt(np.mean(delta**2))
        raw=nodes[node]+delta;start=np.clip(raw,0,1)
        errdose=max(errdose,abs(float(dose['actual_rms'])-np.sqrt(np.mean((start-nodes[node])**2))))
        assert float(dose['clipping_fraction'])==np.mean(raw!=start)
        m.rates=start.copy();dist=[np.linalg.norm(m.rates-nodes[node])]
        for _ in range(len(data['times_ms'])-1):m.step();dist.append(np.linalg.norm(m.rates-nodes[node]))
        errdist=max(errdist,float(np.max(abs(np.array(dist)-data['perturbation_distances'][i]))))
        maxfinal=max(maxfinal,float(dist[-1]))
    assert errdist<1e-12 and errdose<1e-14 and maxfinal<1e-6
    row.update(probe_count=len(doses),dose_error=errdose,independent_distance_error=errdist,max_probe_final_distance=maxfinal)
    results.append(row)
out=Path(__file__).with_name('independent_metrics.json');out.write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
