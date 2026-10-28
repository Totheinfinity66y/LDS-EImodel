"""Independent read-only numerical audit; writes only this audit's reports."""
from pathlib import Path
import sys, json, csv, hashlib, subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from handcrafted_ei.evaluation.figure_data_geometry import load
from handcrafted_ei.evaluation.reference_adapter import load_audited_dataset, reconstruct_currents
from handcrafted_ei.evaluation.population_data import source_identity
from handcrafted_ei.model.ei_network import EINetwork
OUT=ROOT/'artifacts/neural_paper_figures_v3'; RAW=ROOT/'handcrafted_ei/artifacts/v2/run'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvrows(p):
    with p.open(encoding='utf-8') as f:return list(csv.DictReader(f))
def close(a,b,tol=1e-10):
    err=float(np.max(abs(np.asarray(a)-np.asarray(b))))
    assert err<tol,err
    return err
def replay(m,initial,t,u,c,direction=None,mask=None,amplitude=.25):
    x=initial.copy();path=[x.copy()]
    for k in range(1,len(t)):
        drive=m.signed_weights@x+m.tonic-m.theta+u[k]+c[k]
        if direction is not None and mask[k]:drive+=amplitude*direction
        x=x+(m.config['dt_ms']/m.tau)*(-x+np.clip(drive,0,1));path.append(x.copy())
    return np.array(path)
def klass(m,x,branch):
    residual=np.max(abs((-x+np.clip(x@m.signed_weights.T+m.tonic-m.theta,0,1))/m.tau),axis=-1)
    active=x[:,m.groups['R3']].reshape(-1,4,6)>=.2
    codes=[]
    for a,res in zip(active,residual):
        bs=np.flatnonzero(a.any(1));ps=np.flatnonzero(a.any(0))
        codes.append(4 if res>=1e-7 else 3 if not a.any() else 2 if np.any(bs!=branch) else 1 if len(ps)>1 else 0)
    return np.array(codes),residual
