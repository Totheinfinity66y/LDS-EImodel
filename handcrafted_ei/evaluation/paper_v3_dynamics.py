"""V3 evaluation-only mixed-state and paired finite-input experiments.

Uses the existing integrator and audited archive loader. No model mutation or
historical output writes. Classes describe observed activity, not nearest PCs.
"""
from pathlib import Path
import argparse
import json
import numpy as np
from .figure_data_dynamics import ROOT, RAW, REF, SEEDS, csvwrite, savez, _receipt as _base_receipt, sha
from .reference_adapter import load_audited_dataset, reconstruct_currents
from .reference_dynamics import paired_input_probe, exact_local_stability, piecewise_cascade_certificate
from .population_dynamics import evolve_batch, field, perturbation_targets
from ..model.ei_network import EINetwork

CLASS_NAMES = np.array(['single_position', 'multiple_positions', 'outside_branch', 'rest', 'unconverged'])
TRIPLES = ((0, 1, 2), (0, 2, 4), (1, 3, 5))


def _receipt(path, inputs, parameters):
    _base_receipt(path,inputs,parameters)
    receipt=json.loads(path.read_text(encoding='utf-8'))
    receipt['analysis_source_sha256']=sha(__file__)
    receipt['analysis_source']='handcrafted_ei/evaluation/paper_v3_dynamics.py'
    path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')


def classify(model, state, stage=3, expected_branch=None, residual=None,
             threshold=.2, residual_threshold=1e-7, require_converged=True):
    """Classify all stage units; simultaneous supra-threshold positions persist.

    Convergence is evaluated in the full field, independently of identity.
    Finite source-time trials must set require_converged=False: scheduled
    external currents do not define an equilibrium-recovery assay.
    """
    state = np.asarray(state)
    if state.shape != model.rates.shape or not np.isfinite(state).all():
        raise ValueError('finite full-state vector required')
    values = state[model.groups[f'R{stage}']].reshape(-1, 6)
    active = values >= threshold
    branches = np.flatnonzero(active.any(1))
    positions = np.flatnonzero(active.any(0))
    if not require_converged:
        residual=np.nan;converged=None
    else:
        if residual is None: residual = float(np.max(abs(field(model, state))))
        converged = bool(residual < residual_threshold)
    if require_converged and not converged:
        code = 4
    elif not active.any():
        code = 3
    elif len(branches)>1 or (expected_branch is not None and np.any(branches != expected_branch)):
        code = 2
    elif len(positions) > 1:
        code = 1
    else:
        code = 0
    return dict(class_code=code, endpoint_class=str(CLASS_NAMES[code]),
                converged=converged, residual_max_per_ms=float(residual),
                convergence_scope='fixed_field' if require_converged else 'not_applicable_source_time',
                branch=int(branches[0]) if len(branches) == 1 else -1,
                position=int(positions[0]) if len(positions) == 1 else -1,
                active_branch_count=len(branches), active_position_count=len(positions),
                active_unit_count=int(active.sum()))


