"""Paper Figure 8/9 redraws from full-state independent evaluation archives."""
from pathlib import Path
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from .style import configure, panels, save_figure, NAMES
from ..evaluation.figure_data_dynamics import ROOT, REF, sha, savez

COLORS=plt.get_cmap('tab10').colors[:6]


def readcsv(path):
    with Path(path).open(encoding='utf-8') as f:return list(csv.DictReader(f))


def five_axes():
    fig=plt.figure(figsize=(13,8),layout='constrained');gs=fig.add_gridspec(2,6)
    ax=[fig.add_subplot(gs[0,0:2]),fig.add_subplot(gs[0,2:4]),fig.add_subplot(gs[0,4:6]),
        fig.add_subplot(gs[1,0:3]),fig.add_subplot(gs[1,3:6])]
    panels(ax);return fig,ax


def fixed_points(mode, output, branch=0):
    out=Path(output);folder=REF/mode;derived=out/'derived'/mode
    with np.load(folder/'fixed_points.npz') as a:
        endpoints=a['endpoints'];conditions=a['conditions'];times=a['times_ms']
    dr,step=[(1,1),(1,2),(-1,1),(-1,2)][branch]
    ids=np.flatnonzero((conditions[:,1]==dr)&(conditions[:,2]==step));ids=ids[np.argsort(conditions[ids,0])]
    points=endpoints[ids];center=points.mean(0);_,_,vt=np.linalg.svd(points-center,full_matrices=False);basis=vt[:2].T
    coords=(points-center)@basis
    savez(derived/f'fig08_branch{branch}_display_basis.npz',basis=basis,center=center,endpoints=points,trial_indices=ids,conditions=conditions[ids],coordinates=coords)
    fig,ax=five_axes()
    for position,(trial,color) in enumerate(zip(ids,COLORS)):
        ax[0].scatter(*coords[position],color=color,s=60,marker='o',label=f'L={conditions[trial,0]}')
        ax[0].annotate(str(conditions[trial,0]),coords[position],xytext=(4,4),textcoords='offset points')
    ax[0].set(title='Six equilibria in one R3 branch',xlabel='Endpoint PC1',ylabel='Endpoint PC2');ax[0].legend(ncol=2)
    with np.load(folder/'basin_full.npz') as a:
        all_paths=a['rates'];reference_index=a['initial_reference_index'];amplitudes=a['amplitude']
        for position,(trial,color) in enumerate(zip(ids,COLORS)):
            candidates=np.flatnonzero(reference_index==trial)
            dose=amplitudes[candidates];chosen=candidates[np.isclose(dose,.1)]
            if not len(chosen):chosen=candidates[np.argsort(abs(dose-.1))[:3]]
            for k in chosen:
                xy=(all_paths[k]-center)@basis
                ax[1].plot(xy[:,0],xy[:,1],color=color,alpha=.65,lw=.8)
                ax[1].scatter(*xy[0],color=color,s=8,marker='x')
            ax[1].scatter(*coords[position],color=color,s=30,edgecolor='k',linewidth=.3)
    ax[1].set(title='Real full-state-kick trajectories',xlabel='Same endpoint PC1',ylabel='Same endpoint PC2')
    cert=readcsv(derived/'fig08_fixed_point_certificates.csv');chosen=[cert[i] for i in ids]
    residual=np.array([float(x['residual_max_per_ms']) for x in chosen])
    ax[2].scatter(np.arange(6),residual,c=COLORS,s=35);ax[2].set_yscale('log')
    ax[2].set(title='Full132 field residual',xlabel='Initial location L',ylabel='max |f(r*)| (rate / ms)',xticks=np.arange(6))
    re=np.array([float(x['max_real_eigenvalue_per_ms']) for x in chosen]);rho=np.array([float(x['euler_spectral_radius']) for x in chosen])
    ax[3].plot(np.arange(6),re,'o-',color='#0072B2',label='Maximum Re eigenvalue')
    ax[3].axhline(0,color='gray',lw=.6,ls=':');ax[3].set(title='Representative kink slope 0.5 + certificate',xlabel='Initial location L',ylabel='Maximum Re λ (1/ms)',xticks=np.arange(6))
    twin=ax[3].twinx();twin.plot(np.arange(6),rho,'s--',color='#D55E00');twin.axhline(1,color='#D55E00',ls=':',lw=.5);twin.set_ylabel('Euler spectral radius',color='#D55E00')
    good=sum(x['certified']=='True' for x in chosen)
    ax[3].text(.04,.78,f'{good}/6 piecewise-cascade certificates\nClip kink units: '+','.join(x['kink_count'] for x in chosen),transform=ax[3].transAxes,fontsize=7,bbox=dict(facecolor='white',edgecolor='none',alpha=.9))
    basin=readcsv(folder/'basin.csv')
    for position,(trial,color) in enumerate(zip(ids,COLORS)):
        rows=[r for r in basin if int(r['trial'])==trial and r['target']=='full']
        amplitudes=sorted(set(float(r['amplitude_preclip']) for r in rows));x=[];y=[]
        for amp in amplitudes:
            group=[r for r in rows if float(r['amplitude_preclip'])==amp]
            x.append(np.mean([float(r['actual_whole_rms']) for r in group]));y.append(np.mean([r['recovered']=='True' and r['identity_retained']=='True' for r in group]))
        ax[4].plot(x,y,'o-',color=color,label=f'L={conditions[trial,0]}',ms=4)
    ax[4].set(title='Full-state-kick recovery with identity',xlabel='Actual whole-network state-kick RMS',ylabel='Recovered fraction of 3 fixed directions',ylim=(-.04,1.06));ax[4].legend(ncol=3)
    fig.suptitle(f'{NAMES[mode]} | Figure 8 — six R3 states, D={dr:+d}, S={step}; full132 dynamics')
    return fig


