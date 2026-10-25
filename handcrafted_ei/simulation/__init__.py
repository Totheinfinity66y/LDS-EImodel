"""Clock orchestration and full activity recording; no symbolic LDS arithmetic."""
from dataclasses import dataclass
import numpy as np


@dataclass
class TrialResult:
    outputs: tuple
    decisions: np.ndarray
    times: np.ndarray
    rates: np.ndarray
    y: np.ndarray
    events: dict
    groups: dict
    lesions: list


def lesion_edges(model,kind,random_seed=None):
    """Experimental edge cuts, separate from normal state advancement."""
    w=model.weights; g=model.groups
    if kind=='A': pre=g['release12']; post=g['gate12']
    elif kind=='B': pre=g['M_D']; post=g['release12']
    elif kind=='C': pre=g['release23']; post=g['gate23']
    elif kind=='D': pre=np.r_[g['M_D'],g['M_S']]; post=np.r_[g['release12'],g['release23']]
    elif kind=='no_i_to_i':
        pre=post=np.flatnonzero(model.signs==-1)
    else: raise ValueError('unknown intervention')
    mask=np.zeros(w.shape,dtype=bool); mask[np.ix_(post,pre)]=True; mask &= w>0
    edges=np.argwhere(mask)
    if random_seed is not None:
        # Same count, weight magnitude and presynaptic sign, at the same time.
        value=w[tuple(edges[0])]; sign=model.signs[edges[0,1]]
        pool=np.argwhere((w==value)&(model.signs[None,:]==sign))
        edges=pool[np.random.default_rng(random_seed).choice(len(pool),len(edges),replace=False)]
    record={'kind':kind,'random_seed':random_seed,'start_ms':model.time_ms,
            'edges':edges.tolist(),'magnitudes':[float(w[tuple(e)]) for e in edges]}
    w[edges[:,0],edges[:,1]]=0
    return record


def run_trial(model,encoded,intervention=None,random_seed=None,after_readout=None):
    c=model.config; model.initialize()
    times=[model.time_ms]; rates=[model.get_activity()]; events={}; lesions=[]
    def integrate(duration):
        steps=duration/c['dt_ms']
        if steps<0 or not float(steps).is_integer(): raise ValueError('invalid clock duration')
        for _ in range(int(steps)):
            model.step(); times.append(model.time_ms); rates.append(model.get_activity())
    model.apply_input(**encoded); events['sample_start']=model.time_ms
    integrate(c['sample_ms']); model.remove_stimulus(); events['sample_end']=model.time_ms
    integrate(c['delay_ms']); events['delay_end']=model.time_ms
    outputs=[]; decisions=[]
    for stage in range(1,5):
        events[f'readout{stage}_start']=model.time_ms
        integrate(c['readout_ms'])
        n=int(c['decision_ms']/c['dt_ms'])
        if n<1 or c['decision_ms']>c['readout_ms']: raise ValueError('invalid decision window')
        y=np.mean(np.asarray(rates[-n:])[:,model.groups['Y']],axis=0)
        decisions.append(y)
        outputs.append(int(np.argmax(y)) if y.max()>=c['decision_threshold'] else -1)
        events[f'readout{stage}']=model.time_ms
        if after_readout: after_readout(model,stage)
        if stage==4: break
        integrate(c['gap_ms'])
        trigger={'A':1,'B':2,'C':2,'D':3,'no_i_to_i':1}
        if intervention and trigger[intervention]==stage:
            lesions.append(lesion_edges(model,intervention,random_seed))
        event=f'to_R{stage+1}'; events[event]=model.time_ms
        model.advance_phase(event); integrate(c['transfer_ms'])
        event=f'retire{stage}'; events[event]=model.time_ms
        model.advance_phase(event); integrate(c['retire_ms'])
    events['end']=model.time_ms
    for record in lesions: record['end_ms']=model.time_ms
    rates=np.asarray(rates)
    return TrialResult(tuple(outputs),np.asarray(decisions),np.asarray(times),rates,
                       rates[:,model.groups['Y']],events,model.groups,lesions)
