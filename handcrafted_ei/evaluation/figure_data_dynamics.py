"""Figure 8/9 independent full-state assays; fixed model and archived input replay."""
from pathlib import Path
import csv
import hashlib
import json
import platform
import sys
import numpy as np
from scipy.spatial.distance import cdist
from .reference_adapter import load_audited_dataset, reconstruct_currents
from .reference_dynamics import paired_input_probe, exact_local_stability, piecewise_cascade_certificate
from .population_dynamics import evolve_batch, field, state_identity
from ..model.ei_network import EINetwork

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'handcrafted_ei/artifacts/v2/run'
REF = ROOT/'artifacts/paper2agent_reproduction/lds_results'
SEEDS = (7, 11, 19)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''):h.update(x)
    return h.hexdigest()


def csvwrite(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for row in rows for k in row))
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
    temp.replace(path)


def savez(path,**arrays):
    temp=path.with_name(path.stem+'.tmp.npz')
    np.savez_compressed(temp,**arrays)
    temp.replace(path)


def identity_batch(model, rates, stage):
    values=np.asarray(rates)[...,model.groups[f'R{stage}']].reshape(*np.asarray(rates).shape[:-1],-1,6)
    flat=values.reshape(*values.shape[:-2],-1)
    best=flat.argmax(-1);valid=flat.max(-1)>=.2
    return np.where(valid,best//6,-1),np.where(valid,best%6,-1)


def _receipt(path, inputs, parameters):
    payload={'schema_version':1,'inputs':{str(Path(p).relative_to(ROOT)):sha(p) for p in inputs},
             'parameters':parameters,'source_sha256':sha(__file__),'source':'independent evaluation arrays; no model/task changes',
             'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'rates_units':'dimensionless','seeds':list(SEEDS)}
    path.write_text(json.dumps(payload,indent=2),encoding='utf-8')


def fixed_point_data(d, output, grid_size=41, slice_variant='three_endpoint'):
    mode=d['encoding_type']; out=Path(output)/'derived'/mode;out.mkdir(parents=True,exist_ok=True)
    inputs=[REF/mode/'fixed_points.npz',REF/mode/'fixed_points.csv',REF/mode/'basin.csv']
    with np.load(inputs[0]) as source:
        endpoints=source['endpoints'].copy();conditions=source['conditions'].copy()
        clock=source['clock_used'].copy();stimulus=source['stimulus_used'].copy();tonic=source['tonic_used'].copy()
    model=EINetwork(overrides=d['config']);model.clock[:]=clock;model.stimulus[:]=stimulus
    if not np.array_equal(model.tonic,tonic):raise ValueError('fixed field tonic mismatch')
    rows=[];eigenvalues=[]
    for trial,state in enumerate(endpoints):
        stat,eig=exact_local_stability(model,state);cert=piecewise_cascade_certificate(model,state)
        eigenvalues.append(eig)
        rows.append(dict(trial=trial,L=int(conditions[trial,0]),D=int(conditions[trial,1]),S=int(conditions[trial,2]),**stat,**cert))
    csvwrite(out/'fig08_fixed_point_certificates.csv',rows)
    savez(out/'fig08_fixed_point_certificates.npz',endpoints=endpoints,conditions=conditions,eigenvalues=np.array(eigenvalues),
        clock=clock,stimulus=stimulus,tonic=tonic)
    # Four branches are separate six-position collections, never relabelled as six total.
    slice_paths=[]
    for branch,(direction,step) in enumerate([(1,1),(1,2),(-1,1),(-1,2)]):
        trials=np.flatnonzero((conditions[:,1]==direction)&(conditions[:,2]==step))
        trials=trials[np.argsort(conditions[trials,0])];points=endpoints[trials]
        centered=points-points.mean(0);_,singular,vt=np.linalg.svd(centered,full_matrices=False)
        pca_basis=vt[:2].T; center=points.mean(0)
        # A prespecified response-coordinate contrast plane; no rotation to improve recovery.
        observed=int(np.argmax(center[model.groups['R3']].reshape(-1,6).sum(1)))
        q=model.groups['R3'].reshape(-1,6)[observed]
        if slice_variant=='three_endpoint':
            center=points[:3].mean(0)
            q=q[np.argmax(points[:3][:,q],axis=1)]
            if len(set(q.tolist()))!=3:raise ValueError('three endpoint slice requires distinct observed active positions')
        elif slice_variant!='sixmean_control':raise ValueError('unknown slice variant')
        basis=np.zeros((len(center),2));basis[q[0],0]=1/np.sqrt(2);basis[q[1],0]=-1/np.sqrt(2)
        basis[q[0],1]=1/np.sqrt(6);basis[q[1],1]=1/np.sqrt(6);basis[q[2],1]=-2/np.sqrt(6)
        axis=np.linspace(-.8,.8,grid_size);xx,yy=np.meshgrid(axis,axis);xy=np.c_[xx.ravel(),yy.ravel()]
        initials=center+xy@basis.T
        legal=np.all((initials>=0)&(initials<=1),axis=1)
        ids=np.flatnonzero(legal);paths=np.empty((len(ids),401,len(center)))
        for start in range(0,len(ids),64):paths[start:start+64]=evolve_batch(model,initials[ids[start:start+64]],duration_ms=2000)
        end=paths[:,-1];residual=np.array([np.max(abs(field(model,r))) for r in end])
        distances=cdist(end,endpoints);nearest=distances.argmin(1)
        # Classify using full132 max norm and residual, not projected distance.
        maxnorm=np.max(abs(end[:,None,:]-endpoints[None,:,:]),axis=2)
        nearest=maxnorm.argmin(1);matched=maxnorm[np.arange(len(end)),nearest]<.02
        converged=residual<1e-7;classification=np.full(len(xy),-3,dtype=int) # invalid
        classification[ids]=np.where(~converged,-2,np.where(matched,nearest,-1))
        stem='fig08_six_point_basins' if slice_variant=='three_endpoint' else 'fig08_sixmean_control'
        path=out/f'{stem}_branch{branch}.npz'
        savez(path,rates=paths,times_ms=np.arange(0,2005,5),grid_xy=xy,grid_axis=axis,legal_mask=legal,
            legal_grid_indices=ids,initial_rates=initials[ids],classification=classification,endpoint_residual=residual,
            endpoint_maxnorm_to_references=maxnorm,reference_endpoints=endpoints,reference_conditions=conditions,
            selected_trials=trials,basis=basis,center=center,display_basis=pca_basis,singular_values=singular,
            clock=clock,stimulus=stimulus,tonic=tonic,slice_variant=np.array(slice_variant))
        slice_paths.append(path)
        print(f'fig08 {mode} {slice_variant} branch{branch}: {len(ids)}/{len(xy)} legal grid states',flush=True)
    _receipt(out/f'fig08_{slice_variant}_manifest.json',inputs+slice_paths,{'model_config':d['config'],'grid_size':grid_size,'duration_ms':2000,'chunk':64,'invalid':'mask, never clip',
        'classification':{'invalid':-3,'unconverged':-2,'other_equilibrium':-1,'matched':'index in 24 full132 reference endpoints'},
        'convergence_residual_max_per_ms':1e-7,'match_maxnorm':.02,'slice_variant':slice_variant,
        'direction_definition':'orthonormal response contrasts; three_endpoint uses observed active units of first three L conditions; sixmean_control uses first three branch units',
        'field':'archived clock_used/stimulus_used/tonic_used; identical across conditions'} )
    return rows


def stage_perturbations(d, output, amplitude=.25):
    """24 conditions × 3 temporal stages × 3 paired direction seeds, no process noise."""
    mode=d['encoding_type'];out=Path(output)/'derived'/mode;out.mkdir(parents=True,exist_ok=True)
    model=EINetwork(overrides=d['config']);currents=reconstruct_currents(d);times=d['times_ms']
    names=('pre_R2','between_R2_R3','R3_hold');events=d['events'][0]
    onsets=np.array([events['to_R2']-100,events['to_R3']-100,events['readout3_start']+20])
    directions=np.array([np.random.default_rng(seed).normal(size=len(model.rates)) for seed in SEEDS])
    directions/=np.sqrt(np.mean(directions**2,axis=1,keepdims=True))
    perturbed=np.empty((3,3,*d['rates'].shape));pulse=np.empty((3,len(times)),bool)
    rows=[];max_replay_error=0.
    for stage,onset in enumerate(onsets):
        for seed_index,seed in enumerate(SEEDS):
            for trial in range(24):
                probe=paired_input_probe(model,d['rates'][trial,0],times,currents['stimulus'][trial],currents['clock'][trial],
                    directions[seed_index],float(onset),50.,amplitude)
                error=float(np.max(abs(probe['control']-d['rates'][trial])))
                max_replay_error=max(max_replay_error,error)
                if error>1e-12:raise ValueError(f'control replay differs from REC: {error}')
                path=probe['perturbed'];perturbed[stage,seed_index,trial]=path;pulse[stage]=probe['pulse_mask']
                predicted=[];branch_retained=[];position_retained=[]
                for rank in range(1,5):
                    event=d['events'][trial][f'readout{rank}'];k=int(np.flatnonzero(times==event)[0])
                    # Match normal shared Y observation over decision window, never feed it back.
                    window=(times>event-d['config']['decision_ms'])&(times<=event)
                    y=path[window][:,model.groups['Y']].mean(0)
                    predicted.append(int(y.argmax()) if y.max()>=d['config']['decision_threshold'] else -1)
                    cb,cp=identity_batch(model,d['rates'][trial,k],rank);pb,pp=identity_batch(model,path[k],rank)
                    branch_retained.append(bool(cb==pb and cb>=0));position_retained.append(bool(cp==pp and cp>=0))
                task=d['tasks'][trial];target=task['target'];delta=path-d['rates'][trial]
                rows.append(dict(stage=names[stage],seed=seed,trial=trial,L=task['L'],D=task['D'],S=task['S'],
                    onset_ms=float(onset),duration_ms=50,actual_current_rms=amplitude,
                    direction_definition='seeded full132 Gaussian normalized to unit RMS; shared across stages and encodings',
                    replay_max_error=error,final_full_l2=float(np.linalg.norm(delta[-1])),
                    final_maxnorm=float(np.max(abs(delta[-1]))),
                    recovered=bool(np.max(abs(delta[-1]))<.02 and branch_retained[-1] and position_retained[-1]),
                    sequence_correct=predicted==target,outputs=';'.join(map(str,predicted)),
                    target=';'.join(map(str,target)),branch_identity_all=all(branch_retained),position_identity_all=all(position_retained),
                    R4_branch_retained=branch_retained[-1],R4_position_retained=position_retained[-1],
                    **{f'R{i+1}_correct':predicted[i]==target[i] for i in range(4)}))
            print(f'fig09 {mode} {names[stage]} seed{seed} replay_error={max_replay_error:.3g}',flush=True)
    savez(out/'fig09_stage_perturbations.npz',control=d['rates'],perturbed=perturbed,times_ms=times,
        stages=np.array(names),seeds=np.array(SEEDS),onsets_ms=onsets,pulse_mask=pulse,directions=directions,
        added_current=amplitude*pulse[:,None,:,None]*directions[None,:,None,:],
        base_stimulus=currents['stimulus'],clock=currents['clock'],tonic=model.tonic,
        conditions=np.array([(t['L'],t['D'],t['S']) for t in d['tasks']]),neuron_labels=d['labels'],
        actual_current_rms=np.full((3,3),amplitude),noise_control=np.zeros((len(times),len(model.rates))),
        noise_perturbed=np.zeros((len(times),len(model.rates))))
    csvwrite(out/'fig09_recovery_by_stage.csv',rows)
    _receipt(out/'fig09_manifest.json',[Path(d['archive_path']),out/'fig09_stage_perturbations.npz'],
        {'model_config':d['config'],'pulse_duration_ms':50,'onsets_ms':onsets.tolist(),'actual_current_rms':amplitude,
         'max_control_replay_error':max_replay_error,'no_process_noise':True,'independent_unit':'direction seed, not biological repetition',
         'normal_behavior_readout':'same shared Y decision-window mean as simulator','target_access':'evaluation only, after independent replay'})
    return rows


def run(figures=(8,9), encodings=('one_hot','ring','topology'), output=None, grid_size=41):
    output=Path(output or ROOT/'artifacts/neural_paper_figures_v1')
    for mode in encodings:
        d=load_audited_dataset(RAW,mode)
        if 8 in figures:
            for variant in ('sixmean_control','three_endpoint'):fixed_point_data(d,output,grid_size,variant)
        if 9 in figures:stage_perturbations(d,output)
    return output


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--figures',nargs='+',type=int,default=[8,9]);p.add_argument('--encodings',nargs='+',default=['one_hot','ring','topology']);p.add_argument('--output');p.add_argument('--grid-size',type=int,default=41)
    a=p.parse_args();run(a.figures,a.encodings,a.output,a.grid_size)
