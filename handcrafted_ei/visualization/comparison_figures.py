"""Three-encoding comparison with shared scales and no composite score."""
import numpy as np
import matplotlib.pyplot as plt
from .style import panels,NAMES,ENCODING_COLORS
from .dynamics_figures import read_rows
from pathlib import Path


def comparison(data,results,out,kind):
    fig,ax=plt.subplots(3,3,figsize=(13,10),layout='constrained')
    vmax=max(float(results[m]['rsa']['panels'][(3,0)]['rdm']['euclidean'].max()) for m in data)
    for col,(mode,d) in enumerate(data.items()):
        r=results[mode]; color=ENCODING_COLORS[mode]
        if kind=='localization':
            im=ax[0,col].imshow(d['rates'][0].T,origin='lower',aspect='auto',extent=[0,d['times_ms'][-1],-.5,131.5],vmin=0,vmax=1,cmap='viridis'); fig.colorbar(im,ax=ax[0,col],shrink=.65,label='Normalized rate'); ax[0,col].set(xlabel='Time (ms)',ylabel='All units')
            ax[1,col].imshow(r['recruitment']['stages'][3]['functional'].T,origin='lower',aspect='auto',vmin=0,vmax=1,cmap='Greys'); ax[1,col].set(xlabel='All units',ylabel='R3 recruited branch')
            for name in ('R1','R2','R3','R4'): ax[2,col].plot(d['times_ms'],r['activity']['population'][name]['active_fraction'],label=name)
            ax[2,col].set(xlabel='Time (ms)',ylabel='Within-population active fraction',ylim=(0,.19)); ax[2,col].legend(ncol=2)
        elif kind=='geometry':
            scores=r['subspaces']['scores']
            for i,task in enumerate(d['tasks']): ax[0,col].plot(*scores[i,:,:2].T,color=plt.cm.hsv(task['L']/6),ls='-' if task['S']==1 else '--',lw=.6)
            ax[0,col].set(xlabel='PC1 (separate model fit)',ylabel='PC2')
            im=ax[1,col].imshow(r['rsa']['panels'][(3,0)]['rdm']['euclidean'],origin='lower',vmin=0,vmax=vmax,cmap='viridis'); fig.colorbar(im,ax=ax[1,col],shrink=.65,label='Full-state distance'); ax[1,col].set(xlabel='Current location',ylabel='Current location')
            xy=r['rsa']['panels'][(3,0)]['mds']; loop=np.r_[np.arange(6),0]; ax[2,col].plot(*xy[loop].T,'o-',color=color)
            for p in range(6): ax[2,col].annotate(str(p),xy[p])
            ax[2,col].set(xlabel='MDS1',ylabel='MDS2',aspect='equal')
        else:
            with np.load(Path(out)/f'data/dynamics/{mode}_L0_R3.npz') as z:
                t=z['times_ms']; distances=z['distances_l2'][0]
                for i,amp in enumerate(z['amplitudes']): ax[0,col].plot(t,distances[i].mean(0),label=f'RMS {amp}')
            ax[0,col].legend(); ax[0,col].set(xlabel='Time (ms)',ylabel='Full-state perturbation L2 distance')
            rows=[row for row in read_rows(Path(out)/'metrics/dynamics_perturbation.csv') if row['encoding']==mode and row['target']=='full']
            amps=sorted({float(x['amplitude_target_rms_before_clipping']) for x in rows}); ax[1,col].plot(amps,[np.mean([x['recovered']=='True' for x in rows if float(x['amplitude_target_rms_before_clipping'])==amp]) for amp in amps],'o-',color=color)
            ax[1,col].set(xlabel='Pre-clipping full-state RMS',ylabel='Identity-preserving recovery fraction',ylim=(-.02,1.02))
            ax[2,col].axis('off'); ax[2,col].text(0,1,'Evidence classification\n\nLocally stable fixed points under\nconstant tonic background\n\nFinite, narrow tested recovery basin\n\n6 discrete positions, fixed D/S sample\nNo continuous ring attractor evidence\nNo global basin proof',va='top',linespacing=1.4)
        ax[0,col].set_title(NAMES[mode])
    panels(ax); fig.suptitle('Figure 10 | '+kind+' comparison: same definitions; no best-model score'); return fig
