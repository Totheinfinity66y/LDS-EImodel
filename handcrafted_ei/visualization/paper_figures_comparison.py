"""Figure 10: shared neural coordinates and measured current doses."""
from pathlib import Path
import json
import platform
import sys
import numpy as np
import matplotlib.pyplot as plt
from .style import configure, save_figure, panels
from ..evaluation.figure_data_comparison import analyze, csvrows, digest, ROOT, MODES


def run(output=ROOT/'artifacts/neural_paper_figures_v1'):
    output=Path(output); configure(); data,rows=analyze(output)
    file=output/'derived/comparison/fig10_common_basis.npz'
    with np.load(file) as z:
        scores=z['scores']; evr=z['evr']; fixed=z['one_hot_scores']
        fig,ax=plt.subplots(2,3,figsize=(16,9),layout='constrained')
        colors=('#0072B2','#D55E00','#009E73')
        for i,(mode,d,color) in enumerate(zip(MODES,data,colors)):
            sample=np.flatnonzero(d['times_ms']==100)[0]
            rule=[j for j,x in enumerate(d['tasks']) if x['D']==1 and x['S']==1]
            # Raw input dimensionality is printed; actual neural currents plotted.
            input_axes=ax[0,0].inset_axes([.02+i*.33,.57,.29,.37])
            tuning_axes=ax[0,0].inset_axes([.02+i*.33,.09,.29,.33])
            for j in rule:
                input_axes.plot(range(6),d['input_currents'][j,sample,d['groups']['R1']],alpha=.7,lw=.7)
            input_axes.set(title=f'{mode}\nexternal dim {len(d["tasks"][0]["encoded"]["x_L"])}',xlabel='R1 position',ylim=(0,1))
            input_axes.tick_params(labelsize=6);input_axes.title.set_fontsize(7)
            readout=np.flatnonzero(d['times_ms']==d['events'][0]['readout3'])[0]
            branch=d['rates'][rule[0],readout,d['groups']['R3']].reshape(4,6).max(1).argmax()
            ids=np.asarray(d['groups']['R3']).reshape(4,6)[branch]
            for j in rule:tuning_axes.plot(range(6),d['rates'][j,readout,ids],lw=.7)
            tuning_axes.set(xlabel='R3 position',ylim=(0,1.08));tuning_axes.tick_params(labelsize=6)
            trial=0; ax[0,1].plot(scores[i,trial,:,0],scores[i,trial,:,1],color=color,label=mode,lw=1.4-i*.3,ls=('-','--',':')[i])
            for stage in range(1,5):
                k=np.flatnonzero(d['times_ms']==d['events'][trial][f'readout{stage}'])[0]
                ax[0,1].scatter(*scores[i,trial,k,:2],color=color,marker=('o','s','^','D')[stage-1],s=18)
            ax[0,2].plot(fixed[i,trial,:,0],fixed[i,trial,:,1],color=color,ls=('-','--',':')[i],label=mode)
            ref=ROOT/'artifacts/paper2agent_reproduction/lds_results'/mode
            cert=csvrows(ref/'fixed_points.csv')
            # Different units get separate small axes, never a composite score.
            pairs=csvrows(ROOT/'artifacts/neural_representation_v2/metrics'/mode/'subspace_pairs.csv')
            angles=[float(r['mean_angle']) for r in pairs if r['stage']=='3']
            rsa=csvrows(ROOT/'artifacts/neural_representation_v2/metrics'/mode/'rsa_response.csv')
            distances=[float(r['offdiagonal_mean']) for r in rsa if r['stage']=='3']
            if i==0:
                metric_axes=[ax[1,0].inset_axes([.08,.70,.85,.22]),ax[1,0].inset_axes([.08,.39,.85,.22]),ax[1,0].inset_axes([.08,.08,.85,.22])]
                for aa,title in zip(metric_axes,('R3 branch angle (degrees)','R3 Response RDM distance','Certified endpoints / 24')):
                    aa.set_title(title,fontsize=7);aa.tick_params(labelsize=6);aa.set_xticks(range(3),MODES)
            metric_axes[0].scatter(np.full(len(angles),i),angles,color=color,s=12)
            metric_axes[1].scatter(np.full(len(distances),i),distances,color=color,s=12)
            metric_axes[2].scatter(i,sum(r['stable_endpoint']=='True' for r in cert),color=color,s=16)
            for amplitude in (.05,.2,.5):
                rr=[r for r in rows if r['encoding']==mode and r['current_rms']==amplitude]
                ax[1,1].scatter(amplitude+i*.003,np.mean([r['recovered'] for r in rr]),color=color,marker=('o','s','^')[i])
                ax[1,2].scatter(amplitude+i*.003,np.mean([r['final_l2'] for r in rr]),color=color,marker=('o','s','^')[i])
        ax[0,0].set(title='A  Encoded location → neural current',xticks=[],yticks=[])
        ax[0,0].text(.02,.45,'Below: six L conditions; R3 readout, D=+1, S=1',transform=ax[0,0].transAxes,fontsize=7)
        ax[0,1].set(title='B  Joint PCA: equal encoding weights',xlabel=f'PC1 ({evr[0]:.1%})',ylabel=f'PC2 ({evr[1]:.1%})');ax[0,1].legend(fontsize=7)
        ax[0,2].set(title='B sensitivity: one-hot-fitted basis',xlabel='One-hot PC1',ylabel='One-hot PC2')
        ax[1,0].set(title='C  Geometry and fixed-state metrics',xticks=[],yticks=[])
        ax[1,1].set(title='D  Full-state + identity recovery',xlabel='Actual added current RMS',ylabel='Fraction of 24 conditions × 3 directions',ylim=(-.03,1.04))
        ax[1,2].set(title='D  Residual state error at R4',xlabel='Actual added current RMS',ylabel='Mean full132 L2 distance')
        fig.suptitle('Figure 10 | Common neural coordinates; matched 50 ms currents; deterministic assay')
        paths=save_figure(fig,output/'figures/main','fig10_encoding_comparison')
    caption=('Figure 10. Six external L inputs map to the same internal six-position population (A). '
        'All 24 conditions and all 132 neurons enter an equal-weight, stride-4 joint PCA (B); '
        'one-hot-only fit is a sensitivity comparison. Certified endpoints (C) retain source clip-kink certificates. '
        'D uses identical full132 external-current directions at RMS .05/.2/.5 for 50 ms, starting 100 ms after to_R3, '
        'seeds7/11/19 and 24 conditions per encoding. This is not raw-input-coordinate noise. '
        'Recovery requires final R4 branch/position identity and full-state Linf<.02 relative to the paired control. '
        'Dots summarize deterministic condition/direction samples, without biological confidence intervals. '
        'Rates are dimensionless. Sample/clock are reconstructed from verified events. '
        'Trajectories in coincident coordinates can overlap and are distinguished by line style. '
        'C separately shows six R3 branch-pair angles, four branch RDM distances and certified endpoints; '
        'different dots are branch comparisons, not biological repeats. Counts are not exhaustive attractor counts. '
        'No geometry superiority is asserted.')
    (output/'figures/main/fig10_encoding_comparison.caption.md').write_text(caption+'\n',encoding='utf-8')
    inputs={d['archive_path']:d['archive_sha256'] for d in data}
    inputs.update({str(ROOT/'artifacts/paper2agent_reproduction/lds_results'/m/'fixed_points.csv'):digest(ROOT/'artifacts/paper2agent_reproduction/lds_results'/m/'fixed_points.csv') for m in MODES})
    for mode in MODES:
        for name in ('subspace_pairs.csv','rsa_response.csv'):
            p=ROOT/'artifacts/neural_representation_v2/metrics'/mode/name
            inputs[str(p)]=digest(p)
    record=dict(figure=10,inputs=inputs,derived=str(file),derived_sha256=digest(file),outputs={p:digest(p) for p in paths},
        source={str(Path(__file__)):digest(__file__),str(ROOT/'handcrafted_ei/evaluation/figure_data_comparison.py'):digest(ROOT/'handcrafted_ei/evaluation/figure_data_comparison.py')},
        python=sys.version,numpy=np.__version__,platform=platform.platform(),reference='Gallego2018 Fig3; Kobak2016 comparison layout; adapted, source visual review pending',
        numerical_status='paired full-state replay verified at 1e-12',visual_status='pending actual image inspection',
        incomplete_panels=[],events=data[0]['events'],config_by_encoding={d['encoding_type']:d['config'] for d in data},
        neuron_indices=list(range(132)),seeds=[7,11,19],fit_scope='all 24 conditions x all 3 encodings; uniform time stride4',
        derived_outputs={str(p):digest(p) for p in file.parent.glob('fig10*') if p.is_file()},
        references=[{'title':'Cortical population activity within a preserved neural manifold underlies multiple motor behaviors','doi':'10.1038/s41467-018-06560-z','panel':'Figure3a-c; angle spectra and comparison layout'},
                    {'title':'Demixed principal component analysis of neural population data','doi':'10.7554/eLife.10989','panel':'condition comparison layout; not dPCA'}])
    (output/'manifests').mkdir(exist_ok=True)
    (output/'manifests/fig10_comparison.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return paths
