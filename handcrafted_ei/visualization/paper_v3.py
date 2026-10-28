"""Rebuild v3 paper figures from audited recordings and independent assays."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from ..evaluation.paper_figure_v3_geometry import build, PAIRS, project_energy
from ..evaluation.figure_data_geometry import load
from ..evaluation.figure_data_dynamics import REF
from ..evaluation.population_data import source_identity
from .style import configure, save_figure, panels, timeline

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/neural_paper_figures_v3'
OLD=ROOT/'artifacts/neural_paper_figures_v1'
MODES=('one_hot','ring','topology')
COLORS=['#0072B2','#56B4E9','#D55E00','#CC79A7']
MARKERS=['o','s','^','D','P','X']
CLASS_COLORS=['#009E73','#CC79A7','#E69F00','#999999','#222222']


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def rows(path):
    with Path(path).open(encoding='utf-8') as f:return list(csv.DictReader(f))


def kick_outcome(row):
    if row['full_state_recovered']=='True':return 'full-state recovered'
    if row['original_position_retained']=='True':return 'same position; state differs'
    if row['position_switch']=='True':return 'position switch'
    return {'rest':'R3-inactive','multiple_positions':'multiple positions','outside_branch':'outside branch','unconverged':'unconverged'}[row['endpoint_class']]


def kick_panel(ax,folder,ids):
    data=[r for r in rows(folder/'fig09_state_kick_classification.csv') if r['target']=='full' and int(r['trial']) in ids]
    doses=sorted({float(r['amplitude_preclip']) for r in data})
    for kind in ('full-state recovered','same position; state differs','position switch','multiple positions','outside branch','R3-inactive','unconverged'):
        groups=[[r for r in data if float(r['amplitude_preclip'])==v] for v in doses]
        x=[np.mean([float(r['actual_whole_rms_after_clip']) for r in group]) for group in groups]
        ax.plot(x,[np.mean([kick_outcome(r)==kind for r in group]) for group in groups],'o-',ms=3,lw=.8,label=kind)
    ax.set(xlabel='Mean actual postclip state-kick RMS (rate)',ylabel='Fraction of 6 positions × 3 directions',ylim=(-.03,1.03));ax.legend(fontsize=6,ncol=2)


def reuse(output):
    """Copy validated reusable arrays/figures, retaining their explicit origin."""
    old=json.loads((OLD/'figure_manifest.json').read_text(encoding='utf-8'))['files']
    selected=[]
    for folder in ('derived','figures'):
        for p in sorted((OLD/folder).rglob('*')):
            if not p.is_file() or not any(p.name.startswith(f'fig{n:02}') for n in (1,2,3,6,7,10)):continue
            rel=p.relative_to(OLD); key=str(rel).replace('\\','/')
            if key not in old or digest(p)!=old[key]:raise ValueError('unverified reusable artifact '+str(p))
            dest=output/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():shutil.copy2(p,dest)
            selected.append(dict(source=str(p.relative_to(ROOT)),destination=str(rel).replace('\\','/'),sha256=old[key]))
    (output/'manifests/reused_artifacts.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')


def events(ax,d):timeline(ax,d['events'][0],False)


def fig4(d,p):
    fig=plt.figure(figsize=(13,11),layout='constrained');gs=fig.add_gridspec(3,3)
    a=fig.add_subplot(gs[0,:2]);b=fig.add_subplot(gs[0,2]);cs=[fig.add_subplot(gs[1,k]) for k in range(3)];v=fig.add_subplot(gs[2,:2]);distance=fig.add_subplot(gs[2,2])
    t=d['times_ms']; x=p['global_scores']; z=p['branch_scores']; fixed=p['fixed_L_trials']
    for i,task in enumerate(d['tasks']):
        br=(task['D']==-1)*2+task['S']-1
        a.plot(*x[i,:,:2].T,lw=.55,alpha=.55,color=COLORS[br])
        for stage in range(1,5):
            j=np.argmin(abs(t-d['events'][i][f'readout{stage}']));a.scatter(*x[i,j,:2],s=9,marker=MARKERS[stage-1],color=COLORS[br])
    for i in fixed:
        task=d['tasks'][i];br=(task['D']==-1)*2+task['S']-1; label=f"D={task['D']:+}, S={task['S']}"
        b.plot(*z[i,:,:2].T,color=COLORS[br],lw=1,label=label)
        for c,stage in zip(cs,(2,3,4)):
            mask=(t>=d['events'][i][f'to_R{stage}'])&(t<=d['events'][i][f'readout{stage}'])
            c.plot(*z[i,mask,:2].T,color=COLORS[br],lw=1)
            q=z[i,mask,:2];c.scatter(*q[-1],s=23,marker=MARKERS[stage-1],color=COLORS[br]);c.scatter(*q[::12].T,s=3,color=COLORS[br])
        v.plot(p['speed_times_ms'],p['speed'][i],lw=.9,color=COLORS[br],label=label)
    a.set(title='A  24 conditions; markers = readout 1–4',xlabel=f"Global PC1 ({100*p['global_evr'][0]:.1f}%)",ylabel=f"Global PC2 ({100*p['global_evr'][1]:.1f}%)")
    for ax in (b,*cs):ax.set(xlabel=f"Branch axis 1 ({100*p['branch_contrast_evr'][0]:.1f}% contrast variance)",ylabel=f"Branch axis 2 ({100*p['branch_contrast_evr'][1]:.1f}%)")
    from matplotlib.lines import Line2D
    a.legend(handles=[Line2D([],[],ls='',marker=MARKERS[k],c='.3',label=f'Readout {k+1}') for k in range(4)],ncol=4,fontsize=7,loc='upper left')
    b.set_title('B  Fixed L=0: branch-discriminant projection');b.legend(fontsize=7)
    b.text(.03,.03,f"2-D capture of R3 branch variance: {100*float(p['R3_branch_variance_captured_2d']):.1f}%",transform=b.transAxes,fontsize=6)
    for c,stage in zip(cs,(2,3,4)):c.set(title=f'C  R{stage}, same fixed branch axes',xlim=b.get_xlim(),ylim=b.get_ylim())
    v.set(title='D  Speed in all 132 neural coordinates',xlabel='Time (ms)',ylabel='Euclidean speed (dimensionless rate / ms)');events(v,d);v.legend(ncol=2,fontsize=7)
    v.text(.99,.97,'green: gate  |  gray dotted: readout  |  pink dashed: retire',ha='right',va='top',transform=v.transAxes,fontsize=6)
    distance.plot(range(6),p['R3_centroid_distances'],'o',color='#0072B2');distance.set(xticks=range(6),xticklabels=[f'{a}–{b}' for a,b in PAIRS],title='R3 branch-centroid separation',xlabel='D/S branch pair',ylabel='132-D Euclidean distance')
    fig.suptitle('Decompression trajectories and branch selection | '+d['encoding_type'])
    return fig


def fig5(d,p,g,records):
    fig=plt.figure(figsize=(14,10),layout='constrained');gs=fig.add_gridspec(3,3)
    a,b,c=[fig.add_subplot(gs[0,k]) for k in range(3)];t=d['times_ms'];w=(t>=d['events'][0]['to_R3'])&(t<=d['events'][0]['readout3'])
    for i,task in enumerate(d['tasks']):
        br=(task['D']==-1)*2+task['S']-1;q=p['global_scores'][i,w,:2]
        a.plot(*q.T,c=COLORS[br],lw=.5,alpha=.7);a.scatter(*q[-1],c=COLORS[br],marker=MARKERS[task['L']],s=15)
    a.set(title='A  R3 four branches × six positions',xlabel=f"Global PC1 ({100*p['global_evr'][0]:.1f}%)",ylabel=f"Global PC2 ({100*p['global_evr'][1]:.1f}%)")
    a.text(.02,.02,'Overlapping branches/positions in this 2-D projection\nFull-state geometry shown in B–D',transform=a.transAxes,fontsize=7)
    for k,row in enumerate(records):
        angle=np.fromstring(row['angles_degrees'],sep=';');b.plot(np.arange(1,len(angle)+1),angle,'o-',ms=3,lw=.8,label=f"{row['branch_a']}–{row['branch_b']}")
        c.plot([k-.12,k+.12],[float(row['cross_vaf_a_to_b']),float(row['cross_vaf_b_to_a'])],'o-',ms=4,lw=.7)
    b.set(title='B  Archived full principal-angle spectra',xlabel='Principal-angle index (defined dimensions)',ylabel='Principal angle (degrees)',ylim=(0,90.8));b.legend(fontsize=6,ncol=2)
    c.set(title='C  Both projection directions',xlabel='Branch pair: a→b / b→a',ylabel='Captured target variance fraction',xticks=range(6),xticklabels=[f'{a}–{b}' for a,b in PAIRS],ylim=(-.03,1.04))
    for col,name in enumerate(('whole','response','folded')):
        angle=fig.add_subplot(gs[1,col]);dist=fig.add_subplot(gs[2,col]);vals=g[name+'_angles_degrees']
        for k in range(6):
            count=np.isfinite(vals[:,k]).sum(1); avg=np.divide(np.nansum(vals[:,k],axis=1),count,out=np.full(len(t),np.nan),where=count>0)
            angle.plot(t,avg,lw=.7);dist.plot(t,g[name+'_centroid_distance'][:,k],lw=.7)
        angle.set(title='D  '+name+' coordinates',xlabel='Time (ms)',ylabel='Mean defined angle (degrees)',ylim=(-2,92));dist.set(xlabel='Time (ms)',ylabel=('Folded Euclidean distance' if name=='folded' else ('132-D Euclidean distance' if name=='whole' else 'Response Euclidean distance')))
        if name=='folded' and np.max(g[name+'_centroid_distance'])<1e-12:
            dist.set_ylim(0,1);dist.text(.03,.85,'All distances < 10⁻¹²\nNumerical zero',transform=dist.transAxes,fontsize=8)
        if col==0:angle.text(.02,.94,'Pair colors follow panel B; pre-R3 angles may reflect R1/R2',transform=angle.transAxes,va='top',fontsize=6)
        events(angle,d);events(dist,d)
    fig.suptitle('Branch geometry: angle spectra, variance transfer and temporal separation | '+d['encoding_type'])
    return fig


def fig8(mode,output,branch=0):
    d=load(mode);model_groups=d['groups'];folder=output/'derived'/mode
    with np.load(REF/mode/'fixed_points.npz') as z:points=z['endpoints'];cond=z['conditions']
    ids=np.flatnonzero((cond[:,1]==(1,1,-1,-1)[branch])&(cond[:,2]==(1,2,1,2)[branch]));ids=ids[np.argsort(cond[ids,0])]
    fit=points[ids];mu=fit.mean(0);_,s,vt=np.linalg.svd(fit-mu,full_matrices=False);q=vt[:3].T;evr=s*s/np.sum(s*s)
    np.savez_compressed(folder/f'fig08_six_position_fixed_points_branch{branch}.npz',endpoints=fit,conditions=cond[ids],center=mu,basis=q,evr=evr)
    fig,axes=plt.subplots(2,3,figsize=(14,9),layout='constrained');ax=axes.ravel();panels(ax)
    for n,point in enumerate(fit):ax[0].scatter(*((point-mu)@q[:,:2]),marker=MARKERS[n],s=55,label=f'L={n}')
    ax[0].set(title=f'Branch {branch}: six actual endpoints',xlabel=f'Endpoint PC1 ({100*evr[0]:.1f}%)',ylabel=f'Endpoint PC2 ({100*evr[1]:.1f}%)');ax[0].legend(ncol=2)
    with np.load(REF/mode/'basin_full.npz') as z:
        all_paths=z['rates'];reference_index=z['initial_reference_index'];amplitudes=z['amplitude']
        from ..evaluation.paper_v3_dynamics import classify
        from ..model.ei_network import EINetwork
        model=EINetwork(overrides=d['config'])
        for n,trial in enumerate(ids):
            cand=np.flatnonzero((reference_index==trial)&np.isclose(amplitudes,.1))[:3]
            for index in cand:
                path=all_paths[index];xy=(path-mu)@q[:,:2];ax[1].plot(*xy.T,lw=.7,color=plt.cm.tab10(n));ax[1].scatter(*xy[0],s=12,marker='x',color=plt.cm.tab10(n));category=classify(model,path[-1],3,branch)
                ax[1].scatter(*xy[-1],s=24,marker=MARKERS[n] if category['class_code']==0 else 'o',edgecolor=plt.cm.tab10(n) if category['class_code']==0 else 'black',facecolor=plt.cm.tab10(n) if category['class_code']==0 else 'none')
    ax[1].set(title='True kick relaxation; colors = original L',xlabel='Same endpoint PC1',ylabel='Same endpoint PC2')
    ax[1].text(.02,.02,'× initial; hollow black = R3-inactive/other endpoint',transform=ax[1].transAxes,fontsize=6)
    with np.load(folder/'fig08_basin_slices_v3.npz') as z:
        grid=z['grid_axis'];code=z['class_code'][branch,0];cmap=ListedColormap(['#eeeeee',*CLASS_COLORS]);norm=BoundaryNorm(np.arange(-1.5,5.5),6)
        image=ax[2].imshow(code.reshape(len(grid),len(grid)),origin='lower',extent=[grid[0],grid[-1],grid[0],grid[-1]],cmap=cmap,norm=norm,interpolation='nearest')
        ax[2].set(title='2-D initial-state slice: L=(0,1,2)',xlabel='α, endpoint difference',ylabel='β, endpoint difference');cb=fig.colorbar(image,ax=ax[2],ticks=np.arange(-1,5),shrink=.7);cb.ax.set_yticklabels(['invalid','single','multiple','outside','R3-inactive','unconverged'])
    cert=rows(folder/'fig08_v3_fixed_point_certificates.csv');cert=[r for r in cert if int(r['trial']) in ids]
    ax[3].plot(range(6),[float(r['residual_max_per_ms']) for r in cert],'o');ax[3].set(title='Complete 132-D field residual',xlabel='L',ylabel='Max |dr/dt| (rate / ms)');ax[3].axhline(1e-7,ls=':',c='.5')
    ax[4].plot(range(6),[float(r['max_real_eigenvalue_per_ms']) for r in cert],'o-',label='max Re λ (ms⁻¹)');other=ax[4].twinx();other.plot(range(6),[float(r['euler_spectral_radius']) for r in cert],'s--',color='#D55E00',label='Euler radius');ax[4].set(title='Local spectrum; clip-kink certificate separate',xlabel='L',ylabel='Max Re λ (ms⁻¹)');other.set_ylabel('Euler spectral radius')
    kick_panel(ax[5],folder,ids);ax[5].set_title('State kicks: full recovery vs endpoint identity')
    fig.suptitle(f'Six-position equilibria and mixed-state basins | {mode}, R3 branch {branch}; sample=clock=0, tonic retained')
    return fig


def fig9(mode,output,assay='source_time'):
    folder=output/'derived'/mode;fig,axes=plt.subplots(2,3,figsize=(14,9),layout='constrained');ax=axes.ravel();panels(ax)
    with np.load(REF/mode/f'input_{assay}_7.npz') as z:
        ctrl=z['control'];pert=z['perturbed'];t=z['times_ms'];q=z['basis'];center=z['pca_center'];projected=(ctrl-center)@q;pp=(pert-center)@q
        chosen=np.argsort(np.max(abs(pert-ctrl),axis=0))[-3:]
        for i in chosen:ax[0].plot(t,ctrl[:,i],lw=.8,label=f'n{i} control');ax[0].plot(t,pert[:,i],lw=.8,ls='--',label=f'n{i} pulse')
        ax[0].set(title='Representative affected neurons (post hoc)',xlabel='Time (ms)',ylabel='Dimensionless rate');ax[0].legend(ncol=2,fontsize=6)
        ax[1].plot(*projected[:,:2].T,c='#0072B2',lw=1,label='control');ax[1].plot(*pp[:,:2].T,c='#D55E00',lw=1,ls='--',label='50 ms input pulse');ax[1].scatter(*pp[-1,:2],c='#D55E00',marker='s',s=20)
        energy=np.sum((ctrl-center)**2,axis=0).sum();ev=np.sum(projected**2,axis=0)/energy
        ax[1].set(title='Common control-only PCA',xlabel=f'PC1 ({100*ev[0]:.1f}% control energy)',ylabel=f'PC2 ({100*ev[1]:.1f}% control energy)');ax[1].legend()
        ct=z['cross_temporal_times_ms'];im=ax[2].imshow(z['cross_temporal_distance'],origin='lower',aspect='auto',extent=[ct[0],ct[-1],ct[0],ct[-1]],cmap='viridis');fig.colorbar(im,ax=ax[2],label='132-D Euclidean distance');ax[2].set(title='Full-state cross-temporal distance',xlabel='Perturbed time (ms)',ylabel='Control time (ms)')
        full,inside,outside=project_energy(pert-ctrl,q[:,:2]);np.testing.assert_allclose(full,inside+outside,atol=1e-10)
        for y,label,ls in [(full,'full132','-'),(inside,'PC1/2','--'),(outside,'orthogonal complement',':')]:ax[3].plot(t,np.sqrt(y),label=label,ls=ls)
        ax[3].set(title='Errors inside and outside displayed plane',xlabel='Time (ms)',ylabel='Euclidean distance (rate)');ax[3].legend()
        pulse=z['pulse_mask'];onset=t[np.flatnonzero(pulse)[0]]-np.diff(t)[0];offset=t[np.flatnonzero(pulse)[-1]]
        for axis in (ax[0],ax[3]):axis.axvspan(onset,offset,color='#D55E00',alpha=.12)
        ax[1].scatter(*pp[np.flatnonzero(pulse)[0]-1,:2],marker='o',s=20,c='#D55E00',label='pulse onset');ax[1].scatter(*pp[np.flatnonzero(pulse)[-1],:2],marker='x',s=20,c='#D55E00',label='pulse offset');ax[1].legend(fontsize=6)
    d=load(mode);ids=[i for i,task in enumerate(d['tasks']) if task['D']==1 and task['S']==1]
    kick_panel(ax[4],folder,ids);ax[4].set_title('Separate state-kick protocol, R3 branch 0')
    stage=rows(folder/'fig09_perturbation_classification.csv');names=list(dict.fromkeys(r['stage'] for r in stage));cats=list(dict.fromkeys(r['endpoint_outcome'] for r in stage));bottom=np.zeros(len(names))
    for k,cat in enumerate(cats):
        vals=np.array([np.mean([r['endpoint_outcome']==cat for r in stage if r['stage']==n]) for n in names]);ax[5].bar(np.arange(len(names)),vals,bottom=bottom,label=('R4-inactive' if cat=='rest' else cat.replace('_',' ')),color=plt.cm.Set2(k));bottom+=vals
    ax[5].set(title='Four task-time pulse windows',xticks=range(4),xticklabels=['pre R2','post R2','pre R3','post R3'],ylabel='Fraction of 24 conditions × 3 directions',ylim=(0,1.05));ax[5].legend(fontsize=6,loc='lower left')
    fig.suptitle(f'Perturbation, position competition and full-state recovery | {mode} | {assay}')
    return fig


def supplements(mode,output,p):
    d=load(mode);dest=output/'figures/supplementary';fig=plt.figure(figsize=(8,6),layout='constrained');ax=fig.add_subplot(projection='3d')
    for i,task in enumerate(d['tasks']):ax.plot(*p['global_scores'][i,:,:3].T,lw=.55,alpha=.6,color=COLORS[(task['D']==-1)*2+task['S']-1])
    ax.set(xlabel=f"PC1 ({100*p['global_evr'][0]:.1f}%)",ylabel=f"PC2 ({100*p['global_evr'][1]:.1f}%)",zlabel=f"PC3 ({100*p['global_evr'][2]:.1f}%)",title='All 24 trajectories; one common global PCA')
    save_figure(fig,dest,f'fig04_{mode}_global3d')
    with np.load(output/'derived'/mode/'fig08_basin_slices_v3.npz') as z:
        fig,axes=plt.subplots(4,3,figsize=(12,13),layout='constrained');grid=z['grid_axis']
        for b in range(4):
            for s in range(3):
                ax=axes[b,s];image=ax.imshow(z['class_code'][b,s].reshape(len(grid),len(grid)),origin='lower',extent=[grid[0],grid[-1],grid[0],grid[-1]],cmap=ListedColormap(['#eeeeee',*CLASS_COLORS]),norm=BoundaryNorm(np.arange(-1.5,5.5),6),interpolation='nearest');ax.set(title=f"Branch {b}, L={tuple(map(int,z['triples'][s]))}",xlabel='α',ylabel='β')
        cb=fig.colorbar(image,ax=axes.ravel().tolist(),ticks=np.arange(-1,5),shrink=.55);cb.ax.set_yticklabels(['invalid','single','multiple','outside','R3-inactive','unconverged']);fig.suptitle('Multiple 2-D initial-state sections of the complete 132-D system; invalid states masked')
        save_figure(fig,dest,f'fig08_{mode}_multiple_slices')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
    for ax,stage in zip(axes,(2,3,4)):
        start=d['events'][0][f'to_R{stage}'];mask=(p['speed_times_ms']>=start-100)&(p['speed_times_ms']<=start+200)
        for i in p['fixed_L_trials']:ax.plot(p['speed_times_ms'][mask],p['speed'][i,mask],lw=.9)
        ax.set(title=f'R{stage} transition',xlabel='Time (ms)',ylabel='132-D speed (rate / ms)');events(ax,d)
    save_figure(fig,dest,f'fig04_{mode}_transition_speed_zooms')
    with np.load(REF/mode/'fixed_points.npz') as z:points=z['endpoints'];cond=z['conditions']
    fig=plt.figure(figsize=(12,10),layout='constrained')
    for branch,(dr,step) in enumerate(((1,1),(1,2),(-1,1),(-1,2))):
        ax=fig.add_subplot(2,2,branch+1,projection='3d');ids=np.flatnonzero((cond[:,1]==dr)&(cond[:,2]==step));x=points[ids];mu=x.mean(0);_,s,vt=np.linalg.svd(x-mu,full_matrices=False);ev=s*s/np.sum(s*s);xy=(x-mu)@vt[:3].T
        for i,coord in enumerate(xy):ax.scatter(*coord,marker=MARKERS[i],s=40,label=f'L={cond[ids[i],0]}')
        ax.set(title=f'R3 branch {branch}, D={dr:+}, S={step}',xlabel=f'PC1 ({ev[0]*100:.1f}%)',ylabel=f'PC2 ({ev[1]*100:.1f}%)',zlabel=f'PC3 ({ev[2]*100:.1f}%)');ax.legend(fontsize=6,ncol=2)
    save_figure(fig,dest,f'fig08_{mode}_six_endpoints_3d')


def run(output=OUT,modes=MODES,geometry=True,dynamics=True,reusable=True):
    output=Path(output); configure();(output/'manifests').mkdir(parents=True,exist_ok=True)
    source_identity(ROOT/'handcrafted_ei/artifacts/v2/run')
    if reusable:reuse(output)
    for mode in modes:
        destination=output/'figures'/('main' if mode=='one_hot' else 'supplementary')
        if geometry:
            d,p,g,records=build(mode,output);save_figure(fig4(d,p),destination,f'fig04_{mode}_decompression_trajectories');save_figure(fig5(d,p,g,records),destination,f'fig05_{mode}_branch_subspaces')
        else:
            with np.load(output/'derived'/mode/'fig04_trajectories.npz') as z:p={k:z[k] for k in z.files}
        if dynamics:
            for branch in range(4):save_figure(fig8(mode,output,branch),destination if branch==0 else output/'figures/supplementary',f'fig08_{mode}_six_point_attractors_branch{branch}')
            for assay in ('source_time','R3_fixed_clock'):save_figure(fig9(mode,output,assay),destination if assay=='source_time' else output/'figures/supplementary',f'fig09_{mode}_perturbation_dynamics_{assay}')
            supplements(mode,output,p)
        print('rendered',mode,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=OUT);p.add_argument('--encodings',nargs='+',default=list(MODES));p.add_argument('--geometry-only',action='store_true');p.add_argument('--dynamics-only',action='store_true');p.add_argument('--no-reuse',action='store_true');p.add_argument('--rebuild-reused',action='store_true',help='Recompute Figures1/2/3/6/7/10 directly from formal recordings into the chosen output; does not require the v1 figure archive')
    a=p.parse_args()
    if a.rebuild_reused:
        from .paper_figures import run as rebuild
        rebuild(figures=(1,2,3,6,7,10),encodings=tuple(a.encodings),output=a.output)
    run(a.output,a.encodings,not a.dynamics_only,not a.geometry_only,not(a.no_reuse or a.rebuild_reused))
