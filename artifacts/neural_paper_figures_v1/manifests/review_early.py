"""Independent raw-array checks for Figures1–3; no production analyzer imports."""
from pathlib import Path
import csv
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/neural_paper_figures_v1'
checks=[]
for mode in ('one_hot','ring','topology'):
    directory=ROOT/'artifacts/neural_representation_v2/data'/mode
    metadata=json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
    r=np.load(directory/'recording.npz')['rates'];g=metadata['population_indices']
    derived=OUT/'derived'/mode
    with np.load(derived/'fig01_population_activity.npz') as a:
        for name,idx in g.items():
            np.testing.assert_array_equal(a[name+'__trial_peak'],np.max(r[:,:,idx],axis=-1))
            np.testing.assert_array_equal(a[name+'__trial_mean'],np.mean(r[:,:,idx],axis=-1))
    with np.load(derived/'fig02_branch_dynamics.npz') as a:
        assert np.isnan(a['R1__competitor']).all() and np.isnan(a['R1__margin']).all()
        for stage in (2,3,4):
            ids=np.array(metadata['branch_indices'][f'R{stage}'])
            values=np.array([np.max(r[:,:,b],axis=-1) for b in ids]).transpose(1,2,0)
            np.testing.assert_array_equal(values,a[f'R{stage}__activity'])
            chosen=a[f'R{stage}__selected']
            for i,b in enumerate(chosen):
                other=np.max(values[i][:,np.arange(len(ids))!=b],axis=-1)
                np.testing.assert_allclose(a[f'R{stage}__margin'][i],values[i,:,b]-other,atol=1e-14)
    with np.load(derived/'fig03_handoff_axes.npz') as a:
        for population,variable in (('M_D','D'),('R2','D'),('M_S','S'),('R3','S')):
            labels=np.array([x[variable] for x in metadata['tasks']]);low,high=np.unique(labels)
            x=r[:,:,g[population]]
            delta=x[labels==high].mean(0)-x[labels==low].mean(0)
            np.testing.assert_allclose(a[population+'__contrast'],delta,atol=1e-14)
            np.testing.assert_allclose(a[population+'__projection'],(x-a[population+'__center'])@a[population+'__axis'],atol=1e-14)
    with (derived/'fig03_temporal_ablation.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f))
    names={x['experiment'] for x in rows}
    assert all('lesion_'+v in names for v in 'ABCD')
    assert all(f'random_{v}_{s}' in names for v in 'ABCD' for s in (7,11,19))
    checks.append({'encoding':mode,'activity':'PASS','branch_margin':'PASS','balanced_rule_axes':'PASS','temporal_control_inventory':'PASS'})
(OUT/'manifests/review_early.json').write_text(json.dumps({'status':'PASS','reviewer':'root, independent of F01–03 implementation','checks':checks},indent=2)+'\n',encoding='utf-8')
print('Independent Figure1–3 raw-array checks PASS')
