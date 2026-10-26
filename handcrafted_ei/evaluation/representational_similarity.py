"""Six-position RDMs. Constant distances remain undefined, never replaced by zero."""
from itertools import permutations
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist,squareform
from scipy.stats import rankdata
from .population_activity import stage_samples,branch_masks,save_rows


def ring_distance(n=6):
    d=np.abs(np.arange(n)[:,None]-np.arange(n)[None,:]); return np.minimum(d,n-d)


def safe_correlation(a,b):
    a=np.asarray(a); b=np.asarray(b)
    if not np.isfinite(a).all() or not np.isfinite(b).all() or np.ptp(a)<1e-10 or np.ptp(b)<1e-10: return np.nan
    # Numerically equal distances must remain tied (e.g. six exact circle points).
    a=np.round(a/max(1.,np.max(np.abs(a))),12); b=np.round(b/max(1.,np.max(np.abs(b))),12)
    return float(np.corrcoef(rankdata(a),rankdata(b))[0,1])


def rdm(x,metric='euclidean'):
    x=np.asarray(x,float)
    if metric=='correlation': x=x-x.mean(1,keepdims=True); metric='cosine'
    if metric=='cosine':
        norms=np.linalg.norm(x,axis=1); den=norms[:,None]*norms[None,:]
        out=np.full(den.shape,np.nan); np.divide(x@x.T,den,out=out,where=den>1e-24); out=1-out
        np.fill_diagonal(out,0.); return np.clip(out,0,2)
    return squareform(pdist(x,metric))


def classical_mds(distance,dimensions=2):
    n=len(distance); h=np.eye(n)-np.ones((n,n))/n
    values,vectors=np.linalg.eigh(-.5*h@(distance**2)@h); order=np.argsort(values)[::-1]
    values=values[order]; vectors=vectors[:,order]
    coords=vectors[:,:dimensions]*np.sqrt(np.maximum(values[:dimensions],0))
    reconstructed=rdm(coords); denom=np.sum(distance**2)
    stress=float(np.sqrt(np.sum((distance-reconstructed)**2)/denom)) if denom>0 else np.nan
    return coords,stress,values


def topology_metrics(distance):
    upper=np.triu_indices(6,1); ring=ring_distance(); chord=2*np.sin(np.pi*ring/6)
    observed=safe_correlation(distance[upper],ring[upper]); permutations_values=[]
    if np.isfinite(observed):
        for order in permutations(range(6)):
            perm=distance[np.ix_(order,order)]
            permutations_values.append(safe_correlation(perm[upper],ring[upper]))
    null=np.asarray(permutations_values)
    # Ties receive fractional nearest-neighbor credit, so equidistant codes score chance (2/5).
    credits=[]
    for p in range(6):
        candidates=np.delete(np.arange(6),p); values=distance[p,candidates]; smallest=np.partition(values,1)[1]
        strict=values<smallest-1e-10; tied=np.isclose(values,smallest,atol=1e-10,rtol=1e-10)
        weights=strict.astype(float); weights[tied]=(2-strict.sum())/max(1,tied.sum())
        credits.append(float(weights[ring[p,candidates]==1].sum()/2))
    off=distance[upper]; mean_off=float(off.mean()); contrast=float(distance[ring==3].mean()-distance[ring==1].mean())
    return {'ring_spearman':observed,'chord_spearman':safe_correlation(distance[upper],chord[upper]),
            'permutation_p':float(np.mean(null>=observed-1e-12)) if len(null) else np.nan,
            'adjacency_accuracy':float(np.mean(credits)),
            'opposite_minus_adjacent':contrast,
            'offdiagonal_min':float(off.min()),'offdiagonal_max':float(off.max()),'offdiagonal_mean':mean_off,
            'offdiagonal_range_over_mean':float(np.ptp(off)/mean_off) if mean_off>1e-24 else np.nan,
            'relative_opposite_minus_adjacent':contrast/mean_off if mean_off>1e-24 else np.nan,
            'permutation_count':len(null),'undefined_reason':'constant off-diagonal distances' if not np.isfinite(observed) else '',
            'null':null}