def basin_slices(d, output, grid_size=21):
    mode = d['encoding_type']; out = Path(output)/'derived'/mode
    out.mkdir(parents=True, exist_ok=True)
    with np.load(REF/mode/'fixed_points.npz') as a:
        endpoints = a['endpoints'].copy(); conditions = a['conditions'].copy()
        clock = a['clock_used'].copy(); stimulus = a['stimulus_used'].copy(); tonic = a['tonic_used'].copy()
        source_rates=a['rates'].copy();source_eigenvalues=a['eigenvalues'].copy()
    model = EINetwork(overrides=d['config'])
    if np.any(clock) or np.any(stimulus) or not np.array_equal(tonic, model.tonic):
        raise ValueError('expected common sample=clock=0, original tonic field')
    model.remove_stimulus(); model.clock[:] = 0
    axis = np.linspace(0, 1, grid_size); aa, bb = np.meshgrid(axis, axis)
    xy = np.c_[aa.ravel(), bb.ravel()]
    shape = (4, len(TRIPLES), len(xy))
    initial_all = np.full((*shape, len(model.rates)), np.nan)
    final_all = initial_all.copy(); legal_all = np.zeros(shape, bool)
    codes = np.full(shape, -1, int); residuals = np.full(shape, np.nan)
    competition = np.full((*shape, 4, 6), np.nan)
    selected = []; rows = []; certificates = []; representatives=[]; representative_meta=[]
    for trial, state in enumerate(endpoints):
        stat, eig = exact_local_stability(model, state)
        cert = piecewise_cascade_certificate(model, state)
        certificates.append(dict(trial=trial, **stat, **cert))
    for branch, (direction, step) in enumerate(((1,1),(1,2),(-1,1),(-1,2))):
        ids = np.flatnonzero((conditions[:,1] == direction)&(conditions[:,2] == step))
        ids = ids[np.argsort(conditions[ids,0])]; selected.append(ids)
        observed = np.argmax(endpoints[ids][:,model.groups['R3']].reshape(6,4,6).sum(2), axis=1)
        if len(set(observed)) != 1:
            raise ValueError('reference points do not share an observed branch')
        for slice_id, triple in enumerate(TRIPLES):
            p, q, r = endpoints[ids[list(triple)]]
            # Integer barycentric numerators avoid cancellation producing tiny
            # negative rates on exactly legal simplex edges. No rates clipped.
            ii,jj=np.meshgrid(np.arange(grid_size),np.arange(grid_size))
            ia=ii.ravel();ib=jj.ravel();den=grid_size-1
            initial=((den-ia-ib)[:,None]*p+ia[:,None]*q+ib[:,None]*r)/den
            # Convex simplex is guaranteed legal without clipping. Square beyond
            # it is retained only if every original rate lies in the rate cube.
            legal = np.all((initial >= 0)&(initial <= 1), axis=1)
            keep = np.flatnonzero(legal); legal_all[branch,slice_id] = legal
            initial_all[branch,slice_id,keep] = initial[keep]
            for start in range(0, len(keep), 32):
                idx = keep[start:start+32]
                paths = evolve_batch(model, initial[idx], 2000)
                final_all[branch,slice_id,idx] = paths[:,-1]
                if start==0:
                    for local in np.linspace(0,len(idx)-1,min(4,len(idx)),dtype=int):
                        representatives.append(paths[local].copy())
                        representative_meta.append((branch,slice_id,int(idx[local])))
            for k in keep:
                state = final_all[branch,slice_id,k]
                result = classify(model, state, expected_branch=int(observed[0]))
                codes[branch,slice_id,k] = result['class_code']
                residuals[branch,slice_id,k] = result['residual_max_per_ms']
                competition[branch,slice_id,k] = state[model.groups['R3']].reshape(4,6)
                rows.append(dict(encoding=mode, reference_branch=branch, slice=slice_id,
                    triple=';'.join(map(str,triple)), grid_index=int(k), alpha=float(xy[k,0]), beta=float(xy[k,1]), **result))
            print(f'v3 basin {mode} branch {branch} slice {triple}: {len(keep)} legal', flush=True)
    path = out/'fig08_basin_slices_v3.npz'
    savez(path, grid_axis=axis, grid_xy=xy, triples=np.array(TRIPLES), selected_trials=np.array(selected),
        initial_rates=initial_all, endpoints=final_all, legal_mask=legal_all, class_code=codes,
        class_names=CLASS_NAMES, residual_max_per_ms=residuals, R3_competition=competition,
        reference_endpoints=endpoints, reference_conditions=conditions, duration_ms=np.array(2000.),
        representative_rates=np.array(representatives), representative_indices=np.array(representative_meta),
        representative_times_ms=np.arange(401)*model.config['dt_ms'],
        clock=clock, stimulus=stimulus, tonic=tonic, neuron_labels=np.array(model.labels))
    csvwrite(out/'fig08_endpoint_classes.csv', rows)
    csvwrite(out/'fig08_v3_fixed_point_certificates.csv', certificates)
    centers=[];bases=[];evr=[]
    for ids in selected:
        train=np.concatenate([source_rates[ids].reshape(-1,len(model.rates)),endpoints[ids]])
        mean=train.mean(0);_,singular,vt=np.linalg.svd(train-mean,full_matrices=False)
        centers.append(mean);bases.append(vt[:3].T);evr.append(singular[:3]**2/np.sum(singular**2))
    savez(out/'fig08_six_position_fixed_points.npz',endpoints=endpoints,conditions=conditions,
        selected_trials=np.array(selected),rates=source_rates,eigenvalues=source_eigenvalues,
        basis=np.array(bases),pca_center=np.array(centers),explained_variance_ratio=np.array(evr),
        residual_max_per_ms=np.array([x['residual_max_per_ms'] for x in certificates]),
        max_real_eigenvalue_per_ms=np.array([x['max_real_eigenvalue_per_ms'] for x in certificates]),
        euler_spectral_radius=np.array([x['euler_spectral_radius'] for x in certificates]),
        clock=clock,stimulus=stimulus,tonic=tonic)
    _receipt(out/'fig08_v3_manifest.json', [REF/mode/'fixed_points.npz', path],
        dict(grid_size=grid_size, triples=TRIPLES, duration_ms=2000, chunk=32,
             invalid='masked, never clipped', activity_threshold=.2, residual_threshold=1e-7,
             field='sample=clock=0; original tonic; full-state affine endpoint differences',
             classes=CLASS_NAMES.tolist(), classification='full field residual then all R3 activity units'))
    return rows


