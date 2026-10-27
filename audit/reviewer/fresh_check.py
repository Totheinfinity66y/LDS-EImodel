"""Fresh reviewer calculations; imports model coefficients, no analysis functions."""
from pathlib import Path
import sys, json, hashlib, csv
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork

def main():
    report={}
    for mode in ('one_hot','ring','topology'):
        p=ROOT/'artifacts/paper2agent_reproduction/lds_results'/mode
        m=EINetwork(overrides=json.loads((p/'config.json').read_text()))
        w=m.weights*m.signs[None,:]; dt=m.config['dt_ms']
        def f(x,current=0): return (np.clip(x@w.T+m.tonic-m.theta+current,0,1)-x)/m.tau
        with np.load(p/'fixed_points.npz') as a:
            # Different rows/time indices from the numerical auditor's sample.
            r=a['rates']; selected=r[[2,9,21]][:,[7,53,133,399]]
            next_=r[[2,9,21]][:,[8,54,134,400]]
            err=float(abs(next_-selected-dt*f(selected)).max())
            ends=a['endpoints']; distances=np.linalg.norm(ends[:,None]-ends[None,:],axis=-1)
            endpoint_error=float(abs(distances-a['endpoint_distance']).max())
            fullres=float(abs(f(ends)).max())
            # Finite differences at an off-endpoint state avoid merely verifying
            # the saturated endpoint's diagonal spectrum.
            x=r[9,7]; drive=w@x+m.tonic-m.theta; h=1e-6
            numeric=np.stack([(f(x+np.eye(len(x))[q]*h)-f(x-np.eye(len(x))[q]*h))/(2*h) for q in range(len(x))],axis=1)
            kink=(abs(drive)<h)|(abs(drive-1)<h)
            analytic=(-np.eye(len(x))+((drive>0)&(drive<1))[:,None]*w)/m.tau[:,None]
            smooth_error=float(abs(numeric[~kink]-analytic[~kink]).max())
        with np.load(p/'input_source_time_19.npz') as z:
            c=z['control']; v=z['perturbed']; u=z['base_stimulus']+z['clock'];pulse=z['actual_perturbation_current'];b=z['basis'][:,:2]
            inds=np.array([11,63,103,117,163])
            ce=float(abs(c[inds+1]-c[inds]-dt*f(c[inds],u[inds+1])).max())
            pe=float(abs(v[inds+1]-v[inds]-dt*f(v[inds],u[inds+1]+pulse[inds+1])).max())
            delta=v-c; project=delta@b; off=delta-project@b.T
            energy=float(abs((delta**2).sum(1)-(project**2).sum(1)-(off**2).sum(1)).max())
            rr=[3,28,44];ss=[2,24,39]
            cross_error=max(abs(np.linalg.norm(c[i*4]-v[j*4])-z['cross_temporal_distance'][i,j]) for i in rr for j in ss)
            noise_zero=bool(not z['noise_control'].any() and np.array_equal(z['noise_control'],z['noise_perturbed']))
            pulse_duration=float(z['pulse_mask'].sum()*dt)
        report[mode]=dict(step_error=err,endpoint_distance_error=endpoint_error,full_residual=fullres,off_endpoint_smooth_jacobian_error=smooth_error,control_step_error=ce,perturbed_step_error=pe,energy_closure_error=energy,cross_distance_error=float(cross_error),paired_noise_zero=noise_zero,pulse_duration_ms=pulse_duration)
        raw=ROOT/'artifacts/neural_representation_v2/data'/mode
        meta=json.loads((raw/'metadata.json').read_text())
        with np.load(raw/'recording.npz') as z:
            times=z['times_ms']; rates=z['rates']
            samples=np.stack([x[(times>e['readout3']-20)&(times<=e['readout3'])].mean(0) for x,e in zip(rates,meta['events'])])
        bases=[];pr=[]
        for dr,sz in ((1,1),(-1,2)):
            mask=[q['D']==dr and q['S']==sz for q in meta['tasks']]
            x=samples[mask]; _,sing,vt=np.linalg.svd(x-x.mean(0),full_matrices=False)
            rank=int((sing>max(x.shape)*np.finfo(float).eps*sing[0]).sum())
            spectral_energy=sing**2; pr.append(float(spectral_energy.sum()**2/(spectral_energy@spectral_energy)));bases.append(vt[:rank].T)
        angles=np.degrees(np.arccos(np.clip(np.linalg.svd(bases[0].T@bases[1],compute_uv=False),0,1)))
        saved=list(csv.DictReader((ROOT/'artifacts/neural_representation_v2/metrics'/mode/'subspace_pairs.csv').open()))
        pair=next(q for q in saved if q['stage']=='3' and q['branch_a']=='0' and q['branch_b']=='3')
        angle_error=abs(angles.mean()-float(pair['mean_angle']))
        report[mode]['independent_R3_branch0_3_mean_angle']=float(angles.mean())
        report[mode]['independent_R3_PR']=pr
        report[mode]['angle_error']=float(angle_error)
        assert angle_error<1e-9
        with np.load(p/'basin_E.npz') as a:
            k=173;trial=int(a['initial_reference_index'][k]);amp=float(a['amplitude'][k]);seed=int(a['seed'][k])
            idx=np.flatnonzero(m.signs==1);direction=np.random.default_rng(seed).normal(size=len(idx))
            raw=ends[trial].copy();raw[idx]+=amp*direction/np.sqrt(np.mean(direction**2))
            expected=np.clip(raw,0,1);actual=expected-ends[trial]
            records=list(csv.DictReader((p/'basin.csv').open()))
            row=next(q for q in records if q['target']=='E' and int(q['trial'])==trial and int(q['seed'])==seed and float(q['amplitude_preclip'])==amp)
            clip_error=abs(np.mean((raw[idx]<0)|(raw[idx]>1))-float(row['clipping_fraction_target']))
            rms_error=abs(np.sqrt(np.mean(actual[idx]**2))-float(row['actual_target_rms']))
            assert max(clip_error,rms_error,float(abs(expected-a['rates'][k,0]).max()))<1e-12
            report[mode]['E_basin_sample']=dict(row=k,trial=trial,seed=seed,amplitude_preclip=amp,clip_fraction=float(row['clipping_fraction_target']),actual_target_rms=float(row['actual_target_rms']),clipping_error=float(clip_error),rms_error=float(rms_error))
        assert max(err,endpoint_error,smooth_error,ce,pe,energy,cross_error)<1e-8
        assert noise_zero and pulse_duration==50
    report['status']='PASS finite independent samples; no global-basin proof'
    report['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
