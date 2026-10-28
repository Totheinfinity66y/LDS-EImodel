"""Paper Figure 4--7 rendering. Every curve derives from archived rates."""
from pathlib import Path
import json
import platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ..evaluation.figure_data_geometry import build, digest

COLORS=['#0072B2','#56B4E9','#D55E00','#CC79A7']
LABELS=['D=+1, S=1','D=+1, S=2','D=-1, S=1','D=-1, S=2']


def timeline(ax,d):
    for s in range(1,5):
        ax.axvline(d['events'][0][f'readout{s}'],c='.65',lw=.6,ls=':')


def letter(ax,s,title):
    ax.set_title(s+'  '+title,loc='left',fontweight='bold',fontsize=10)


def pcalabel(ax,p):
    ax.set_xlabel(f"PC1 ({p['pca_evr'][0]*100:.1f}%)")
    ax.set_ylabel(f"PC2 ({p['pca_evr'][1]*100:.1f}%)")


def fig4(d,p):
    fig=plt.figure(figsize=(14,12),layout='constrained')
    gs=fig.add_gridspec(3,3)
    a=fig.add_subplot(gs[0,:2]); b=fig.add_subplot(gs[0,2],projection='3d')
    cs=[fig.add_subplot(gs[1,k]) for k in range(3)]; dt=fig.add_subplot(gs[2,:2]); vel=fig.add_subplot(gs[2,2])
    x=p['pca_scores']; t=d['times_ms']
    for i,task in enumerate(d['tasks']):
        if task['L']!=0: continue
        q=i%4
        a.plot(*x[i,:,:2].T,color=COLORS[q],label=LABELS[q]); b.plot(*x[i,:,:3].T,color=COLORS[q])
        for s in range(1,5):
            j=np.argmin(abs(t-d['events'][i][f'readout{s}']))
            a.scatter(*x[i,j,:2],color=COLORS[q],marker=['o','s','^','D'][s-1],s=35)
        for c,s in zip(cs,(2,3,4)):
            start=d['events'][0][f'to_R{s}']; end=d['events'][0][f'readout{s}']; mask=(t>=start)&(t<=end)
            c.plot(*x[i,mask,:2].T,color=COLORS[q])
    a.legend(fontsize=8,ncol=2); letter(a,'A','L=0: four rule trajectories; shapes = readout 1–4')
    letter(b,'B','Same global PCA, 3-D'); b.set_zlabel('PC3',labelpad=-3); b.set_box_aspect((1,1,1),zoom=.78)
    for c,s in zip(cs,(2,3,4)):
        letter(c,'C' if s==2 else '',f'R{s}: fixed L=0, four D/S conditions'); pcalabel(c,p)
        c.set_xlim(a.get_xlim()); c.set_ylim(a.get_ylim())
    # Descriptive fixed regression axes from existing global analysis.
    factors=np.array([[np.cos(2*np.pi*v['L']/6),np.sin(2*np.pi*v['L']/6),v['D'],2*v['S']-3] for v in d['tasks']])
    for k,name in enumerate(('L cos','L sin','D','S')):
        dt.plot(t,(p['variable_scores'][:,:,k]*factors[:,k,None]).mean(0)/np.mean(factors[:,k]**2),label=name)
    timeline(dt,d); dt.legend(ncol=4); dt.set(xlabel='Time (ms)',ylabel='Balanced projection coefficient'); letter(dt,'D','Task regression axes (descriptive; no dPCA)')
    for i in range(4): vel.plot(p['speed_times_ms'],p['full_state_speed_per_ms'][i],color=COLORS[i])
    vel.set(xlabel='Time (ms)',ylabel='Full-state speed (rate units / ms)'); timeline(vel,d); letter(vel,'','132-D speed, L=0')
    pcalabel(a,p); pcalabel(b,p)
    return fig,'All trajectories share the archived PCA fitted to all 24 conditions × uniformly subsampled time points (stride 4; exact indices archived) × 132 neurons, then applied to every recorded time point. A/B use L=0 and four rule combinations; markers show recorded readout events. C uses the same limits and basis across stages. D shows balanced L cosine/sine, D and S regression projections from archived axes fitted by joint least squares to trial-mean activity. The extra panel reports unprojected Euclidean speed with the measured time step. Rates are dimensionless. Conditions are deterministic task tuples, not independent biological repeats.'


