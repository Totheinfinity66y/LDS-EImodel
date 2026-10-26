import numpy as np


def spectrum(matrix):
    s=np.linalg.svd(matrix,compute_uv=False)
    energy=s*s
    vaf=energy/energy.sum() if energy.sum() else np.zeros_like(energy)
    rank=int((s>max(matrix.shape)*np.finfo(float).eps*(s[0] if len(s) else 0)).sum())
    return {'rank':rank,'singular_values':s.tolist(),'vaf':vaf.tolist(),
            'participation_ratio':float(1/(vaf@vaf)) if vaf.sum() else 0.}


def analyze(results):
    report={}
    for stage in range(1,5):
        x=np.array([r.rates[np.argmin(abs(r.times-r.events[f'readout{stage}']))] for r in results])
        width=results[0].y.shape[1]
        indices=results[0].groups[f'R{stage}']; branch_indices=indices.reshape(-1,width)
        branch_activity=x[:,indices].reshape(len(x),-1,width).max(axis=2)
        branch_id=np.argmax(branch_activity,axis=1)
        branches=[]; bases=[]
        for branch in range(len(branch_indices)):
            samples=x[branch_id==branch][:,indices]
            if not len(samples): continue
            centered=samples-samples.mean(axis=0)
            item={'branch':branch,'positions_linear':spectrum(samples),
                  'positions_centered':spectrum(centered)}
            branches.append(item)
            # Use centered positional contrasts, in shared ambient coordinates.
            _,_,v=np.linalg.svd(centered,full_matrices=False)
            bases.append(v[:item['positions_centered']['rank']].T)
        angles=[]
        for a in range(len(bases)):
            for b in range(a+1,len(bases)):
                cos=np.clip(np.linalg.svd(bases[a].T@bases[b],compute_uv=False),0,1)
                angles.append({'branches':[a,b],'degrees':np.degrees(np.arccos(cos)).tolist()})
        folded=x[:,indices].reshape(len(x),-1,width).sum(axis=1)
        positions=folded.argmax(axis=1)
        means=np.array([folded[positions==p].mean(axis=0) for p in range(width)])
        distance=np.linalg.norm(means[:,None]-means[None,:],axis=2)
        a=np.arange(width); delta=np.abs(a[:,None]-a[None,:]); circular=np.minimum(delta,width-delta)
        upper=np.triu_indices(width,1)
        corr=None if np.std(distance[upper])<1e-12 else float(np.corrcoef(distance[upper],circular[upper])[0,1])
        top=np.sort(branch_activity,axis=1)
        selectivity=np.ones(len(top)) if len(branch_indices)==1 else (top[:,-1]-top[:,-2])/(top[:,-1]+1e-15)
        # Same trials and timestamps, no latent-coordinate interpolation.
        response_indices=np.concatenate([results[0].groups[f'R{s}'] for s in range(1,5)])
        avg=np.mean([r.rates[:,response_indices] for r in results],axis=0)
        all_centered=x[:,response_indices]-x[:,response_indices].mean(axis=0)
        _,_,components=np.linalg.svd(all_centered,full_matrices=False)
        stability=[]
        if stage in (2,3):
            memory='M_D' if stage==2 else 'M_S'
            for result in results:
                window=(result.times>=result.events[f'to_R{stage}'])&(result.times<=result.events[f'readout{stage}'])
                low=window&(result.rates[:,result.groups[memory]].max(axis=1)<.05)
                if low.any():
                    act=result.rates[low][:,indices].reshape(-1,len(branch_indices),width)
                    stability.append(float(act.max(axis=2).max(axis=1).min()))
        report[f'R{stage}']={'response_spectrum':spectrum(x[:,indices]-x[:,indices].mean(axis=0)),
                              'active_fraction':float((x[:,indices]>.1).mean()),
                              'position_units':width,'position_distances':distance.tolist(),
                              'all_response_spectrum':spectrum(all_centered),
                              'all_response_pca_components':components[:3].tolist(),
                              'all_response_pca_trial_scores':(all_centered@components[:3].T).tolist(),
                              'position_topology_distance_correlation':corr,
                              'branch_selectivity':float(np.mean(selectivity)),
                              'post_memory_decay_stability':stability,
                              'trial_averaged_trajectory':{'times_ms':results[0].times[::10].tolist(),
                                  'all_response_rates':avg[::10].tolist()},
                              'branches':branches,'separation_angles':angles}
    return report