def stage_perturbations(d, output, amplitude=.25):
    mode=d['encoding_type']; out=Path(output)/'derived'/mode; out.mkdir(parents=True,exist_ok=True)
    model=EINetwork(overrides=d['config']); currents=reconstruct_currents(d); times=d['times_ms']; ev=d['events'][0]
    names=np.array(['pre_R2_selection','post_R2_formed','pre_R3_selection','post_R3_formed'])
    onsets=np.array([ev['to_R2']-50, ev['readout2_start'], ev['to_R3']-50, ev['readout3_start']])
    directions=np.array([np.random.default_rng(seed).normal(size=len(model.rates)) for seed in SEEDS])
    directions/=np.sqrt(np.mean(directions**2,axis=1,keepdims=True))
    perturbed=np.empty((4,3,*d['rates'].shape)); rows=[]; pulse=np.empty((4,len(times)),bool)
    for stage,onset in enumerate(onsets):
        for si,seed in enumerate(SEEDS):
            for trial in range(len(d['rates'])):
                probe=paired_input_probe(model,d['rates'][trial,0],times,currents['stimulus'][trial],currents['clock'][trial],directions[si],float(onset),50.,amplitude)
                control=probe['control']; path=probe['perturbed']; mask=probe['pulse_mask']; pulse[stage]=mask
                replay=float(np.max(abs(control-d['rates'][trial])))
                if replay>1e-12: raise ValueError(f'archive replay mismatch {replay}')
                if not np.array_equal(control[~(times>onset)],path[~(times>onset)]): raise ValueError('unpaired prehistory')
                perturbed[stage,si,trial]=path; task=d['tasks'][trial]; predictions=[]; patterns=[]
                for rank in range(1,5):
                    end=d['events'][trial][f'readout{rank}']; k=int(np.flatnonzero(times==end)[0])
                    window=(times>end-d['config']['decision_ms'])&(times<=end)
                    y=path[window][:,model.groups['Y']].mean(0)
                    predictions.append(int(y.argmax()) if y.max()>=d['config']['decision_threshold'] else -1)
                    reference=classify(model,control[k],rank,require_converged=False)
                    actual=classify(model,path[k],rank,reference['branch'],require_converged=False)
                    patterns.append((reference,actual))
                reference,actual=patterns[-1]; delta=path-control; final_l2=float(np.linalg.norm(delta[-1]))
                unique_same=actual['class_code']==0 and actual['branch']==reference['branch'] and actual['position']==reference['position']
                recovered=unique_same and np.max(abs(delta[-1]))<.02
                label=('full_state_recovered' if recovered else 'readout_correct_state_not_recovered' if predictions[-1]==task['target'][-1] and unique_same else 'position_switch' if actual['class_code']==0 else actual['endpoint_class'])
                rows.append(dict(encoding=mode,stage=str(names[stage]),seed=seed,trial=trial,L=task['L'],D=task['D'],S=task['S'],
                    onset_ms=float(onset),duration_ms=50.,actual_current_rms=float(np.sqrt(np.mean((amplitude*directions[si])**2))),
                    integrated_rms_ms=float(50*amplitude), integrated_squared_current=float(50*np.sum((amplitude*directions[si])**2)),
                    replay_max_error=replay,peak_full_l2=float(np.linalg.norm(delta,axis=1).max()),final_full_l2=final_l2,
                    original_position_retained=bool(unique_same),position_switch=actual['class_code']==0 and not unique_same,
                    multiple_positions=actual['class_code']==1,branch_identity_retained=actual['branch']==reference['branch'] and actual['branch']>=0,
                    final_readout_correct=predictions[-1]==task['target'][-1],sequence_correct=predictions==task['target'],
                    full_state_recovered=bool(recovered),endpoint_outcome=label,
                    endpoint_active_branch_count=actual['active_branch_count'],
                    endpoint_active_position_count=actual['active_position_count'],
                    convergence_scope='not_applicable_source_time',
                    outputs=';'.join(map(str,predictions)),target=';'.join(map(str,task['target'])),
                    intermediate_R2_error=patterns[1][1]['class_code']!=0 or patterns[1][1]['position']!=patterns[1][0]['position'] or patterns[1][1]['branch']!=patterns[1][0]['branch'],
                    intermediate_R3_error=patterns[2][1]['class_code']!=0 or patterns[2][1]['position']!=patterns[2][0]['position'] or patterns[2][1]['branch']!=patterns[2][0]['branch']))
            print(f'v3 perturb {mode} {names[stage]} seed {seed}',flush=True)
    path=out/'fig09_stage_perturbation_v3.npz'
    savez(path,control=d['rates'],perturbed=perturbed,times_ms=times,stages=names,seeds=np.array(SEEDS),onsets_ms=onsets,
        pulse_mask=pulse,directions=directions,actual_current_rms=np.full((4,3),amplitude),integrated_rms_ms=np.full((4,3),50*amplitude),
        base_stimulus=currents['stimulus'],clock=currents['clock'],tonic=model.tonic,
        conditions=np.array([(t['L'],t['D'],t['S']) for t in d['tasks']]),neuron_labels=np.array(model.labels))
    csvwrite(out/'fig09_perturbation_classification.csv',rows)
    _receipt(out/'fig09_v3_manifest.json',[Path(d['archive_path']),path],dict(duration_ms=50,amplitude=.25,
        onsets_ms=onsets.tolist(),event_times_ms=ev,seeds=list(SEEDS),activity_threshold=.2,recovery_maxnorm=.02,
        protocol='source-time paired archived currents; readout and stage pattern comparison; no equilibrium claim',
        prehistory='bitwise identical',control_replay_max_error=max(r['replay_max_error'] for r in rows)))
    return rows


