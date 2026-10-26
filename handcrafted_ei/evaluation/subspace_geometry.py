"""Centered sample subspaces, with shared coordinates and explicit support controls."""
from pathlib import Path
import numpy as np
from .population_activity import stage_samples,branch_masks,save_rows


def pca(x,center=True):
    x=np.asarray(x,dtype=float); mean=x.mean(0) if center else np.zeros(x.shape[1]); xc=x-mean
    _,s,vt=np.linalg.svd(xc,full_matrices=False); energy=s*s
    tolerance=max(x.shape)*np.finfo(float).eps*(s[0] if len(s) else 0)
    rank=int((s>tolerance).sum()); evr=energy/energy.sum() if energy.sum()>0 else np.zeros_like(energy)
    return {'mean':mean,'components':vt,'scores':xc@vt.T,'singular_values':s,'evr':evr,'rank':rank,
            'effective_dimension':float(1/(evr@evr)) if evr.sum() else 0.,
            'dim90':int(np.searchsorted(np.cumsum(evr),.9)+1) if rank else 0,
            'dim95':int(np.searchsorted(np.cumsum(evr),.95)+1) if rank else 0,
            'basis':vt[:rank].T}


def principal_angles(q1,q2):
    if q1.shape[0]!=q2.shape[0]: raise ValueError('neural coordinates must match')
    return np.degrees(np.arccos(np.clip(np.linalg.svd(q1.T@q2,compute_uv=False),0,1)))


def cross_vaf(x,q):
    xc=x-x.mean(0); total=float(np.sum(xc*xc))
    return float(np.sum((xc@q)**2)/total) if total>1e-24 else np.nan


def compare(x,y):
    a,b=pca(x),pca(y); qa,qb=a['basis'],b['basis']; angles=principal_angles(qa,qb)
    overlap=float(np.sum((qa.T@qb)**2))
    return {'angles':angles,'mean_angle':float(angles.mean()) if len(angles) else np.nan,
            'projection_overlap':overlap/min(a['rank'],b['rank']) if min(a['rank'],b['rank']) else np.nan,
            'cross_vaf_a_to_b':cross_vaf(y,qa),'cross_vaf_b_to_a':cross_vaf(x,qb),
            'subspace_distance':float(np.sqrt(max(0.,a['rank']+b['rank']-2*overlap)))}


