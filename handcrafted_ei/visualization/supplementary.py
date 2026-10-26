"""Additional panels preserve metrics that would overcrowd the main figures."""
import numpy as np
import matplotlib.pyplot as plt
from .style import panels,NAMES


def population_metrics(d,r):
    fig,ax=plt.subplots(2,3,figsize=(13,7),layout='constrained'); t=d['times_ms']
    for axis,metric in zip(ax.ravel(),('mean','peak','baseline_subtracted','active_fraction','total')):
        for name in ('R1','R2','R3','R4','M_D','M_S','E_gate_D','I_decay_D','I_tonic_R'):
            axis.plot(t,r['activity']['population'][name][metric],label=name,lw=.9)
        axis.set(title=metric.replace('_',' '),xlabel='Time (ms)',ylabel='Fraction' if metric=='active_fraction' else 'Dimensionless rate' if metric!='total' else 'Summed dimensionless rate')
    ax[0,0].legend(ncol=3); ax[1,2].axis('off'); ax[1,2].text(0,1,'All 24 conditions averaged\nBaseline: actual t=0 vector\nActive: baseline-subtracted rate > .1\nPeak: across trials and units\nNo confidence intervals for deterministic trials\nRaw per-trial trajectories are archived',va='top',linespacing=1.7)
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 1 supplement: all population summary definitions'); return fig


def geometry_metrics(d,r):
    fig,ax=plt.subplots(4,4,figsize=(14,12),layout='constrained'); a=r['subspaces']
    for col,s in enumerate(range(1,5)):
        for b,v in enumerate(a['stages'][s]['branches']):
            ax[0,col].semilogy(np.arange(1,len(v['whole']['singular_values'])+1),np.maximum(v['whole']['singular_values'],1e-18),'o-',ms=2,label=f'b{b}')
            ax[1,col].plot(np.arange(1,len(v['whole']['evr'])+1),v['whole']['evr'],'o-',ms=2,label=f'b{b}')
        ax[0,col].set(title=f'R{s} singular values',xlabel='Index',ylabel='Singular value'); ax[1,col].set(title=f'R{s} individual VAF',xlabel='PC',ylabel='Variance fraction')
        im=ax[2,col].imshow(a['stages'][s]['overlap'],vmin=0,vmax=1,origin='lower',aspect='auto'); ax[2,col].set(title=f'R{s} full-state subspace overlap',xlabel='Branch',ylabel='Branch'); fig.colorbar(im,ax=ax[2,col],shrink=.6)
        rows=[x for x in r['seed_stability'] if x['stage']==s]; branches=sorted({x['branch'] for x in rows})
        for j,b in enumerate(branches):
            vals=[x['projection_overlap'] for x in rows if x['branch']==b]; ax[3,col].scatter(np.full(len(vals),b),vals,s=14)
        ax[3,col].set(title=f'R{s} independent noise-seed fits',xlabel='Branch',ylabel='95%-VAF projection overlap',ylim=(-.02,1.02))
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 5 supplement: spectra and seed stability (sigma=.03)'); return fig


def position_controls(d,r):
    fig,ax=plt.subplots(3,4,figsize=(13,9),layout='constrained'); panels_data=r['rsa']['panels']
    vmax=max(p['rdm']['euclidean'].max() for p in panels_data.values())
    for col,s in enumerate(range(1,5)):
        p=panels_data[(s,0)]
        for row,kind in enumerate(('cosine','correlation')):
            im=ax[row,col].imshow(p['rdm'][kind],vmin=0,vmax=2,origin='lower'); ax[row,col].set(title=f'R{s}: full-state {kind}',xlabel='Current location',ylabel='Current location'); fig.colorbar(im,ax=ax[row,col],shrink=.65)
        response=p.get('response_rdm',p['rdm']['euclidean'])
        if isinstance(response,dict): response=response['euclidean']
        im=ax[2,col].imshow(response,vmin=0,vmax=vmax,origin='lower'); ax[2,col].set(title=f'R{s}: current-Response Euclidean',xlabel='Current location',ylabel='Current location'); fig.colorbar(im,ax=ax[2,col],shrink=.65)
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 6 supplement: distance definitions and current-stage control'); return fig


