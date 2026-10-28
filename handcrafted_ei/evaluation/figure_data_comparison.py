"""Common-coordinate encoding comparison; independent read-only evaluation."""
from pathlib import Path
import csv
import json
import hashlib
import numpy as np
from .reference_adapter import load_audited_dataset, reconstruct_currents
from .population_data import load_dataset
from .reference_dynamics import paired_input_probe
from ..model.ei_network import EINetwork

ROOT = Path(__file__).resolve().parents[2]
MODES = ('one_hot', 'ring', 'topology')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def csvrows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def common_pca(arrays, stride=4):
    """Equal samples per encoding; all conditions and all neurons retained."""
    if len({x.shape for x in arrays}) != 1:
        raise ValueError('encoding trajectories must have identical coordinates')
    train = np.concatenate([x[:, ::stride].reshape(-1, x.shape[-1]) for x in arrays])
    center = train.mean(0)
    _, s, vt = np.linalg.svd(train-center, full_matrices=False)
    return center, vt.T, s*s/np.sum(s*s)


def analyze(output):
    out = Path(output)/'derived'/'comparison'; out.mkdir(parents=True, exist_ok=True)
    source = ROOT/'handcrafted_ei/artifacts/v2/run'
    data = [load_audited_dataset(source, mode) for mode in MODES]
    doses=[]
    for mode,baseline in zip(MODES,data):
        for seed in (7,11,19):
            noisy=load_dataset(source,mode,f'noise_0.03_{seed}')
            for j,(b,n) in enumerate(zip(baseline['tasks'],noisy['tasks'])):
                raw=np.asarray(n['encoded']['x_L'])-np.asarray(b['encoded']['x_L'])
                if mode=='ring':raw=np.arctan2(np.sin(raw),np.cos(raw))
                sample=(baseline['times_ms']>0)&(baseline['times_ms']<=baseline['events'][j]['sample_end'])
                ix=np.asarray(baseline['groups']['R1'])
                delta=(noisy['input_currents']-baseline['input_currents'])[j][:,ix][sample]
                doses.append(dict(encoding=mode,trial=j,seed=seed,sigma_L=.03,
                    raw_coordinate_dimension=len(raw),raw_coordinate_l2=float(np.linalg.norm(raw)),
                    actual_R1_current_rms=float(np.sqrt(np.mean(delta**2))),
                    actual_R1_current_l2=float(np.linalg.norm(delta[0])),
                    noise_archive_sha256=noisy['archive_sha256'],
                    protocol='archived raw-coordinate L noise; unmatched actual current doses'))
    write_csv(out/'fig10_raw_noise_doses.csv',doses)
    cache=out/'fig10_cache.json'
    signature={'analysis_sha256':digest(__file__),'archives':{d['encoding_type']:d['archive_sha256'] for d in data}}
    if cache.exists():
        old=json.loads(cache.read_text(encoding='utf-8'))
        if old.get('signature')==signature and all((out/name).exists() and digest(out/name)==value for name,value in old.get('outputs',{}).items()) and len(old.get('outputs',{}))==3:
            rr=csvrows(out/'fig10_encoding_comparison.csv')
            for r in rr:
                for key in ('current_rms','final_l2','final_linf','max_l2'):r[key]=float(r[key])
                for key in ('recovered','final_identity_retained','sequence_matches_control'):r[key]=r[key]=='True'
            return data,rr
    arrays = [d['rates'] for d in data]
    for d in data[1:]:
        if not np.array_equal(d['labels'], data[0]['labels']):
            raise ValueError('cross-encoding neuron identity mismatch')
        if [(x['L'],x['D'],x['S']) for x in d['tasks']] != [(x['L'],x['D'],x['S']) for x in data[0]['tasks']]:
            raise ValueError('cross-encoding task order mismatch')
    center, basis, evr = common_pca(arrays)
    oh_center, oh_basis, oh_evr = common_pca(arrays[:1])
    scores = np.array([(x-center)@basis[:, :3] for x in arrays])
    oh_scores = np.array([(x-oh_center)@oh_basis[:, :3] for x in arrays])
    rows = []; controls = []; perturbed = []; currents = []; distances = []
    seeds = (7,11,19); amplitudes = (.05,.2,.5)
    # Same full-state external current, independent of original coordinate dimension.
    # No assertion of equivalence to noise in the raw L input coordinates.
    for mode, d in zip(MODES, data):
        model = EINetwork(overrides=d['config']); drive = reconstruct_currents(d)
        t = d['times_ms']; onset = d['events'][0]['to_R3'] + 100
        mode_control=[]; mode_pert=[]; mode_current=[]; mode_dist=[]
        for trial in range(24):
            for amplitude in amplitudes:
                for seed in seeds:
                    direction=np.random.default_rng(seed).normal(size=132)
                    direction/=np.sqrt(np.mean(direction**2))
                    p=paired_input_probe(model,d['rates'][trial,0],t,drive['stimulus'][trial],drive['clock'][trial],direction,onset,50,amplitude)
                    if not np.allclose(p['control'],d['rates'][trial],atol=1e-12,rtol=0):
                        raise ValueError('paired replay differs from archived baseline')
                    delta=p['perturbed']-p['control']; error=np.linalg.norm(delta,axis=1)
                    pulse=p['pulse_mask'][:,None]*amplitude*direction
                    # Identity derives from control activity; target labels never set state.
                    group=np.asarray(d['groups']['R4']); b=p['control'][-1,group].reshape(-1,6)
                    q=p['perturbed'][-1,group].reshape(-1,6)
                    identity=bool(q.max()>=.2 and np.argmax(q)==np.argmax(b))
                    expected=[]; observed=[]
                    for stage in range(1,5):
                        event=d['events'][trial][f'readout{stage}']
                        window=(t>event-d['config']['decision_ms'])&(t<=event)
                        for path,decoded in ((p['control'],expected),(p['perturbed'],observed)):
                            y=path[window][:,d['groups']['Y']].mean(0)
                            decoded.append(int(y.argmax()) if y.max()>=d['config']['decision_threshold'] else -1)
                    rows.append(dict(encoding=mode,trial=trial,seed=seed,current_rms=amplitude,
                        raw_coordinate_noise='NA; matched neural-current assay',onset_ms=onset,duration_ms=50,
                        final_identity_retained=identity,sequence_matches_control=expected==observed,
                        final_l2=float(error[-1]),final_linf=float(np.max(abs(delta[-1]))),
                        recovered=bool(identity and np.max(abs(delta[-1]))<.02),
                        max_l2=float(error.max()),independent_unit='deterministic condition x fixed current direction'))
                    mode_control.append(p['control']); mode_pert.append(p['perturbed']); mode_current.append(pulse); mode_dist.append(error)
        controls.append(mode_control); perturbed.append(mode_pert); currents.append(mode_current); distances.append(mode_dist)
    conditions=np.array([(x['L'],x['D'],x['S']) for x in data[0]['tasks']])
    np.savez_compressed(out/'fig10_common_basis.npz',basis=basis,center=center,evr=evr,scores=scores,
        one_hot_basis=oh_basis,one_hot_center=oh_center,one_hot_evr=oh_evr,one_hot_scores=oh_scores,
        encodings=MODES,times_ms=data[0]['times_ms'],conditions=conditions,
        neuron_indices=np.arange(132),neuron_labels=data[0]['labels'],fit_stride=4)
    np.savez_compressed(out/'fig10_matched_current_full.npz',
        control=np.array(controls),perturbed=np.array(perturbed),actual_current=np.array(currents),full_l2=np.array(distances),
        seeds=seeds,amplitudes=amplitudes,
        trial_order='trial then amplitude then seed; within encoding',
        noise_protocol='50ms matched additive whole-network current; not raw-coordinate noise')
    write_csv(out/'fig10_encoding_comparison.csv',rows)
    cache.write_text(json.dumps({'signature':signature,'outputs':{name:digest(out/name) for name in ('fig10_common_basis.npz','fig10_matched_current_full.npz','fig10_encoding_comparison.csv')}},indent=2)+'\n',encoding='utf-8')
    return data,rows
