"""Source-style fixed-point portrait with full-state numerical evidence."""
from pathlib import Path
from hashlib import sha256
import json,platform,sys
import numpy as np
from .style import configure,save_figure,NAMES
import matplotlib.pyplot as plt
from ..evaluation.local_fixed_points import closed_pair,find_nodes
from ..evaluation.population_dynamics import evolve_batch,jacobian,field
from ..evaluation.reference_adapter import load_audited_dataset
from ..evaluation.reference_reproduction import ROOT,dump,csvwrite
from ..model.ei_network import EINetwork

DEFAULT=ROOT/'artifacts/local_fixed_points_v2'


def run(source,out=DEFAULT,modes=('one_hot','ring','topology')):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);configure();records=[];summary=[]
    for mode in modes:
        d=load_audited_dataset(source,mode);m=EINetwork(overrides=d['config']);m.remove_stimulus();m.clock[:]=0
        # Select an actually active response coordinate, without using task answers.
        idx=m.groups['R3'];activity=d['rates'][:,:,idx].max(axis=1);trial=int(activity.max(axis=1).argmax());local=int(activity[trial].argmax())
        q=int(idx[local]);z=int(m.groups['I_decay_S'][local]);high=m.rates.copy();high[[q,z]]=1
        high=evolve_batch(m,high[None],2000)[0,-1];nodes,rows=find_nodes(m,q,z,high)
        axis=np.linspace(0,1,101);xx,yy=np.meshgrid(axis,axis);xy=np.c_[xx.ravel(),yy.ravel()];pair=closed_pair(m,q,z,xy)
        if pair['nuisance_field_max']>1e-13:raise ValueError('silent upstream background is not invariant')
        eig,vec=np.linalg.eig(jacobian(m,nodes[1]));v=vec[:,eig.real.argmax()].real;v*=1 if v[q]>0 else -1;v/=np.max(abs(v))
        initial=nodes[1]+np.array([-1,1])[:,None]*1e-5*v
        if initial.min() < -1e-12 or initial.max()>1+1e-12:raise ValueError('unstable seed outside cube')
        initial=np.clip(initial,0,1);paths=evolve_batch(m,initial,1600);times=np.arange(paths.shape[1])*m.config['dt_ms']
        perturb=[];doses=[]
        for node in (0,2):
            for amp in (.001,.01,.03):
                for seed in (7,11,19):
                    delta=np.random.default_rng(seed).normal(size=len(m.rates));delta*=amp/np.sqrt(np.mean(delta**2))
                    raw=nodes[node]+delta;start=np.clip(raw,0,1);path=evolve_batch(m,start[None],1600)[0]
                    distance=np.linalg.norm(path-nodes[node],axis=1);perturb.append(distance)
                    doses.append(dict(node=node,seed=seed,requested_rms=amp,actual_rms=float(np.sqrt(np.mean((start-nodes[node])**2))),clipping_fraction=float(np.mean(raw!=start)),initial_distance=float(distance[0]),final_distance=float(distance[-1])))
        folder=out/mode;folder.mkdir(exist_ok=True)
        dump(folder/'config.json',d['config']);dump(folder/'nodes.json',rows);csvwrite(folder/'perturbations.csv',doses)
        np.savez_compressed(folder/'analysis.npz',nodes=nodes,grid=xy,velocity=pair['velocity'],unstable_paths=paths,times_ms=times,perturbation_distances=perturb,pair_indices=[q,z],full_jacobians=np.array([jacobian(m,r) for r in nodes]),full_eigenvalues=np.array([np.linalg.eigvals(jacobian(m,r)) for r in nodes]))
        fig,ax=plt.subplots(figsize=(6.2,6.2));velocity=pair['velocity'].reshape(101,101,2)
        ax.streamplot(axis,axis,velocity[:,:,0],velocity[:,:,1],color='#52758a',density=1.35,linewidth=.65,arrowsize=.85)
        # Analytic stable manifold of the CLOSED PAIR, not a full-state manifold.
        ax.plot([nodes[1,q]]*2,[0,1],color='#df2424',lw=2,label='Stable manifold (closed pair)')
        for start,end in ((.15,.33),(.97,.85)):
            ax.annotate('',xy=(nodes[1,q],end),xytext=(nodes[1,q],start),arrowprops=dict(arrowstyle='->',color='#df2424',lw=2))
        for path in paths:
            ax.plot(path[:,q],path[:,z],color='blue',lw=2.3)
            k=int(np.argmin(abs(path[:,q]-(.5 if path[-1,q]<.5 else .97))))
            ax.annotate('',xy=path[min(k+3,len(path)-1),[q,z]],xytext=path[max(0,k-3),[q,z]],arrowprops=dict(arrowstyle='->',color='blue',lw=2))
        ax.plot([],[],color='blue',lw=2.3,label='Unstable branches (full-state integration)')
        ax.scatter(nodes[[0,2],q],nodes[[0,2],z],s=105,c='blue',edgecolors='black',zorder=5,label='Full-state locally stable equilibria')
        ax.scatter(nodes[1,q],nodes[1,z],s=100,c='white',edgecolors='black',zorder=6,label='Full-state saddle')
        ax.annotate('Rest control',(.02,.02),xytext=(.10,.10),fontsize=9)
        ax.annotate('Held R3 state',(.99,.99),xytext=(.65,.94),fontsize=9)
        ax.annotate('Saddle',nodes[1,[q,z]],xytext=(.56,.72),arrowprops={'arrowstyle':'->'},fontsize=9)
        ax.set(xlim=(-.025,1.025),ylim=(-.025,1.025),xlabel='Selected R3 response rate (dimensionless)',ylabel='Paired I_decay_S rate (dimensionless)',title=NAMES[mode]+' | Local fixed-point stability')
        ax.set_aspect('equal');ax.legend(loc='upper left',fontsize=7,frameon=True)
        fig.text(.13,.015,'Sample = clock = 0; original tonic retained. Closed pair on silent upstream background.\nFilled points verified in all 132 states; two sinks shown are rest/held, not two positions.',fontsize=7)
        fig.subplots_adjust(bottom=.17)
        figs=[('fixed_point_portrait',fig)]
        fig,axs=plt.subplots(1,2,figsize=(9,3.5))
        for i,row in enumerate(doses):axs[0].semilogy(times,np.maximum(perturb[i],1e-18),color='blue' if row['node']==2 else '#888888',alpha=.5,lw=.8)
        axs[0].set(xlabel='Time after state perturbation (ms)',ylabel='Full 132-state distance',title='Finite probes: 3 doses × 3 seeds × 2 sinks')
        for i,r in enumerate(nodes):
            e=np.linalg.eigvals(jacobian(m,r));axs[1].scatter(e.real,e.imag,s=18,label=['Rest','Saddle','Held R3'][i],alpha=.6)
        axs[1].axvline(0,color='black',lw=.7);axs[1].set(xlabel='Real eigenvalue (1/ms)',ylabel='Imaginary eigenvalue (1/ms)',title='Full-state midpoint spectra; kink certificate separate');axs[1].legend()
        fig.tight_layout();figs.append(('stability_diagnostics',fig))
        for stem,figure in figs:
            files=save_figure(figure,folder,stem);records.append(dict(id=stem+'_'+mode,encoding=mode,paths=files,output_sha256={p:sha256(Path(p).read_bytes()).hexdigest() for p in files}))
        info=dict(encoding=mode,selected_recorded_trial=trial,pair_indices=[q,z],nuisance_field_max=pair['nuisance_field_max'],nodes=rows,archive_sha256=d['archive_sha256'],protected_sources=d['protected_source_identity'],max_final_probe_distance=max(r['final_distance'] for r in doses))
        summary.append(info);print(mode,[r['classification'] for r in rows],flush=True)
    dump(out/'summary.json',summary);dump(out/'figure_manifest.json',dict(figures=records))
    dump(out/'provenance.json',dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,seeds=[7,11,19],source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (ROOT/'handcrafted_ei').rglob('*.py')},source_figure='https://www.nature.com/articles/s41598-017-16994-y/figures/1',method='LDS adaptation; no author code execution; full rate field roots, generalized triangular local certificate; closed pair flow'))
    from .quality_check import check
    check(out)