def analyze(d,output_dir=None):
    r=np.asarray(d['rates']); stride=max(1,r.shape[1]//160)
    fit=pca(r[:,::stride,:].reshape(-1,r.shape[2])); comp=fit['components'][:3]
    scores=(r-fit['mean'])@comp.T
    variables=np.array([[np.cos(2*np.pi*t['L']/6),np.sin(2*np.pi*t['L']/6),t['D'],2*t['S']-3] for t in d['tasks']])
    # Descriptive condition-difference axes: fit jointly to time-averaged rates.
    variable_weights=np.linalg.lstsq(np.c_[np.ones(len(r)),variables],r.mean(1),rcond=None)[0][1:]
    lengths=np.linalg.norm(variable_weights,axis=1)
    variable_axes=np.divide(variable_weights,lengths[:,None],out=np.zeros_like(variable_weights),where=lengths[:,None]>1e-12)
    variable_scores=(r-fit['mean'])@variable_axes.T
    stages={}; rows=[]; pairs=[]; packed={'global_scores':scores,'global_components':comp,
                                         'variable_axes':variable_axes,'variable_scores':variable_scores,
                                         'global_mean':fit['mean'],'global_evr':fit['evr']}
    for s in range(1,5):
        x=stage_samples(d,s); masks=branch_masks(d,s); idx=np.asarray(d['groups'][f'R{s}']); branches=[]
        for b,mask in enumerate(masks):
            z=x[mask]; whole=pca(z); local=pca(z[:,idx]); folded=z[:,idx].reshape(len(z),-1,6).sum(1)
            # Condition split: parity of L, no reuse of samples across the two fits.
            loc=np.array([task['L'] for task in d['tasks']])[mask]
            stability=compare(z[loc%2==0],z[loc%2==1]) if (loc%2==0).sum()>1 and (loc%2==1).sum()>1 else None
            branches.append({'whole':whole,'response':local,'folded':pca(folded),'samples':z,'folded_samples':folded,'split':stability})
            rows.append({'stage':s,'branch':b,'n_samples':len(z),'n_neurons':r.shape[2],
                         'whole_rank':whole['rank'],'effective_dimension':whole['effective_dimension'],
                         'normalized_dimension':whole['effective_dimension']/r.shape[2],
                         'dim90':whole['dim90'],'dim95':whole['dim95'],'response_rank':local['rank'],
                         'split_overlap':stability['projection_overlap'] if stability else np.nan,
                         'split_note':'disjoint L parity; different sampled positions, not independent noise repeats'})
            packed[f'R{s}_b{b}_singular_values']=whole['singular_values']; packed[f'R{s}_b{b}_evr']=whole['evr']
        mat=np.eye(len(branches)); folded_mat=np.eye(len(branches)); angle_mat=np.zeros_like(mat)
        for a in range(len(branches)):
            for b in range(a+1,len(branches)):
                v=compare(branches[a]['samples'],branches[b]['samples']); folded=compare(branches[a]['folded_samples'],branches[b]['folded_samples'])
                mat[a,b]=mat[b,a]=v['projection_overlap']; folded_mat[a,b]=folded_mat[b,a]=folded['projection_overlap']; angle_mat[a,b]=angle_mat[b,a]=v['mean_angle']
                pairs.append({'stage':s,'branch_a':a,'branch_b':b,**{k:v[k] for k in v if k!='angles'},
                              'angles_degrees':';'.join(map(str,v['angles'])),'folded_overlap':folded['projection_overlap'],
                              'structural_support_overlap':0.})
        stages[s]={'branches':branches,'overlap':mat,'folded_overlap':folded_mat,'angles':angle_mat,'spectrum':pca(x)}
        packed[f'R{s}_overlap']=mat; packed[f'R{s}_folded_overlap']=folded_mat; packed[f'R{s}_angles']=angle_mat
    adjacent=[]
    for s in range(1,4):
        v=compare(stage_samples(d,s),stage_samples(d,s+1)); adjacent.append({'stage_a':s,'stage_b':s+1,**{k:v[k] for k in v if k!='angles'}})
    if output_dir:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
        save_rows(out/'subspace_geometry.csv',rows); save_rows(out/'subspace_pairs.csv',pairs); save_rows(out/'subspace_adjacent.csv',adjacent)
        np.savez_compressed(out/'subspace_geometry.npz',**packed)
    return {'global':fit,'scores':scores,'stages':stages,'rows':rows,'pairs':pairs,'adjacent':adjacent,
            'variable_axes':variable_axes,'variable_scores':variable_scores,'variable_names':['L_cos','L_sin','D','S'],
            'fit_stride':stride,'fit_scope':'all conditions, all neurons, uniform temporal subsample'}


def independent_seed_stability(datasets,output_dir=None):
    """Same-condition subspaces across independent input-noise realizations.

    All neuron labels and trial condition order must match; never align unmatched
    neural coordinates. Retain each sample matrix's 95%-VAF dimension, rather
    than expanding the subspace to include all tiny numerical/noise directions.
    """
    rows=[]
    for a in range(len(datasets)):
        for b in range(a+1,len(datasets)):
            da,db=datasets[a],datasets[b]
            if not np.array_equal(da['labels'],db['labels']): raise ValueError('seed neuron coordinates differ')
            key=lambda d:[(t['L'],t['D'],t['S']) for t in d['tasks']]
            if key(da)!=key(db): raise ValueError('seed condition ordering differs')
            for s in range(1,5):
                xa,xb=stage_samples(da,s),stage_samples(db,s)
                for branch,mask in enumerate(branch_masks(da,s)):
                    pa,pb=pca(xa[mask]),pca(xb[mask]); qa=pa['components'][:pa['dim95']].T; qb=pb['components'][:pb['dim95']].T
                    angles=principal_angles(qa,qb); den=min(qa.shape[1],qb.shape[1])
                    seed_a=da.get('protocol',{}).get('seed',da['tasks'][0].get('experiment_seed'))
                    seed_b=db.get('protocol',{}).get('seed',db['tasks'][0].get('experiment_seed'))
                    sigma=da.get('protocol',{}).get('noise_sigma_L',da['tasks'][0].get('sigma_L',np.nan))
                    rows.append({'stage':s,'branch':branch,'seed_a':seed_a,'seed_b':seed_b,
                                 'sigma':sigma,'dim95_a':qa.shape[1],'dim95_b':qb.shape[1],
                                 'projection_overlap':float(np.sum((qa.T@qb)**2)/den) if den else np.nan,
                                 'mean_angle':float(angles.mean()) if len(angles) else np.nan,
                                 'cross_vaf_a_to_b':cross_vaf(xb[mask],qa),'cross_vaf_b_to_a':cross_vaf(xa[mask],qb),
                                 'replicate_unit':'independent encoded-input noise realization; fixed network'})
    if output_dir: save_rows(Path(output_dir)/'subspace_seed_stability.csv',rows)
    return rows
