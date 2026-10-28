"""Fresh reviewer recomputation, independent of Figure 8--10 analysis helpers."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
from zipfile import ZipFile
from handcrafted_ei.model.ei_network import EINetwork

ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/'artifacts/neural_paper_figures_v1'
reports=[]
readcsv=lambda path:list(csv.DictReader(Path(path).open(encoding='utf-8-sig')))
def equal(a,b):np.testing.assert_allclose(a,b,atol=1e-10,rtol=1e-9)
def field(model,x,external):return (-x+np.clip(x@model.signed_weights.T+external,0,1))/model.tau
def ident(x,idx):
    z=x[idx].reshape(-1,6);return tuple(np.unravel_index(z.argmax(),z.shape)) if z.max()>=.2 else (-1,-1)
for enc in ('one_hot','ring','topology'):
    folder=OUT/'derived'/enc; meta=json.loads((ROOT/'artifacts/neural_representation_v2/data'/enc/'metadata.json').read_text()); model=EINetwork(overrides=meta['config']); raw=np.load(ROOT/'artifacts/neural_representation_v2/data'/enc/'recording.npz'); base=raw['rates']; legal_count=[]; labelsets=[]
    certs=readcsv(folder/'fig08_fixed_point_certificates.csv')
    for branch in range(4):
        z=np.load(folder/f'fig08_six_point_basins_branch{branch}.npz'); path=z['rates']; endpoint=path[:,-1]; external=z['clock']+z['stimulus']+z['tonic']-model.theta
        initials=z['center']+z['grid_xy']@z['basis'].T; legal=np.all((initials>=0)&(initials<=1),axis=1); assert np.array_equal(legal,z['legal_mask']); assert np.array_equal(np.flatnonzero(legal),z['legal_grid_indices']); equal(initials[legal],path[:,0]); equal(z['basis'].T@z['basis'],np.eye(2)); assert path.shape[1:]==(401,132)
        for j in (0,1,50,150,300,399):equal(path[:,j+1],path[:,j]+5*field(model,path[:,j],external))
        residue=np.max(abs(field(model,endpoint,external)),axis=1); distances=np.max(abs(endpoint[:,None]-z['reference_endpoints'][None]),axis=2); equal(residue,z['endpoint_residual']); equal(distances,z['endpoint_maxnorm_to_references']); best=distances.argmin(1); classified=np.full(len(legal),-3); classified[legal]=np.where(residue>=1e-7,-2,np.where(distances[np.arange(len(best)),best]<.02,best,-1)); assert np.array_equal(classified,z['classification'])
        legal_count.append(int(legal.sum())); labelsets.append(np.unique(classified).tolist())
        if branch==0:
            refs=z['reference_endpoints']
            for state,row in zip(refs,certs):
                drive=model.signed_weights@state+external;res=field(model,state,external); equal(float(row['residual_max_per_ms']),abs(res).max()); kink=(abs(drive)<=1e-7)|(abs(drive-1)<=1e-7); enabled=((drive>0)&(drive<1))|kink
                edges=enabled[:,None]&(model.signed_weights!=0); deg=edges.sum(1); queue=list(np.flatnonzero(deg==0)); order=[]
                while queue:
                    a=queue.pop();order.append(a)
                    for b in np.flatnonzero(edges[:,a]):
                        deg[b]-=1
                        if deg[b]==0:queue.append(b)
                assert len(order)==132 and row['acyclic_union']=='True' and row['certified']=='True'
                eq=state.copy()
                for q in order:eq[q]=np.clip(model.signed_weights[q]@eq+external[q],0,1)
                assert abs(field(model,eq,external)).max()<1e-12
                equal(abs(eq-state).max(),float(row['equilibrium_max_difference'])); assert abs(eq-state).max()<float(row['regime_neighborhood_maxnorm_margin'])
                slope=((drive>0)&(drive<1)).astype(float);slope[np.isclose(drive,0,atol=1e-10)|np.isclose(drive,1,atol=1e-10)]=.5; jac=(-np.eye(132)+slope[:,None]*model.signed_weights)/model.tau[:,None];eig=np.linalg.eigvals(jac); equal(eig.real.max(),float(row['max_real_eigenvalue_per_ms'])); equal(abs(1+5*eig).max(),float(row['euler_spectral_radius']))
    controls_checked=0
    for branch in range(4):
        source=folder/f'fig08_sixmean_control_branch{branch}.npz'
        if not source.exists():continue
        q=np.load(source);state=q['rates'];initials=q['center']+q['grid_xy']@q['basis'].T;legal=np.all((initials>=0)&(initials<=1),axis=1);assert np.array_equal(legal,q['legal_mask']);equal(state[:,0],initials[legal]);external=q['clock']+q['stimulus']+q['tonic']-model.theta;end=state[:,-1];res=np.max(abs(field(model,end,external)),axis=1);distance=np.max(abs(end[:,None]-q['reference_endpoints'][None]),axis=2);best=distance.argmin(1);labels=np.full(len(legal),-3);labels[legal]=np.where(res>=1e-7,-2,np.where(distance[np.arange(len(best)),best]<.02,best,-1));assert np.array_equal(labels,q['classification']);controls_checked+=1
    z=np.load(folder/'fig09_stage_perturbations.npz'); ctrl=z['control']; pert=z['perturbed']; t=z['times_ms']; equal(ctrl,base); assert np.count_nonzero(z['noise_control'])==np.count_nonzero(z['noise_perturbed'])==0; equal(np.sqrt(np.mean(z['directions']**2,axis=1)),np.ones(3)); pulse=z['added_current']; mask=z['pulse_mask']
    for s,onset in enumerate(z['onsets_ms']):
        assert np.array_equal(mask[s],(t>onset)&(t<=onset+50))
        for k in range(3):
            equal(pulse[s,k],.25*mask[s,:,None]*z['directions'][k]);equal(np.sqrt(np.mean(pulse[s,k,mask[s]]**2)),.25)
            for j in np.unique(np.r_[0,100,np.flatnonzero(mask[s])[[0,-1]]-1,661]):
                ext=z['tonic']-model.theta+z['base_stimulus'][:,j+1]+z['clock'][:,j+1]+pulse[s,k,j+1];equal(pert[s,k,:,j+1],pert[s,k,:,j]+5*field(model,pert[s,k,:,j],ext))
    rows=readcsv(folder/'fig09_recovery_by_stage.csv'); assert len(rows)==216
    for row in rows:
        s=list(z['stages']).index(row['stage']);k=list(z['seeds']).index(int(row['seed']));i=int(row['trial']); path=pert[s,k,i];delta=path-ctrl[i];equal(float(row['final_full_l2']),np.linalg.norm(delta[-1]));equal(float(row['final_maxnorm']),abs(delta[-1]).max());assert (row['recovered']=='True')==(abs(delta[-1]).max()<.02)
        cb,cp=ident(ctrl[i,-1],model.groups['R4']);pb,pp=ident(path[-1],model.groups['R4']);assert (row['R4_branch_retained']=='True')==(cb==pb and cb>=0);assert (row['R4_position_retained']=='True')==(cp==pp and cp>=0)
        observed=[]
        for stage in range(1,5):
            event=meta['events'][i][f'readout{stage}'];window=(t>event-meta['config']['decision_ms'])&(t<=event);y=path[window][:,model.groups['Y']].mean(0);observed.append(int(y.argmax()) if y.max()>=meta['config']['decision_threshold'] else -1)
        assert row['outputs']==';'.join(map(str,observed));assert (row['sequence_correct']=='True')==(observed==meta['tasks'][i]['target'])
    reports.append({'encoding':enc,'figure8':'PASS','legal_grid_counts':legal_count,'classifications':labelsets,'sixmean_control_slices_verified':controls_checked,'certified_endpoints':24,'figure9':'PASS','paired_conditions':216,'limitations':'Finite affine initial-state slices and local piecewise certificate, not exhaustive/global attractor proof'})
    for assay in ('source_time','R3_fixed_clock'):
        for seed in (7,11,19):
            q=np.load(ROOT/'artifacts/paper2agent_reproduction/lds_results'/enc/f'input_{assay}_{seed}.npz');c=q['control'];p=q['perturbed'];delta=p-c;ii=np.searchsorted(q['times_ms'],q['cross_temporal_times_ms']);equal(q['times_ms'][ii],q['cross_temporal_times_ms']);equal(q['cross_temporal_distance'],np.sqrt(np.sum((c[ii,None]-p[None,ii])**2,axis=2)));equal(q['full_squared'],np.sum(delta*delta,axis=1));equal(q['basis'].T@q['basis'],np.eye(3));equal(q['projected_squared'],np.sum((delta@q['basis'][:,:2])**2,axis=1));equal(q['noise_control'],q['noise_perturbed']);assert q['pulse_mask'].sum()==10
    print(enc,'Figures8/9 PASS',flush=True)

z=np.load(OUT/'derived/comparison/fig10_common_basis.npz'); big=np.load(OUT/'derived/comparison/fig10_matched_current_full.npz'); arrays=[np.load(ROOT/'artifacts/neural_representation_v2/data'/str(e)/'recording.npz')['rates'] for e in z['encodings']];train=np.concatenate([r[:,::int(z['fit_stride'])].reshape(-1,132) for r in arrays]);equal(z['center'],train.mean(0));equal(z['basis'].T@z['basis'],np.eye(132));cov=(train-z['center']).T@(train-z['center']);ev=np.linalg.eigvalsh(cov)[::-1];equal(z['evr'],ev/ev.sum())
for i,r in enumerate(arrays):equal(z['scores'][i],(r-z['center'])@z['basis'][:,:3]);equal(z['one_hot_scores'][i],(r-z['one_hot_center'])@z['one_hot_basis'][:,:3])
rows=readcsv(OUT/'derived/comparison/fig10_encoding_comparison.csv');control=big['control'];perturbed=big['perturbed'];currents=big['actual_current'];error=np.linalg.norm(perturbed-control,axis=-1);equal(big['full_l2'],error);equal(currents[0],currents[1]);equal(currents[0],currents[2]);assert len(rows)==648
for i,enc in enumerate(z['encodings']):
    meta=json.loads((ROOT/'artifacts/neural_representation_v2/data'/str(enc)/'metadata.json').read_text());ids=meta['population_indices']['R4'];t=z['times_ms'];group=[row for row in rows if row['encoding']==enc]
    for k,row in enumerate(group):
        trial=int(row['trial']);equal(control[i,k],arrays[i][trial]);pulse=np.linalg.norm(currents[i,k],axis=1)>0;assert pulse.sum()==10;equal(np.sqrt(np.mean(currents[i,k,pulse]**2)),float(row['current_rms']));delta=perturbed[i,k]-control[i,k];equal(float(row['final_l2']),error[i,k,-1]);equal(float(row['max_l2']),error[i,k].max());equal(float(row['final_linf']),abs(delta[-1]).max());identity=ident(perturbed[i,k,-1],ids)==ident(control[i,k,-1],ids) and ident(perturbed[i,k,-1],ids)!=(-1,-1);assert (row['final_identity_retained']=='True')==identity;assert (row['recovered']=='True')==(identity and abs(delta[-1]).max()<.02)
        decoded=[]
        for path in (control[i,k],perturbed[i,k]):
            sequence=[]
            for stage in range(1,5):
                event=meta['events'][trial][f'readout{stage}'];window=(t>event-meta['config']['decision_ms'])&(t<=event);y=path[window][:,meta['population_indices']['Y']].mean(0);sequence.append(int(y.argmax()) if y.max()>=meta['config']['decision_threshold'] else -1)
            decoded.append(sequence)
        assert (row['sequence_matches_control']=='True')==(decoded[0]==decoded[1])
reports.append({'figure10':'PASS','matched_assays':648,'same_current_arrays_all_encodings':True,'joint_PCA':'orthonormality/mean/eigenvariance/scores PASS','raw_coordinate_noise':'separate fig10_raw_noise_doses.csv; not pooled with matched R3-current assay'})
raw_doses=readcsv(OUT/'derived/comparison/fig10_raw_noise_doses.csv');assert len(raw_doses)==216
angles=np.arange(6)*np.pi/3;vectors=np.c_[np.cos(angles),np.sin(angles)]
for enc in ('one_hot','ring','topology'):
    meta=json.loads((ROOT/'artifacts/neural_representation_v2/data'/enc/'metadata.json').read_text());kappa=meta['config']['encoding_kappa'];gain=meta['config']['w_input']
    def embed(x):
        if enc=='one_hot':v=x.copy()
        elif enc=='ring':v=np.exp(kappa*(np.cos(x[0]-angles)-1))
        else:v=np.exp(kappa*(vectors@(x/np.linalg.norm(x))-1))
        return gain*v/np.linalg.norm(v)
    for seed in (7,11,19):
        path=ROOT/'handcrafted_ei/artifacts/v2/run'/f'{enc}__noise_0.03_{seed}.zip';sha=hashlib.sha256(path.read_bytes()).hexdigest()
        with ZipFile(path) as archive:
            for row in [r for r in raw_doses if r['encoding']==enc and int(r['seed'])==seed]:
                i=int(row['trial']);task=json.loads(archive.read(f'{i:02}_task.json'));a=np.array(task['encoded']['x_L']);b=np.array(meta['tasks'][i]['encoded']['x_L']);delta=a-b
                if enc=='ring':delta=np.arctan2(np.sin(delta),np.cos(delta))
                equal(float(row['raw_coordinate_l2']),np.linalg.norm(delta));current=embed(a)-embed(b);equal(float(row['actual_R1_current_rms']),np.sqrt(np.mean(current**2)));equal(float(row['actual_R1_current_l2']),np.linalg.norm(current));assert row['noise_archive_sha256']==sha
reports.append({'raw_noise_dose_rows':216,'independent_encoded_to_R1_formula_audit':'PASS','dose_types':'raw coordinate L2 and mapped R1 current RMS/L2 kept separate'})
payload={'status':'PASS_WITH_LIMITS','reviewer':'fig04_07 agent; did not implement Figures8–10','checks':reports,'reference_Zhou':'original local Fig7 and caption actually viewed; full Euclidean distances and finite input pulse are adapted, original 17 trained-network statistics are not reproduced','source_exact':'BLOCKED: author Fig7 analysis, trained weights and original raw trajectories absent; no training executed','validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'manifests/independent_validation.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');print(json.dumps(payload,indent=2))