def fig5(d,p):
    fig=plt.figure(figsize=(15,12),layout='constrained'); gs=fig.add_gridspec(3,3)
    a=fig.add_subplot(gs[0,0]); b=fig.add_subplot(gs[0,1]); c=fig.add_subplot(gs[0,2])
    time=d['times_ms']; window=(time>=d['events'][0]['to_R3'])&(time<=d['events'][0]['readout3'])
    for i,task in enumerate(d['tasks']):
        br=(task['D']==-1)*2+task['S']-1
        a.plot(*p['pca_scores'][i,window,:2].T,color=COLORS[br],alpha=.6,lw=.8)
    for br in range(4): a.plot([],[],color=COLORS[br],label=f'b{br}: '+LABELS[br])
    a.legend(fontsize=7)
    pcalabel(a,p); letter(a,'A','R3: four branches × six locations')
    rows=[v for v in p['angle_rows'] if v['scope']=='whole']
    for k,row in enumerate(rows):
        vals=np.fromstring(row['angles_degrees'],sep=';')
        b.plot(np.arange(1,len(vals)+1),vals,'o-',ms=3,label=f"{row['branch_a']}–{row['branch_b']}")
        c.plot([k-.1,k+.1],[row['cross_vaf_a_to_b'],row['cross_vaf_b_to_a']],'o-',ms=4)
    b.set(xlabel='Principal angle index',ylabel='Angle (degrees)',ylim=(0,95)); b.legend(ncol=2,fontsize=7); letter(b,'B','Full angle spectra, R3 decision window')
    c.axhline(1,c='.3',ls=':',label='Within-VAF (full retained rank)'); c.set_xticks(range(6),[f"{v['branch_a']}–{v['branch_b']}" for v in rows]); c.set(xlabel='Branch pair (left a→b, right b→a)',ylabel='Cross-VAF',ylim=(-.04,1.06)); c.legend(fontsize=6); letter(c,'C','Bidirectional variance transfer')
    c.text(.03,.35,'R3 structural support overlap = 0\nSupport-folded position overlap = '+f"{np.mean([v['folded_R3_position_overlap'] for v in rows]):.3f}",transform=c.transAxes,fontsize=8)
    for j,scope in enumerate(('whole','response','shared')):
        ax=fig.add_subplot(gs[1,j]); dist=fig.add_subplot(gs[2,j])
        angles=p[f'{scope}_angles_degrees']
        for pair in range(6):
            vals=angles[:,pair]; valid=np.any(np.isfinite(vals),axis=1); avg=np.full(len(time),np.nan); avg[valid]=np.nanmean(vals[valid],axis=1)
            ax.plot(time,avg,lw=.8,label=f"{p['pairs'][pair,0]}–{p['pairs'][pair,1]}")
            dist.plot(time,p[f'{scope}_centroid_distance'][:,pair],lw=.8)
        ax.set(xlabel='Time (ms)',ylabel='Mean defined principal angle (degrees)',ylim=(-2,95)); dist.set(xlabel='Time (ms)',ylabel='Centroid Euclidean distance')
        letter(ax,'D' if j==0 else '',scope+' temporal separation'); letter(dist,'',scope+' centroids'); timeline(ax,d); timeline(dist,d)
        if j==0: ax.legend(ncol=3,fontsize=7)
    return fig,'A shows actual R3 trajectories in a single global whole-network PCA, using all six locations in each rule branch. B/C independently recompute principal angles and bidirectional cross-VAF from condition-centered 20 ms R3 decision-window states; within-VAF uses each branch’s full retained numerical rank. D computes each time point separately in whole-network, all Response, and shared non-Response coordinates. Singular values ≤ max(1e−8, largest×1e−8) are excluded; total variance ≤1e−8 yields NA, never zero angles. Centroid distances complement angle summaries. Disjoint handcrafted Response supports have zero structural overlap; orthogonality alone is not an emergent dynamical claim. Full spectra, ranks, indices and numerical values are archived.'