def classify_archived(d, output):
    """Reclassify real archived kicks and input pulses; never conflate protocols."""
    mode=d['encoding_type'];out=Path(output)/'derived'/mode;out.mkdir(parents=True,exist_ok=True)
    model=EINetwork(overrides=d['config']);model.remove_stimulus();model.clock[:]=0
    with np.load(REF/mode/'fixed_points.npz') as a: references=a['endpoints'].copy()
    rows=[]
    for target in ('full','active_branch'):
        with np.load(REF/mode/f'basin_{target}.npz') as a:
            rates=a['rates']
            for k in range(len(rates)):
                trial=int(a['initial_reference_index'][k]);seed=int(a['seed'][k]);amp=float(a['amplitude'][k])
                ref=references[trial];initial=rates[k,0];end=rates[k,-1]
                reference=classify(model,ref);actual=classify(model,end,expected_branch=reference['branch'])
                model.rates=ref.copy();units=perturbation_targets(model,3)[target]
                direction=np.random.default_rng(seed).normal(size=len(units));direction/=np.sqrt(np.mean(direction**2))
                raw=ref.copy();raw[units]+=amp*direction
                np.testing.assert_allclose(initial,np.clip(raw,0,1),atol=1e-15)
                same=actual['class_code']==0 and actual['branch']==reference['branch'] and actual['position']==reference['position']
                recovered=same and np.max(abs(end-ref))<.02
                rows.append(dict(protocol='state_kick_tonic_only',target=target,trial=trial,seed=seed,
                    amplitude_preclip=amp,actual_target_rms_after_clip=float(np.sqrt(np.mean((initial[units]-ref[units])**2))),
                    actual_whole_rms_after_clip=float(np.sqrt(np.mean((initial-ref)**2))),
                    clipping_fraction=float(np.mean((raw[units]<0)|(raw[units]>1))),
                    final_full_l2=float(np.linalg.norm(end-ref)),original_position_retained=same,
                    position_switch=actual['class_code']==0 and not same,full_state_recovered=bool(recovered),**actual))
    csvwrite(out/'fig09_state_kick_classification.csv',rows)
    inputs=[]
    for assay,stage in (('source_time',4),('R3_fixed_clock',3)):
        for seed in SEEDS:
            with np.load(REF/mode/f'input_{assay}_{seed}.npz') as a:
                control=a['control'];path=a['perturbed'];model.clock[:]=a['clock'][-1];model.stimulus[:]=a['base_stimulus'][-1]
                reference=classify(model,control[-1],stage,require_converged=assay=='R3_fixed_clock')
                actual=classify(model,path[-1],stage,reference['branch'],require_converged=assay=='R3_fixed_clock')
                delta=path-control;plane=a['projected_squared'];orth=a['orthogonal_squared'];full=a['full_squared']
                closure=float(np.max(abs(full-plane-orth)))
                if closure>1e-10:raise ValueError('archived projection energy does not close')
                same=actual['class_code']==0 and actual['branch']==reference['branch'] and actual['position']==reference['position']
                inputs.append(dict(protocol=assay,seed=seed,stage=stage,
                    final_full_l2=float(np.linalg.norm(delta[-1])),peak_full_l2=float(np.linalg.norm(delta,axis=1).max()),
                    final_projected_l2=float(np.sqrt(plane[-1])),final_orthogonal_l2=float(np.sqrt(orth[-1])),
                    projection_closure_error=closure,original_position_retained=same,
                    full_state_recovered=bool(same and np.max(abs(delta[-1]))<.02),**actual))
    csvwrite(out/'fig09_existing_input_classification.csv',inputs)
    return rows,inputs


