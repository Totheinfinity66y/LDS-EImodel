"""Three-column stream portraits with actual full-state trajectories in red."""
from pathlib import Path
import json
from hashlib import sha256
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from .style import save_figure,NAMES


def arrows_on_path(ax,xy):
    distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    if distance[-1]<1e-7:return
    for fraction in (.25,.65):
        k=min(len(xy)-2,max(0,int(np.searchsorted(distance,fraction*distance[-1]))))
        j=min(len(xy)-1,k+3)
        ax.annotate('',xy=xy[j],xytext=xy[k],arrowprops=dict(arrowstyle='-|>',color='#c71922',lw=1.3,mutation_scale=12),zorder=6)


def portrait(z,mode):
    fig,axes=plt.subplots(1,3,figsize=(11.5,5.2),sharex=True,sharey=True)
    fig.subplots_adjust(left=.075,right=.985,bottom=.29,top=.82,wspace=.12)
    size=int(z['grid_size']);x=np.linspace(0,1,size);y=x.copy()
    for ax,key,title in zip(axes,z['condition_keys'],z['condition_titles']):
        valid=z[f'{key}_valid'].reshape(size,size);v=z[f'{key}_coordinate_velocity'].reshape(size,size,2)
        mask=(~valid)|(~np.isfinite(v).all(2))
        ax.streamplot(x,y,np.ma.array(v[:,:,0],mask=mask),np.ma.array(v[:,:,1],mask=mask),
                      density=1.2,color='#267aa5',linewidth=.8,arrowsize=1.05,minlength=.08,broken_streamlines=True)
        if mask.any():
            ax.contourf(x,y,mask.astype(float),levels=[.5,1.5],colors=['#eeeeee'],zorder=0)
        for i in z['red_path_indices']:
            xy=z[f'{key}_coordinates'][i]
            ax.plot(xy[:,0],xy[:,1],color='#c71922',lw=1.8,zorder=4)
            ax.scatter(*xy[0],s=12,facecolors='white',edgecolors='#c71922',zorder=5)
            ax.scatter(*xy[-1],s=12,color='#c71922',zorder=5)
            arrows_on_path(ax,xy)
        residual=z[f'{key}_anchor_residual_max_per_ms']
        for j,(a,b,label) in enumerate(((0,0,'0'),(1,0,'1'),(0,1,'2'),(1,1,'1+2'))):
            stationary=np.isfinite(residual[j]) and residual[j]<1e-8
            color='#c71922' if j in (1,2) and stationary else '#333333' if stationary else '#999999'
            ax.scatter(a,b,s=18,facecolors=color if stationary else 'white',edgecolors=color,zorder=7,clip_on=False)
            ax.annotate(label,(a,b),xytext=(5 if a==0 else -6,5 if b==0 else -15),textcoords='offset points',
                        ha='left' if a==0 else 'right',color=color,fontsize=10,zorder=8)
        ax.set(title=title,xlim=(-.035,1.035),ylim=(-.035,1.035),xticks=[0,.5,1],yticks=[0,.5,1])
        ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False)
        ax.tick_params(direction='out',length=3)
        fraction=z[f'{key}_offplane_fraction'];finite=fraction[np.isfinite(fraction)]
        departure=z[f'{key}_path_offplane_distance'].max()
        ax.text(.5,-.18,f'Field outside plane: {np.median(finite):.1%} median\nMax path departure: {departure:.3f} state L2',transform=ax.transAxes,ha='center',fontsize=8)
    fig.supxlabel(r'$\lambda_1$ (LDS rate-state coefficient)',y=.135,fontsize=11)
    fig.supylabel(r'$\lambda_2$ (LDS rate-state coefficient)',x=.015,fontsize=11)
    fig.suptitle(NAMES[mode]+' | Response-state flow',y=.97,fontsize=14)
    fig.legend(handles=[Line2D([0],[0],color='#267aa5',lw=1,label='Projected slice streamlines'),
                        Line2D([0],[0],color='#c71922',lw=1.8,label='Full132 trajectories, projected')],
               loc='lower center',bbox_to_anchor=(.5,.005),ncol=2,frameon=False,fontsize=8)
    fig.text(.5,.89,'Shared state directions; condition-equilibrated backgrounds; no training or weight changes',ha='center',fontsize=8)
    fig.text(.5,.08,'Non-invariant slice. Filled numbered anchors: full-field stationary; hollow numbered anchors: reference only.',ha='center',fontsize=7.5)
    return fig


def diagnostic(z,mode):
    fig,axes=plt.subplots(2,3,figsize=(12,6),layout='constrained');size=int(z['grid_size'])
    for column,(key,title) in enumerate(zip(z['condition_keys'],z['condition_titles'])):
        ratio=z[f'{key}_offplane_fraction'].reshape(size,size)
        im=axes[0,column].imshow(ratio,origin='lower',extent=[0,1,0,1],vmin=0,vmax=1,cmap='magma',aspect='equal')
        axes[0,column].set(title=title,xlabel=r'$\lambda_1$',ylabel=r'$\lambda_2$')
        for i,path in enumerate(z[f'{key}_path_offplane_distance']):
            axes[1,column].plot(z['times_ms'],path,color='#c71922' if i in z['red_path_indices'] else '#999999',lw=.9,alpha=.8)
        axes[1,column].set(xlabel='Full-state integration time (ms)',ylabel='Distance from affine plane')
    fig.colorbar(im,ax=axes[0,:],label='Off-plane field fraction',shrink=.7)
    fig.suptitle(NAMES[mode]+' | Non-invariant plane diagnostics (zero-field fraction is undefined)')
    return fig


def render(root,modes):
    root=Path(root);records=[]
    with plt.rc_context({'font.family':'DejaVu Serif','font.size':10,'axes.titlesize':12,'svg.fonttype':'none','pdf.fonttype':42}):
        for mode in modes:
            with np.load(root/mode/'phase_portrait.npz') as z:
                for name,maker in [('phase_portrait',portrait),('projection_diagnostics',diagnostic)]:
                    paths=save_figure(maker(z,mode),root/mode,name)
                    records.append(dict(encoding=mode,id=mode+'_'+name,paths=paths,dpi=300,
                        output_sha256={p:sha256(Path(p).read_bytes()).hexdigest() for p in paths}))
    (root/'figure_index.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    (root/'figure_manifest.json').write_text(json.dumps({'figures':records},indent=2)+'\n',encoding='utf-8')