def analyze(d,output_dir=None):
    rows=[]; response_rows=[]; contribution_rows=[]; panels={}; packed={}; response_packed={}; tasks=d['tasks']; initial_locations=np.array([x['L'] for x in tasks])
    all_response=np.concatenate([d['groups'][f'R{k}'] for k in range(1,5)])
    for s in range(1,5):
        samples=stage_samples(d,s)
        locations=np.asarray(d['outputs'])[:,s-1] if 'outputs' in d else initial_locations
        for b,mask in enumerate(branch_masks(d,s)):
            means=np.stack([samples[mask&(locations==p)].mean(0) for p in range(6)])
            distances={m:rdm(means,m) for m in ('euclidean','cosine','correlation')}
            xy,stress,eigen=classical_mds(distances['euclidean']); metrics=topology_metrics(distances['euclidean'])
            response_means=means[:,d['groups'][f'R{s}']]
            response_distances={m:rdm(response_means,m) for m in ('euclidean','cosine','correlation')}
            response_xy,response_stress,_=classical_mds(response_distances['euclidean'])
            response_metrics=topology_metrics(response_distances['euclidean'])
            all_response_distance=rdm(means[:,all_response]); all_response_metrics=topology_metrics(all_response_distance)
            panels[(s,b)]={'means':means,'rdm':distances,'mds':xy,'stress':stress,'metrics':metrics,
                           'response_rdm':response_distances,'response_mds':response_xy,'response_metrics':response_metrics,
                           'response_stress':response_stress,'response_definition':'all branches of current Response stage',
                           'all_response_rdm':all_response_distance,'all_response_metrics':all_response_metrics}
            rows.append({'stage':s,'branch':b,'neuron_count':means.shape[1],'metric':'Euclidean; no neural normalization',
                         **{k:v for k,v in metrics.items() if k!='null'},'mds_stress':stress,
                         'position_label':'observed current readout' if 'outputs' in d else 'initial input L (fixed-branch permutation preserves distances)'})
            for name,array in {**distances,'mds':xy,'means':means,'permutation_null':metrics['null']}.items(): packed[f'R{s}_b{b}_{name}']=array
            response_rows.append({'stage':s,'branch':b,'neuron_count':response_means.shape[1],
                                  'population':f'current stage R{s}, all candidate branches','metric':'Euclidean; no neural normalization',
                                  **{k:v for k,v in response_metrics.items() if k!='null'},'mds_stress':response_stress,
                                  'all_response_ring_spearman':all_response_metrics['ring_spearman'],
                                  'all_response_relative_contrast':all_response_metrics['relative_opposite_minus_adjacent']})
            for name,array in {**response_distances,'mds':response_xy,'means':response_means,
                               'all_response_euclidean':all_response_distance,'permutation_null':response_metrics['null']}.items(): response_packed[f'R{s}_b{b}_{name}']=array
            # Squared Euclidean distance decomposes exactly over disjoint neural groups.
            ring=ring_distance(); whole_square=distances['euclidean']**2
            for group,idx in d['groups'].items():
                group_square=rdm(means[:,idx])**2
                contribution_rows.append({'stage':s,'branch':b,'population':group,
                                          'mean_squared_distance':float(group_square[np.triu_indices(6,1)].mean()),
                                          'squared_opposite_minus_adjacent':float(group_square[ring==3].mean()-group_square[ring==1].mean()),
                                          'whole_squared_opposite_minus_adjacent':float(whole_square[ring==3].mean()-whole_square[ring==1].mean())})
    if output_dir:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); save_rows(out/'rsa.csv',rows); np.savez_compressed(out/'rsa.npz',**packed)
        save_rows(out/'rsa_response.csv',response_rows); np.savez_compressed(out/'rsa_response.npz',**response_packed)
        save_rows(out/'rsa_population_contributions.csv',contribution_rows)
    return {'panels':panels,'rows':rows,'response_rows':response_rows,'contribution_rows':contribution_rows,
            'ideal_ring':ring_distance(),'ideal_chord':2*np.sin(np.pi*ring_distance()/6)}