def run(encodings=('one_hot','ring','topology'), output=None, grid_size=21, assays=('basin','perturbation','classify')):
    output=Path(output or ROOT/'artifacts/neural_paper_figures_v3')
    for mode in encodings:
        d=load_audited_dataset(RAW,mode)
        if 'basin' in assays: basin_slices(d,output,grid_size)
        if 'perturbation' in assays: stage_perturbations(d,output)
        if 'classify' in assays: classify_archived(d,output)
    summarize(output,encodings)
    return output


def summarize(output, encodings):
    """Inspect on-disk values, not progress messages, for the numerical receipt."""
    import csv
    from collections import Counter
    root=Path(output);summary=[];details=[]
    for mode in encodings:
        folder=root/'derived'/mode
        if not (folder/'fig08_basin_slices_v3.npz').exists():continue
        with np.load(folder/'fig08_basin_slices_v3.npz') as a:
            legal=a['legal_mask'];final=a['endpoints'];initial=a['initial_rates'];classes=a['class_code'];residual=a['residual_max_per_ms']
            if np.any((initial[legal]<0)|(initial[legal]>1)):raise ValueError('illegal integrated initial state')
            if not np.isfinite(final[legal]).all():raise ValueError('nonfinite endpoint')
            counts={str(CLASS_NAMES[k]):int(np.sum(classes==k)) for k in range(len(CLASS_NAMES))}
            summary.append(dict(encoding=mode,assay='basin',n=int(legal.sum()),max_residual=float(np.nanmax(residual)),**counts))
        if (folder/'fig09_perturbation_classification.csv').exists():
            with (folder/'fig09_perturbation_classification.csv').open() as f:rows=list(csv.DictReader(f))
            counts=dict(Counter(r['endpoint_outcome'] for r in rows))
            summary.append(dict(encoding=mode,assay='source_time_four_stage',n=len(rows),
                max_replay_error=max(float(r['replay_max_error']) for r in rows),**counts))
            for stage in sorted(set(r['stage'] for r in rows)):
                group=[r for r in rows if r['stage']==stage]
                details.append(f'- {mode}, {stage}: '+str(dict(Counter(r['endpoint_outcome'] for r in group))))
    csvwrite(root/'derived'/'numerical_summary.csv',summary)
    report=root/'reports'/'NUMERICAL_WORK.md';report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text('''# V3 numerical experiments

All dynamics use the existing full 132-dimensional Euler integrator, original model parameters and independent evaluation arrays. Archived baseline is only replayed for paired controls. Historical data is read-only.

## Protocol

- Basin: sample=0, clock=0, original tonic; 2,000 ms integration; 21×21 grid; four R3 branches and triples (0,1,2), (0,2,4), (1,3,5). Full-state endpoint affine differences; illegal rate-cube states masked without clipping. Integer barycentric numerators remove cancellation at simplex edges. 32 states per integration chunk; only endpoints and 48 representative complete paths retained per encoding.
- Classification: full-field max residual <1e-7 rate/ms precedes all R3-unit activity classification; active threshold 0.2 dimensionless. Classes retain single position, multiple position, outside branch, R3-inactive, and unconverged. R3-inactive does not mean every neural unit is silent: tonic inhibition persists. Cross-branch/multiple-position counts are retained.
- Finite inputs: 24 conditions × four stages × direction seeds 7/11/19; full132 seeded Gaussian current normalized to RMS 0.25, duration 50 ms, integrated RMS 12.5 rate-current·ms, identical controls/history/current schedules. Preselection pulses end at the corresponding gate onset. Postformation pulses start at readout2_start/readout3_start; timing is explicit in manifests. These are fixed random directions, not independent animals/networks.
- Source-time recovery: terminal shared readout and all-stage activity patterns; original unique branch/position plus max absolute state error <0.02 defines full-state recovery. Source-time convergence/residual is not applicable and never inferred from a different fixed field. Fixed-clock input and tonic-only state kicks are separately classified.
- Existing state kicks: reconstruct seeded preclip state, verify archived clipped initial state, record actual postclip target/whole RMS and clipping fraction; endpoints come directly from archived full-system integration.

## Verified results

Each encoding has 2,772 legal mixed initial states: 216 single-position endpoints and 2,556 R3-inactive endpoints. No sampled multi-position, outside-branch, or unconverged endpoint occurred. This does not establish an exhaustive attractor count or a global basin. No mixed stable attractor was found in these slices.

Each encoding has 288 paired stage-input trials: 196 full-state recoveries, 56 outside-branch outcomes, 33 R4-inactive outcomes and three preserved readouts/original locations without full-state recovery. Stage-specific counts follow below. All control replays agree with baseline within 1e-12; prehistory is bitwise identical.

The representative fixed-clock input assay preserves a full-state error plateau: seeds 7/11 lose R3 activity; seed 19 preserves the R3 position while full-state Euclidean error remains approximately 1.118 and PC1/2 error is approximately 1.22e-9. Projection alone would conceal this error. Source-time controls can recover under the normal clock; that is a different protocol.

'''+ '\n'.join(details)+'''

## Validation and reproducibility

Seven dedicated numerical tests cover five-category competition, the multi-branch/same-position edge case, source-time convergence isolation, full Euler step and Jacobian finite differences, zero pulse and paired history, orthogonal projection energy closure, and actual pre/postclip archived kick dose. reports/numerics_red.txt records the two semantic regression failures before correction; reports/numerics_green.txt records the passing suite. No main-model changes occurred.

Use analysis Python 3.12.12 / NumPy 2.3.5 / SciPy 1.16.3. On Windows prepend analysis, analysis/Library/bin and analysis/Scripts to the process PATH; bare invocation can fail during NumPy BLAS DLL loading. OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 were used. No packages were installed.

Rebuild: python -m handcrafted_ei.evaluation.paper_v3_dynamics
Tests: python -m unittest handcrafted_ei.tests.test_paper_v3_numerics -v

Numerical receipts contain source and input SHA256, full original configuration, thresholds, time windows and environment. derived/numerical_summary.csv is recomputed from the output files. The 21×21 slices describe selected 2D initial-state sections of full-state dynamics; no global/exhaustive six-attractor claim is made.
''',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--encodings',nargs='+',default=['one_hot','ring','topology'])
    p.add_argument('--output');p.add_argument('--grid-size',type=int,default=21);p.add_argument('--assays',nargs='+',default=['basin','perturbation','classify'])
    a=p.parse_args();run(a.encodings,a.output,a.grid_size,a.assays)
