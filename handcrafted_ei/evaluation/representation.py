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
        indices=results[0].groups[f'R{stage}']; branch_indices=indices.reshape(-1,6)
        branch_id=np.argmax(x[:,indices].reshape(len(x),-1,6).max(axis=2),axis=1)
        branches=[]; bases=[]
        for branch in range(len(branch_indices)):
            samples=x[branch_id==branch][:,indices]
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
        report[f'R{stage}']={'response_spectrum':spectrum(x[:,indices]-x[:,indices].mean(axis=0)),
                              'active_fraction':float((x[:,indices]>.1).mean()),
                              'branches':branches,'separation_angles':angles}
    return report