def run():
    report={'reviewer':'independent_audit (no implementation edits)','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protected_source':source_identity(RAW),'encodings':{}}
    for mode in ('one_hot','ring','topology'):
        d=load(mode);a=load_audited_dataset(RAW,mode);r=d['rates'];t=d['times_ms'];folder=OUT/'derived'/mode
        rec={'recording_shape':list(r.shape),'archive_equality_error':close(r,a['rates']),'inputs':{}}
        for p in [ROOT/f'artifacts/neural_representation_v2/data/{mode}/recording.npz',ROOT/f'artifacts/neural_representation_v2/data/{mode}/metadata.json',Path(a['archive_path'])]:rec['inputs'][str(p.relative_to(ROOT))]=sha(p)
        tasks=d['tasks'];conditions=np.array([(v['L'],v['D'],v['S']) for v in tasks]);assert len(set(map(tuple,conditions)))==24
        with np.load(folder/'fig04_trajectories.npz') as z:
            close(z['global_scores'],(r-z['global_mean'])@z['global_components'].T)
            close(z['speed'],np.linalg.norm(np.diff(r,axis=1),axis=2)/np.diff(t)[None])
            fixed=z['fixed_L_trials'];assert len(fixed)==4 and np.all(conditions[fixed,0]==0)
            assert set(map(tuple,conditions[fixed,1:]))=={(1,1),(1,2),(-1,1),(-1,2)}
            sample=[]
            for rank in (2,3):
                sample.append(np.array([r[i,(t>v[f'readout{rank}']-d['config']['decision_ms'])&(t<=v[f'readout{rank}'])].mean(0) for i,v in enumerate(d['events'])])[fixed])
            dc=np.array([sample[0][conditions[fixed,1]==v].mean(0) for v in (1,-1)])
            contrast=np.concatenate([(dc-dc.mean(0))/np.sqrt(2),(sample[1]-sample[1].mean(0))/2]);_,sv,vt=np.linalg.svd(contrast-contrast.mean(0),full_matrices=False);q=vt[sv>max(1e-8,sv[0]*1e-8)].T
            close(q@q.T,z['branch_basis']@z['branch_basis'].T);close(z['branch_scores'],(r-z['branch_center'])@z['branch_basis'])
            rec['geometry']={'balanced_fixed_L':True,'fixed_basis_rank':q.shape[1],'R3_branch_variance_2d':float(z['R3_branch_variance_captured_2d'])}
        original=[x for x in csvrows(ROOT/f'artifacts/neural_representation_v2/metrics/{mode}/subspace_pairs.csv') if int(x['stage'])==3]
        copied=csvrows(folder/'fig05_principal_angle_spectra.csv');assert original==copied
        rec['geometry']['angle_rows_verbatim']=len(copied)
        ids=[np.flatnonzero((conditions[:,1]==di)&(conditions[:,2]==st)) for di,st in ((1,1),(1,2),(-1,1),(-1,2))]
        response=np.concatenate([d['groups'][f'R{s}'] for s in range(1,5)])
        with np.load(folder/'fig05_time_resolved_geometry.npz') as z:
            for scope,states in [('whole',r),('response',r[:,:,response]),('folded',r[:,:,d['groups']['R3']].reshape(24,len(t),4,6).sum(2))]:
                ranks=z[scope+'_ranks'];assert ranks.max()<=5
                angles=z[scope+'_angles_degrees'];assert np.isnan(angles[0]).all()
                for k in (0,100,250,400,550,662):
                    qs=[]
                    for b,ix in enumerate(ids):
                        x=states[ix,k];_,s,v=np.linalg.svd(x-x.mean(0),full_matrices=False);keep=s>max(1e-8,s[0]*1e-8);assert int(keep.sum())==ranks[k,b];qs.append(v[keep].T)
                        close(s,z[scope+'_singular_values'][k,b,:len(s)])
                    for pair,(b,c) in enumerate(z['pairs']):
                        angle=np.degrees(np.arccos(np.clip(np.linalg.svd(qs[b].T@qs[c],compute_uv=False),0,1)))
                        close(angle,angles[k,pair,:len(angle)]) if len(angle) else None
                        assert np.isnan(angles[k,pair,len(angle):]).all()
                        close(np.linalg.norm(states[ids[b],k].mean(0)-states[ids[c],k].mean(0)),z[scope+'_centroid_distance'][k,pair])
                rec['geometry'][scope+'_max_rank']=int(ranks.max())
        m=EINetwork(overrides=d['config']);m.clock[:]=0;m.stimulus[:]=0
        certrows=csvrows(folder/'fig08_v3_fixed_point_certificates.csv')
        with np.load(ROOT/f'artifacts/paper2agent_reproduction/lds_results/{mode}/fixed_points.npz') as fixed:
            maxfd=0.;maxres=0.
            for row,x in zip(certrows,fixed['endpoints']):
                drive=m.signed_weights@x+m.tonic-m.theta;slope=((drive>0)&(drive<1)).astype(float);slope[np.isclose(drive,0,atol=1e-10)|np.isclose(drive,1,atol=1e-10)]=.5
                analytic=(-np.eye(132)+slope[:,None]*m.signed_weights)/m.tau[:,None]
                def f(v):return (-v+np.clip(m.signed_weights@v+m.tonic-m.theta,0,1))/m.tau
                numeric=np.column_stack([(f(x+np.eye(132)[k]*1e-7)-f(x-np.eye(132)[k]*1e-7))/(2e-7) for k in range(132)])
                fd=float(np.max(abs(analytic-numeric)));maxfd=max(maxfd,fd);assert fd<1e-8
                eig=np.linalg.eigvals(analytic);close(eig.real.max(),float(row['max_real_eigenvalue_per_ms']));close(np.max(abs(1+5*eig)),float(row['euler_spectral_radius']))
                residual=float(np.max(abs(f(x))));maxres=max(maxres,residual);close(residual,float(row['residual_max_per_ms']));assert residual<1e-7
                assert row['strict_local_stability']=='False' and int(row['kink_count'])==13 and row['certified']=='True'
            rec['fixed_points']={'count':24,'max_full_residual_per_ms':maxres,'max_finite_difference_Jacobian_error':maxfd,'kinks_per_point':13,'strict_smooth_stability':False,'piecewise_cascade_certificate_reported':True,'warning':'Smooth eigenvalues alone are not a kink stability proof; separate cascade certificate is required.'}
        with np.load(folder/'fig08_basin_slices_v3.npz') as z:
            assert np.all(z['clock']==0) and np.all(z['stimulus']==0);assert np.array_equal(z['tonic'],m.tonic)
            initial=z['initial_rates'];end=z['endpoints'];legal=z['legal_mask'];assert np.isnan(initial[~legal]).all() and np.isnan(end[~legal]).all()
            assert np.all((initial[legal]>=0)&(initial[legal]<=1));counts={}
            for b in range(4):
                expected=np.argmax(z['reference_endpoints'][z['selected_trials'][b,0]][m.groups['R3']].reshape(4,6).sum(1))
                codes,res=klass(m,end[b][legal[b]],expected);assert np.array_equal(codes,z['class_code'][b][legal[b]]);close(res,z['residual_max_per_ms'][b][legal[b]])
                for sl,triple in enumerate(z['triples']):
                    pts=z['reference_endpoints'][z['selected_trials'][b][triple]];ix=np.flatnonzero(legal[b,sl]);xy=z['grid_xy'][ix]
                    close(initial[b,sl,ix],pts[0]+xy[:,0,None]*(pts[1]-pts[0])+xy[:,1,None]*(pts[2]-pts[0]))
                    k=int(ix[len(ix)//2]);path=replay(m,initial[b,sl,k],np.arange(401)*5,np.zeros((401,132)),np.zeros((401,132)));close(path[-1],end[b,sl,k])
                counts[str(b)]={str(v):int(np.sum(codes==v)) for v in np.unique(codes)}
            rec['basin']={'shape':list(legal.shape),'legal_count':int(legal.sum()),'class_counts_by_branch':counts,'sample_replays':12,'all_endpoints_full_field_classification':True}
        with np.load(folder/'fig09_stage_perturbation_v3.npz') as z:
            p=z['perturbed'];assert p.shape==(4,3,24,663,132);close(z['control'],r);assert np.array_equal(z['conditions'],conditions)
            cur=reconstruct_currents(a);close(z['clock'],cur['clock']);close(z['base_stimulus'],cur['stimulus']);maxerr=0
            for stage in range(4):
                mask=z['pulse_mask'][stage];assert mask.sum()==10
                for seed in range(3):
                    direction=z['directions'][seed];close(np.sqrt(np.mean(direction**2)),1)
                    close(p[stage,seed][:,t<=z['onsets_ms'][stage]],r[:,t<=z['onsets_ms'][stage]],1e-12)
                # Independently replay all controls, one pulse per stage.
                trial=stage*6
                control=replay(m,r[trial,0],t,cur['stimulus'][trial],cur['clock'][trial]);maxerr=max(maxerr,close(control,r[trial]))
                pulse=replay(m,r[trial,0],t,cur['stimulus'][trial],cur['clock'][trial],z['directions'][0],mask);close(pulse,p[stage,0,trial])
                zero=replay(m,r[trial,0],t,cur['stimulus'][trial],cur['clock'][trial],z['directions'][0],mask,0);assert np.array_equal(zero,control)
            rec['stage_pulse']={'shape':list(p.shape),'paired_histories':288,'independent_control_and_pulse_replays':4,'zero_pulse_replays':4,'max_replay_error':maxerr,'duration_ms':50,'current_rms':.25}
            rows=csvrows(folder/'fig09_perturbation_classification.csv');assert len(rows)==288
            def pattern(state,rank):
                ac=state[m.groups[f'R{rank}']].reshape(-1,6)>=.2;bs=np.flatnonzero(ac.any(1));ps=np.flatnonzero(ac.any(0))
                return (3 if not ac.any() else 2 if len(bs)>1 else 1 if len(ps)>1 else 0,int(bs[0]) if len(bs)==1 else -1,int(ps[0]) if len(ps)==1 else -1)
            for row in rows:
                st=list(z['stages']).index(row['stage']);si=list(z['seeds']).index(int(row['seed']));tr=int(row['trial']);path=p[st,si,tr];pred=[]
                for rank in range(1,5):
                    end=d['events'][tr][f'readout{rank}'];k=np.flatnonzero(t==end)[0];win=(t>end-d['config']['decision_ms'])&(t<=end);y=path[win][:,m.groups['Y']].mean(0)
                    pred.append(int(y.argmax()) if y.max()>=d['config']['decision_threshold'] else -1)
                    if rank in (2,3):
                        ref=pattern(r[tr,k],rank);actual=pattern(path[k],rank);bad=actual[0]!=0 or actual[1:]!=ref[1:]
                        assert (row[f'intermediate_R{rank}_error']=='True')==bad
                assert row['outputs']==';'.join(map(str,pred))
                assert (row['final_readout_correct']=='True')==(pred[-1]==d['tasks'][tr]['target'][-1])
                close(float(row['actual_current_rms']),.25);close(float(row['integrated_rms_ms']),12.5);close(float(row['integrated_squared_current']),412.5)
            rec['stage_pulse']['all_288_readouts_intermediate_flags_and_doses_recomputed']=True
        rec['input_projection']={}
        for assay in ('source_time','R3_fixed_clock'):
            for seed in (7,11,19):
                with np.load(ROOT/f'artifacts/paper2agent_reproduction/lds_results/{mode}/input_{assay}_{seed}.npz') as z:
                    delta=z['perturbed']-z['control'];q=z['basis'][:,:2];proj=delta@q;orth=delta-proj@q.T
                    close(np.sum(delta**2,axis=1),z['full_squared']);close(np.sum(proj**2,axis=1),z['projected_squared']);close(np.sum(orth**2,axis=1),z['orthogonal_squared'])
                    rec['input_projection'][f'{assay}_{seed}']=close(z['full_squared'],z['projected_squared']+z['orthogonal_squared'])
        report['encodings'][mode]=rec;print('INDEPENDENT NUMERIC PASS',mode,flush=True)
    report['input_and_analysis_hashes']={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'handcrafted_ei/evaluation/paper_figure_v3_geometry.py',ROOT/'handcrafted_ei/evaluation/paper_v3_dynamics.py',ROOT/'handcrafted_ei/visualization/paper_v3.py',Path(__file__)]}
    report['protected_source_after']=source_identity(RAW)
    reused=json.loads((OUT/'manifests/reused_artifacts.json').read_text(encoding='utf-8'))
    for item in reused:
        assert sha(ROOT/item['source'])==item['sha256']==sha(OUT/item['destination'])
    report['reused_artifacts_independently_hash_checked']=len(reused)
    report['derived_and_figure_sha256']={str(p.relative_to(OUT)):sha(p) for folder in ('derived','figures') for p in sorted((OUT/folder).rglob('*')) if p.is_file() and '.tmp' not in p.name}
    report['status']='NUMERICAL_PASS_VISUAL_REVIEW_PENDING'
    (OUT/'manifests/independent_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if __name__=='__main__':run()
