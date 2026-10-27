"""Rebuild LDS figures under audited, explicit source-method adaptations.

Usage: python -m handcrafted_ei.evaluation.reference_reproduction
Historical archives and model mechanisms are read-only.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import csv
import json
import platform
import sys
import numpy as np
from scipy.spatial.distance import cdist
from .reference_adapter import load_audited_dataset,extract_snapshots,reconstruct_currents
from .reference_dynamics import projection_energy,cross_temporal_distance,endpoint_clusters,paired_input_probe,exact_local_stability,piecewise_cascade_certificate
from .population_dynamics import evolve_batch,state_identity,recovery,perturbation_targets,field
from ..model.ei_network import EINetwork

ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'artifacts/paper2agent_reproduction'
SEEDS=(7,11,19)
AMPLITUDES=(.001,.02,.1,.3)


def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def csvwrite(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def finalize_manifest(out):
    """Refresh after all renderers/consistency checks; no circular self hashes."""
    out=Path(out)
    paths=[p for folder in ('model','task','simulation','config','evaluation','visualization','tests') for p in (ROOT/'handcrafted_ei'/folder).glob('*') if p.is_file()]
    paths += [ROOT/n for n in ('AGENTS.md','architecture.md','todo.md','README.md','handcrafted_ei/requirements.txt')]
    sources={str(f.relative_to(ROOT)).replace('\\','/'):sha256(f.read_bytes()).hexdigest() for f in paths}
    dump(out/'manifests/source_hashes.json',sources)
    results={str(f.relative_to(out)).replace('\\','/'):sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and ('lds_results' in f.parts or 'figures' in f.parts)}
    dump(out/'manifests/result_hashes.json',results)
    skill=Path('C:/Users/Totheinfinity/.codex/skills/paper2agent')
    dump(out/'manifests/skill_identity.json',{str(p):sha256(p.read_bytes()).hexdigest() for p in (skill/'SKILL.md',skill/'paper2skill/SKILL.md',skill/'paper2mcp/SKILL.md',skill/'paper2skill/scripts/paper_bundle.py')})


def identify(model,r):
    identity=state_identity(model,r,3)
    return identity if identity is not None else (-1,-1)


def run_mode(source,out,mode):
    d=load_audited_dataset(source,mode); snap=extract_snapshots(d); model=EINetwork(overrides=d['config'])
    folder=out/'lds_results'/mode;folder.mkdir(parents=True,exist_ok=True)
    dump(folder/'config.json',d['config'])
    model.remove_stimulus();model.clock[:]=0
    paths=evolve_batch(model,snap['rates'],2000); ends=paths[:,-1]
    times=np.arange(paths.shape[1])*model.config['dt_ms']
    labels=endpoint_clusters(ends); distances=cdist(ends,ends); fixed=[]; eigs=[]
    for i,state in enumerate(ends):
        metrics,eig=exact_local_stability(model,state);eigs.append(eig)
        start_id=identify(model,snap['rates'][i]); end_id=identify(model,state)
        certificate=piecewise_cascade_certificate(model,state)
        stable=bool((metrics['strict_local_stability'] or certificate['certified']) and metrics['residual_max_per_ms']<1e-8 and metrics['jacobian_fd_max_error']<1e-8)
        fixed.append(dict(trial=i,L=int(snap['conditions'][i,0]),D=int(snap['conditions'][i,1]),S=int(snap['conditions'][i,2]),
            endpoint_cluster=int(labels[i]),initial_branch=start_id[0],initial_position=start_id[1],endpoint_branch=end_id[0],endpoint_position=end_id[1],
            identity_retained=bool(start_id==end_id and end_id!=(-1,-1)),stable_endpoint=stable,
            tail_change_l2_100ms=float(np.linalg.norm(paths[i,-1]-paths[i,-21])),**metrics,**certificate))
    rng_states=np.array([np.random.default_rng(s).uniform(0,1,(24,len(model.rates))) for s in SEEDS])
    random_paths=evolve_batch(model,rng_states.reshape(-1,len(model.rates)),2000)
    random_ends=random_paths[:,-1]
    # CD deliberately pairwise and descriptive: fixed D/S, opposing positions.
    conditions=snap['conditions']; pairs=[np.flatnonzero((conditions[:,0]==l)&(conditions[:,1]==1)&(conditions[:,2]==1))[0] for l in (0,3)]
    cd=ends[pairs[1]]-ends[pairs[0]];cd/=np.linalg.norm(cd)
    center=(ends[pairs[0]]+ends[pairs[1]])/2
    coordinate=(paths-center)@cd
    # Perturbation PCA uses control trajectories, not a perturbed fit.
    train=paths[:,::4].reshape(-1,len(model.rates));origin=train.mean(0)
    _,singular,bt=np.linalg.svd(train-origin,full_matrices=False);basis=bt[:2].T
    np.savez_compressed(folder/'fixed_points.npz',times_ms=times,rates=paths,endpoints=ends,endpoint_distance=distances,
        cluster_labels=labels,conditions=conditions,initial_rates=snap['rates'],initial_clock=snap['clock'],
        clock_used=np.zeros(len(model.rates)),stimulus_used=np.zeros(len(model.rates)),tonic_used=model.tonic,
        eigenvalues=np.array(eigs),coding_direction=cd,coding_center=center,coding_coordinate=coordinate,
        coding_pair_trial_indices=pairs,random_initial_rates=rng_states,random_endpoints=random_ends,
        neuron_labels=d['labels'],neuron_types=d['neuron_types'],basis=basis,pca_center=origin,singular_values=singular)
    csvwrite(folder/'fixed_points.csv',fixed)
    basin=[];representative={}
    group_names=('full','response','active_branch','unselected_branch','E','I')
    for name in group_names:
        initial=[];meta=[]
        for i,endpoint in enumerate(ends):
            model.rates=endpoint.copy();indices=perturbation_targets(model,3)[name]
            for amplitude in AMPLITUDES:
                for seed in SEEDS:
                    eps=np.zeros(len(endpoint));direction=np.random.default_rng(seed).normal(size=len(indices))
                    eps[indices]=amplitude*direction/np.sqrt(np.mean(direction**2))
                    raw=endpoint+eps;clipped=np.clip(raw,0,1)
                    initial.append(clipped);meta.append((i,amplitude,seed,indices,raw))
        trace=evolve_batch(model,np.array(initial),2000)
        # Full local trajectories retained once, no duplicated matrices in reports.
        np.savez_compressed(folder/f'basin_{name}.npz',rates=trace,times_ms=times,initial_reference_index=[m[0] for m in meta],
                            amplitude=[m[1] for m in meta],seed=[m[2] for m in meta])
        for k,(i,amplitude,seed,indices,raw) in enumerate(meta):
            control=paths[i,-1];final=trace[k,-1];delta0=trace[k,0]-control
            model.rates=control.copy();same=identify(model,final)==identify(model,control) and identify(model,control)!=(-1,-1)
            masks=perturbation_targets(model,3)
            row=dict(trial=i,target=name,amplitude_preclip=amplitude,seed=seed,
                actual_target_rms=float(np.sqrt(np.mean(delta0[indices]**2))),actual_whole_rms=float(np.sqrt(np.mean(delta0**2))),
                clipping_fraction_target=float(np.mean((raw[indices]<0)|(raw[indices]>1))),
                initial_l2=float(np.linalg.norm(delta0)),final_l2=float(np.linalg.norm(final-control)),
                recovered=recovery(model,final,control,3),identity_retained=bool(same),
                branch_retained=bool(identify(model,control)[0]>=0 and identify(model,final)[0]==identify(model,control)[0]),
                position_retained=bool(identify(model,control)[1]>=0 and identify(model,final)[1]==identify(model,control)[1]))
            for group in group_names:
                row[f'final_{group}_l2']=float(np.linalg.norm((final-control)[masks[group]]))
                row[f'{group}_recovered']=bool(np.max(abs((final-control)[masks[group]]))<.02 and same)
            basin.append(row)
            if i==0 and name=='full' and amplitude==.3 and seed==7:
                reference=evolve_batch(model,control[None],2000)[0];delta=trace[k]-reference
                energy=projection_energy(delta,basis)
                representative=dict(control=reference,perturbed=trace[k],times_ms=times,
                    cross_temporal_distance=cross_temporal_distance(reference[::4],trace[k,::4]),cross_temporal_times_ms=times[::4],
                    basis=basis,pca_center=origin,**energy)
    csvwrite(folder/'basin.csv',basin)
    np.savez_compressed(folder/'state_perturbation.npz',**representative)
    currents=reconstruct_currents(d);inputs=[];input_summary=[]
    for assay in ('source_time','R3_fixed_clock'):
        if assay=='source_time':
            t=d['times_ms'];u=currents['stimulus'][0];clock=currents['clock'][0];initial=d['rates'][0,0];onset=500.
        else:
            t=times;u=np.zeros((len(t),len(model.rates)));clock=np.repeat(snap['clock'][0,None],len(t),axis=0);initial=snap['rates'][0];onset=20.
        # Same fixed random input mapping across conditions/encodings for each seed.
        for seed in SEEDS:
            direction=np.random.default_rng(seed).normal(size=len(model.rates));direction/=np.sqrt(np.mean(direction**2))
            pulse=paired_input_probe(model,initial,t,u,clock,direction,onset,50.,.25)
            if assay=='source_time': np.testing.assert_allclose(pulse['control'],d['rates'][0],atol=3e-15)
            train=pulse['control'];mu=train.mean(0);_,sv,bt=np.linalg.svd(train-mu,full_matrices=False);b=bt[:3].T
            energy=projection_energy(pulse['perturbed']-train,b[:,:2])
            actual=pulse['pulse_mask'][:,None]*.25*direction[None]
            payload={**pulse,**energy,'times_ms':t,'basis':b,'pca_center':mu,'singular_values':sv,
                'actual_perturbation_current':actual,'base_stimulus':u,'clock':clock,'tonic':model.tonic,
                'cross_temporal_distance':cross_temporal_distance(train[::4],pulse['perturbed'][::4]),'cross_temporal_times_ms':t[::4],
                'recorded_trial_id':0,'condition_LDS':conditions[0],'neuron_labels':d['labels'],'neuron_types':d['neuron_types']}
            np.savez_compressed(folder/f'input_{assay}_{seed}.npz',**payload)
            inputs.append((assay,seed))
            input_summary.append(dict(assay=assay,seed=seed,onset_ms=onset,duration_ms=50.,scalar_amplitude=.25,
                actual_current_rms=.25,current_l2=float(np.linalg.norm(.25*direction)),integrated_rms_ms=12.5,
                final_full_l2=float(np.linalg.norm(pulse['perturbed'][-1]-train[-1])),
                peak_full_l2=float(np.linalg.norm(pulse['perturbed']-train,axis=1).max()),
                max_projection_closure_error=float(abs(energy['closure_error']).max())))
    csvwrite(folder/'input_summary.csv',input_summary)
    # Honest fixed-point-centered slice, separate from Zhou Figure7.
    model.rates=ends[0].copy();grid=np.array([(x,y) for y in np.linspace(-.5,.5,11) for x in np.linspace(-.5,.5,11)])
    states=np.clip(ends[0]+grid@basis.T,0,1);vectors=np.array([field(model,r) for r in states]);pv=vectors@basis
    np.savez_compressed(folder/'local_flow.npz',xy=(states-ends[0])@basis,velocity=pv,
        offplane_norm=np.linalg.norm(vectors-pv@basis.T,axis=1),actual_states=states,full_field=vectors,basis=basis,origin=ends[0])
    stable_clusters=set(r['endpoint_cluster'] for r in fixed if r['stable_endpoint'])
    summary=dict(encoding=mode,neuron_count=len(model.rates),input_dimension={'one_hot':6,'ring':1,'topology':2}[mode],
        task_conditions=24,distinct_endpoint_clusters=len(set(labels)),stable_endpoint_clusters=len(stable_clusters),
        stable_endpoints=sum(r['stable_endpoint'] for r in fixed),identity_retained=sum(r['identity_retained'] for r in fixed),
        max_residual=max(r['residual_max_per_ms'] for r in fixed),max_fd_error=max(r['jacobian_fd_max_error'] for r in fixed),
        max_euler_consistency_error=max(r['euler_consistency_max_error'] for r in fixed),
        spectral_radius_range=[min(r['euler_spectral_radius'] for r in fixed),max(r['euler_spectral_radius'] for r in fixed)],
        clipping_spectrum_explanation='Saturated units have zero activation derivative: eigenvalues include -1/tau. Slow I_decay tau=120ms gives Euler 1-5/120=0.958333; equal radii do not establish identical basins.',
        basis_scope='unperturbed 24-condition tonic-only extension, stride4; full132 centered; tied singular directions not individually identifiable',
        fixed_field='sample=0, clock=0, original tonic retained; identical vector field for all24 states',
        random_initial_domain='72 independent uniform [0,1]^132 initial states, 24 per seed; not population/statistical repeats',
        random_endpoint_clusters=int(len(set(endpoint_clusters(random_ends)))),
        source_archive_sha256=d['archive_sha256'],model_parameters_changed=False,
        classification='METHOD ADAPTED; LDS-specific full-state diagnosis; source experimental data/statistics INCOMPATIBLE')
    dump(folder/'summary.json',summary)
    return summary


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'handcrafted_ei/artifacts/v2/run')
    p.add_argument('--output',type=Path,default=DEFAULT);p.add_argument('--encoding',choices=['one_hot','ring','topology','all'],default='all')
    p.add_argument('--render-only',action='store_true');p.add_argument('--no-render',action='store_true');args=p.parse_args(argv)
    args.output.mkdir(parents=True,exist_ok=True);modes=('one_hot','ring','topology') if args.encoding=='all' else (args.encoding,)
    if not args.render_only:
        summary=[]
        for mode in modes:
            print('Reconstructing',mode,flush=True);summary.append(run_mode(args.input,args.output,mode))
        dump(args.output/'manifests/numerical_summary.json',summary)
    if not args.no_render:
        from ..visualization.reference_figures import render
        render(args.output,modes)
    dump(args.output/'manifests/environment.json',dict(python=sys.version,executable=sys.executable,numpy=np.__version__,platform=platform.platform(),seeds=SEEDS,training=False))
    finalize_manifest(args.output)


if __name__=='__main__': main()
