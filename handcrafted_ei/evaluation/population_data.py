"""Read-only, checksum-verified whole-population recording interface.

Task metadata stays offline. Reconstructed input currents are explicitly marked;
they are not claimed to have been recorded by the original simulator.
"""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from ..model.ei_network import EINetwork

MODES=('one_hot','ring','topology')


def source_identity(input_dir):
    root=Path(__file__).resolve().parents[2]
    archived=json.loads((Path(input_dir)/'source_hashes.json').read_text(encoding='utf-8'))
    rows={}
    for name,expected in archived.items():
        portable=name.replace('\\','/')
        if portable.startswith(('handcrafted_ei/model/','handcrafted_ei/task/','handcrafted_ei/simulation/','handcrafted_ei/config/')):
            p=root/portable
            actual=sha256(p.read_bytes()).hexdigest()
            rows[portable]={'archived':expected,'current':actual,'matches':expected==actual}
    if not rows or not all(r['matches'] for r in rows.values()):
        raise ValueError('archived dynamics do not match current protected source')
    return rows


def validate_dataset(d):
    x=np.asarray(d['rates']); t=np.asarray(d['times_ms'])
    if x.ndim!=3 or x.shape[1:]!=(len(t),len(d['labels'])):
        raise ValueError('rates/time/labels shape mismatch')
    if not np.isfinite(x).all() or (x<0).any() or (x>1).any(): raise ValueError('invalid rates')
    if len(d['tasks'])!=len(x) or len(d['events'])!=len(x): raise ValueError('trial metadata mismatch')
    if len(set(d['labels']))!=x.shape[-1]: raise ValueError('duplicate neuron labels')
    if len(d['neuron_types'])!=x.shape[-1] or set(d['neuron_types'])-{'E','I'}:
        raise ValueError('incomplete E/I map')
    idx=np.concatenate(list(d['groups'].values()))
    if sorted(idx.tolist())!=list(range(x.shape[-1])): raise ValueError('invalid population partition')
    if not np.allclose(np.diff(t),d['config']['dt_ms'],atol=0,rtol=0): raise ValueError('time spacing')
    for s in range(1,5):
        if len(d['groups'][f'R{s}'])%6: raise ValueError('invalid branch width')
    return True


def load_dataset(input_dir, mode, experiment='baseline'):
    if mode not in MODES: raise ValueError('unknown encoding')
    directory=Path(input_dir); name=f'{mode}__{experiment}'
    archive=directory/(name+'.zip')
    if not archive.exists(): raise FileNotFoundError(archive)
    hashes=json.loads((directory/'archives.json').read_text(encoding='utf-8'))
    actual=sha256(archive.read_bytes()).hexdigest()
    if actual!=hashes[archive.name]: raise ValueError('archive checksum mismatch')
    protocols=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    protocol=next(p for p in protocols if p['experiment']==name)
    config=protocol['config']; m=EINetwork(overrides=config)
    tasks=[]; events=[]; rates=[]; outputs=[]; lesions=[]; currents=[]
    with ZipFile(archive) as z:
        for i in range(24):
            task=json.loads(z.read(f'{i:02}_task.json')); event=json.loads(z.read(f'{i:02}_events.json'))
            with np.load(BytesIO(z.read(f'{i:02}_rates.npz')),allow_pickle=False) as a:
                t=a['times_ms'].copy(); x=a['rates'].copy(); labels=a['labels'].copy()
            if i and (not np.array_equal(t,times) or not np.array_equal(labels,reference_labels)):
                raise ValueError('inconsistent trial recording coordinates')
            times=t; reference_labels=labels
            m.apply_input(**{k:np.asarray(v) for k,v in task['encoded'].items()})
            u=np.zeros_like(x)
            # A row is the current used to integrate INTO that time sample.
            mask=(t>event['events']['sample_start'])&(t<=event['events']['sample_end'])
            u[mask]=m.stimulus
            currents.append(u); rates.append(x); tasks.append(task); events.append(event['events'])
            outputs.append(event['outputs']); lesions.append(event['lesions'])
            groups={k:np.asarray(v,dtype=int) for k,v in event['groups'].items()}
    d={'rates':np.stack(rates),'times_ms':times,'labels':reference_labels,
       'neuron_labels':reference_labels,'neuron_types':np.where(m.signs>0,'E','I'),
       'groups':groups,'population_indices':groups,
       'branch_indices':{f'R{s}':groups[f'R{s}'].reshape(-1,6) for s in range(1,5)},
       'tasks':tasks,'events':events,'config':config,'model_config':config,
       'encoding_type':mode,'trial_id':np.arange(24),'outputs':np.asarray(outputs),
       'input_currents':np.stack(currents),'input_current_origin':'reconstructed from recorded encoded input and sample schedule; row=current integrated into sample',
       'lesions':lesions,'archive_path':str(archive.resolve()),'archive_sha256':actual,
       'protocol':protocol,'seed':[task['seed'] for task in tasks]}
    validate_dataset(d)
    return d


def save_dataset(d, output_dir):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'recording.npz',rates=d['rates'],times_ms=d['times_ms'],
        neuron_labels=d['labels'],neuron_types=d['neuron_types'],input_currents=d['input_currents'],
        outputs=d['outputs'],trial_id=d['trial_id'])
    metadata={k:d[k] for k in ('tasks','events','config','encoding_type','archive_path','archive_sha256','input_current_origin','protocol','seed')}
    metadata['population_indices']={k:v.tolist() for k,v in d['groups'].items()}
    metadata['branch_indices']={k:v.tolist() for k,v in d['branch_indices'].items()}
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
