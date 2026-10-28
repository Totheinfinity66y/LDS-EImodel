"""Read-only Figure 1--3 derivatives; all coordinates originate in REC metadata."""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
from .population_data import validate_dataset, source_identity, load_dataset
from .population_activity import branch_masks, save_rows

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'handcrafted_ei/artifacts/v2/run'


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def recording(encoding):
    directory = ROOT/'artifacts/neural_representation_v2/data'/encoding
    meta = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
    with np.load(directory/'recording.npz', allow_pickle=False) as f:
        d = {k:f[k].copy() for k in f.files}
    d.update(meta)
    d['labels'] = d['neuron_labels']
    d['groups'] = {k:np.array(v,int) for k,v in meta['population_indices'].items()}
    d['branch_indices'] = {k:np.array(v,int) for k,v in meta['branch_indices'].items()}
    validate_dataset(d)
    protected = source_identity(RAW)
    archive = RAW/f'{encoding}__baseline.zip'
    if digest(archive) != meta['archive_sha256']:
        raise ValueError('REC source archive mismatch')
    archived = load_dataset(RAW, encoding)
    if not np.array_equal(d['rates'], archived['rates']):
        raise ValueError('REC rates do not match original archive')
    d['lesions']=archived['lesions']
    provenance = {'recording':str(directory/'recording.npz'),
                  'recording_sha256':digest(directory/'recording.npz'),
                  'metadata_sha256':digest(directory/'metadata.json'),
                  'archive_sha256':digest(archive), 'protected_sources':protected,
                  'rates_shape':list(d['rates'].shape), 'units':'dimensionless',
                  'independent_repeats':False, 'active_threshold':0.1,
                  'events':d['events'][0], 'indices':meta['population_indices'],
                  'branch_indices':meta['branch_indices'], 'config':meta['config']}
    return d,provenance


def derive(d, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    r=d['rates'];t=d['times_ms'];g=d['groups']; arrays={'times_ms':t};rows=[]
    for name,idx in g.items():
        arrays[name+'__trial_peak']=r[:,:,idx].max(2)
        arrays[name+'__trial_mean']=r[:,:,idx].mean(2)
    for kind in ('E','I'):
        idx=np.flatnonzero(d['neuron_types']==kind)
        arrays[kind+'__total']=r[:,:,idx].sum(2)
        arrays[kind+'__active_fraction']=(r[:,:,idx]>.1).mean(2)
    np.savez_compressed(output/'fig01_population_activity.npz',**arrays)
    grouped=[]
    for stage in range(1,5):
        for i,task in enumerate(d['tasks']):
            end=d['events'][i][f'readout{stage}'];window=(t>end-d['config'].get('decision_ms',20))&(t<=end)
            for branch,idx in enumerate(d['branch_indices'][f'R{stage}']):
                for position,unit in enumerate(idx):
                    grouped.append({'trial_id':i,'L':task['L'],'D':task['D'],'S':task['S'],
                                    'stage':stage,'population':f'R{stage}','branch':branch,'position':position,
                                    'neuron_index':int(unit),'neuron_label':str(d['labels'][unit]),
                                    'decision_window_mean_rate':float(r[i,window,unit].mean())})
    save_rows(output/'fig01_stage_branch_position.csv',grouped)
    branch={'times_ms':t};summaries=[]
    for s in range(1,5):
        idx=d['branch_indices'][f'R{s}'];a=r[:,:,idx].max(3)
        selected=np.argmax(np.stack(branch_masks(d,s),axis=1),axis=1)
        chosen=np.take_along_axis(a,selected[:,None,None],axis=2)[:,:,0]
        other=a.copy();other[np.arange(len(r)),:,selected]=-np.inf
        competitor=other.max(2) if len(idx)>1 else np.full_like(chosen,np.nan)
        branch[f'R{s}__activity']=a;branch[f'R{s}__selected']=selected
        branch[f'R{s}__margin']=chosen-competitor
        branch[f'R{s}__competitor']=competitor
        for i in range(len(r)):
            end=d['events'][i][f'readout{s}'];start=d['events'][i].get(f'to_R{s}',0)
            window=(t>=start)&(t<=end);onset=np.flatnonzero(window&(chosen[i]>.1))
            decision=(t>end-d['config'].get('decision_ms',20))&(t<=end)
            summaries.append({'trial_id':i,'stage':s,'branch':int(selected[i]),
                'active_branches_at_readout':int((a[i,decision].mean(0)>.1).sum()),
                'selected_peak_at_readout':float(chosen[i,decision].mean()),
                'competitor_peak_at_readout':float(competitor[i,decision].mean()),
                'onset_ms':float(t[onset[0]]) if len(onset) else np.nan,
                'error_branch_activity_integral_rate_ms':float(np.trapezoid(competitor[i,window],t[window])),
                'selected_std_after_onset':float(chosen[i,window&(t>=t[onset[0]])].std()) if len(onset) else np.nan})
    np.savez_compressed(output/'fig02_branch_dynamics.npz',**branch)
    save_rows(output/'fig02_branch_dynamics.csv',summaries)
    handoff={'times_ms':t}
    for name,var,stage in [('M_D','D',2),('R2','D',2),('M_S','S',3),('R3','S',3)]:
        y=np.array([v[var] for v in d['tasks']]);lo,hi=np.unique(y)
        x=r[:,:,g[name]]
        # Balanced full-factorial means; axis trained at a declared fixed time.
        delta=x[y==hi].mean(0)-x[y==lo].mean(0)
        anchor=d['events'][0]['delay_end' if name.startswith('M') else f'readout{stage}']
        axis=delta[np.argmin(abs(t-anchor))];norm=np.linalg.norm(axis)
        unit=axis/norm if norm>1e-12 else np.zeros_like(axis)
        center=x[:,np.argmin(abs(t-anchor))].mean(0)
        handoff[name+'__axis']=unit;handoff[name+'__center']=center
        handoff[name+'__axis_anchor_ms']=anchor
        handoff[name+'__contrast']=delta
        handoff[name+'__projection']=(x-center)@unit
        handoff[name+'__levels']=np.array([lo,hi])
    np.savez_compressed(output/'fig03_handoff_axes.npz',**handoff)
    return arrays,branch,summaries,handoff
