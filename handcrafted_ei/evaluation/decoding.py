"""Descriptive nearest-centroid probes with disjoint LDS-condition folds.

These are fixed handcrafted network conditions, not independent animals/networks.
No probe output is ever fed into a model. No in-sample generalization is reported.
"""
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedKFold
from .population_activity import population_sets,save_rows


def condition_folds(tasks,labels,n_splits=2,seed=7):
    keys=[(t['L'],t['D'],t['S']) for t in tasks]; unique=sorted(set(keys))
    # Label must be constant within a condition, including all noise repeats.
    y=[]
    for key in unique:
        values=np.unique(np.asarray(labels)[[k==key for k in keys]])
        if len(values)!=1: raise ValueError('condition labels inconsistent')
        y.append(values[0])
    _,counts=np.unique(y,return_counts=True)
    if counts.min()<n_splits: return []
    splitter=StratifiedKFold(n_splits=n_splits,shuffle=True,random_state=seed)
    folds=[]
    for train,test in splitter.split(np.zeros(len(unique)),y):
        trainkeys={unique[i] for i in train}; testkeys={unique[i] for i in test}
        folds.append((np.flatnonzero([k in trainkeys for k in keys]),np.flatnonzero([k in testkeys for k in keys])))
    return folds


def centroid_accuracy(train,ytrain,test,ytest):
    classes=np.unique(ytrain); centers=np.stack([train[ytrain==c].mean(0) for c in classes])
    # Balanced accuracy is ordinary accuracy here because folds are stratified.
    distances=np.sum((test[:,None,:]-centers[None,:,:])**2,axis=2)
    nearest=np.isclose(distances,distances.min(1,keepdims=True),rtol=1e-9,atol=1e-12)
    # Fractional tie credit avoids spuriously perfect constant-state readouts.
    correct=np.stack([classes==v for v in ytest]); return float(np.mean((nearest&correct).sum(1)/nearest.sum(1)))


def analyze(d,output_dir=None,max_times=41):
    r=np.asarray(d['rates']); tids=np.unique(np.linspace(0,r.shape[1]-1,min(max_times,r.shape[1]),dtype=int)); times=np.asarray(d['times_ms'])[tids]
    task=d['tasks']; labels={'L':np.array([x['L'] for x in task]),'D':np.array([x['D'] for x in task]),'S':np.array([x['S'] for x in task])}
    # Current-location and branch labels are defined only during a readout stage;
    # avoid assigning truth to transition periods. They are separately stage-probed.
    populations=population_sets(d); names=['whole','response','memory','M_D','M_S','R2','R3']
    for s in range(1,5):
        for b,idx in enumerate(np.asarray(d['groups'][f'R{s}']).reshape(-1,6)):
            name=f'R{s}_branch{b}'; populations[name]=idx; names.append(name)
    curves={}; cross={}; rows=[]; packed={'times_ms':times}; split_records={}
    for variable,y in labels.items():
        folds=condition_folds(task,y); split_records[variable]=[(a.tolist(),b.tolist()) for a,b in folds]
        chance=1/len(np.unique(y)); crossmat=np.full((len(tids),len(tids)),np.nan)
        for population in names:
            idx=populations[population]; x=r[:,tids,:][:,:,idx]; curve=[]
            for k in range(len(tids)):
                vals=[centroid_accuracy(x[a,k],y[a],x[b,k],y[b]) for a,b in folds]
                curve.append(np.mean(vals) if vals else np.nan)
                rows.append({'population':population,'variable':variable,'time_ms':float(times[k]),'accuracy':curve[-1],
                             'chance':chance,'split':'two stratified disjoint LDS-condition folds','n_folds':len(folds),'independent_repeats':False})
            curves[(population,variable)]=np.array(curve); packed[f'{population}__{variable}']=curve
            if population=='whole':
                for i in range(len(tids)):
                    for j in range(len(tids)):
                        vals=[centroid_accuracy(x[a,i],y[a],x[b,j],y[b]) for a,b in folds]
                        crossmat[i,j]=np.mean(vals) if vals else np.nan
        cross[variable]=crossmat; packed[f'cross_temporal__{variable}']=crossmat
    stage_rows=[]
    from .population_activity import stage_samples
    for s in range(1,5):
        x=stage_samples(d,s); l=labels['L']; direction=labels['D']; step=labels['S']
        location=(l+(s>=2)*direction+(s>=3)*direction*step+(s>=4)*direction)%6
        branch=np.zeros(len(l),int) if s==1 else (direction==-1).astype(int)*(1 if s==2 else 2)+(step-1 if s>=3 else 0)
        for variable,y in [('L',l),('D',direction),('S',step),('current_location',location),('branch',branch)]:
            branch_pops=[name for name in names if name.startswith(f'R{s}_branch')]
            for pop in ['whole','response','memory',f'R{s}']+branch_pops:
                folds=condition_folds(task,y); idx=populations[pop]
                vals=[centroid_accuracy(x[a][:,idx],y[a],x[b][:,idx],y[b]) for a,b in folds]
                stage_rows.append({'stage':s,'population':pop,'variable':variable,'accuracy':float(np.mean(vals)) if vals else np.nan,
                                   'chance':1/len(np.unique(y)),'fold_count':len(folds)})
    if output_dir:
        import json
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); save_rows(out/'decoding.csv',rows); save_rows(out/'decoding_stages.csv',stage_rows)
        np.savez_compressed(out/'decoding.npz',**packed)
        (out/'decoding_splits.json').write_text(json.dumps(split_records,indent=2),encoding='utf-8')
    return {'times_ms':times,'curves':curves,'cross_temporal':cross,'rows':rows,'stage_rows':stage_rows,'splits':split_records,
            'method':'nearest-centroid linear probe; fractional tie credit; disjoint condition folds; descriptive generalization across task tuples only'}