def fig6(d,p):
    fig=plt.figure(figsize=(14,10),layout='constrained'); gs=fig.add_gridspec(2,4)
    a=fig.add_subplot(gs[0,:2]); b=fig.add_subplot(gs[0,2:]); c=fig.add_subplot(gs[1,0]); c2=fig.add_subplot(gs[1,1]); rate=fig.add_subplot(gs[1,2]); margin=fig.add_subplot(gs[1,3])
    for i,xy in enumerate(p['pca_scores']):
        a.scatter(*xy,marker=['o','s','^','D','P','X'][i],s=65,label=f"position {p['expected_position'][i]}")
    pcalabel(a,p); a.legend(fontsize=8,ncol=2); letter(a,'A','Six real R3 states: D=+1, S=1')
    vmax=max(p['whole_rdm'].max(),p['response_rdm'].max())
    for ax,data,title in ((b,p['whole_rdm'],'B  Whole-network RDM'),(c,p['response_rdm'],'C  Response RDM'),(c2,p['whole_rdm'],'Whole-network RDM')):
        im=ax.imshow(data,vmin=0,vmax=vmax,cmap='viridis'); ax.set_xticks(range(6),p['expected_position']); ax.set_yticks(range(6),p['expected_position']); ax.set(xlabel='Represented position',ylabel='Represented position',title=title); fig.colorbar(im,ax=ax,shrink=.7,label='Euclidean distance')
    time=p['times_ms']; use=(time>=d['events'][0]['to_R3'])&(time<=d['events'][0]['readout3'])
    for i in range(6):
        color=plt.cm.tab10(i)
        rate.plot(time[use],p['selected_rate'][i,use],c=color,label=f"pos {p['expected_position'][i]}")
        rate.plot(time[use],p['competitor_rate'][i,use],c=color,ls=':',lw=.8)
        margin.plot(time[use],p['position_margin'][i,use],c=color)
    rate.set(xlabel='Time (ms)',ylabel='Dimensionless rate'); margin.set(xlabel='Time (ms)',ylabel='Selected − highest competitor'); letter(rate,'D','Position identity holding'); letter(margin,'','Selection margin')
    rate.legend(fontsize=7,ncol=2)
    return fig,'D=+1/S=1 is held fixed; the six initial locations yield six represented R3 positions. A fits PCA to six actual 132-D decision-window states and saves the mean and basis; no regular polygon or connecting loop is imposed. B/C use exact Euclidean distances in full and Response-only coordinates, with matched color limits. D shows selected-position rates (solid), maximum competitor (dotted), and selection margins during the R3 interval. The archive also contains argmax identity and full-state drift relative to readout3. This finite time interval tests maintained task states; it does not establish an autonomous attractor or a continuous ring manifold.'


