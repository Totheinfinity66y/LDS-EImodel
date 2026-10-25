"""Portable archives and independent reconstruction of every saved decision."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
from .task import encode, target
from .evaluation.behavior import accuracy


def pack_and_verify(out):
    out=Path(out)
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    index={}
    for item in manifest:
        name=item['experiment']; directory=out/name
        archive=out/(name+'.zip')
        with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as z:
            for path in sorted(directory.iterdir()): z.write(path,path.name)
        index[archive.name]=hashlib.sha256(archive.read_bytes()).hexdigest()
    (out/'archives.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    return verify(out)


def verify(out):
    out=Path(out)
    def read(name): return json.loads((out/name).read_text(encoding='utf-8'))
    index=read('archives.json'); summary=read('summary.json'); config=read('config.json')
    checked=0
    for filename,expected_hash in index.items():
        archive=out/filename
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected_hash:
            raise ValueError(f'archive checksum mismatch: {filename}')
        outputs=[]; references=[]
        with ZipFile(archive) as z:
            if z.testzip() is not None: raise ValueError('archive CRC failure')
            for i in range(24):
                task=json.loads(z.read(f'{i:02}_task.json'))
                obs=json.loads(z.read(f'{i:02}_events.json'))
                expected_input=encode(task['L'],task['D'],task['S'],task['sigma_L'],task['seed'])
                for key,value in expected_input.items():
                    np.testing.assert_array_equal(value,task['encoded'][key])
                with np.load(BytesIO(z.read(f'{i:02}_rates.npz')),allow_pickle=False) as data:
                    rates=data['rates']; times=data['times_ms']; y=data['y']; labels=data['labels']
                    if rates.shape!=(len(times),104) or len(labels)!=104:
                        raise ValueError('incomplete rate recording')
                    if not np.all(np.isfinite(rates)) or rates.min()<0 or rates.max()>1:
                        raise ValueError('invalid archived neural rates')
                    np.testing.assert_allclose(np.diff(times),config['dt_ms'],rtol=0,atol=0)
                    predictions=[]
                    for stage in range(1,5):
                        end=obs['events'][f'readout{stage}']
                        window=(times>end-config['decision_ms'])&(times<=end)
                        values=y[window].mean(axis=0)
                        np.testing.assert_allclose(values,obs['decisions'][stage-1],atol=1e-14)
                        predictions.append(int(values.argmax()) if values.max()>=config['decision_threshold'] else -1)
                        if stage<4 and not end<obs['events'][f'to_R{stage+1}']:
                            raise ValueError('readout ordering violated')
                if predictions!=obs['outputs']: raise ValueError('decision mismatch')
                truth=target(task['L'],task['D'],task['S'])
                if list(truth)!=task['target']: raise ValueError('truth mismatch')
                outputs.append(predictions); references.append(truth); checked+=1
        name=filename[:-4]
        if accuracy(outputs,references)!=summary[name]: raise ValueError(f'metrics mismatch: {name}')
    result={'status':'PASS','experiments':len(index),'trials_recomputed':checked,
            'checks':['archive SHA256/CRC','input regeneration','104 rates per step/bounds',
                      'timestamp spacing','four Y decisions from saved trajectories','readout ordering',
                      'independent truth and summary reconstruction']}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result,flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