def independent_seed_probe(datasets,output_dir=None,max_times=41):
    """Leave one encoded-input noise realization out, with all LDS tuples seen.

    This tests noise-repeat reproducibility of information availability. It is
    explicitly NOT generalization to unseen task conditions or learned networks.
    The condition-held-out analysis above remains a separate, stricter result.
    Low but nonzero memory rates can remain decodable at machine precision;
    neither this probe nor amplitude decay establishes information erasure.
    """
    import json
    from .population_activity import event_times
    if len(datasets)<3: raise ValueError('need at least three independent noise seeds')
    reference=datasets[0]; expected={(l,d,s) for l in range(6) for d in (1,-1) for s in (1,2)}
    keys=lambda data:[(t['L'],t['D'],t['S']) for t in data['tasks']]
    order=keys(reference); seed_ids=[]; sigma=[]; trial_noise_seed_sets=[]
    for data in datasets:
        if not np.array_equal(data['labels'],reference['labels']) or not np.array_equal(data['times_ms'],reference['times_ms']):
            raise ValueError('seed neural coordinates or sampling times differ')
        if keys(data)!=order or set(keys(data))!=expected or len(keys(data))!=24:
            raise ValueError('seed trials must share ordered complete 24 LDS conditions')
        if np.asarray(data['rates']).shape!=np.asarray(reference['rates']).shape: raise ValueError('seed rates shape differs')
        if data.get('encoding_type')!=reference.get('encoding_type'): raise ValueError('seed encodings differ')
        for group,index in reference['groups'].items():
            if not np.array_equal(data['groups'][group],index): raise ValueError('seed population coordinates differ')
        seed_ids.append(data.get('protocol',{}).get('seed',data['tasks'][0].get('experiment_seed')))
        sigma.append(data.get('protocol',{}).get('noise_sigma_L',data['tasks'][0].get('sigma_L')))
        trial_seeds=[task.get('seed') for task in data['tasks']]
        if None in trial_seeds or len(set(trial_seeds))!=24: raise ValueError('per-trial noise seed identities missing or repeated')
        trial_noise_seed_sets.append(set(trial_seeds))
    if None in seed_ids or len(set(seed_ids))!=len(seed_ids): raise ValueError('noise seed identities missing or overlap')
    for a in range(len(datasets)):
        for b in range(a+1,len(datasets)):
            if trial_noise_seed_sets[a]&trial_noise_seed_sets[b]: raise ValueError('per-trial noise seeds overlap between realizations')
    if any(value is None or value<=0 for value in sigma) or not np.allclose(sigma,sigma[0]):
        raise ValueError('need matched positive encoded-input noise amplitude')
    t=np.asarray(reference['times_ms']); ntime=len(t)
    uniform=np.linspace(0,ntime-1,min(max_times,ntime),dtype=int)
    readouts=[int(np.argmin(abs(t-event_times(reference,f'readout{s}')[0]))) for s in range(1,5)]
    tids=np.unique(np.r_[uniform,readouts]); times=t[tids]
    populations=population_sets(reference); names=['whole','response','memory','M_D','M_S','R2','R3']
    targets={v:np.array([task[v] for task in reference['tasks']]) for v in ('L','D','S')}
    stacked=np.stack([np.asarray(data['rates'])[:,tids,:] for data in datasets])
    curves={}; per_seed={}; rows=[]; packed={'times_ms':times,'seed_ids':seed_ids}; records=[]
    for heldout,seed_id in enumerate(seed_ids):
        training=[i for i in range(len(datasets)) if i!=heldout]
        records.append({'heldout_seed':seed_id,'training_seeds':[seed_ids[i] for i in training],
                        'test_trial_ids':list(range(24)),'training_trial_ids_by_seed':{str(seed_ids[i]):list(range(24)) for i in training},
                        'test_trial_noise_seeds':[task['seed'] for task in datasets[heldout]['tasks']],
                        'training_trial_noise_seeds_by_seed':{str(seed_ids[i]):[task['seed'] for task in datasets[i]['tasks']] for i in training},
                        'condition_order':[list(key) for key in order],'sigma_L':sigma[heldout],
                        'sample_identity':'(experiment_seed, LDS condition); training and test seed sets are disjoint',
                        'scope':'all 24 task conditions seen during training; held-out independent encoded-input noise realization'})
        for variable,y in targets.items():
            train_y=np.tile(y,len(training))
            for population in names:
                idx=populations[population]; accuracies=[]
                for k in range(len(tids)):
                    train_x=stacked[training,:,k,:].reshape(-1,stacked.shape[-1])[:,idx]
                    test_x=stacked[heldout,:,k,:][:,idx]
                    accuracies.append(centroid_accuracy(train_x,train_y,test_x,y))
                per_seed[(population,variable,seed_id)]=np.asarray(accuracies)
    for variable,y in targets.items():
        for population in names:
            repetitions=np.stack([per_seed[(population,variable,seed)] for seed in seed_ids]); mean=repetitions.mean(0)
            curves[(population,variable)]=mean; packed[f'{population}__{variable}']=mean
            packed[f'{population}__{variable}__seed_accuracies']=repetitions
            for k,time in enumerate(times):
                for j,seed in enumerate(seed_ids):
                    rows.append({'population':population,'variable':variable,'time_ms':float(time),'heldout_seed':seed,
                                 'accuracy':float(repetitions[j,k]),'mean_seed_accuracy':float(mean[k]),'chance':1/len(np.unique(y)),
                                 'noise_sigma_L':sigma[0],'n_training_seeds':len(seed_ids)-1,
                                 'split':'leave-one-noise-seed-out; all 24 conditions seen','independent_repeats':True,
                                 'uncertainty_note':'fold estimates share training seeds; no independent-fold confidence interval'})
    if output_dir:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
        save_rows(out/'decoding_noise_seed.csv',rows); np.savez_compressed(out/'decoding_noise_seed.npz',**packed)
        (out/'decoding_noise_seed_splits.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    return {'times_ms':times,'curves':curves,'per_seed_curves':per_seed,'rows':rows,'splits':records,
            'cross_temporal':{},'stage_rows':[],
            'method':'nearest-centroid probe; held-out independent encoded-input noise seed; all conditions already observed; fractional tie credit'}
