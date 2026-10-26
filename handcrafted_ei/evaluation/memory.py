"""Measures from archived activity. No state updates or task targets."""
import numpy as np


def sustained_crossing(times,values,threshold,start_ms=0,above=True,hold_ms=30):
    mask=(values>=threshold if above else values<=threshold)&(times>=start_ms)
    n=max(1,int(round(hold_ms/(times[1]-times[0]))))
    for i in np.flatnonzero(mask):
        if i+n<=len(mask) and mask[i:i+n].all(): return float(times[i])
    return None


def analyze_memory(result):
    rows={}
    t=result.times; r=result.rates; g=result.groups
    for memory,response,event in [('M_D','R2','to_R2'),('M_S','R3','to_R3')]:
        m=r[:,g[memory]].max(axis=1); active=r[:,g[response]].max(axis=1)
        trigger=result.events[event]
        formation=sustained_crossing(t,active,.9,trigger)
        half=sustained_crossing(t,m,.5,trigger,above=False)
        efold=sustained_crossing(t,m,1/np.e,trigger,above=False)
        decay90=sustained_crossing(t,m,.1,trigger,above=False)
        before=(t>=result.events['sample_end'])&(t<=trigger)
        after=t>=trigger
        band=after&(m>=.2)&(m<=.8)
        tau=None
        if band.sum()>2:
            slope=np.polyfit(t[band],np.log(m[band]),1)[0]
            if slope<0: tau=float(-1/slope)
        at_readout=result.events['readout2' if response=='R2' else 'readout3']
        idx=np.argmin(abs(t-at_readout))
        branches=r[idx,g[response]].reshape(-1,6).max(axis=1)
        rows[memory]={'response_formation_ms':formation,'half_activity_ms':half,
                      'half_after_formation_ms':None if half is None or formation is None else half-formation,
                      'efold_after_formation_ms':None if efold is None or formation is None else efold-formation,
                      'decay_to_10percent_ms':decay90,'fit_effective_tau_ms_80_to_20':tau,
                      'pre_handoff_min':float(m[before].min()),'terminal_activity':float(m[-1]),
                      'auc_after_sample_rate_ms':float(np.trapezoid(m[t>=result.events['sample_end']],t[t>=result.events['sample_end']])),
                      'auc_after_permission_rate_ms':float(np.trapezoid(m[after],t[after])),
                      'response_selected_branch_margin_at_readout':float(np.sort(branches)[-1]-np.sort(branches)[-2])}
    return rows
