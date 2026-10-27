"""Independent formula recomputation from final NPZ, without plotting metrics."""
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'artifacts/paper2agent_reproduction/lds_results'
rows=[]
for mode in ('one_hot','ring','topology'):
    for assay in ('source_time','R3_fixed_clock'):
        for seed in (7,11,19):
            with np.load(DATA/mode/f'input_{assay}_{seed}.npz') as z:
                c=z['control'];p=z['perturbed'];delta=p-c;t=z['times_ms'];mask=z['pulse_mask'];b=z['basis'][:,:2]
                u=z['actual_perturbation_current'];dt=np.diff(t)[0]
                assert mask.sum()==10
                assert np.array_equal(z['noise_control'],z['noise_perturbed']) and not np.any(z['noise_control'])
                np.testing.assert_array_equal(c[~(t>t[np.flatnonzero(mask)[0]]-dt)],p[~(t>t[np.flatnonzero(mask)[0]]-dt)])
                assert not np.any(u[~mask])
                rms=np.sqrt(np.mean(u[mask]**2,axis=1));np.testing.assert_allclose(rms,.25,atol=1e-15)
                duration=float(mask.sum()*dt);dose=float(np.sum(rms)*dt)
                full=np.einsum('tn,tn->t',delta,delta)
                proj=delta@b;orth=delta-proj@b.T
                eproj=np.einsum('tk,tk->t',proj,proj);eorth=np.einsum('tn,tn->t',orth,orth)
                np.testing.assert_allclose(full,z['full_squared'],atol=2e-14)
                np.testing.assert_allclose(eproj,z['projected_squared'],atol=2e-14)
                np.testing.assert_allclose(eorth,z['orthogonal_squared'],atol=2e-14)
                smallc=c[::4];smallp=p[::4]
                cross=np.linalg.norm(smallc[:,None]-smallp[None,:],axis=-1)
                np.testing.assert_allclose(cross,z['cross_temporal_distance'],atol=2e-14)
                # Check mean and principal subspace were fitted to controls only.
                np.testing.assert_allclose(c.mean(0),z['pca_center'],atol=1e-15)
                _,_,vh=np.linalg.svd(c-c.mean(0),full_matrices=False)
                np.testing.assert_allclose(b@b.T,vh[:2].T@vh[:2],atol=1e-12)
                rows.append(dict(encoding=mode,assay=assay,seed=seed,duration_ms=duration,current_rms=float(rms[0]),
                    integrated_rms_ms=dose,final_l2=float(np.sqrt(full[-1])),peak_l2=float(np.sqrt(full).max()),
                    final_projected_energy_fraction=None if full[-1]==0 else float(eproj[-1]/full[-1]),
                    projection_closure_max=float(abs(full-eproj-eorth).max()),
                    cross_distance_max_error=float(abs(cross-z['cross_temporal_distance']).max())))
    with np.load(DATA/mode/'state_perturbation.npz') as z:
        d=z['perturbed']-z['control'];b=z['basis'];full=np.sum(d*d,axis=1)
        proj=d@b;other=d-proj@b.T
        np.testing.assert_allclose(full,z['full_squared'],atol=2e-14)
        np.testing.assert_allclose(np.sum(other*other,axis=1),z['orthogonal_squared'],atol=2e-14)
        rows.append(dict(encoding=mode,assay='state_kick',initial_l2=float(np.sqrt(full[0])),final_l2=float(np.sqrt(full[-1])),
            final_projected_energy_fraction=float(np.sum(proj[-1]**2)/full[-1])))
    with np.load(DATA/mode/'local_flow.npz') as z:
        f=z['full_field'];b=z['basis'];v=f@b;residual=f-v@b.T
        np.testing.assert_allclose(v,z['velocity'],atol=1e-15)
        np.testing.assert_allclose(np.linalg.norm(residual,axis=1),z['offplane_norm'],atol=1e-15)
        rows.append(dict(encoding=mode,assay='flow',maximum_hidden_field_norm=float(np.linalg.norm(residual,axis=1).max())))

out=Path(__file__).parent/'ACTUAL_RESULTS_VERIFICATION.json'
out.write_text(json.dumps({'status':'PASS','checks':'independent NumPy formulas; all18 input NPZ plus3 state and3 flow datasets','rows':rows},indent=2),encoding='utf-8')
print(out)
print(json.dumps(rows[:7],indent=2))
