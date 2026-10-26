"""Balanced factorial effect energies and structural-versus-functional support."""
from itertools import combinations
from pathlib import Path
import numpy as np
from .population_activity import stage_samples,branch_masks,save_rows


def factorial_effects(x,tasks):
    """Exact orthogonal ANOVA on balanced 6x2x2 condition means; no p values."""
    x=np.asarray(x); means=np.empty((6,2,2,x.shape[-1])); ds=(1,-1)
    for l in range(6):
        for j,d in enumerate(ds):
            for k,s in enumerate((1,2)):
                mask=np.array([t['L']==l and t['D']==d and t['S']==s for t in tasks])
                if not mask.any(): raise ValueError('factorial analysis requires all 24 conditions')
                means[l,j,k]=x[mask].mean(0)
    grand=means.mean((0,1,2),keepdims=True); effects={}; energies={}
    for count in (1,2,3):
        for axes in combinations(range(3),count):
            keep=set(axes); other=tuple(i for i in range(3) if i not in keep)
            effect=means.mean(other,keepdims=True)-grand if other else means-grand
            for previous,value in effects.items():
                if set(previous)<keep: effect=effect-value
            effects[axes]=effect; name=':'.join('LDS'[i] for i in axes)
            energies[name]=np.broadcast_to(effect,means.shape).__pow__(2).mean((0,1,2))
    total=((means-grand)**2).mean((0,1,2))
    return {'energy':energies,'total':total,'fraction':{k:np.divide(v,total,out=np.zeros_like(v),where=total>1e-24) for k,v in energies.items()}}


def support_similarity(support):
    a=support.astype(float); inter=a.T@a; union=a.sum(0)[:,None]+a.sum(0)[None,:]-inter
    return np.divide(inter,union,out=np.full_like(inter,np.nan),where=union>0)


def analyze(d,output_dir=None,active_threshold=.1):
    rows=[]; effects=[]; stages={}; packed={}; n=len(d['labels'])
    for s in range(1,5):
        x=stage_samples(d,s)-np.asarray(d['rates'])[:,0,:]; masks=branch_masks(d,s)
        activity=np.stack([x[m].mean(0) for m in masks],axis=1)
        # Max across positions identifies participation; condition mean dilutes six-position tuning.
        functional=np.stack([(x[m]>active_threshold).any(0) for m in masks],axis=1)
        structural=np.zeros((n,len(masks)),dtype=bool)
        for b,idx in enumerate(np.asarray(d['groups'][f'R{s}']).reshape(-1,6)): structural[idx,b]=True
        overlap=support_similarity(functional); structural_overlap=support_similarity(structural)
        norm=np.linalg.norm(activity,axis=0); den=norm[:,None]*norm[None,:]
        cosine=np.divide(activity.T@activity,den,out=np.full_like(den,np.nan),where=den>1e-24)
        maxa=activity.max(1); select=np.divide(maxa-activity.mean(1),maxa,out=np.zeros(n),where=maxa>1e-24)
        anova=factorial_effects(x,d['tasks'])
        stages[s]={'activity':activity,'functional':functional,'structural':structural,'jaccard':overlap,
                   'structural_jaccard':structural_overlap,'cosine':cosine,'selectivity':select,'anova':anova,'condition_samples':x}
        for b in range(len(masks)):
            v=np.maximum(activity[:,b],0); pr=float(v.sum()**2/(v@v)) if v@v else 0
            rows.append({'stage':s,'branch':b,'whole_active_fraction':float(functional[:,b].mean()),
                         'response_support_size':int(structural[:,b].sum()),'functional_support_size':int(functional[:,b].sum()),
                         'activity_participation_ratio':pr,'structural_precision':float(functional[structural[:,b],b].mean())})
        for i,label in enumerate(d['labels']):
            effects.append({'stage':s,'neuron':label,'total_variance':float(anova['total'][i]),
                            **{name:float(value[i]) for name,value in anova['fraction'].items()}})
        for name,v in {'activity':activity,'functional':functional,'structural':structural,'jaccard':overlap,'cosine':cosine,'selectivity':select}.items(): packed[f'R{s}_{name}']=v
    if output_dir:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); save_rows(out/'recruitment.csv',rows); save_rows(out/'selectivity.csv',effects); np.savez_compressed(out/'recruitment.npz',**packed)
    return {'stages':stages,'rows':rows,'effect_rows':effects,'active_threshold':active_threshold,
            'structural_definition':'direct Response branch support from connectivity group ordering; excludes shared downstream and background units'}
