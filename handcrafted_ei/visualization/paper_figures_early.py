"""Paper Figure 1--3: reproducible small multiples from verified full-rate arrays."""
from pathlib import Path
import json
import platform
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .style import configure, panels, timeline, save_figure
from ..evaluation.figure_data_early import recording, derive, digest, ROOT, RAW
from ..evaluation.population_data import load_dataset
from ..evaluation.population_activity import save_rows

COLORS=plt.get_cmap('tab10').colors


def finish(fig, axes, title):
    panels(axes);fig.suptitle(title,fontsize=13)
    for a in np.asarray(axes).ravel():
        if a.has_data():a.tick_params(labelsize=7)
    return fig


def fig01(d,a):
    t=d['times_ms'];g=d['groups'];r=d['rates']
    i=next(i for i,v in enumerate(d['tasks']) if (v['L'],v['D'],v['S'])==(0,1,1))
    fig,ax=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for s in range(1,5):ax[0,0].plot(t,a[f'R{s}__trial_peak'][i],label=f'R{s}')
    ax[0,0].set(title='A single condition: L=0, D=+1, S=1',ylabel='Population peak rate')
    for name in ('M_D','M_S','E_gate_D','E_gate_S','I_decay_D','I_decay_S'):
        ax[0,1].plot(t,a[name+'__trial_peak'][i],label=name,ls='--' if name.endswith('S') else '-')
    ax[0,1].set(title='Memory, excitatory gates and inhibitory feedback',ylabel='Population peak rate')
    for l in range(6):
        j=next(i for i,v in enumerate(d['tasks']) if (v['L'],v['D'],v['S'])==(l,1,1))
        ax[1,0].plot(t,r[j,:,g['R1'][0]],color=plt.cm.viridis(l/5),label=f'L={l}')
    ax[1,0].set(title='One fixed R1 position unit across six initial locations',ylabel='Unit rate')
    for kind,color in [('E',COLORS[0]),('I',COLORS[1])]:
        ax[1,1].plot(t,a[kind+'__active_fraction'].mean(0),color=color,label=kind+' active fraction')
    twin=ax[1,1].twinx()
    for kind,color in [('E',COLORS[0]),('I',COLORS[1])]:
        twin.plot(t,a[kind+'__total'].mean(0),color=color,ls='--',alpha=.5)
    twin.set_ylabel('Total E/I rate (dashed)',fontsize=8)
    ax[1,1].set(title='All 24 conditions: E/I activity and recruitment',ylabel='Fraction with rate > 0.1')
    for axis in ax.ravel():
        timeline(axis,d['events'][i]);axis.set_xlabel('Time (ms)');axis.legend(fontsize=6,ncol=2)
    return finish(fig,ax,'Figure 1 | Temporal organization of the fixed E/I network')


