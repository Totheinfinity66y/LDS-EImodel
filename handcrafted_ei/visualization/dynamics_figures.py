"""Fixed-input, full-state metrics; projected figures never define recovery."""
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from .style import panels,NAMES


def read_rows(path):
    with Path(path).open(encoding='utf-8') as f: return list(csv.DictReader(f))


def fixed_points(mode,out):
    root=Path(out); rows=read_rows(root/'metrics/dynamics_fixed_points.csv')
    fig,ax=plt.subplots(2,3,figsize=(13,8),layout='constrained')
    for s in range(1,5):
        with np.load(root/f'data/dynamics/{mode}_L0_R{s}.npz') as z:
            t=z['times_ms']; response=np.arange((0,6,18,42)[s-1],(6,18,42,66)[s-1])
            for condition,ls in [('forced','-'),('tonic_only','--')]:
                x=z[f'control_{condition}']; ax[0,0].plot(t,x[:,response].max(1),label=f'R{s} {condition}',ls=ls,lw=.9)
                ax[0,1].plot(t,np.linalg.norm(x-x[0],axis=1),ls=ls,lw=.9)
                ax[0,2].semilogy(t[1:],np.maximum(np.linalg.norm(np.diff(x,axis=0),axis=1)/5,1e-18),ls=ls,lw=.9)
    selected=[r for r in rows if r['encoding']==mode]
    ax[1,0].semilogy([float(r['residual_l2_per_ms']) for r in selected],'o',ms=3)
    ax[1,1].plot([float(r['euler_spectral_radius']) for r in selected],'o',ms=3); ax[1,1].axhline(1,color='black',ls=':')
    endpoints=read_rows(root/'metrics/dynamics_endpoints.csv'); states=[]
    for row in endpoints:
        if row['encoding']!=mode: continue
        x=np.array(__import__('json').loads(row['endpoint_state']))
        if all(np.max(abs(x-y))>1e-8 for y in states): states.append(x)
    states=np.array(states); distances=np.linalg.norm(states[:,None]-states[None,:],axis=2)
    im=ax[1,2].imshow(distances,origin='lower',aspect='auto',cmap='viridis'); fig.colorbar(im,ax=ax[1,2],label='Full-state L2 distance',shrink=.7)
    titles=['State persistence (L=0; four stages)','Distance to sampled readout state','Full-state velocity','Endpoint continuous field residual','Euler map local spectral radius','Distinct random-start endpoints (deduplicated)']
    for axis,title in zip(ax.ravel(),titles): axis.set_title(title)
    ax[0,0].legend(ncol=2,fontsize=5.5); ax[0,0].set(ylabel='Response peak normalized rate',ylim=(0,1.03)); ax[0,1].set_ylabel('L2 distance'); ax[0,2].set_ylabel('L2 rate / ms')
    for axis in ax[0]: axis.set_xlabel('Extended time (ms)')
    ax[1,0].set(xlabel='Snapshot / fixed-input condition',ylabel='||f(r)||2 per ms'); ax[1,1].set(xlabel='Snapshot / condition',ylabel='rho(I + dt J)'); ax[1,2].set(xlabel='Initial-state experiment',ylabel='Initial-state experiment')
    panels(ax); fig.suptitle(NAMES[mode]+' | Figure 8: fixed-input state extension; tonic-only = autonomous'); return fig


def perturbation(mode,out):
    root=Path(out); fig,ax=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    with np.load(root/f'data/dynamics/{mode}_L0_R3.npz') as z:
        t=z['times_ms']; baseline=z['perturbation_control']; paths=z['perturbation_rates']; basis=z['vector_basis']; origin=z['vector_origin']
        ref=(baseline-origin)@basis; p=(paths[0,2,0]-origin)@basis
        ax[0,0].plot(*ref.T,color='black',label='Control'); ax[0,0].plot(*p.T,color='#D55E00',label='Full RMS .3, seed 7'); ax[0,0].scatter(*p[::40].T,s=10,c=t[::40],cmap='viridis'); ax[0,0].legend(); ax[0,0].set(xlabel='Endpoint PC1',ylabel='Endpoint PC2',title='Projected perturbation (L=0, R3)')
        final_distance=float(np.linalg.norm(paths[0,2,0,-1]-baseline[-1])); ax[0,0].text(.02,.02,f'Full-state final L2 = {final_distance:.3g}\nProjection alone does not define recovery',transform=ax[0,0].transAxes,fontsize=7)
        for target in range(6):
            ds=z['distances_l2'][target,1]; denom=np.where(ds[:,0]>0,ds[:,0],1)
            ax[0,1].plot(t,(ds/denom[:,None]).mean(0),label=str(z['target_names'][target]))
        ax[0,1].set(title='RMS .1: normalized full-state distance',xlabel='Time (ms)',ylabel='d(t) / d(0)'); ax[0,1].legend(ncol=2)
        ct=z['cross_temporal_times_ms']; im=ax[0,2].imshow(z['cross_temporal_distance'],origin='lower',aspect='auto',extent=[ct[0],ct[-1],ct[0],ct[-1]]); fig.colorbar(im,ax=ax[0,2],label='Full-state L2'); ax[0,2].set(title='Full RMS .3: cross-temporal distance',xlabel='Control time (ms)',ylabel='Perturbed time (ms)')
        xy=z['vector_grid_xy']; v=z['vector_xy_per_ms']; off=z['vector_offplane_norm_per_ms']; im=ax[1,2].quiver(*xy.T,*v.T,off,cmap='viridis'); fig.colorbar(im,ax=ax[1,2],label='Off-plane ||f|| / ms'); ax[1,2].set(title='Clipped local slice; projected flow',xlabel='Endpoint PC1 offset',ylabel='Endpoint PC2 offset')
    rows=[r for r in read_rows(root/'metrics/dynamics_perturbation.csv') if r['encoding']==mode and r['status']=='OK']; amplitudes=sorted({float(r['amplitude_target_rms_before_clipping']) for r in rows})
    for name in ('full','response','active_branch','unselected_branch','E','I'):
        recovery=[]; switching=[]
        for amplitude in amplitudes:
            subset=[r for r in rows if r['target']==name and float(r['amplitude_target_rms_before_clipping'])==amplitude]
            recovery.append(np.mean([r['recovered']=='True' for r in subset])); switching.append(np.mean([r['state_switched']=='True' for r in subset]))
        ax[1,0].plot(amplitudes,recovery,'o-',label=name); ax[1,1].plot(amplitudes,switching,'o-',label=name)
    ax[1,0].set(title='Finite-basin recovery with identity retained',xlabel='Target RMS before clipping',ylabel='Recovery fraction',ylim=(-.02,1.02)); ax[1,0].legend(ncol=2)
    ax[1,1].set(title='Position / branch identity switches',xlabel='Target RMS before clipping',ylabel='Switch fraction',ylim=(-.02,1.02))
    panels(ax); fig.suptitle(NAMES[mode]+' | Figure 9: six perturbation targets; full-state recovery, no rest-as-recovery'); return fig
