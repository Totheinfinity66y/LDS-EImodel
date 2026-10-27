"""Independent archived-data check: does not import production analysis/renderer."""
from pathlib import Path
import json, sys, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork

results=[]
for mode in ('one_hot','ring','topology'):
    folder=ROOT/'artifacts/local_fixed_points_v2'/mode
    data=np.load(folder/'analysis.npz');m=EINetwork(overrides=json.loads((folder/'config.json').read_text()))
    w=m.signed_weights;external=m.tonic-m.theta;dt=m.config['dt_ms'];q,z=data['pair_indices'];nodes=data['nodes']
    def f(r):return (-r+np.clip(r@w.T+external,0,1))/m.tau
    xy=data['grid'];expected=np.c_[(-xy[:,0]+np.clip(2*xy[:,0]-.9,0,1))/40,(-xy[:,1]+np.clip(2.4*xy[:,0]-1.4,0,1))/120]
    full=np.repeat(m.rates[None],len(xy),axis=0);full[:,[q,z]]=xy
    nuisance=np.ones(len(m.rates),bool);nuisance[[q,z]]=False;nuisance[m.groups['Y']]=False
    classifications=[]
    for r in nodes:
        drive=w@r+external;kink=(abs(drive)<1e-8)|(abs(drive-1)<1e-8);inside=(drive>0)&(drive<1)
        graph=(inside|kink)[:,None]&(w!=0);np.fill_diagonal(graph,False)
        # Independent reachability cycle test, distinct from production Kahn sorting.
        reach=graph.copy()
        for k in range(len(r)):reach |= reach[:,k,None]&reach[None,k,:]
        slo=inside.astype(float);shi=slo.copy();slo[kink]=0;shi[kink]=1
        a=(-1+slo*np.diag(w))/m.tau;b=(-1+shi*np.diag(w))/m.tau
        lower=np.minimum(a,b);upper=np.maximum(a,b)
        classifications.append(dict(full_residual=float(abs(f(r)).max()),union_graph_acyclic=not bool(np.diag(reach).any()),positive=int((lower>0).sum()),negative=int((upper<0).sum()),max_real_bound=float(upper.max()),euler_radius_bound=float(np.maximum(abs(1+dt*lower),abs(1+dt*upper)).max()),kink_count=int(kink.sum())))
    paths=data['unstable_paths'];step_error=float(abs(paths[:,1:]-paths[:,:-1]-dt*f(paths[:,:-1])).max())
    saddle=nodes[1];red=np.repeat(saddle[None],11,axis=0);red[:,z]=np.linspace(0,1,11)
    redf=f(red)
    row=dict(encoding=mode,states=len(m.rates),pair_indices=[int(q),int(z)],grid_points=len(xy),pair_formula_error=float(abs(data['velocity']-expected).max()),full_pair_error=float(abs(f(full)[:,[q,z]]-expected).max()),nuisance_grid_field=float(abs(f(full)[:,nuisance]).max()),readout_feedback_nonzero=int(np.count_nonzero(w[:,m.groups['Y']])),nodes=classifications,node_pair=nodes[:,[q,z]].tolist(),unstable_path_euler_error=step_error,branch_end_distance=[float(np.linalg.norm(paths[0,-1]-nodes[0])),float(np.linalg.norm(paths[1,-1]-nodes[2]))],stable_line_r_velocity_max=float(abs(redf[:,q]).max()),stable_line_z_formula_error=float(abs(redf[:,z]-(.76-red[:,z])/120).max()),source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'handcrafted_ei/evaluation/local_fixed_points.py',ROOT/'handcrafted_ei/visualization/local_fixed_points.py',folder/'analysis.npz',folder/'nodes.json']})
    assert row['pair_formula_error']<1e-15 and row['full_pair_error']<1e-15 and row['nuisance_grid_field']<1e-13
    assert all(n['union_graph_acyclic'] and n['full_residual']<1e-11 for n in classifications)
    assert [n['positive'] for n in classifications]==[0,1,0] and [n['negative'] for n in classifications]==[132,131,132]
    print(mode,'step_error',step_error,'branch_end_distance',row['branch_end_distance'],flush=True)
    # Finite 1600-ms paths approach sinks, they are not algebraic roots.
    assert step_error<1e-14 and max(row['branch_end_distance'])<1e-4
    assert row['stable_line_r_velocity_max']<1e-14 and row['stable_line_z_formula_error']<1e-14
    results.append(row)
out=Path(__file__).with_suffix('.json');out.write_text(json.dumps(dict(status='PASS',method='independent direct full-rate field; transitive-closure cycle check; archived free-Euler residual',results=results),indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
