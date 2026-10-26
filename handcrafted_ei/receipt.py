"""Portable archives and independent reconstruction of every saved decision."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from .task import encode, target
from .evaluation.behavior import accuracy
from .evaluation.memory import analyze_memory
from .simulation import TrialResult


def verify(out,write_result=True):
    out=Path(out)
    def read(name): return json.loads((out/name).read_text(encoding='utf-8'))
    index=read('archives.json'); summary=read('summary.json'); config=read('config.json')
    manifest={item['experiment']:item for item in read('manifest.json')}
    if any(item.get('schema')!=2 for item in manifest.values()):
        raise ValueError('current receipt requires schema 2')
    checked=0
    for filename,expected_hash in index.items():
        name=filename[:-4]; protocol=manifest[name]
        resolved=protocol.get('config',config)
        archive=out/filename
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected_hash:
            raise ValueError(f'archive checksum mismatch: {filename}')
        outputs=[]; references=[]
        with ZipFile(archive) as z:
            if z.testzip() is not None: raise ValueError('archive CRC failure')
            for i in range(24):
                task=json.loads(z.read(f'{i:02}_task.json'))
                obs=json.loads(z.read(f'{i:02}_events.json'))
                if task.get('schema')!=2: raise ValueError('current trial requires schema 2')
                expected_input=encode(task['L'],task['D'],task['S'],task['sigma_L'],task['seed'],mode=task['encoding'],kappa=resolved['encoding_kappa'])
                for key,value in expected_input.items():
                    np.testing.assert_array_equal(value,task['encoded'][key])
                with np.load(BytesIO(z.read(f'{i:02}_rates.npz')),allow_pickle=False) as data:
                    rates=data['rates']; times=data['times_ms']; y=data['y']; labels=data['labels']
                    n_units=len(labels)
                    if rates.shape!=(len(times),n_units) or n_units!=132:
                        raise ValueError('incomplete rate recording')
                    if not np.all(np.isfinite(rates)) or rates.min()<0 or rates.max()>1:
                        raise ValueError('invalid archived neural rates')
                    np.testing.assert_allclose(np.diff(times),resolved['dt_ms'],rtol=0,atol=0)
                    y_indices=[j for j,label in enumerate(labels) if str(label).startswith('Y[')]
                    np.testing.assert_array_equal(y,rates[:,y_indices])
                    predictions=[]
                    for stage in range(1,5):
                        end=obs['events'][f'readout{stage}']
                        window=(times>end-resolved['decision_ms'])&(times<=end)
                        values=y[window].mean(axis=0)
                        np.testing.assert_allclose(values,obs['decisions'][stage-1],atol=1e-14)
                        predictions.append(int(values.argmax()) if values.max()>=resolved['decision_threshold'] else -1)
                        if stage<4 and not end<obs['events'][f'to_R{stage+1}']:
                            raise ValueError('readout ordering violated')
                    groups={k:np.asarray(v) for k,v in obs['groups'].items()}
                    rebuilt=TrialResult(tuple(predictions),np.asarray(obs['decisions']),times,rates,y,obs['events'],groups,obs['lesions'])
                    actual=analyze_memory(rebuilt)
                    if actual!=obs['memory']: raise ValueError('memory metrics mismatch')
                if predictions!=obs['outputs']: raise ValueError('decision mismatch')
                truth=target(task['L'],task['D'],task['S'])
                if list(truth)!=task['target']: raise ValueError('truth mismatch')
                outputs.append(predictions); references.append(truth); checked+=1
        if accuracy(outputs,references)!=summary[name]: raise ValueError(f'metrics mismatch: {name}')
    result={'status':'PASS','experiments':len(index),'trials_recomputed':checked,
            'checks':['archive SHA256/CRC','schema-specific input regeneration','all rates per step/bounds',
                      'timestamp spacing','four Y decisions from saved trajectories','readout ordering',
                      'Y equals recorded rate subset','memory metrics reconstructed for schema 2',
                      'independent truth and summary reconstruction']}
    if write_result:
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result,flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
