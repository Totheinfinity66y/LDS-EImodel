"""Independent formula checks. Run from repository root using analysis Python.

Imports the protected model only for its fixed coefficients; never calls the
production analysis, adapter, field, Jacobian, integrator or metric functions.
"""
from pathlib import Path
import csv, hashlib, json, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork

def main():
    result={"scope":"independent formulas; finite samples; no proof of global stability", "encodings":{}}
    cfg=json.loads((ROOT/'handcrafted_ei/artifacts/v2/run/config.json').read_text())
    for mode in ('one_hot','ring','topology'):
        folder=ROOT/'artifacts/paper2agent_reproduction/lds_results'/mode
        m=EINetwork(overrides={**cfg,'location_encoding':mode})
        w=m.weights*m.signs[None,:]; ext=m.tonic-m.theta; dt=cfg['dt_ms']
        def f(x,extra=0): return (np.clip(x@w.T+ext+extra,0,1)-x)/m.tau
        def ident(x):
            a=x[m.groups['R3']].reshape(-1,6)
            return list(map(int,np.unravel_index(a.argmax(),a.shape))) if a.max()>=.2 else None
        with np.load(folder/'fixed_points.npz') as z:
            x=z['rates']; ends=z['endpoints']; initial=z['initial_rates']; eig_saved=z['eigenvalues']
            dist=np.sqrt(np.sum((ends[:,None,:]-ends[None,:,:])**2,axis=-1))
            matrix_error=float(abs(dist-z['endpoint_distance']).max())
            step_error=float(abs(np.diff(x,axis=1)-dt*f(x[:,:-1])).max())
            b=z['basis']; identity_count=sum(ident(a)==ident(e) and ident(e) is not None for a,e in zip(initial,ends))
            # Independent complete-link assignment under the declared max norm.
            clusters=[]
            for e in ends:
                for group in clusters:
                    if all(np.max(abs(e-p))<.02 for p in group): group.append(e); break
                else: clusters.append([e])
            r=ends[0]; drive=w@r+ext; kink=np.flatnonzero((abs(drive)<1e-7)|(abs(drive-1)<1e-7))
            h=1e-7; eye=np.eye(len(r)); fd=np.column_stack([(f(r+h*v)-f(r-h*v))/(2*h) for v in eye])
            slope=((drive>0)&(drive<1)).astype(float)
            slope[kink]=.5
            j=(-eye+slope[:,None]*w)/m.tau[:,None]
            eig=np.linalg.eigvals(j)
            # At constant-drive kinks W row is zero, so the vector field is
            # smooth in state despite activation kink; test explicitly.
            effective_kink=kink[np.any(w[kink]!=0,axis=1)]
            # Union of possible local active-state edges. If this graph is a
            # DAG, ONE common neuron permutation triangularizes every local
            # piecewise Jacobian; a cascade of stable scalar leaks proves
            # local stability, unlike merely sampling Hurwitz matrices.
            slopes_union=((drive>0)&(drive<1)).astype(float); slopes_union[kink]=1
            union=slopes_union[:,None]*w
            edge=union!=0; indegree=edge.sum(1); pending=list(np.flatnonzero(indegree==0)); order=[]
            while pending:
                source=pending.pop(); order.append(int(source))
                for target in np.flatnonzero(edge[:,source]):
                    indegree[target]-=1
                    if indegree[target]==0: pending.append(int(target))
            dag=len(order)==len(r)
            distances_to_kinks=np.minimum(abs(drive),abs(drive-1))
            nonk=np.ones(len(r),bool); nonk[kink]=False
            row_norm=np.sum(abs(w),axis=1)
            relevant=nonk&(row_norm>0)
            # Sufficient max-norm radius retaining every non-kink clip branch.
            radius=float(np.min(distances_to_kinks[relevant]/row_norm[relevant]))
            cascade=[]
            for q,endpoint_state in enumerate(ends):
                v=endpoint_state.copy(); local_drive=w@v+ext
                local_kink=(abs(local_drive)<1e-7)|(abs(local_drive-1)<1e-7)
                enabled=((local_drive>0)&(local_drive<1))|local_kink
                local_edge=enabled[:,None]&(w!=0); deg=local_edge.sum(1)
                queue=list(np.flatnonzero(deg==0)); sequence=[]
                while queue:
                    source=queue.pop(); sequence.append(int(source))
                    for target in np.flatnonzero(local_edge[:,source]):
                        deg[target]-=1
                        if deg[target]==0: queue.append(int(target))
                assert len(sequence)==len(v)
                for neuron in sequence: v[neuron]=np.clip(w[neuron]@v+ext[neuron],0,1)
                exact_residual=float(abs(f(v)).max())
                exact_drive=w@v+ext
                ek=(abs(exact_drive)<1e-7)|(abs(exact_drive-1)<1e-7)
                relevant=(~ek)&(row_norm>0)
                margin=float(np.min(np.minimum(abs(exact_drive[relevant]),abs(exact_drive[relevant]-1))/row_norm[relevant]))
                cascade.append({'trial':q,'union_DAG':True,'equilibrium_residual':exact_residual,
                    'equilibrium_endpoint_maxdiff':float(abs(v-endpoint_state).max()),
                    'identity_preserved':ident(v)==ident(endpoint_state),
                    'neighborhood_margin':margin,'topological_order':sequence,
                    'nonkink_interior_rows':np.flatnonzero((exact_drive>0)&(exact_drive<1)&~ek).tolist(),
                    'variable_kink_rows':np.flatnonzero(ek&(row_norm>0)).tolist()})
                assert exact_residual<1e-12
            endpoint={"trajectory_step_error":step_error,"endpoint_matrix_error":matrix_error,
                "residual_max":float(abs(f(ends)).max()),"clusters_maxnorm_002":len(clusters),
                "identity_retained":int(identity_count),"jacobian_fd_error":float(abs(j-fd).max()),
                "continuous_max_real":float(eig.real.max()),"euler_rho":float(abs(1+dt*eig).max()),
                "kink_labels":[m.labels[i] for i in kink],"state_dependent_kink_labels":[m.labels[i] for i in effective_kink],
                "kink_weight_row_norms":np.linalg.norm(w[kink],axis=1).tolist(),
                "local_union_graph_acyclic":dag,"local_union_topological_order":order,
                "maxnorm_clip_pattern_radius_lower_bound":radius,
                "cascade_equilibrium_checks":cascade,
                "saved_eigenvalue_sorted_error":float(abs(np.sort_complex(eig)-np.sort_complex(eig_saved[0])).max())}
        basin_checks=[]
        rows=list(csv.DictReader((folder/'basin.csv').open()))
        for group in ('full','active_branch','I'):
            with np.load(folder/f'basin_{group}.npz') as z:
                a=z['rates']; chosen=[0,6,11,12*23+11]
                for k in chosen:
                    trial=int(z['initial_reference_index'][k]); amp=z['amplitude'][k]; seed=int(z['seed'][k])
                    reference=ends[trial]; branch=int(np.argmax(reference[m.groups['R3']].reshape(-1,6).sum(1)))
                    ix={'full':np.arange(len(reference)),'active_branch':m.groups['R3'].reshape(-1,6)[branch],'I':np.flatnonzero(m.signs<0)}[group]
                    g=np.random.default_rng(seed).normal(size=len(ix)); kick=np.zeros(len(reference));kick[ix]=amp*g/np.sqrt(np.mean(g*g))
                    raw=reference+kick; delta=np.clip(raw,0,1)-reference
                    row=next(q for q in rows if q['target']==group and int(q['trial'])==trial and int(q['seed'])==seed and float(q['amplitude_preclip'])==amp)
                    basin_checks.append({"group":group,"row":k,"initial_error":float(abs(a[k,0]-np.clip(raw,0,1)).max()),
                        "rms_error":float(abs(np.sqrt(np.mean(delta[ix]**2))-float(row['actual_target_rms']))),
                        "clip_fraction_error":float(abs(np.mean((raw[ix]<0)|(raw[ix]>1))-float(row['clipping_fraction_target']))),
                        "one_step_error":float(abs(a[k,1]-a[k,0]-dt*f(a[k,0])).max())})
        with np.load(folder/'state_perturbation.npz') as z:
            delta=z['perturbed']-z['control']; b=z['basis']; plane=delta@b; off=delta-plane@b.T
            closure=np.sum(delta*delta,1)-np.sum(plane*plane,1)-np.sum(off*off,1)
            ct=np.sqrt(np.sum((z['control'][::4,None,:]-z['perturbed'][None,::4,:])**2,axis=-1))
            projection={"orthonormal_error":float(abs(b.T@b-np.eye(2)).max()),"closure_max":float(abs(closure).max()),
                "cross_temporal_error":float(abs(ct-z['cross_temporal_distance']).max()),
                "initial_projected_energy_fraction":float(np.sum(plane[0]**2)/np.sum(delta[0]**2))}
        pulses=[]
        for assay in ('source_time','R3_fixed_clock'):
            with np.load(folder/f'input_{assay}_7.npz') as z:
                t=z['times_ms']; control=z['control']; pert=z['perturbed']; current=z['actual_perturbation_current']
                baseline=z['base_stimulus']+z['clock']; onset=500 if assay=='source_time' else 20
                ix=np.flatnonzero(np.linalg.norm(current,axis=1)>0)
                control_error=float(abs(np.diff(control,axis=0)-dt*f(control[:-1],baseline[1:])).max())
                pert_error=float(abs(np.diff(pert,axis=0)-dt*f(pert[:-1],baseline[1:]+current[1:])).max())
                pulses.append({"assay":assay,"control_step_error":control_error,"perturbed_step_error":pert_error,
                    "pulse_sample_times":t[ix].tolist(),"pulse_integrated_target_rms_ms":float(dt*np.sqrt(np.mean(current**2,axis=1)).sum()),
                    "pre_onset_difference":float(abs(control[t<=onset]-pert[t<=onset]).max()),
                    "shared_noise_exact":bool(np.array_equal(z['noise_control'],z['noise_perturbed']))})
        result['encodings'][mode]={"endpoints":endpoint,"basin_checks":basin_checks,"projection":projection,"pulses":pulses}
        assert step_error<1e-12 and matrix_error<1e-12 and endpoint['jacobian_fd_error']<1e-8
        assert all(max(q['initial_error'],q['rms_error'],q['clip_fraction_error'],q['one_step_error'])<1e-12 for q in basin_checks)
        assert projection['closure_max']<1e-12 and projection['cross_temporal_error']<1e-12
        assert all(max(q['control_step_error'],q['perturbed_step_error'],q['pre_onset_difference'])<1e-12 and q['shared_noise_exact'] for q in pulses)
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['status']='PASS_NUMERICAL_FORMULAS_WITH_STABILITY_CLASSIFICATION_CAVEAT'
    out=Path(__file__).with_name('independent_check.json')
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(out)
    for mode,data in result['encodings'].items():
        print(mode,'endpoints',data['endpoints']['clusters_maxnorm_002'],
              'step_error',data['endpoints']['trajectory_step_error'],
              'local_DAG_count',sum(q['union_DAG'] for q in data['endpoints']['cascade_equilibrium_checks']))

if __name__=='__main__': main()
