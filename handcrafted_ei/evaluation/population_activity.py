"""Read-only whole-population summaries. Rates are dimensionless, not Hz."""
import csv
from pathlib import Path
import numpy as np


def save_rows(path, rows):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: return
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader()
        for row in rows:
            writer.writerow({k:('NA' if isinstance(v,(float,np.floating)) and not np.isfinite(v) else v) for k,v in row.items()})


def validate_dataset(d):
    r=np.asarray(d['rates']); t=np.asarray(d['times_ms'])
    if r.ndim!=3 or r.shape[1]!=len(t) or r.shape[2]!=len(d['labels']): raise ValueError('rates/time/labels mismatch')
    if len(d['tasks'])!=len(r) or len(d['neuron_types'])!=r.shape[2]: raise ValueError('metadata mismatch')
    if not np.isfinite(r).all() or not np.all(np.diff(t)>0): raise ValueError('nonfinite rates or unordered times')
    if set(d['neuron_types'])-{'E','I'}: raise ValueError('incomplete E/I classification')
    for name,idx in d['groups'].items():
        idx=np.asarray(idx,dtype=int)
        if np.any(idx<0) or np.any(idx>=r.shape[2]) or len(set(idx))!=len(idx): raise ValueError('invalid group '+name)
    for stage in range(1,5):
        if len(d['groups'][f'R{stage}'])!=6*(1,2,4,4)[stage-1]: raise ValueError('invalid branch layout')
    return True


def event_times(d, key):
    e=d['events']
    if isinstance(e,dict): return np.full(len(d['rates']),e[key],dtype=float)
    return np.array([x[key] for x in e],dtype=float)


def stage_samples(d,stage,window_ms=None):
    """Average final decision window before each recorded readout, inclusive."""
    end=event_times(d,f'readout{stage}')
    width=d['config'].get('decision_ms',20.) if window_ms is None else window_ms
    t=np.asarray(d['times_ms']); r=np.asarray(d['rates'])
    return np.stack([x[(t>e-width)&(t<=e)].mean(0) for x,e in zip(r,end)])


def branch_masks(d,stage):
    tasks=d['tasks']; ds=np.array([x['D'] for x in tasks]); ss=np.array([x['S'] for x in tasks])
    if stage==1: return [np.ones(len(tasks),dtype=bool)]
    if stage==2: return [ds==v for v in (1,-1)]
    return [(ds==v)&(ss==s) for v in (1,-1) for s in (1,2)]


def population_sets(d):
    g=d['groups']
    return {'whole':np.arange(np.asarray(d['rates']).shape[2]),
            'response':np.concatenate([g[f'R{s}'] for s in range(1,5)]),
            'memory':np.r_[g['M_D'],g['M_S']],
            **{k:np.asarray(v) for k,v in g.items()}}


def analyze(d,output_dir=None,active_threshold=.1):
    validate_dataset(d); r=np.asarray(d['rates']); base=r[:,0:1,:]; delta=r-base
    metrics={}; rows=[]
    for name,idx in population_sets(d).items():
        x=r[:,:,idx]; dx=delta[:,:,idx]
        metrics[name]={'mean':x.mean((0,2)),'peak':x.max((0,2)),
                       'baseline_subtracted':dx.mean((0,2)),'active_fraction':(dx>active_threshold).mean((0,2)),
                       'total':x.sum(2).mean(0)}
        for k,t in enumerate(d['times_ms']):
            rows.append({'population':name,'time_ms':float(t),**{v:float(a[k]) for v,a in metrics[name].items()}})
    stages=np.stack([stage_samples(d,s)-r[:,0,:] for s in range(1,5)])
    result={'population':metrics,'stage_samples':stages,'baseline':base[:,0,:], 'active_threshold':active_threshold}
    if output_dir:
        save_rows(Path(output_dir)/'population_activity.csv',rows)
        np.savez_compressed(Path(output_dir)/'population_activity.npz',stage_samples=stages,
                            **{f'{p}__{k}':v for p,x in metrics.items() for k,v in x.items()})
    return result
