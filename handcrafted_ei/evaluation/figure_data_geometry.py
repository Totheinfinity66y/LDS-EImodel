"""Read-only, auditable data products for paper Figures 4--7."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from .population_activity import validate_dataset, population_sets, branch_masks, stage_samples, save_rows
from .decoding import condition_folds, centroid_accuracy

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'artifacts/neural_representation_v2'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(encoding):
    folder = SOURCE / 'data' / encoding
    meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
    with np.load(folder / 'recording.npz') as z:
        d = {k: z[k] for k in z.files}
    d.update(meta)
    d['groups'] = {k: np.asarray(v, int) for k, v in meta['population_indices'].items()}
    d['labels'] = d['neuron_labels']
    validate_dataset(d)
    if d['rates'].shape != (24, 663, 132):
        raise ValueError('baseline contract changed; audit before plotting')
    return d


def pca(x, k=3):
    mean = x.mean(0)
    _, s, vt = np.linalg.svd(x - mean, full_matrices=False)
    return (x - mean) @ vt[:k].T, mean, vt[:k], s*s / np.sum(s*s)


def basis(x, tol=1e-8):
    x = x - x.mean(0)
    _, s, vt = np.linalg.svd(x, full_matrices=False)
    keep = s > max(tol, s[0]*1e-8)
    return vt[keep].T, float(np.sum(s*s))


def build(encoding, output, figures=(4, 5, 6, 7)):
    d = load(encoding); r=d['rates']; t=d['times_ms']; tasks=d['tasks']
    met=SOURCE/'metrics'/encoding
    out=Path(output)/'derived'/encoding; out.mkdir(parents=True, exist_ok=True)
    result={'dataset':d, 'products':{}, 'inputs':[SOURCE/'data'/encoding/'recording.npz', SOURCE/'data'/encoding/'metadata.json']}
    geometry=np.load(met/'subspace_geometry.npz'); result['inputs'].append(met/'subspace_geometry.npz')
    scores=geometry['global_scores']; mean=geometry['global_mean']; comp=geometry['global_components']
    np.testing.assert_allclose(scores, (r-mean)@comp.T, atol=1e-10)
    fit_stride=max(1,r.shape[1]//160)
    np.testing.assert_allclose(mean,r[:,::fit_stride,:].reshape(-1,r.shape[2]).mean(0),atol=1e-10)
    common={'times_ms':t, 'pca_scores':scores, 'pca_components':comp,'pca_mean':mean,'pca_evr':geometry['global_evr'],'pca_fit_time_indices':np.arange(0,len(t),fit_stride)}
    if 4 in figures:
        speed=np.linalg.norm(np.diff(r,axis=1),axis=2)/np.diff(t)[None,:]
        pack={**common, 'speed_times_ms':t[1:],'full_state_speed_per_ms':speed, 'variable_scores':geometry['variable_scores'], 'variable_axes':geometry['variable_axes']}
        for s in (2,3,4):
            j=np.argmin(abs(t-d['events'][0][f'to_R{s}']))
            pack[f'R{s}_displacement']=np.linalg.norm(r-r[:,j:j+1,:],axis=2)
        result['products'][4]=pack
        save_rows(out/'fig04_transition_kinematics.csv',[{'trial':i,'time_ms':float(t[j+1]),'speed_full_132_per_ms':float(speed[i,j])} for i in range(len(r)) for j in range(len(t)-1)])
    if 5 in figures:
        pairs=[(a,b) for a in range(4) for b in range(a+1,4)]
        masks=branch_masks(d,3); pops=population_sets(d)
        scopes={'whole':pops['whole'],'response':pops['response'],'shared':np.setdiff1d(pops['whole'],pops['response'])}
        pack={**common, 'pairs':np.array(pairs), 'variance_tolerance':np.array(1e-8)}; rows=[]
        states=stage_samples(d,3)
        for scope,idx in scopes.items():
            angles=np.full((len(t),6,5),np.nan); cent=np.zeros((len(t),6)); ranks=np.zeros((len(t),4),int)
            for j in range(len(t)):
                bs=[basis(r[m,j][:,idx]) for m in masks]
                ranks[j]=[q.shape[1] for q,v in bs]
                for p,(a,b) in enumerate(pairs):
                    cent[j,p]=np.linalg.norm(r[masks[a],j][:,idx].mean(0)-r[masks[b],j][:,idx].mean(0))
                    qa,va=bs[a]; qb,vb=bs[b]
                    if va>1e-8 and vb>1e-8 and qa.shape[1] and qb.shape[1]:
                        vals=np.degrees(np.arccos(np.clip(np.linalg.svd(qa.T@qb,compute_uv=False),0,1)))
                        angles[j,p,:min(5,len(vals))]=vals[:5]
            pack[f'{scope}_angles_degrees']=angles; pack[f'{scope}_centroid_distance']=cent; pack[f'{scope}_ranks']=ranks; pack[f'{scope}_indices']=idx
            for a,b in pairs:
                xa=states[masks[a]][:,idx]; xb=states[masks[b]][:,idx]; qa,va=basis(xa); qb,vb=basis(xb)
                ang=np.degrees(np.arccos(np.clip(np.linalg.svd(qa.T@qb,compute_uv=False),0,1))) if va>1e-8 and vb>1e-8 else np.array([])
                a0=xa-xa.mean(0); b0=xb-xb.mean(0)
                folded=[states[m][:,d['groups']['R3']].reshape(6,4,6).sum(1) for m in masks]
                fa,_=basis(folded[a]); fb,_=basis(folded[b]); rank=min(fa.shape[1],fb.shape[1])
                rows.append({'scope':scope,'branch_a':a,'branch_b':b,'angles_degrees':';'.join(map(str,ang)), 'rank_a':qa.shape[1],'rank_b':qb.shape[1], 'cross_vaf_a_to_b':np.sum((a0@qb)**2)/va if va>1e-8 else np.nan,'cross_vaf_b_to_a':np.sum((b0@qa)**2)/vb if vb>1e-8 else np.nan,'within_vaf_a':1. if va>1e-8 else np.nan,'within_vaf_b':1. if vb>1e-8 else np.nan,'structural_response_support_overlap':0.,'folded_R3_position_overlap':float(np.sum((fa.T@fb)**2)/rank) if rank else np.nan})
        save_rows(out/'fig05_principal_angles.csv',rows); pack['angle_rows']=rows
        result['products'][5]=pack
    if 6 in figures:
        ids=np.array([i for i,v in enumerate(tasks) if v['D']==1 and v['S']==1]); states=stage_samples(d,3)[ids]
        xy,mu,components,evr=pca(states,2)
        idx=d['groups']['R3'][:6]; x=r[ids][:,:,idx]; target=np.array([v['target'][2] for v in np.array(tasks,dtype=object)[ids]])
        chosen=np.take_along_axis(x,target[:,None,None].repeat(len(t),1),axis=2)[:,:,0]
        competitors=x.copy()
        for i,c in enumerate(target): competitors[i,:,c]=-np.inf
        j=np.argmin(abs(t-d['events'][0]['readout3']))
        response=population_sets(d)['response']
        rd=lambda a:np.linalg.norm(a[:,None]-a[None,:],axis=2)
        result['products'][6]={'times_ms':t,'trial_indices':ids,'states':states,'pca_scores':xy,'pca_mean':mu,'pca_components':components,'pca_evr':evr,'whole_rdm':rd(states),'response_rdm':rd(states[:,response]),'response_indices':response,'active_branch_indices':idx,'position_identity':x.argmax(2),'expected_position':target,'selected_rate':chosen,'competitor_rate':competitors.max(2),'position_margin':chosen-competitors.max(2),'position_drift':np.linalg.norm(r[ids]-r[ids,j:j+1],axis=2)}
        metrics=result['products'][6]
        save_rows(out/'fig06_position_stability.csv',[{'trial':int(ids[i]),'time_ms':float(t[k]),'expected_position':int(target[i]),'position_identity':int(metrics['position_identity'][i,k]),'selected_rate':float(chosen[i,k]),'competitor_rate':float(metrics['competitor_rate'][i,k]),'position_margin':float(metrics['position_margin'][i,k]),'position_drift_full_132':float(metrics['position_drift'][i,k])} for i in range(6) for k in range(len(t))])
    if 7 in figures:
        baseline=np.load(met/'decoding.npz'); noise=np.load(met/'decoding_noise_seed.npz')
        result['inputs'] += [met/f for f in ('decoding.npz','decoding_splits.json','decoding_noise_seed.npz','decoding_noise_seed_splits.json')]
        tids=np.array([np.argmin(abs(t-v)) for v in baseline['times_ms']]); branch=np.array([(v['D']==-1)*2+v['S']-1 for v in tasks]); folds=condition_folds(tasks,branch)
        xx=r[:,tids,:][:,:,population_sets(d)['response']]
        curve=np.array([np.mean([centroid_accuracy(xx[a,k],branch[a],xx[b,k],branch[b]) for a,b in folds]) for k in range(len(tids))])
        # Four-way D/S branch identity is defined only from the R3 transfer onward.
        curve[t[tids]<d['events'][0]['to_R3']]=np.nan
        result['products'][7]={'times_ms':t[tids],'branch_accuracy':curve,'branch_chance':np.array(.25),'response_indices':population_sets(d)['response'],**{f'baseline__{k}':baseline[k] for k in baseline.files},**{f'noise__{k}':noise[k] for k in noise.files}}
        save_rows(out/'fig07_branch_decoding.csv',[{'time_ms':float(tt),'accuracy':float(value),'chance':.25,'valid_label':bool(tt>=d['events'][0]['to_R3']),'split':'disjoint LDS condition folds'} for tt,value in zip(t[tids],curve)])
        (out/'fig07_branch_decoding_splits.json').write_text(json.dumps({'train_test_folds':[(a.tolist(),b.tolist()) for a,b in folds],'label':'D/S four-way branch; valid after R3 transfer','method':'nearest centroid; fractional tie credit; disjoint condition tuples'},indent=2),encoding='utf-8')
    names={4:'transition_kinematics',5:'temporal_subspaces',6:'position_stability',7:'branch_decoding'}
    for number,pack in result['products'].items():
        np.savez_compressed(out/f'fig{number:02d}_{names[number]}.npz',**{k:v for k,v in pack.items() if k!='angle_rows'})
    return result
