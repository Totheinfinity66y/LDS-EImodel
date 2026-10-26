"""Post-hoc experiments on isolated copies; never advance task state."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np


def save_trace_shards(path,arrays):
    """One portable NPZ per snapshot; keep every individual array unchanged."""
    directory=Path(path).with_suffix(''); directory.mkdir(parents=True,exist_ok=True)
    prefixes=sorted({key.rsplit('_autonomous',1)[0] for key in arrays if key.endswith('_autonomous')})
    index={}
    for prefix in prefixes:
        data={key:arrays[key] for key in arrays if key.startswith(prefix+'_')}
        dest=directory/(prefix+'.npz')
        np.savez_compressed(dest,**data)
        with np.load(dest,allow_pickle=False) as saved:
            for key,value in data.items(): np.testing.assert_array_equal(saved[key],value)
        index[dest.name]={'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'arrays':sorted(data)}
    if sum(len(item['arrays']) for item in index.values())!=len(arrays):
        raise ValueError('unassigned trajectory arrays')
    (directory/'index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    return index


def free_evolution(model,duration_ms=2000,keep_clock=False,initial_rates=None):
    probe=deepcopy(model)
    probe.remove_stimulus()
    if not keep_clock: probe.clock[:]=0
    if initial_rates is not None:
        initial=np.asarray(initial_rates,dtype=float)
        if initial.shape!=probe.rates.shape or not np.all(np.isfinite(initial)) or np.any(initial<0) or np.any(initial>1):
            raise ValueError('invalid experimental initial state')
        probe.rates=initial.copy()
    steps=duration_ms/probe.config['dt_ms']
    if steps<0 or not float(steps).is_integer(): raise ValueError('invalid probe duration')
    trace=[probe.rates.copy()]
    for _ in range(int(steps)):
        probe.step(); trace.append(probe.rates.copy())
    return probe,np.array(trace)


def local_stability(model):
    r=model.rates
    w=model.signed_weights
    drive=w@r+model.tonic+model.stimulus+model.clock-model.theta
    field=(-r+np.clip(drive,0,1))/model.tau
    # Analytic derivative away from kinks, symmetric derivative at kinks.
    slope=((drive>0)&(drive<1)).astype(float)
    kink=np.isclose(drive,0,atol=1e-10)|np.isclose(drive,1,atol=1e-10)
    slope[kink]=.5
    jac=(-np.eye(len(r))+slope[:,None]*w)/model.tau[:,None]
    discrete=np.eye(len(r))+model.config['dt_ms']*jac
    return {'field_residual_per_ms':float(np.max(np.abs(field))),
            'euler_spectral_radius':float(np.max(np.abs(np.linalg.eigvals(discrete)))),
            'max_real_continuous_eigenvalue_per_ms':float(np.max(np.linalg.eigvals(jac).real)),
            'kink_units':int(kink.sum()),
            'jacobian_method':'piecewise-linear analytic; symmetric slope at threshold, not a global proof'}


def basin_probe(model,amplitudes=(.02,.1,.3,.7),seeds=(7,11,19),duration_ms=2000,trace_store=None,prefix=''):
    reference=model.rates.copy()
    rows=[]
    response=np.concatenate([model.groups[f'R{s}'] for s in range(1,5)])
    for amplitude in amplitudes:
        for seed in seeds:
            eps=np.random.default_rng(seed).normal(size=len(reference))
            eps=amplitude*eps/np.sqrt(np.mean(eps**2))
            initial=np.clip(reference+eps,0,1)
            end,trace=free_evolution(model,duration_ms=duration_ms,initial_rates=initial)
            if trace_store is not None: trace_store[f'{prefix}_basin_{amplitude}_{seed}']=trace
            error=float(np.max(np.abs(end.rates-reference)))
            response_error=float(np.max(np.abs(end.rates[response]-reference[response])))
            delta=float(np.max(np.abs(trace[-1]-trace[-21])))
            rows.append({'amplitude_rms_before_clipping':amplitude,'seed':seed,
                         'actual_rms':float(np.sqrt(np.mean((initial-reference)**2))),
                         'initial_max_distance':float(np.max(np.abs(initial-reference))),
                         'final_max_distance':error,'response_max_distance':response_error,
                         'tail_change_100ms':delta,'recovered':error<.02,
                         'final_field_residual_per_ms':float(np.max(np.abs(
                             (-end.rates+np.clip(end.signed_weights@end.rates+end.tonic+end.clock-end.theta,0,1))/end.tau))),
                         'response_recovered':response_error<.02,
                         'final_rates':end.rates.tolist()})
    return rows


def analyze_snapshots(snapshots,out=None):
    """Each snapshot is a network copied at an independent readout event."""
    report=[]
    arrays={}
    for key,model in snapshots.items():
        autonomous,trace=free_evolution(model)
        forced,forced_trace=free_evolution(model,keep_clock=True)
        stability=local_stability(autonomous)
        probes=basin_probe(autonomous,trace_store=arrays,prefix=key)
        arrays[key+'_initial_rates']=model.rates
        arrays[key+'_initial_clock']=model.clock
        # Explicit zero and six broad/random initial conditions.
        initial_results=[]
        for seed in (7,11,19):
            initial=np.random.default_rng(seed).uniform(0,1,len(model.rates))
            end,path=free_evolution(model,initial_rates=initial)
            arrays[f'{key}_initial_{seed}']=path
            initial_results.append({'seed':seed,'end_rates':end.rates.tolist(),
                                    'tail_change':float(np.max(np.abs(path[-1]-path[-21]))),
                                    'residual':local_stability(end)['field_residual_per_ms']})
        arrays[key+'_autonomous']=trace; arrays[key+'_forced']=forced_trace
        report.append({'snapshot':key,'sample_off':True,'autonomous_clock_off':True,
                       'tonic_background_retained':True,'duration_ms':2000,
                       'autonomous':stability,'forced':local_stability(forced),
                       'forced_vs_autonomous_max_distance':float(np.max(abs(forced.rates-autonomous.rates))),
                       'autonomous_final_rates':autonomous.rates.tolist(),
                       'small_perturbation_local_recovery':all(p['recovered'] for p in probes if p['amplitude_rms_before_clipping']<=.1),
                       'basin_probes':probes,'random_initial_states':initial_results})
    endpoints={key:np.array(row['autonomous_final_rates']) for key,row in zip(snapshots,report)}
    for row in report:
        mode=row['snapshot'].split('_L')[0]
        candidates={key:state for key,state in endpoints.items() if key.startswith(mode+'_L')}
        for probe in row['basin_probes']:
            final=np.array(probe['final_rates'])
            distances={key:float(np.max(abs(final-state))) for key,state in candidates.items()}
            nearest=min(distances,key=distances.get)
            probe['nearest_sampled_fixed_state']=nearest
            probe['nearest_fixed_state_max_distance']=distances[nearest]
            probe['outcome']=('recovered' if probe['recovered'] else
                              'jump_to_sampled_state' if distances[nearest]<.02 else
                              'other_converged_state' if probe['final_field_residual_per_ms']<1e-8 else
                              'not_converged_in_window')
    zero,_=free_evolution(next(iter(snapshots.values())).__class__())
    if out is not None:
        save_trace_shards(out,arrays)
    distinct={}
    for mode in sorted({key.split('_L')[0] for key in snapshots}):
        representatives=[]
        for key,state in endpoints.items():
            if key.startswith(mode+'_L') and all(np.max(abs(state-other))>.02 for other in representatives):
                representatives.append(state)
        distinct[mode]=len(representatives)
    return {'criteria':{'residual_per_ms':1e-8,'local_recovery_max_error':.02,
                        'small_amplitudes':[.02,.1],'euler_spectral_radius_upper_bound':1},
            'rest':local_stability(zero),'distinct_sampled_endpoints_by_encoding':distinct,'snapshots':report,
            'scope':'local fixed-point and finite basin probes; not continuous attractors or global basin coverage'}
