"""Independent Figure4--7 formulas; never imports the figure-data implementation."""
from pathlib import Path
from hashlib import sha256
import csv,json
import numpy as np
from scipy.linalg import subspace_angles,svd
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/neural_paper_figures_v1'

def check(a,b,atol=1e-8):
    np.testing.assert_allclose(a,b,atol=atol,rtol=1e-8,equal_nan=True)
    return float(np.nanmax(abs(np.asarray(a)-np.asarray(b)))) if np.any(np.isfinite(a)) else None

def orth(x):
    u,s,v=svd(x-x.mean(0),full_matrices=False)
    q=v[s>max(1e-8,s[0]*1e-8)].T
    return q,float(np.linalg.norm(x-x.mean(0),'fro')**2)

def run():
    result={'reviewer':'/root/fig01_03; independent of Figure4--7 implementation','encodings':{},'visual_review':{'status':'PASS one_hot figures 4--7; other encoding images not claimed inspected','method':'actual view_image, no blank panels or cropped axes; see docs/figure_redraw/review_geometry.md','png_sha256':{str(p):sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'figures/main').glob('fig0[4567]_one_hot.png'))}}}
    for enc in ('one_hot','ring','topology'):
        rec=ROOT/'artifacts/neural_representation_v2/data'/enc
        meta=json.loads((rec/'metadata.json').read_text());r=np.load(rec/'recording.npz')['rates'];t=np.load(rec/'recording.npz')['times_ms'];tasks=meta['tasks']
        g={k:np.array(v,int) for k,v in meta['population_indices'].items()};ev=meta['events'][0]
        derived=OUT/'derived'/enc;summary={}
        f4=np.load(derived/'fig04_transition_kinematics.npz')
        summary['pca_projection_maxerr']=check(f4['pca_scores'],np.einsum('ntj,kj->ntk',r-f4['pca_mean'],f4['pca_components']))
        fit=r[:,f4['pca_fit_time_indices']].reshape(-1,r.shape[-1]);check(f4['pca_mean'],fit.mean(0))
        covariance=(fit-fit.mean(0)).T@(fit-fit.mean(0));vals,vec=np.linalg.eigh(covariance);order=np.argsort(vals)[::-1]
        # Independent eigen-decomposition, compare subspace rather than arbitrary PC signs.
        check(np.cos(subspace_angles(f4['pca_components'].T,vec[:,order[:len(f4['pca_components'])]])),np.ones(len(f4['pca_components'])))
        check(f4['pca_evr'][:len(f4['pca_components'])],vals[order[:len(f4['pca_components'])]]/vals.sum())
        summary['speed_maxerr']=check(f4['full_state_speed_per_ms'],np.sqrt(np.sum((r[:,1:]-r[:,:-1])**2,axis=-1))/np.diff(t))
        response=np.concatenate([g[f'R{s}'] for s in (1,2,3,4)])
        scopes={'whole':np.arange(132),'response':response,'shared':np.setdiff1d(np.arange(132),response)}
        masks=[np.array([v['D']==d and v['S']==s for v in tasks]) for d in (1,-1) for s in (1,2)]
        f5=np.load(derived/'fig05_temporal_subspaces.npz');max_angle_error=0.;na_count=0
        end=ev['readout3'];width=meta['config'].get('decision_ms',20);decision=r[:,(t>end-width)&(t<=end)].mean(1)
        for scope,idx in scopes.items():
            check(f5[scope+'_indices'],idx)
            for ti in range(len(t)):
                state=[r[m,ti][:,idx] for m in masks];qb=[orth(x) for x in state]
                check(f5[scope+'_ranks'][ti],[q.shape[1] for q,v in qb])
                for p,(a,b) in enumerate(f5['pairs']):
                    qa,va=qb[a];qbb,vb=qb[b]
                    stored=f5[scope+'_angles_degrees'][ti,p]
                    check(f5[scope+'_centroid_distance'][ti,p],np.linalg.norm(state[a].mean(0)-state[b].mean(0)))
                    if va<=1e-8 or vb<=1e-8 or not qa.shape[1] or not qbb.shape[1]:
                        assert np.isnan(stored).all();na_count+=1
                    else:
                        angles=np.sort(np.degrees(subspace_angles(qa,qbb)));defined=np.isfinite(stored)
                        # acos loses precision very near 0; angular tolerance is 1e-5 degrees.
                        error=check(stored[defined],angles,atol=1e-5);max_angle_error=max(max_angle_error,error)
                        assert np.isnan(stored[len(angles):]).all()
            with (derived/'fig05_principal_angles.csv').open() as fp:
                rows=[row for row in csv.DictReader(fp) if row['scope']==scope]
            assert len(rows)==6
            for row in rows:
                a,b=int(row['branch_a']),int(row['branch_b']);xa,xb=decision[masks[a]][:,idx],decision[masks[b]][:,idx];qa,va=orth(xa);qb,vb=orth(xb)
                if va>1e-8 and vb>1e-8:
                    angles=np.sort(np.degrees(subspace_angles(qa,qb)));check(np.fromstring(row['angles_degrees'],sep=';'),angles,atol=1e-5)
                    a0=xa-xa.mean(0);b0=xb-xb.mean(0)
                    check(float(row['cross_vaf_a_to_b']),1-np.linalg.norm(a0-a0@qb@qb.T,'fro')**2/va)
                    check(float(row['cross_vaf_b_to_a']),1-np.linalg.norm(b0-b0@qa@qa.T,'fro')**2/vb)
        summary.update(temporal_angle_maxerr_degrees=max_angle_error,undefined_temporal_pairs=na_count,scopes=3,decision_pairs_per_scope=6)
        f6=np.load(derived/'fig06_position_stability.npz');states=decision[f6['trial_indices']]
        check(f6['states'],states)
        check(f6['whole_rdm'],np.array([[np.linalg.norm(x-y) for y in states] for x in states]))
        check(f6['response_rdm'],np.array([[np.linalg.norm((x-y)[response]) for y in states] for x in states]))
        check(f6['pca_scores'],(states-f6['pca_mean'])@f6['pca_components'].T)
        f7=np.load(derived/'fig07_branch_decoding.npz');splits=json.loads((derived/'fig07_branch_decoding_splits.json').read_text())['train_test_folds']
        y=np.array([(v['D']==-1)*2+v['S']-1 for v in tasks]);conditions=[(v['L'],v['D'],v['S']) for v in tasks];assert len(set(conditions))==24
        tids=[np.flatnonzero(t==tt)[0] for tt in f7['times_ms']];recomputed=[]
        for a,b in splits:
            assert not(set(a)&set(b));assert len(set(a))==len(a) and len(set(b))==len(b)
            assert {conditions[i] for i in a}.isdisjoint({conditions[i] for i in b})
            assert set(y[a])==set(y[b])==set(range(4))
        for tt,j in zip(f7['times_ms'],tids):
            if tt<ev['to_R3']:recomputed.append(np.nan);continue
            scores=[]
            for a,b in splits:
                train=r[a,j][:,response];test=r[b,j][:,response];centers=np.array([train[y[a]==c].mean(0) for c in range(4)])
                distance=np.sum((test[:,None,:]-centers)**2,axis=-1);tied=np.isclose(distance,distance.min(1)[:,None],rtol=1e-9,atol=1e-12)
                scores.append(np.mean(tied[np.arange(len(b)),y[b]]/tied.sum(1)))
            recomputed.append(np.mean(scores))
        summary['branch_probe_maxerr']=check(f7['branch_accuracy'],recomputed);summary['branch_folds']=len(splits);summary['class_presence']='4/4 in each train and test'
        summary['input_sha256']={str(rec/p):sha256((rec/p).read_bytes()).hexdigest() for p in ('recording.npz','metadata.json')}
        summary['derived_sha256']={str(p):sha256(p.read_bytes()).hexdigest() for p in sorted(derived.glob('fig0[4567]*'))}
        summary['status']='PASS';result['encodings'][enc]=summary;print(enc,summary)
    (OUT/'manifests/review_geometry.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    return result

if __name__=='__main__':run()
