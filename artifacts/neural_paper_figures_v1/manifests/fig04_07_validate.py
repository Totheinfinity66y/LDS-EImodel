"""Independent NumPy recomputation of Figure 4--7 exported numerical arrays."""
from pathlib import Path
import csv
import json
import hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/neural_paper_figures_v1'
checks=[]
for enc in ('one_hot','ring','topology'):
    base=ROOT/'artifacts/neural_representation_v2/data'/enc
    raw=np.load(base/'recording.npz'); m=json.loads((base/'metadata.json').read_text())
    r=raw['rates']; t=raw['times_ms']; groups=m['population_indices']; tasks=m['tasks']; ev=m['events'][0]
    p4=np.load(OUT/'derived'/enc/'fig04_transition_kinematics.npz')
    np.testing.assert_allclose(p4['pca_scores'],(r-p4['pca_mean'])@p4['pca_components'].T,atol=1e-11)
    np.testing.assert_allclose(p4['full_state_speed_per_ms'],np.sqrt(np.sum(np.diff(r,axis=1)**2,axis=2))/np.diff(t))
    np.testing.assert_allclose(p4['pca_mean'],r[:,p4['pca_fit_time_indices']].reshape(-1,132).mean(0),atol=1e-11)
    p5=np.load(OUT/'derived'/enc/'fig05_temporal_subspaces.npz'); masks=[np.array([q['D']==d and q['S']==s for q in tasks]) for d in (1,-1) for s in (1,2)]
    def qfit(x):
        x=x-x.mean(0); _,s,v=np.linalg.svd(x,full_matrices=False)
        return v[s>max(1e-8,s[0]*1e-8)].T,np.sum(s*s)
    undefined=0
    for scope in ('whole','response','shared'):
        idx=p5[scope+'_indices']
        for time in (0,200,1900,2000,2500,2840,3310):
            j=np.argmin(abs(t-time)); mats=[r[mask,j][:,idx] for mask in masks]
            for pair,(a,b) in enumerate(p5['pairs']):
                qa,va=qfit(mats[a]); qb,vb=qfit(mats[b]); stored=p5[scope+'_angles_degrees'][j,pair]
                if va<=1e-8 or vb<=1e-8 or not qa.shape[1] or not qb.shape[1]:
                    assert np.isnan(stored).all(); undefined+=1
                else:
                    ang=np.degrees(np.arccos(np.clip(np.linalg.svd(qa.T@qb,compute_uv=False),0,1)))
                    np.testing.assert_allclose(stored[:len(ang)],ang,atol=1e-6)
                np.testing.assert_allclose(p5[scope+'_centroid_distance'][j,pair],np.linalg.norm(mats[a].mean(0)-mats[b].mean(0)))
    states=np.stack([v[(t>ev['readout3']-m['config'].get('decision_ms',20))&(t<=ev['readout3'])].mean(0) for v in r])
    for row in csv.DictReader((OUT/'derived'/enc/'fig05_principal_angles.csv').open()):
        scope=row['scope']; idx=p5[scope+'_indices']; a=int(row['branch_a']); b=int(row['branch_b']); xa=states[masks[a]][:,idx]; xb=states[masks[b]][:,idx]; qa,va=qfit(xa); qb,vb=qfit(xb)
        if va>1e-8:
            np.testing.assert_allclose(float(row['cross_vaf_a_to_b']),np.sum(((xa-xa.mean(0))@qb)**2)/va,atol=1e-10)
        if vb>1e-8:
            np.testing.assert_allclose(float(row['cross_vaf_b_to_a']),np.sum(((xb-xb.mean(0))@qa)**2)/vb,atol=1e-10)
    p6=np.load(OUT/'derived'/enc/'fig06_position_stability.npz'); x=p6['states']; np.testing.assert_allclose(p6['whole_rdm'],np.sqrt(np.sum((x[:,None]-x[None,:])**2,axis=2)))
    idx=p6['response_indices']; np.testing.assert_allclose(p6['response_rdm'],np.sqrt(np.sum((x[:,None,idx]-x[None,:,idx])**2,axis=2)))
    np.testing.assert_allclose(p6['pca_scores'],(x-p6['pca_mean'])@p6['pca_components'].T)
    np.testing.assert_allclose(p6['position_margin'],p6['selected_rate']-p6['competitor_rate'])
    p7=np.load(OUT/'derived'/enc/'fig07_branch_decoding.npz'); splits=json.loads((OUT/'derived'/enc/'fig07_branch_decoding_splits.json').read_text())['train_test_folds']; y=np.array([(v['D']==-1)*2+v['S']-1 for v in tasks])
    for k,time in enumerate(p7['times_ms']):
        if time<ev['to_R3']: assert np.isnan(p7['branch_accuracy'][k]); continue
        j=np.argmin(abs(t-time)); xx=r[:,j][:,p7['response_indices']]; scores=[]
        for tr,te in splits:
            assert not set(tr)&set(te); labels=np.unique(y[tr]); centers=np.stack([xx[np.asarray(tr)[y[tr]==v]].mean(0) for v in labels]); distances=((xx[te,None]-centers)**2).sum(2); nearest=np.isclose(distances,distances.min(1,keepdims=True),rtol=1e-9,atol=1e-12); correct=labels[None,:]==y[te,None]; scores.append(np.mean((nearest&correct).sum(1)/nearest.sum(1)))
        np.testing.assert_allclose(p7['branch_accuracy'][k],np.mean(scores))
    for number in (4,5,6,7):
        manifest=json.loads((OUT/'manifests'/f'fig{number:02d}_{enc}.json').read_text())
        for key in ('input_sha256','source_sha256','outputs_sha256'):
            for name,expected in manifest[key].items():
                assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected,(name,'hash mismatch')
    checks.append({'encoding':enc,'status':'PASS','independent_recomputed':'PCA scores/fit mean/full-state speed; temporal angles, NA gates, centroids; all CSV cross-VAF; six-state RDM/PCA/margin; all branch-probe times; all manifest hashes','NA_checks':undefined})
(OUT/'manifests/fig04_07_numeric_validation.json').write_text(json.dumps({'status':'PASS','checks':checks,'validator_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
print(json.dumps(checks,indent=2))