def fig7(d,p):
    fig=plt.figure(figsize=(16,13),layout='constrained'); gs=fig.add_gridspec(4,3)
    bt=p['baseline__times_ms']; nt=p['noise__times_ms']
    for j,var in enumerate(('L','D','S')):
        ax=fig.add_subplot(gs[0,j]); chance=1/6 if var=='L' else .5
        for pop in ('whole','memory','response'): ax.plot(bt,p[f'baseline__{pop}__{var}'],label=pop)
        ax.axhline(chance,c='k',ls=':'); ax.set(xlabel='Time (ms)',ylabel='Accuracy',ylim=(0,1.04)); ax.legend(fontsize=7); letter(ax,'A' if j==0 else '',var+': disjoint task-condition folds'); timeline(ax,d)
    for j,var in enumerate(('D','S')):
        ax=fig.add_subplot(gs[1,j]); im=ax.imshow(p[f'baseline__cross_temporal__{var}'],origin='lower',aspect='auto',extent=[bt[0],bt[-1],bt[0],bt[-1]],vmin=0,vmax=1,cmap='viridis'); ax.set(xlabel='Test time (ms)',ylabel='Train time (ms)'); letter(ax,'B' if j==0 else '',var+' cross-temporal, whole network'); fig.colorbar(im,ax=ax,label='Accuracy')
    ax=fig.add_subplot(gs[1,2]); ax.plot(p['times_ms'],p['branch_accuracy'],c='#0072B2'); ax.axhline(.25,c='k',ls=':'); ax.set(xlabel='Time (ms)',ylabel='Accuracy',ylim=(0,1.04)); letter(ax,'','Response four-way D/S branch probe')
    for j,(var,mem,resp,start,end) in enumerate((('D','M_D','R2',1750,2400),('S','M_S','R3',2200,2900))):
        ax=fig.add_subplot(gs[2,j])
        for pop in (mem,resp): ax.plot(bt,p[f'baseline__{pop}__{var}'],label=pop)
        ax.axhline(.5,c='k',ls=':'); ax.set(xlim=(start,end),ylim=(0,1.04),xlabel='Time (ms)',ylabel='Accuracy'); ax.legend(); timeline(ax,d); letter(ax,'C' if j==0 else '',var+' handoff: held-out task conditions')
    ax=fig.add_subplot(gs[2,2]); ax.axis('off'); ax.text(0,1,'Two distinct questions\n\nBaseline: unseen LDS tuples\n\nNoise: seen tuples, unseen noise seed\n\nFour-way branch labels are defined\nonly after R3 transfer.\n\nLow memory amplitude can remain\nlinearly readable. No erasure claim.',va='top',fontsize=10)
    for j,var in enumerate(('L','D','S')):
        ax=fig.add_subplot(gs[3,j]); chance=1/6 if var=='L' else .5
        for k,seed in enumerate(p['noise__seed_ids']):
            ax.plot(nt,p[f'noise__response__{var}__seed_accuracies'][k],lw=.8,label=f'held seed {seed}')
            for stage in (2,3,4):
                target=d['events'][0][f'readout{stage}']; q=np.argmin(abs(nt-target)); ax.scatter(nt[q],p[f'noise__response__{var}__seed_accuracies'][k,q],s=18)
        ax.axhline(chance,c='k',ls=':'); ax.set(xlabel='Time (ms)',ylabel='Response accuracy',ylim=(0,1.04)); ax.legend(fontsize=7); letter(ax,'D' if j==0 else '',var+': independent noise realization')
    return fig,'A–C reuse nearest-centroid probes with stratified disjoint LDS-condition folds, fractional tie credit, and archived split identities. A plots whole, memory, and Response populations; B shows D/S cross-temporal accuracy; C zooms on memory-to-Response availability. The extra branch probe predicts four D/S branch labels from Response with disjoint condition folds, masked before R3 transfer. D separately reports each held-out noise seed (7/11/19) with all task tuples present in training; these are noise realizations, not independent networks or biological repeats. Chance is 1/6 (L), 1/2 (D/S), 1/4 (branch). Low rates may remain decodable; activity decay is not information erasure. No decoder feeds back to the network.'


RENDER={4:fig4,5:fig5,6:fig6,7:fig7}


def run(figures=(4,5,6,7), encodings=('one_hot',), output=Path('artifacts/neural_paper_figures_v1')):
    output=Path(output); outputs=[]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    for enc in encodings:
        result=build(enc,output,figures); d=result['dataset']; main='main' if enc=='one_hot' else 'supplementary'
        folder=output/'figures'/main; folder.mkdir(parents=True,exist_ok=True)
        manifests=output/'manifests'; manifests.mkdir(parents=True,exist_ok=True)
        for n,p in result['products'].items():
            fig,caption=RENDER[n](d,p); fig.suptitle(f'Figure {n} | {enc} | fixed E/I decompression',fontsize=15,fontweight='bold')
            paths=[]
            for ext in ('png','svg','pdf'):
                path=folder/f'fig{n:02d}_{enc}.{ext}'; fig.savefig(path,dpi=300,bbox_inches='tight'); paths.append(path)
            plt.close(fig)
            cap=folder/f'fig{n:02d}_{enc}_caption.md'; cap.write_text(caption+'\n',encoding='utf-8')
            source=[Path(__file__),Path(__file__).parents[1]/'evaluation/figure_data_geometry.py']
            manifest={'figure':n,'encoding':enc,'status':'NUMERIC_AND_RENDER_COMPLETE_PENDING_INDEPENDENT_REVIEW','rates_units':'dimensionless','input_sha256':{str(v):digest(v) for v in result['inputs']},'source_sha256':{str(v):digest(v) for v in source},'outputs_sha256':{str(v):digest(v) for v in [*paths,cap,*sorted((output/'derived'/enc).glob(f'fig{n:02d}*'))]},'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__},'events':d['events'][0],'config':d['config'],'preprocessing':'raw rates; center each fitted condition matrix; no neuron exclusion','independent_repeat_unit':'none for baseline; held-out input noise realization for noise probe','reference_scope':'method adaptation; original reference-panel visual verification remains separate'}
            dest=manifests/f'fig{n:02d}_{enc}.json'; dest.write_text(json.dumps(manifest,indent=2),encoding='utf-8'); outputs.append(str(dest))
    return outputs


if __name__=='__main__':
    run(encodings=('one_hot','ring','topology'))
