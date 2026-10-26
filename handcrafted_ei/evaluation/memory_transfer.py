"""Offline timing and causal-control summaries, with explicit missing crossings."""
from pathlib import Path
import numpy as np
from .population_data import load_dataset
from .population_activity import save_rows


def first_crossing(t,x,threshold,after=0,below=False):
    selected=(t>=after)&((x<=threshold) if below else (x>=threshold))
    return float(t[np.flatnonzero(selected)[0]]) if selected.any() else np.nan


def analyze(d,input_dir=None,output_dir=None):
    t=d['times_ms']; g=d['groups']; rows=[]; traces={}; base=d['rates'][:,0,:]
    for memory,stage in (('M_D',2),('M_S',3)):
        for i,x in enumerate(d['rates']):
            m=x[:,g[memory]].max(1); response=x[:,g[f'R{stage}']].max(1)
            start=d['events'][i][f'to_R{stage}']; pre=m[t<start].max()
            onset=first_crossing(t,response,.1,after=start)
            stable=first_crossing(t,response,.9,after=start)
            decay=first_crossing(t,m,.95*pre,after=start,below=True)
            half=first_crossing(t,m,.5*pre,after=start,below=True)
            baseline=first_crossing(t,m,.05,after=start,below=True)
            rows.append({'trial_id':i,'memory':memory,'peak':float(m.max()),'response_onset_ms':onset,
                         'response_90pct_ms':stable,'decay_onset_95pct_ms':decay,
                         'half_crossing_ms':half,'half_life_from_decay_ms':half-decay,
                         'time_to_baseline_ms':baseline,'memory_response_lag_ms':decay-onset,
                         'na_rule':'NA means threshold not reached during recorded trial'})
    for name in ('M_D','M_S','R2','R3','I_decay_D','I_decay_S','E_gate_D','E_gate_S'):
        traces[name]=d['rates'][:,:,g[name]].max(2)
    controls={}; control_rows=[]
    if input_dir:
        for experiment in ('baseline','no_feedback','no_tonic','random_feedback_D_7','random_feedback_S_7'):
            c=d if experiment=='baseline' else load_dataset(input_dir,d['encoding_type'],experiment)
            targets=np.array([task['target'] for task in c['tasks']]); accuracy=float(np.all(c['outputs']==targets,axis=1).mean())
            controls[experiment]={name:c['rates'][:,:,g[name]].max(2).mean(0) for name in ('M_D','M_S','R2','R3')}
            controls[experiment]['accuracy']=accuracy
            for name in ('M_D','M_S','R2','R3'):
                control_rows.append({'experiment':experiment,'population':name,'terminal_max_rate_trial_mean':float(controls[experiment][name][-1]),'sequence_accuracy':accuracy})
    if output_dir:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); save_rows(out/'memory_transfer.csv',rows); save_rows(out/'memory_controls.csv',control_rows)
        np.savez_compressed(out/'memory_transfer.npz',times_ms=t,**traces,**{f'{exp}__{name}':v for exp,items in controls.items() for name,v in items.items()})
    return {'rows':rows,'traces':traces,'controls':controls,'control_rows':control_rows}
