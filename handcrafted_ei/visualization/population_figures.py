"""Figure 1--7 from the complete recorded network, plus explicit controls."""
import numpy as np
import matplotlib.pyplot as plt
from .style import panels,timeline,image,D_COLORS,NAMES
from ..evaluation.population_activity import stage_samples,population_sets
from ..model.location_encoding import LocationEncoding


def activity(d,a):
    fig,ax=plt.subplots(2,2,figsize=(13,9),layout='constrained'); t=d['times_ms']; x=d['rates'][0]
    g=d['groups']; order_names=['R1','R2','R3','R4','M_D','M_S','E_gate_D','E_gate_S','E_gate_34','I_tonic_R','I_tonic_M','I_decay_D','I_decay_S','Y','comp_R1','comp_D','comp_S','retire']
    order=np.concatenate([g[k] for k in order_names]); boundaries=np.cumsum([len(g[k]) for k in order_names])
    for axis,values,title in ((ax[0,0],x,'Absolute normalized rate'),(ax[0,1],x-x[0],'Baseline-subtracted normalized rate')):
        im=axis.imshow(values[:,order].T,origin='lower',aspect='auto',extent=[t[0],t[-1],-.5,len(order)-.5],vmin=0,vmax=1,cmap='viridis',interpolation='nearest')
        centers=np.r_[0,boundaries[:-1]]+(np.diff(np.r_[0,boundaries])-1)/2
        if axis is ax[0,0]:
            axis.set_yticks([])
            for center,text_y,k in zip(centers,np.linspace(1,len(order)-2,len(order_names)),order_names):
                axis.annotate(k+(' [I]' if d['neuron_types'][g[k][0]]=='I' else ' [E]'),xy=(0,center),xytext=(-.04,text_y),
                    xycoords=('axes fraction','data'),textcoords=('axes fraction','data'),ha='right',va='center',fontsize=6,
                    arrowprops={'arrowstyle':'-','lw':.4,'color':'#555555'},annotation_clip=False)
        else: axis.set_yticks([0,33,66,99,131])
        for b in boundaries[:-1]: axis.axhline(b-.5,color='white',lw=.4)
        axis.set(title=title,xlabel='Time (ms)',ylabel='All 132 neural units'); timeline(axis,d['events'][0]); fig.colorbar(im,ax=axis,label='Dimensionless rate',shrink=.75)
        if axis is ax[0,0]: axis.set_ylabel('')
        for stage in (2,3,4):
            first=int(np.where(order==g[f'R{stage}'][0])[0][0])
            for b in range(1,len(g[f'R{stage}'])//6): axis.axhline(first+6*b-.5,color='white',lw=.3,ls=':',alpha=.7)
    names=['R1','R2','R3','M_D','M_S','E_gate_D','I_decay_D','I_decay_S','I_tonic_R']
    for name in names:
        idx=g[name][x[:,g[name]].max(0).argmax()]; ax[1,0].plot(t,x[:,idx],label=d['labels'][idx],lw=.9)
    inactive=g['R2'][x[:,g['R2']].max(0).argmin()]; ax[1,0].plot(t,x[:,inactive],ls='--',color='black',label=f'{d["labels"][inactive]} unselected')
    ax[1,0].set(title='Real representative units: trial 0',xlabel='Time (ms)',ylabel='Dimensionless rate'); ax[1,0].legend(ncol=2); timeline(ax[1,0],d['events'][0],True)
    for name in ('R1','R2','R3','R4','M_D','M_S','I_decay_D','I_decay_S'):
        ax[1,1].plot(t,a['population'][name]['mean'],label=name)
    ax[1,1].set(title='Population mean, all 24 conditions',xlabel='Time (ms)',ylabel='Mean dimensionless rate'); ax[1,1].legend(ncol=2); timeline(ax[1,1],d['events'][0],True)
    fig.suptitle(NAMES[d['encoding_type']]+' | Figure 1: complete network activity (trial 0: L=0, D=+1, S=1)'); panels(ax); return fig


def recruitment(d,a):
    fig,ax=plt.subplots(4,4,figsize=(15,12),layout='constrained'); response=population_sets(d)['response']
    for row,s in enumerate(range(1,5)):
        item=a['stages'][s]; x=item['condition_samples']; sorting=np.lexsort(([v['S'] for v in d['tasks']],[v['D'] for v in d['tasks']],[v['L'] for v in d['tasks']]));
        for col,values,title in ((0,x[sorting],f'R{s} whole network'),(1,x[sorting][:,response],f'R{s} Response only')):
            im=image(ax[row,col],values,title,'Neural unit','Condition (L/D/S sorted)',vmin=0,vmax=1); fig.colorbar(im,ax=ax[row,col],shrink=.65)
        # Structural support and functional support are shown in identical full-network coordinates.
        support=np.c_[item['structural'],np.zeros((len(d['labels']),1)),item['functional']]
        image(ax[row,2],support.T,f'R{s} structural | functional','All neural units','Branch support',vmin=0,vmax=1,cmap='Greys')
        im=image(ax[row,3],item['jaccard'],f'R{s} functional Jaccard','Branch','Branch',vmin=0,vmax=1); fig.colorbar(im,ax=ax[row,3],shrink=.65)
    fig.suptitle(NAMES[d['encoding_type']]+' | Figure 2: predefined branch support and measured recruitment'); panels(ax); return fig


def selectivity(d,a):
    fig,ax=plt.subplots(2,4,figsize=(14,6),layout='constrained')
    for col,s in enumerate(range(1,5)):
        item=a['stages'][s]; names=list(item['anova']['fraction']); arr=np.stack([item['anova']['fraction'][k] for k in names])
        im=image(ax[0,col],arr,f'R{s}: factorial effect fractions','All neural units','L / D / S / interactions',vmin=0,vmax=1)
        ax[0,col].set_yticks(range(len(names)),names); fig.colorbar(im,ax=ax[0,col],shrink=.7)
        for name in ('L','D','S','D:S','L:D','L:S'):
            ax[1,col].hist(item['anova']['fraction'][name],bins=np.linspace(0,1,16),histtype='step',label=name)
        ax[1,col].set(title=f'R{s}: descriptive selectivity',xlabel='Fraction of condition variance',ylabel='Neurons'); ax[1,col].legend(ncol=2)
    panels(ax); fig.suptitle('Figure 2 supplement: balanced factorial decomposition; no significance tests'); return fig


def memory(d,a,decode=None):
    t=d['times_ms']; fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for name,tr in a['traces'].items(): ax[0,0].plot(t,tr.mean(0),label=name)
    ax[0,0].legend(ncol=2); ax[0,0].set(title='Memory / Response / gate / feedback',xlabel='Time (ms)',ylabel='Trial-mean peak rate'); timeline(ax[0,0],d['events'][0],True)
    metric_names=['response_onset_ms','response_90pct_ms','decay_onset_95pct_ms','half_crossing_ms','time_to_baseline_ms']
    for m,color in [('M_D','#0072B2'),('M_S','#D55E00')]:
        vals=np.array([[r[k] for k in metric_names] for r in a['rows'] if r['memory']==m]); ax[0,1].plot(range(len(metric_names)),np.nanmean(vals,0),'o-',label=m,color=color)
    ax[0,1].set_xticks(range(len(metric_names)),['Response .1','Response .9','Memory .95','Memory .5','Memory .05'],rotation=20); ax[0,1].set(title='Threshold crossings (all conditions)',ylabel='Time (ms)'); ax[0,1].legend()
    # Full population condition contrast, not a claim of classifier generalization.
    for population,var in [('M_D','D'),('R2','D'),('M_S','S'),('R3','S')]:
        values=np.array([v[var] for v in d['tasks']]); levels=np.unique(values); x=d['rates'][:,:,d['groups'][population]]
        contrast=np.linalg.norm(x[values==levels[1]].mean(0)-x[values==levels[0]].mean(0),axis=1)
        ax[1,0].plot(t,contrast,label=population+': '+var)
    ax[1,0].set(title='Rule-conditioned centroid separation (descriptive)',xlabel='Time (ms)',ylabel='Euclidean neural distance'); ax[1,0].legend(ncol=2); timeline(ax[1,0],d['events'][0])
    for exp,c in a['controls'].items():
        ax[1,1].plot(t,c['M_D'],label=exp+' D',lw=.9); ax[1,1].plot(t,c['M_S'],ls='--',lw=.9,label=exp+' S')
    ax[1,1].set(title='Feedback / tonic / matched random edge controls',xlabel='Time (ms)',ylabel='Mean peak memory rate'); ax[1,1].legend(ncol=2,fontsize=5)
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 3: activity-dependent memory handoff'); return fig


def trajectories(d,a):
    fig=plt.figure(figsize=(12,9),layout='constrained'); axes=[fig.add_subplot(221),fig.add_subplot(222,projection='3d'),fig.add_subplot(223),fig.add_subplot(224)]
    scores=a['scores']; evr=a['global']['evr']; t=d['times_ms']
    for i,task in enumerate(d['tasks']):
        line='-' if task['S']==1 else '--'; color=D_COLORS[task['D']]
        axes[0].plot(*scores[i,:,:2].T,color=color,ls=line,lw=.65,alpha=.6)
        axes[1].plot(*scores[i,:,:3].T,color=plt.cm.hsv(task['L']/6),ls=line,lw=.6,alpha=.6)
        for s in range(1,5):
            j=np.argmin(abs(t-d['events'][i][f'readout{s}'])); axes[0].scatter(*scores[i,j,:2],s=8*s,color=color)
        if task['L']==0: axes[2].plot(*scores[i,:,:2].T,color=color,ls=line,label=f'D={task["D"]}, S={task["S"]}')
    for axis in axes[:3]:
        axis.set_xlabel(f'PC1 ({100*evr[0]:.1f}%)'); axis.set_ylabel(f'PC2 ({100*evr[1]:.1f}%)')
    axes[1].set_zlabel(f'PC3 ({100*evr[2]:.1f}%)'); axes[0].set_title('All 24 conditions: D color, S linestyle; readout markers grow'); axes[1].set_title('All 24 conditions: initial L color'); axes[2].set_title('Fixed L=0, variable D/S (same PCA)'); axes[2].legend()
    variables=np.array([[np.cos(2*np.pi*x['L']/6),np.sin(2*np.pi*x['L']/6),x['D'],2*x['S']-3] for x in d['tasks']])
    for k,var in enumerate(a['variable_names']):
        weight=variables[:,k]; projection=(weight[:,None]*a['variable_scores'][:,:,k]).mean(0)/np.mean(weight**2)
        axes[3].plot(t,projection,label=var+' regression axis')
    axes[3].set(title='Task-variable projections (descriptive, no dPCA fit)',xlabel='Time (ms)',ylabel='Condition projection coefficient'); axes[3].legend(ncol=2); timeline(axes[3],d['events'][0])
    panels(axes); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 4: unified whole-network PCA, no per-trial fits'); return fig


def subspaces(d,a):
    fig,ax=plt.subplots(3,4,figsize=(14,10),layout='constrained')
    for col,s in enumerate(range(1,5)):
        for b,branch in enumerate(a['stages'][s]['branches']):
            spec=branch['whole']; ax[0,col].plot(np.arange(1,len(spec['evr'])+1),np.cumsum(spec['evr']),'o-',ms=2,label=f'b{b}: PR={spec["effective_dimension"]:.2f}')
        ax[0,col].set(title=f'R{s} within-branch full-state spectrum',xlabel='PC',ylabel='Cumulative VAF',ylim=(0,1.03)); ax[0,col].legend()
        im=image(ax[1,col],a['stages'][s]['angles'],f'R{s} mean principal angles','Branch','Branch',vmin=0,vmax=90); fig.colorbar(im,ax=ax[1,col],shrink=.65,label='degrees')
        im=image(ax[2,col],a['stages'][s]['folded_overlap'],f'R{s} support-folded overlap','Branch','Branch',vmin=0,vmax=1); fig.colorbar(im,ax=ax[2,col],shrink=.65)
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 5: full-state geometry / six-coordinate support control'); return fig


def ring_geometry(d,a):
    fig,ax=plt.subplots(3,4,figsize=(13,10),layout='constrained')
    enc=LocationEncoding(d['encoding_type']); geometry=enc.geometry(); currents=np.array(geometry['currents'])
    im=image(ax[0,0],currents,'Designed input currents (prior)','Six current units','Input position',vmin=0,vmax=1); fig.colorbar(im,ax=ax[0,0],shrink=.65)
    im=image(ax[0,1],a['ideal_ring'],'Ideal ring geodesic distance','Position','Position',vmin=0,vmax=3); fig.colorbar(im,ax=ax[0,1],shrink=.65)
    theta=np.arange(6)*np.pi/3; ax[0,2].plot(np.cos(np.r_[theta,theta[0]]),np.sin(np.r_[theta,theta[0]]),'o-'); ax[0,2].set(title='Six input positions; ring adjacency prior',aspect='equal');
    for p in range(6): ax[0,2].text(np.cos(theta[p]),np.sin(theta[p]),str(p))
    ax[0,3].axis('off'); ax[0,3].text(0,1,'132 neural units in every encoding\nExternal dimensions: 6 / 1 / 2\nNo neural normalization\nFixed branch b0; all six positions\nNA = constant off-diagonal distances\nMDS stress measures distance distortion\nSix discrete points do not prove a manifold',va='top',linespacing=1.6)
    vmax=max(float(p['rdm']['euclidean'].max()) for p in a['panels'].values())
    for col,s in enumerate(range(1,5)):
        p=a['panels'][(s,0)]; rho=p['metrics']['ring_spearman']; contrast=p['metrics']['relative_opposite_minus_adjacent']; title=f'R{s} whole-network RDM\nrho='+('NA' if not np.isfinite(rho) else f'{rho:.2f}')+f'; relative delta={contrast:.2g}'
        im=image(ax[1,col],p['rdm']['euclidean'],title,'Position','Position',vmin=0,vmax=vmax); fig.colorbar(im,ax=ax[1,col],shrink=.65)
        xy=p['mds']; loop=np.r_[np.arange(6),0]; ax[2,col].plot(*xy[loop].T,color='#777777',lw=.7); ax[2,col].scatter(*xy.T,c=np.arange(6),cmap='hsv',vmin=0,vmax=6)
        for j in range(6): ax[2,col].annotate(str(j),xy[j],xytext=(3,3),textcoords='offset points')
        ax[2,col].set(title=f'R{s} classical MDS; stress={p["stress"]:.3f}',xlabel='MDS 1',ylabel='MDS 2',aspect='equal')
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 6: designed input vs measured neural geometry'); return fig


def decoding(d,a):
    fig,ax=plt.subplots(3,3,figsize=(13,10),layout='constrained'); t=a['times_ms']
    populations=['whole','response','memory','M_D','M_S','R2','R3']
    for col,var in enumerate(('L','D','S')):
        for name in populations: ax[0,col].plot(t,a['curves'][(name,var)],label=name,lw=.9)
        chance=1/6 if var=='L' else .5; ax[0,col].axhline(chance,color='black',ls=':',lw=.7)
        ax[0,col].set(title=var+' condition-held-out probe',xlabel='Time (ms)',ylabel='Accuracy',ylim=(0,1.04)); ax[0,col].legend(ncol=2); timeline(ax[0,col],d['events'][0])
        im=ax[1,col].imshow(a['cross_temporal'][var],origin='lower',aspect='auto',extent=[t[0],t[-1],t[0],t[-1]],vmin=chance,vmax=1,cmap='viridis'); ax[1,col].set(title=var+' whole-network cross-temporal',xlabel='Test time (ms)',ylabel='Train time (ms)'); fig.colorbar(im,ax=ax[1,col],shrink=.65)
        availability=np.stack([a['curves'][(p,var)] for p in populations]); im=ax[2,col].imshow(availability,origin='lower',aspect='auto',extent=[t[0],t[-1],-.5,len(populations)-.5],vmin=chance,vmax=1,cmap='viridis'); ax[2,col].set_yticks(range(len(populations)),populations); ax[2,col].set(title=var+' availability',xlabel='Time (ms)'); fig.colorbar(im,ax=ax[2,col],shrink=.65)
    panels(ax); fig.suptitle(NAMES[d['encoding_type']]+' | Figure 7: disjoint task-condition probes; fixed network, no animal/generalization claim'); return fig