def basin_slices(mode,output,variant='three_endpoint'):
    fig,ax=plt.subplots(2,2,figsize=(11,9),layout='constrained');panels(ax)
    # Fixed global colors for 24 reference states, with explicit other/unconverged.
    colors=['#eeeeee','#333333','#999999']+list(plt.get_cmap('tab20').colors)+list(plt.get_cmap('Set2').colors[:4])
    cmap=ListedColormap(colors);norm=BoundaryNorm(np.arange(-3.5,24.5,1),len(colors))
    for b,axis in enumerate(ax.ravel()):
        stem='fig08_six_point_basins' if variant=='three_endpoint' else 'fig08_sixmean_control'
        with np.load(Path(output)/'derived'/mode/f'{stem}_branch{b}.npz') as a:
            t=a['grid_axis'];labels=a['classification'].reshape(len(t),len(t))
            image=axis.imshow(labels,origin='lower',extent=[t[0],t[-1],t[0],t[-1]],cmap=cmap,norm=norm,interpolation='nearest')
            dr,step=[(1,1),(1,2),(-1,1),(-1,2)][b]
            counts={int(x):int(np.sum(a['classification']==x)) for x in np.unique(a['classification'])}
            axis.set(title=f'D={dr:+d}, S={step}: {np.sum(a["legal_mask"])} legal states',xlabel='Response contrast α',ylabel='Response contrast β')
            axis.text(.02,.90,'Mask -3: outside rate cube\n-2: unconverged; -1: other equilibrium',transform=axis.transAxes,fontsize=7,bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
    cb=fig.colorbar(image,ax=ax.ravel().tolist(),ticks=[-3,-2,-1,0,5,11,17,23],shrink=.7);cb.set_label('Matched full132 reference-state index')
    fig.suptitle(f'{NAMES[mode]} | Figure 8 supplement — {variant} full132-integrated initial-state slices\nPrespecified Response contrasts; 41×41 grid; invalid states masked, never clipped')
    return fig


def perturbation(mode,output,assay='source_time'):
    fig,ax=five_axes();folder=REF/mode
    with np.load(folder/f'input_{assay}_7.npz') as a:
        control=a['control'];pert=a['perturbed'];t=a['times_ms'];basis=a['basis'];center=a['pca_center']
        # Pick observed control-modulated units, never using target location.
        candidates=np.array([i for i,label in enumerate(a['neuron_labels']) if str(label).startswith(('R','M_','I_decay'))])
        units=candidates[np.argsort(np.ptp(control[:,candidates],axis=0))[-3:]]
        for j,q in enumerate(units):
            ax[0].plot(t,control[:,q]+1.15*j,color='black',lw=.9,label='Control' if j==0 else None)
            ax[0].plot(t,pert[:,q]+1.15*j,color='#D55E00',ls='--',lw=.9,label='Input pulse' if j==0 else None)
            ax[0].text(t[-1],1.15*j+.1,str(a['neuron_labels'][q]),ha='right',fontsize=6)
        active=np.flatnonzero(a['pulse_mask']);onset=t[active[0]]-5;offset=t[active[-1]]
        ax[0].axvspan(onset,offset,color='#D55E00',alpha=.15);ax[0].legend()
        ax[0].set(title='Control / 50 ms external-current pulse',xlabel='Time (ms)',ylabel='Dimensionless rate + 1.15 offsets')
        cp=(control-center)@basis;pp=(pert-center)@basis
        ax[1].plot(cp[:,0],cp[:,1],color='black',label='Control');ax[1].plot(pp[:,0],pp[:,1],color='#D55E00',label='Perturbed')
        ax[1].scatter(*pp[active[0],:2],marker='^',color='#D55E00',s=35,label='Pulse onset');ax[1].scatter(*pp[active[-1],:2],marker='s',color='#D55E00',s=25,label='Pulse offset')
        ax[1].set(title='Common control-only PCA',xlabel='PC1',ylabel='PC2');ax[1].legend()
        ct=a['cross_temporal_times_ms'];image=ax[2].imshow(a['cross_temporal_distance'],origin='lower',extent=[ct[0],ct[-1],ct[0],ct[-1]],aspect='auto',cmap='viridis')
        fig.colorbar(image,ax=ax[2],label='Full132 Euclidean distance',shrink=.8)
        ax[2].set(title='Control-time × perturbed-time distance',xlabel='Perturbed time (ms)',ylabel='Control time (ms)')
    for seed in (7,11,19):
        with np.load(folder/f'input_{assay}_{seed}.npz') as a:
            ax[3].plot(a['times_ms'],np.linalg.norm(a['perturbed']-a['control'],axis=1),label=f'Direction seed {seed}')
    ax[3].axvspan(onset,offset,color='#D55E00',alpha=.15);ax[3].legend();ax[3].set(title='Paired full-state deviation',xlabel='Time (ms)',ylabel='||r perturbed − r control||₂')
    rows=readcsv(folder/'basin.csv')
    for target in ('full','active_branch'):
        selected=[r for r in rows if r['target']==target]
        amplitudes=sorted(set(float(r['amplitude_preclip']) for r in selected));x=[];y=[]
        for amp in amplitudes:
            group=[r for r in selected if float(r['amplitude_preclip'])==amp]
            x.append(np.mean([float(r['actual_whole_rms']) for r in group]));y.append(np.mean([r['recovered']=='True' and r['identity_retained']=='True' for r in group]))
        ax[4].plot(x,y,'o-',label=target)
    ax[4].set(title='Separate state-kick assay (24 conditions)',xlabel='Actual whole-network state-kick RMS',ylabel='Identity-constrained recovery fraction',ylim=(-.04,1.06));ax[4].legend()
    fig.suptitle(f'{NAMES[mode]} | Figure 9 — finite input pulse and separate state-kick recovery ({assay})')
    return fig


def stage_comparison(mode,output):
    with np.load(Path(output)/'derived'/mode/'fig09_stage_perturbations.npz') as a:
        t=a['times_ms'];stages=a['stages'];dist=np.linalg.norm(a['perturbed']-a['control'][None,None],axis=-1)
        onsets=a['onsets_ms'];seeds=a['seeds']
    rows=readcsv(Path(output)/'derived'/mode/'fig09_recovery_by_stage.csv')
    fig,ax=plt.subplots(2,3,figsize=(13,7),layout='constrained');panels(ax)
    for stage,name in enumerate(stages):
        for k,seed in enumerate(seeds):
            ax[0,stage].plot(t,dist[stage,k].T,color=f'C{k}',lw=.25,alpha=.12)
            ax[0,stage].plot(t,dist[stage,k].mean(0),color=f'C{k}',label=f'Seed {seed}',lw=1.4)
        ax[0,stage].axvspan(onsets[stage],onsets[stage]+50,color='#D55E00',alpha=.14)
        ax[0,stage].set(title=f'{name}: paired full132 distance',xlabel='Time (ms)',ylabel='Euclidean deviation');ax[0,stage].legend()
        for k,seed in enumerate(seeds):
            group=[r for r in rows if r['stage']==name and int(r['seed'])==seed]
            values=[np.mean([r[key]=='True' for r in group]) for key in ['sequence_correct','R4_branch_retained','R4_position_retained','recovered']]
            ax[1,stage].plot(np.arange(4)+.08*(k-1),values,'o',color=f'C{k}',label=f'{seed}')
        ax[1,stage].set(xticks=np.arange(4),xticklabels=['4-output\ncorrect','R4 branch\nretained','R4 position\nretained','full-state\nrecovery'],ylim=(-.04,1.06),ylabel='Fraction of 24 conditions')
    fig.suptitle(f'{NAMES[mode]} | Figure 9 supplement — 24 conditions × 3 temporal stages × 3 fixed input directions\n50 ms pulse; actual current RMS=0.25; faint lines are conditions, no biological repeats or error bars')
    return fig


def run(figures=(8,9),encodings=('one_hot','ring','topology'),output=None):
    configure();output=Path(output or ROOT/'artifacts/neural_paper_figures_v1');manifest=[]
    captions=[]
    for mode in encodings:
        destination=output/'figures'/('main' if mode=='one_hot' else 'supplementary')
        if 8 in figures:
            for branch in range(4):
                dest=destination if branch==0 else output/'figures/supplementary'
                paths=save_figure(fixed_points(mode,output,branch),dest,f'fig08_{mode}_branch{branch}')
                manifest.append({'figure':8,'encoding':mode,'branch':branch,'paths':paths,'data':str(output/'derived'/mode/'fig08_fixed_point_certificates.csv')})
            for variant in ('sixmean_control','three_endpoint'):
                paths=save_figure(basin_slices(mode,output,variant),output/'figures/supplementary',f'fig08_{mode}_{variant}_slices')
                manifest.append({'figure':8,'encoding':mode,'assay':f'affine_initial_state_slices_{variant}','paths':paths})
        if 9 in figures:
            for assay in ('source_time','R3_fixed_clock'):
                dest=destination if assay=='source_time' else output/'figures/supplementary'
                paths=save_figure(perturbation(mode,output,assay),dest,f'fig09_{mode}_{assay}')
                manifest.append({'figure':9,'encoding':mode,'assay':assay,'paths':paths})
            paths=save_figure(stage_comparison(mode,output),output/'figures/supplementary',f'fig09_{mode}_stage_perturbations')
            manifest.append({'figure':9,'encoding':mode,'assay':'24_condition_stage_pulses','paths':paths})
    for record in manifest:
        mode=record['encoding'];assay=record.get('assay','')
        if record['figure']==8:
            inputs=[REF/mode/'fixed_points.npz',REF/mode/'basin_full.npz',REF/mode/'basin.csv',output/'derived'/mode/'fig08_fixed_point_certificates.csv']
            if 'branch' in record:inputs.append(output/'derived'/mode/f'fig08_branch{record["branch"]}_display_basis.npz')
            if 'slices' in assay:
                stem='fig08_sixmean_control' if 'sixmean_control' in assay else 'fig08_six_point_basins'
                inputs.extend(output/'derived'/mode/f'{stem}_branch{b}.npz' for b in range(4))
        elif assay=='24_condition_stage_pulses':inputs=[output/'derived'/mode/'fig09_stage_perturbations.npz',output/'derived'/mode/'fig09_recovery_by_stage.csv']
        else:inputs=[REF/mode/f'input_{assay}_{seed}.npz' for seed in (7,11,19)]+[REF/mode/'basin.csv']
        record['input_sha256']={str(p.relative_to(ROOT)):sha(p) for p in inputs}
        record['output_sha256']={str(Path(p).relative_to(ROOT)):sha(p) for p in record['paths']}
        record['render_source_sha256']=sha(__file__)
        record['caption_status']='see fig08_fig09_CAPTIONS.md; numerical verification independent of visual review'
    folder=output/'manifests';folder.mkdir(exist_ok=True,parents=True)
    (folder/'fig08_fig09_figures.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (output/'fig08_fig09_CAPTIONS.md').write_text('''# Figure 8 / Figure 9 captions

Figure 8. Each branch figure fixes D/S and shows its six initial-location conditions. A: six full132 equilibrium endpoints in one PCA fitted only to those endpoints, with no ring edges. B: real full132 trajectories from archived whole-state kicks, projected in the same endpoint PCA; crosses mark initial states. C: independently recomputed full-state infinity-norm field residual (rate/ms). D: representative clip-kink slope 0.5 Jacobian maximum real eigenvalue and Euler spectral radius; points at clip kinks require the separately recomputed piecewise-cascade certificate, rather than an unqualified smooth-Jacobian claim. E: identity-constrained recovery over three fixed perturbation directions per location; x is their mean actual whole-state RMS after clipping, not nominal dose. No confidence intervals or biological trial repetitions are implied. Source method inspiration: Sussillo & Barak (2013), Inagaki (2019); these are LDS adaptations, not author-code execution or original-data reproduction.

Figure 8 affine-slice supplement. Two distinct prespecified planes are retained. sixmean_control uses the first three units of the activity-selected R3 branch and the six-endpoint mean. three_endpoint uses the first three L conditions in fixed order, their observed active R3 position units and their three-endpoint mean. No recovery-based selection is used. The six-mean negative result is retained alongside the three-endpoint slice. It is not a PCA plane and need not contain all six equilibria. Every legal point in a 41×41 grid is integrated for 2000 ms in the full132 system with archived identical clock/stimulus/tonic. Illegal cube states are masked and never clipped. Final labels require full-state max-norm distance <0.02 to one of all24 reference states and max field residual <1e-7 rate/ms; -1 is another equilibrium, -2 unconverged, -3 invalid. The slice is not a global basin proof. All paths, axes, directions, center, legal mask, classifications and residuals are archived. The reference set contains task-initialized equilibria and does not establish the exact total attractor count.

Figure 9. A–D use the same preselected archived trial within each assay; source-time replay and fixed-R3-clock replay are separate figures. A: three units selected by control modulation, control and 50-ms external-current pulse, with vertical rate offsets. B: common control-only PCA; pulse onset/offset marked. C: control-time by perturbed-time full132 Euclidean distance; axes preserve this order. D: full-state matched-time deviation for three fixed direction seeds 7/11/19. E: a separate instantaneous state-kick assay, with identity-constrained recovery across24 conditions; it is not pooled with the input pulse. The x coordinates are actual whole-state RMS averaged within nominal kick strata. Projected overlap alone does not establish recovery. Source method inspiration: Inagaki (2019), Zhou (2023); LDS adaptation, not original-data reproduction.

Figure 9 stage supplement. Each of24 task conditions is independently replayed with exactly paired zero process noise, at pre-R2 / between-R2-and-R3 / R3-hold windows. Three seeded full132 Gaussian directions are normalized to unit RMS and reused identically across stages and encodings. A50-ms pulse has actual current RMS0.25. All control replays are verified against REC within1e-12. Faint lines are task conditions; bold lines are descriptive means across conditions for each fixed direction, with no confidence interval. Bottom panels show exact fractions of24 conditions for four-output accuracy, final R4 branch/position identity, and identity-constrained full-state max-norm recovery <0.02. Shared Y is read in the unchanged final20-ms decision window; targets are used only for post-replay evaluation. Full trajectories, reconstructed baseline stimulus/clock, explicit added currents, zero-noise arrays, conditions and seeds are archived.
''',encoding='utf-8')
    return manifest


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--figures',nargs='+',type=int,default=[8,9]);p.add_argument('--encodings',nargs='+',default=['one_hot','ring','topology']);p.add_argument('--output');a=p.parse_args();run(a.figures,a.encodings,a.output)
