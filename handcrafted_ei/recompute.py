"""Independent post-hoc representation and attractor receipt checks.

Only archive arrays enter these calculations; task state is never resumed.
"""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
from .model.ei_network import EINetwork
from .simulation import TrialResult
from .evaluation.representation import analyze
from .evaluation.attractors import local_stability


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def close_tree(actual,expected):
    if isinstance(expected,dict):
        if set(actual)!=set(expected): raise ValueError('different representation fields')
        for key in expected: close_tree(actual[key],expected[key])
    elif isinstance(expected,list):
        if len(actual)!=len(expected): raise ValueError('different representation lengths')
        for a,b in zip(actual,expected): close_tree(a,b)
    elif isinstance(expected,(float,int)):
        np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12)
    elif actual!=expected: raise ValueError('different representation values')


def audit(out,report_path=None):
    out=Path(out)
    geometry=read_json(out/'representation.json')
    attractors=read_json(out/'attractors.json')
    config=read_json(out/'config.json')
    snapshots={}; trials=0
    for mode in geometry:
        results=[]
        with ZipFile(out/(mode+'__baseline.zip')) as z:
            for i in range(24):
                obs=json.loads(z.read(f'{i:02}_events.json'))
                with np.load(BytesIO(z.read(f'{i:02}_rates.npz')),allow_pickle=False) as data:
                    rates=data['rates']; times=data['times_ms']; y=data['y']
                groups={k:np.array(v) for k,v in obs['groups'].items()}
                r=TrialResult(tuple(obs['outputs']),np.array(obs['decisions']),times,rates,y,obs['events'],groups,obs['lesions'])
                results.append(r); trials+=1
                if i%4==0:
                    for stage in range(1,5):
                        snapshots[f'{mode}_L{i//4}_R{stage}']=rates[np.argmin(abs(times-r.events[f'readout{stage}']))]
        close_tree(analyze(results),geometry[mode]['neural'])
    worst_update_error=0.; probe_count=0
    trace_directory=out/'attractor_trajectories'
    trace_index=read_json(trace_directory/'index.json')
    for row in attractors['snapshots']:
        shard=trace_directory/(row['snapshot']+'.npz')
        entry=trace_index[shard.name]
        if hashlib.sha256(shard.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('attractor trace shard checksum mismatch')
        with np.load(shard,allow_pickle=False) as arrays:
            if sorted(arrays.files)!=entry['arrays']: raise ValueError('trace array index mismatch')
            key=row['snapshot']; mode=key.split('_L')[0]
            m=EINetwork(overrides={**config,'location_encoding':mode})
            initial=arrays[key+'_initial_rates']; clock=arrays[key+'_initial_clock']
            np.testing.assert_array_equal(initial,snapshots[key])
            autonomous=arrays[key+'_autonomous']; forced=arrays[key+'_forced']
            for suffix,trace,c in [('autonomous',autonomous,np.zeros_like(clock)),('forced',forced,clock)]:
                np.testing.assert_array_equal(trace[0],initial)
                m.rates=trace[-1].copy(); m.clock=c.copy()
                close_tree(local_stability(m),row[suffix])
            np.testing.assert_array_equal(autonomous[-1],row['autonomous_final_rates'])
            traces=[(autonomous,np.zeros_like(clock)),(forced,clock)]
            for p in row['basin_probes']:
                a=p['amplitude_rms_before_clipping']; seed=p['seed']
                trace=arrays[f'{key}_basin_{a}_{seed}']
                eps=np.random.default_rng(seed).normal(size=len(initial))
                start=np.clip(autonomous[-1]+a*eps/np.sqrt(np.mean(eps**2)),0,1)
                np.testing.assert_array_equal(trace[0],start)
                np.testing.assert_array_equal(trace[-1],p['final_rates'])
                error=float(np.max(abs(trace[-1]-autonomous[-1])))
                np.testing.assert_allclose(error,p['final_max_distance'],rtol=0,atol=0)
                if (error<.02)!=p['recovered']: raise ValueError('recovery classification mismatch')
                traces.append((trace,np.zeros_like(clock))); probe_count+=1
            for p in row['random_initial_states']:
                trace=arrays[f'{key}_initial_{p["seed"]}']
                np.testing.assert_array_equal(trace[-1],p['end_rates'])
                np.testing.assert_array_equal(trace[0],np.random.default_rng(p['seed']).uniform(0,1,len(initial)))
                traces.append((trace,np.zeros_like(clock)))
            for trace,c in traces:
                if trace.shape!=(401,len(initial)) or not np.isfinite(trace).all() or trace.min()<0 or trace.max()>1:
                    raise ValueError('invalid free-evolution trace')
                drive=trace[:-1]@m.signed_weights.T+m.tonic+c-m.theta
                expected=trace[:-1]+m.config['dt_ms']/m.tau*(-trace[:-1]+np.clip(drive,0,1))
                err=float(np.max(abs(trace[1:]-expected)))
                worst_update_error=max(worst_update_error,err)
                if err>1e-13: raise ValueError('autonomous/forced Euler evolution mismatch')
    root=Path(__file__).parent.parent
    executed=read_json(out/'source_hashes.json')
    changed={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p,h in executed.items()
             if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h}
    model_changed=[p for p in changed if 'handcrafted_ei/model/' in p.replace('\\','/') or
                   'handcrafted_ei/config/baseline.yaml' in p.replace('\\','/') or
                   'handcrafted_ei/simulation/' in p.replace('\\','/') or
                   'handcrafted_ei/task/' in p.replace('\\','/')]
    if model_changed: raise ValueError(f'executed model source drift: {model_changed}')
    result={'status':'PASS','baseline_trials_recomputed':trials,'snapshots_checked':len(snapshots),
            'perturbations_recomputed':probe_count,'max_euler_update_error':worst_update_error,
            'all_trajectory_steps_checked':True,'executed_model_source_unchanged':True,
            'post_experiment_file_changes':changed,
            'checks':['full representation from archived baselines','snapshot identity',
                      'autonomous and forced local spectrum','regenerated perturbations and random starts',
                      'all free/forced/perturbed/initial-state Euler steps','recovery classification']}
    destination=Path(report_path) if report_path else out/'analysis_verification.json'
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(result,flush=True)
    return result


def snapshot_sources(out):
    root=Path(__file__).parent.parent; package=root/'handcrafted_ei'
    sources=[p for p in package.rglob('*') if p.is_file() and 'artifacts' not in p.parts and '__pycache__' not in p.parts]
    sources += [root/n for n in ('AGENTS.md','architecture.md','README.md','todo.md','docs/v2_protocol.md','docs/v2_implementation_report.md')]
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    with ZipFile(out/'final_source.zip','w',ZIP_DEFLATED) as z:
        for p in sources: z.write(p,p.relative_to(root))
    (out/'final_source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('directory',type=Path)
    parser.add_argument('--report-directory',type=Path)
    args=parser.parse_args(); directory=args.directory
    reports=args.report_directory or directory
    reports.mkdir(parents=True,exist_ok=True)
    audit(directory,report_path=reports/'analysis_verification.json'); snapshot_sources(reports)
