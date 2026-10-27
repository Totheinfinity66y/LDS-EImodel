"""Source-informed organization with explicit LDS adaptation labels."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from .style import configure,panels,save_figure,NAMES
from ..evaluation.reference_reproduction import csvwrite,dump


def fixed_points(root,mode):
    folder=root/'lds_results'/mode
    with np.load(folder/'fixed_points.npz') as z:
        t=z['times_ms'];rates=z['rates'];coords=z['coding_coordinate'];dist=z['endpoint_distance'];eig=z['eigenvalues']
        conditions=z['conditions'];groups=[np.flatnonzero(conditions[:,1]==d) for d in (-1,1)]
        fig,ax=plt.subplots(2,3,figsize=(14,8),layout='constrained')
        for i in range(24):
            ax[0,0].plot(t,rates[i,:,18:42].max(1),lw=.6,alpha=.5)
        ax[0,0].set(title='24 R3 snapshots; identical fixed field',xlabel='Extension time (ms)',ylabel='R3 peak rate (dimensionless)',ylim=(0,1.05))
        ax[0,0].text(.03,.12,f'Largest peak excursion: {np.ptp(rates[:,:,18:42].max(2),axis=1).max():.3g}',transform=ax[0,0].transAxes,fontsize=8)
        im=ax[0,1].imshow(dist,origin='lower',cmap='viridis');fig.colorbar(im,ax=ax[0,1],label='Full-state Euclidean distance')
        ax[0,1].set(title='24 × 24 endpoint distances',xlabel='Recorded condition index',ylabel='Recorded condition index')
        # A transparent two-condition descriptive CD, not the experimental CD estimator.
        pair=z['coding_pair_trial_indices']
        for i,color in zip(pair,('#0072B2','#D55E00')):
            ax[0,2].plot(t,coords[i],color=color,label=f'trial {i}: L={conditions[i,0]}')
        ax[0,2].legend();ax[0,2].set(title='Pairwise CD: fixed D=+1, S=1',xlabel='Extension time (ms)',ylabel='Unnormalized CD coordinate')
        for i,color in zip(pair,('#0072B2','#D55E00')):
            coord=coords[i,::2];tt=t[::2]
            ax[1,0].plot(coord[1:-1],(coord[2:]-coord[:-2])/2,color=color,lw=1)
        ax[1,0].axhline(0,color='gray',lw=.6);ax[1,0].set(title='Descriptive deterministic phase trace',xlabel='Pairwise CD coordinate',ylabel='CD change / 10 ms')
        from ..evaluation.reference_reproduction import ROOT
        import csv
        with (folder/'fixed_points.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
        residual=np.array([float(r['residual_l2_per_ms']) for r in rows])
        ax[1,1].semilogy(np.arange(24),np.maximum(residual,1e-18),'o',ms=3)
        ax[1,1].set(title='Full-state field residual at endpoints',xlabel='Recorded condition index',ylabel='||f(r)||₂ (rate / ms)')
        ax[1,2].scatter(eig.real.ravel(),eig.imag.ravel(),s=15,alpha=.3)
        ax[1,2].axvline(0,color='gray',ls=':');ax[1,2].set(title='Representative spectrum (kink slope = 0.5)',xlabel='Re λ (1/ms)',ylabel='Im λ (1/ms)')
        summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
        ax[1,2].text(.03,.92,f"{summary['stable_endpoint_clusters']} stable endpoint clusters\n{summary['identity_retained']}/24 identities retained\nEuler ρ = {summary['spectral_radius_range'][1]:.6f}",transform=ax[1,2].transAxes,va='top',fontsize=8)
    panels(ax);fig.suptitle(NAMES[mode]+' | Figure 8 — METHOD ADAPTED: fixed-input LDS diagnosis; no session statistics')
    return fig


def input_perturbation(root,mode,assay):
    folder=root/'lds_results'/mode
    with np.load(folder/f'input_{assay}_7.npz') as z:
        t=z['times_ms'];control=z['control'];pert=z['perturbed'];b=z['basis'];mu=z['pca_center'];mask=z['pulse_mask']
        fig,ax=plt.subplots(2,3,figsize=(14,8),layout='constrained')
        # Activity-based unit selection is display only; all132 units enter distances.
        ids=np.argsort(np.ptp(control,axis=0))[-5:]
        for k,q in enumerate(ids):
            ax[0,0].plot(t,control[:,q]+1.2*k,color='black',lw=.8)
            ax[0,0].plot(t,pert[:,q]+1.2*k,color='#D55E00',lw=.7,ls='--')
        ax[0,0].set(title='Five control-modulated units; offsets 1.2',xlabel='Assay time (ms)',ylabel='Dimensionless rate + offset')
        cp=(control-mu)@b;pp=(pert-mu)@b
        ax[0,1].plot(cp[:,0],cp[:,1],color='black',label='Control');ax[0,1].plot(pp[:,0],pp[:,1],color='#D55E00',label='50 ms input')
        ax[0,1].scatter(pp[::40,0],pp[::40,1],c=t[::40],s=8,cmap='viridis');ax[0,1].legend()
        ax[0,1].set(title='Control-only PCA (display; no recovery claim)',xlabel='PC1',ylabel='PC2')
        ct=z['cross_temporal_times_ms'];D=z['cross_temporal_distance']
        im=ax[0,2].imshow(D,origin='lower',extent=[ct[0],ct[-1],ct[0],ct[-1]],aspect='auto',cmap='viridis')
        fig.colorbar(im,ax=ax[0,2],label='Full132 Euclidean distance');ax[0,2].set(title='D(control t, perturbed s)',xlabel='Perturbed s (ms)',ylabel='Control t (ms)')
        for key,label,style in [('full_squared','Full132','-'),('projected_squared','PC1/2','--'),('orthogonal_squared','Outside PC1/2',':')]:
            ax[1,0].plot(t,np.sqrt(z[key]),style,label=label)
        ax[1,0].legend();ax[1,0].set(title='Matched-time distance decomposition',xlabel='Assay time (ms)',ylabel='Euclidean distance')
        current=z['actual_perturbation_current'];ax[1,1].step(t,np.sqrt(np.mean(current**2,axis=1)),where='pre',color='#D55E00')
        ax[1,1].set(title='Recorded added external current',xlabel='Assay time (ms)',ylabel='Whole-network current RMS',ylim=(-.01,.28))
        for seed in (7,11,19):
            with np.load(folder/f'input_{assay}_{seed}.npz') as a:
                ax[1,2].plot(t,np.linalg.norm(a['perturbed']-a['control'],axis=1),label=f'projection seed {seed}')
        ax[1,2].legend();ax[1,2].set(title='Three fixed input directions; no SEM',xlabel='Assay time (ms)',ylabel='Full132 distance')
        onset=t[np.flatnonzero(mask)[0]]-5;offset=t[np.flatnonzero(mask)[-1]]
        for axis in (ax[0,0],ax[1,0],ax[1,1],ax[1,2]): axis.axvspan(onset,offset,color='#D55E00',alpha=.12)
    panels(ax);fig.suptitle(NAMES[mode]+f' | Figure 9 input — {assay}; METHOD ADAPTED; noise-free pair; no original π channel')
    return fig


def state_perturbation(root,mode):
    folder=root/'lds_results'/mode
    with np.load(folder/'state_perturbation.npz') as z:
        t=z['times_ms'];delta=z['perturbed']-z['control'];basis=z['basis'];mu=z['pca_center']
        fig,ax=plt.subplots(1,3,figsize=(14,4),layout='constrained')
        for key,label in [('full_squared','Full132'),('projected_squared','PC1/2'),('orthogonal_squared','Outside PC1/2')]: ax[0].plot(t,np.sqrt(z[key]),label=label)
        ax[0].legend();ax[0].set(title='State kick ≠ finite input perturbation',xlabel='Extension time (ms)',ylabel='Euclidean distance')
        cp=(z['control']-mu)@basis;pp=(z['perturbed']-mu)@basis
        ax[1].plot(*cp.T,color='black',label='Control');ax[1].plot(*pp.T,color='#D55E00',label='State kick');ax[1].legend()
        ax[1].set(title='Control-only basis; projection can conceal error',xlabel='PC1',ylabel='PC2')
        import csv
        with (folder/'basin.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
        for name in ('full','response','active_branch','unselected_branch','E','I'):
            subset=[r for r in rows if r['target']==name];x=[];y=[]
            for a in (.001,.02,.1,.3):
                rr=[r for r in subset if float(r['amplitude_preclip'])==a]
                x.append(np.mean([float(r['actual_target_rms']) for r in rr]));y.append(np.mean([r['recovered']=='True' for r in rr]))
            ax[2].plot(x,y,'o-',label=name)
        ax[2].legend(ncol=2,fontsize=6);ax[2].set(title='Finite sample: 24 states × 3 directions',xlabel='Actual target RMS after clipping (mean)',ylabel='Full-state + identity recovery fraction',ylim=(-.02,1.02))
    panels(ax);fig.suptitle(NAMES[mode]+' | Figure 9 supplement — LDS state-kick basin assay; not Zhou input protocol')
    return fig


def local_flow(root,mode):
    with np.load(root/'lds_results'/mode/'local_flow.npz') as z:
        fig,ax=plt.subplots(1,2,figsize=(10,4),layout='constrained');xy=z['xy'];v=z['velocity']
        im=ax[0].quiver(*xy.T,*v.T,z['offplane_norm'],cmap='viridis');fig.colorbar(im,ax=ax[0],label='Off-plane field norm (rate/ms)')
        ax[0].set(title='Clipped fixed-point-centered slice',xlabel='PC1 offset',ylabel='PC2 offset')
        ax[1].scatter(np.linalg.norm(v,axis=1),z['offplane_norm'],s=8)
        ax[1].set(title='Hidden versus projected field magnitude',xlabel='Projected ||f|| (rate/ms)',ylabel='Off-plane ||f|| (rate/ms)')
    panels(ax);fig.suptitle(NAMES[mode]+' | LDS-specific flow diagnostic; not a panel of Zhou Figure 7')
    return fig


def render(root,modes):
    root=Path(root);configure();records=[]
    for mode in modes:
        makers=[('figure_08',8,lambda:fixed_points(root,mode)),
            ('figure_09_input_source_time',9,lambda:input_perturbation(root,mode,'source_time')),
            ('figure_09_input_R3_fixed_clock',9,lambda:input_perturbation(root,mode,'R3_fixed_clock')),
            ('figure_09_state',9,lambda:state_perturbation(root,mode)),('figure_09_flow',9,lambda:local_flow(root,mode))]
        for name,number,make in makers:
            paths=save_figure(make(),root/'figures'/mode,name)
            records.append(dict(id=f'{mode}_{name}',figure_number=number,encoding=mode,paths=paths,
                output_sha256={p:__import__('hashlib').sha256(Path(p).read_bytes()).hexdigest() for p in paths},
                scientific_status='METHOD ADAPTED / LDS-specific diagnosis',population='all132; selected display units explicit',
                source='Inagaki 2019 Fig5/6 and ED1/9' if number==8 else 'Zhou2023 Fig7; state and flow explicitly supplemental',
                metrics_directory=str(root/'lds_results'/mode),dpi=300))
    dump(root/'figure_manifest.json',dict(figures=records))


def comparison10(root,rows):
    fig,ax=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for axis,key,title in zip(ax.ravel(),('input_dimension','neuron_count','branch_effective_dim','whole_mean_angle','stable_endpoint_clusters','identity_retained'),
            ('External input dimensions','Internal rate dimensions','R3 branch effective dimension','Whole-state mean branch angle (deg)','Certified task-seeded endpoint clusters','Identities retained / 24')):
        axis.bar([NAMES[r['encoding']] for r in rows],[r[key] for r in rows],color=['#0072B2','#D55E00','#009E73'])
        axis.set_title(title)
    panels(ax);fig.suptitle('Figure 10 — audited encoding comparison; fixed network; no composite score')
    paths=save_figure(fig,root/'figures/comparison','figure_10_audited')
    manifest_path=root/'figure_manifest.json';m=json.loads(manifest_path.read_text(encoding='utf-8'))
    m['figures']=[r for r in m['figures'] if r['id']!='figure_10_audited']
    m['figures'].append(dict(id='figure_10_audited',figure_number=10,encoding='comparison',paths=paths,
        output_sha256={p:__import__('hashlib').sha256(Path(p).read_bytes()).hexdigest() for p in paths},dpi=300))
    dump(manifest_path,m)