def fig02(d,b,rows):
    fig=plt.figure(figsize=(13,9),layout='constrained');gs=fig.add_gridspec(2,2)
    aa=fig.add_subplot(gs[0,0]);ab=fig.add_subplot(gs[0,1]);ad=fig.add_subplot(gs[1,1]);t=d['times_ms']
    cg=gs[1,0].subgridspec(2,2);caxes=[fig.add_subplot(cg[i//2,i%2]) for i in range(4)]
    for s,n in enumerate((1,2,4,4)):
        yy=np.linspace(.15,.85,n) if n>1 else [.5]
        for j,y in enumerate(yy):
            aa.scatter(s,y,s=170,color=COLORS[j]);aa.text(s,y,f'b{j}',ha='center',va='center',color='white',fontsize=6)
            if s:
                prev=np.linspace(.15,.85,(1,2,4,4)[s-1]) if s>1 else [.5]
                source=(j//2 if s==2 else j) if s>1 else 0
                aa.annotate('',xy=(s-.08,y),xytext=(s-1+.08,prev[source]),arrowprops={'arrowstyle':'->','lw':.8,'color':'#777'})
    aa.set(xticks=range(4),xticklabels=['R1','R2','R3','R4'],yticks=[],title='Handcrafted structural support: 1 → 2 → 4 → 4');aa.set_ylim(0,1)
    for s in (2,3):
        a=b[f'R{s}__activity'][0];offset=(s-2)*1.2
        for j in range(a.shape[1]):ab.plot(t,a[:,j]+offset,color=COLORS[j],ls='-' if j==b[f'R{s}__selected'][0] else '--',label=f'R{s} b{j}')
    ab.set(title='Selected (solid) and unselected (dashed), trial 0',xlabel='Time (ms)',ylabel='Peak branch rate + stage offset');ab.legend(ncol=2,fontsize=6);timeline(ab,d['events'][0])
    # Six real units per branch, with L on the x axis; no averaging across L.
    for branch,axis in enumerate(caxes):
        direction=(1,-1)[branch//2];step=branch%2+1
        values=[]
        for l in range(6):
            i=next(i for i,v in enumerate(d['tasks']) if (v['L'],v['D'],v['S'])==(l,direction,step))
            idx=d['branch_indices']['R3'][branch];end=d['events'][i]['readout3']
            window=(t>end-d['config'].get('decision_ms',20))&(t<=end)
            values.append(d['rates'][i,window][:,idx].mean(0))
        for p in range(6):axis.plot(range(6),np.array(values)[:,p],'o-',ms=2,lw=.7,color=plt.cm.viridis(p/5),label=f'unit {p}')
        axis.set(title=f'R3 b{branch}: D={direction:+d}, S={step}',xlabel='Initial position L',ylabel='Readout-window rate',xticks=range(6))
    caxes[0].legend(ncol=3,fontsize=5)
    for s in range(1,5):
        subset=[v for v in rows if v['stage']==s]
        for i,v in enumerate(subset):
            x=s+(i-11.5)*.009
            if np.isfinite(v['competitor_peak_at_readout']):
                ad.plot([x-.07,x+.07],[v['selected_peak_at_readout'],v['competitor_peak_at_readout']],color='0.8',lw=.5)
                ad.scatter(x+.07,v['competitor_peak_at_readout'],s=9,color=COLORS[1])
            ad.scatter(x-.07,v['selected_peak_at_readout'],s=9,color=COLORS[0])
        ad.text(s,.55,f"active branches: {min(v['active_branches_at_readout'] for v in subset)}–{max(v['active_branches_at_readout'] for v in subset)}",ha='center',fontsize=6,rotation=10)
    ad.scatter([],[],color=COLORS[0],label='Selected');ad.scatter([],[],color=COLORS[1],label='Max competitor')
    ad.set(xticks=range(1,5),xticklabels=['R1','R2','R3','R4'],ylabel='Readout-window peak rate',title='Paired deterministic conditions; no independent repeats');ad.legend(fontsize=6)
    return finish(fig,[aa,ab,caxes[0],ad],'Figure 2 | Measured routing through predefined Response branches')


def causal_controls(d,out):
    traces={};rows=[];sources={}
    experiments=['baseline','no_feedback','lesion_feedback_D','lesion_feedback_S']+[f'lesion_{v}' for v in 'ABCD']
    experiments += [f'random_{v}_{seed}' for v in 'ABCD' for seed in (7,11,19)]
    experiments += [f'random_feedback_{v}_{seed}' for v in ('D','S') for seed in (7,11,19)]
    for experiment in experiments:
        c=d if experiment=='baseline' else load_dataset(RAW,d['encoding_type'],experiment)
        sources[experiment]=digest(RAW/f"{d['encoding_type']}__{experiment}.zip")
        target=np.array([v['target'] for v in c['tasks']]);correct=c['outputs']==target
        for name in ('M_D','M_S','R2','R3'):
            traces[experiment+'__'+name]=c['rates'][:,:,c['groups'][name]].max(2)
        for s in range(4):
            rows.append({'experiment':experiment,'stage':s+1,'accuracy':float(correct[:,s].mean()),
                         'sequence_accuracy':float(correct.all(1).mean()),'n_conditions':24,
                         'intervention_records':json.dumps(c['lesions'])})
    np.savez_compressed(out/'fig03_feedback_controls.npz',times_ms=d['times_ms'],**traces)
    save_rows(out/'fig03_temporal_ablation.csv',rows)
    return traces,rows,sources


def fig03(d,a,h,controls):
    fig,axes=plt.subplots(2,3,figsize=(15,8),layout='constrained');ax=axes.ravel();t=d['times_ms']
    for k,(memory,decay,response,start,end) in enumerate([('M_D','I_decay_D','R2',1910,2270),('M_S','I_decay_S','R3',2380,2740)]):
        start=d['events'][0]['to_'+response];mask=(t>=start)&(t<=start+360)
        for name in (memory,decay,response):ax[k].plot(t[mask],a[name+'__trial_peak'].mean(0)[mask],label=name)
        ax[k].set(title=f'{memory} → {response}: actual rates',xlabel='Time (ms)',ylabel='Mean condition peak rate');ax[k].legend(fontsize=6)
    for name,var in [('M_D','D'),('R2','D'),('M_S','S'),('R3','S')]:
        y=np.array([v[var] for v in d['tasks']]);lo,hi=np.unique(y);p=h[name+'__projection']
        ax[2].plot(t,p[y==hi].mean(0)-p[y==lo].mean(0),label=f'{name} {var}')
    ax[2].set(title='Balanced rule contrast along fixed condition-mean axes',xlabel='Time (ms)',ylabel='High−low projection');ax[2].legend(fontsize=6,ncol=2);timeline(ax[2],d['events'][0])
    for name,color in [('M_D',COLORS[0]),('M_S',COLORS[1])]:
        for exp,ls in [('baseline','-'),('lesion_feedback_'+name[-1],'--')]:ax[3].plot(t,controls[exp+'__'+name].mean(0),color=color,ls=ls,label=f'{name} {exp}')
        for seed in (7,11,19):ax[3].plot(t,controls[f'random_feedback_{name[-1]}_{seed}__'+name].mean(0),color=color,lw=.5,alpha=.25)
    ax[3].set(title='Feedback cut and matched random-edge seeds 7/11/19',xlabel='Time (ms)',ylabel='Mean condition peak rate');ax[3].legend(fontsize=6);timeline(ax[3],d['events'][0])
    path=ROOT/'artifacts/neural_representation_v2/metrics'/d['encoding_type']/'decoding.npz'
    with np.load(path) as dec:
        for name,var in [('M_D','D'),('R2','D'),('M_S','S'),('R3','S')]:ax[4].plot(dec['times_ms'],dec[name+'__'+var],label=f'{name} {var}')
    ax[4].axhline(.5,color='0.5',ls=':');ax[4].set(ylim=(0,1.05),title='Disjoint-condition nearest-centroid probe',xlabel='Time (ms)',ylabel='Accuracy (chance 0.5)');ax[4].legend(fontsize=6,ncol=2);timeline(ax[4],d['events'][0])
    ax[5].axis('off');ax[5].text(0,.95,'Interpretation limits\n\nMemory amplitude decay is not information erasure.\n\nAxes use balanced condition means at fixed anchor times;\nthey are descriptive and are not decoder fits.\n\nRandom edge cuts match count, magnitude, sign and timing.\nCondition-held-out probes differ from noise-repeat probes.\n\nRates are dimensionless. Conditions are not biological repeats.',va='top',fontsize=9,linespacing=1.7)
    return finish(fig,ax[:5],'Figure 3 | Activity-dependent rule-memory handoff and causal controls')


def run(figures=(1,2,3),encodings=('one_hot',),output=None):
    output=Path(output) if output else ROOT/'artifacts/neural_paper_figures_v1';configure();results=[]
    for encoding in encodings:
        d,provenance=recording(encoding);out=output/'derived'/encoding
        a,b,rows,h=derive(d,out)
        controls=None;sources={}
        if 3 in figures:controls,_,sources=causal_controls(d,out)
        for number in figures:
            fig={1:lambda:fig01(d,a),2:lambda:fig02(d,b,rows),3:lambda:fig03(d,a,h,controls)}[number]()
            fig._suptitle.set_text(fig._suptitle.get_text()+' | '+encoding)
            dest=output/'figures'/('main' if encoding=='one_hot' else 'supplementary')
            stem=f'fig{number:02}_{encoding}';paths=save_figure(fig,dest,stem)
            caption={1:'A: single-condition R1–R4 maxima; B: memory/gate/feedback actual peak rates; C: fixed R1 position-0 unit across six L, D=+1 S=1; D: all-condition E/I active fractions (>0.1) and total rates. Vertical markers come from recorded events; dotted readout, green transfer, dashed retire. All rates dimensionless.',2:'A: handcrafted branch support, not emergent dimensionality. B: actual branch peak rates for trial 0, correct solid vs competitor dashed; stage offsets labelled. C: selected R3 branch, six actual positional units per six L conditions. D: paired selected/max-unselected peak rates in each decision window; 24 deterministic task conditions are not repetitions. R1 has no competitor and its comparison is defined as zero.',3:'A/B: actual (not amplitude-renormalized) condition-mean peak rates in 360 ms windows after recorded transfer. C: fixed normalized rule contrast axes fitted to balanced condition means at delay end (memory) or readout (Response); projection axes and centers saved. D: feedback removed versus baseline and three matched random controls. E: existing disjoint-task-condition nearest-centroid cross-validation, fractional tie credit. Chance 0.5; activity decay does not establish information erasure. Companion temporal-ablation CSV reuses pre/post handoff edge cuts and all matched random seed controls. No noise-repeat and condition-held-out results are pooled.'}[number]
            if number==2:
                caption=caption.replace('C: selected R3 branch, six actual positional units per six L conditions.', 'C: four R3 branch small multiples; six actual positional units tuned across six initial L conditions at the readout window, with D/S fixed to the branch rule. No averaging across L.')
                caption=caption.replace('R1 has no competitor and its comparison is defined as zero.', 'R1 has no competitor; competitor activity, leakage and margin are undefined (NPZ NaN / CSV NA), and no competitor dot is drawn.')
            cap=dest/(stem+'_caption.md');cap.write_text(caption+'\n',encoding='utf-8')
            manifests=output/'manifests';manifests.mkdir(parents=True,exist_ok=True)
            derived=sorted(out.glob(f'fig{number:02}*'))
            manifest={'figure':number,'encoding':encoding,'provenance':provenance,
                      'environment':{'python':sys.version,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'platform':platform.platform()},
                      'analysis_sources':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'handcrafted_ei/evaluation/figure_data_early.py']},
                      'control_archive_sha256':sources if number==3 else {},
                      'decoder_source_sha256':digest(ROOT/'artifacts/neural_representation_v2/metrics'/encoding/'decoding.npz') if number==3 else None,
                      'outputs':{str(p):digest(p) for p in [*map(Path,paths),cap,*derived]},
                      'caption':caption,'reference_status':'Methods-inspired redraw; source paper panel visual verification delegated to reference audit; no claim of author-code reproduction.',
                      'visual_review':'pending actual PNG inspection'}
            (manifests/(stem+'.json')).write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding='utf-8')
            results.append({'figure':number,'encoding':encoding,'paths':paths})
    return results


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--encodings',nargs='+',default=['one_hot'])
    parser.add_argument('--figures',nargs='+',type=int,default=[1,2,3])
    args=parser.parse_args()
    print(json.dumps(run(figures=args.figures,encodings=args.encodings),indent=2))