def noisy_trajectories(d,r,noise):
    fit=r['subspaces']['global']; comp=fit['components'][:2]; origin=fit['mean']; scores=(noise-origin)@comp.T; mean=scores.mean(0)
    fig,ax=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for trial,task in enumerate(d['tasks']):
        color=plt.cm.hsv(task['L']/6)
        for repeat in range(len(scores)): ax[0].plot(*scores[repeat,trial].T,color=color,alpha=.25,lw=.55)
        ax[1].plot(*mean[trial].T,color=color,lw=.8,ls='-' if task['S']==1 else '--')
    for a in ax: a.set(xlabel='Baseline-fit PC1',ylabel='Baseline-fit PC2')
    ax[0].set_title('Three independent encoded-input noise realizations'); ax[1].set_title('Event-aligned mean: sigma .03, seeds 7 / 11 / 19')
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 4 supplement: individual trials and means in the same PCA'); return fig


def input_geometry(d,r):
    from ..model.location_encoding import LocationEncoding
    geometry=LocationEncoding(d['encoding_type']).geometry(); coords=np.array(geometry['coordinates'])
    fig,ax=plt.subplots(2,2,figsize=(10,8),layout='constrained')
    im=ax[0,0].imshow(coords.T,aspect='auto',origin='lower',cmap='coolwarm'); fig.colorbar(im,ax=ax[0,0]); ax[0,0].set(title='Designed raw input coordinates',xlabel='Input position',ylabel=f'External coordinate (dim={coords.shape[1]})')
    distances=geometry['circular_distances'] if d['encoding_type']=='ring' else geometry['coordinate_euclidean_distances']
    im=ax[0,1].imshow(distances,origin='lower'); fig.colorbar(im,ax=ax[0,1]); ax[0,1].set(title='Periodic phase distance (rad)' if d['encoding_type']=='ring' else 'Raw coordinate Euclidean distance',xlabel='Input position',ylabel='Input position')
    im=ax[1,0].imshow(geometry['current_distances'],origin='lower'); fig.colorbar(im,ax=ax[1,0]); ax[1,0].set(title='Designed six-channel current distance',xlabel='Input position',ylabel='Input position')
    im=ax[1,1].imshow(r['rsa']['panels'][(3,0)]['response_rdm']['euclidean'],origin='lower'); fig.colorbar(im,ax=ax[1,1]); ax[1,1].set(title='Measured R3 current-Response distance',xlabel='Current output position',ylabel='Current output position')
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 6 input supplement: priors vs neural state'); return fig


def memory_controls(d,r):
    controls=r['memory']['controls']; names=list(controls); fig,ax=plt.subplots(2,2,figsize=(12,7),layout='constrained'); t=d['times_ms']
    for name,c in controls.items():
        for j,pop in enumerate(('M_D','M_S')): ax[0,j].plot(t,c[pop],label=name)
    for j,pop in enumerate(('M_D','M_S')): ax[0,j].set(title=pop+' survival',xlabel='Time (ms)',ylabel='Peak memory rate'); ax[0,j].legend(fontsize=6)
    for s,offset in ((2,-.15),(3,.15)):
        k=np.argmin(abs(t-d['events'][0][f'readout{s}'])); ax[1,0].bar(np.arange(len(names))+offset,[controls[n][f'R{s}'][k] for n in names],width=.3,label=f'R{s} at its own readout')
    ax[1,0].set(title='Response stability at matched stage',ylabel='Peak Response rate'); ax[1,0].set_xticks(range(len(names)),names,rotation=20,ha='right',fontsize=6); ax[1,0].legend()
    ax[1,1].bar(range(len(names)),[controls[n]['accuracy'] for n in names],color='#777777'); ax[1,1].set(title='Complete-sequence behavioral accuracy',ylabel='Fraction correct',ylim=(0,1.05)); ax[1,1].set_xticks(range(len(names)),names,rotation=20,ha='right',fontsize=6)
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 3 supplement: mechanism metrics and behavioral controls'); return fig


def noise_decoding(d,r):
    a=r['noise_decoding']; t=a['times_ms']; fig,ax=plt.subplots(1,3,figsize=(13,4.5),layout='constrained')
    for col,var in enumerate(('L','D','S')):
        for name in ('whole','response','memory','M_D','M_S','R2','R3'):
            ax[col].plot(t,a['curves'][(name,var)],label=name,lw=.9)
        ax[col].axhline(1/6 if var=='L' else .5,ls=':',color='black',lw=.7); ax[col].set(title=var+' independent input-noise seed test',xlabel='Time (ms)',ylabel='Accuracy',ylim=(-.02,1.03)); ax[col].legend(ncol=2); from .style import timeline; timeline(ax[col],d['events'][0])
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 7 noise supplement: held-out seed; all task conditions seen in training\nRate decay does not guarantee loss of numerically decodable residual rule information'); return fig
