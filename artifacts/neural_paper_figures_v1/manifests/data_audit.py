"""Read-only input audit; run with the verified analysis environment."""
import csv
import hashlib
import io
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'artifacts/neural_representation_v2'
REF = ROOT / 'artifacts/paper2agent_reproduction/lds_results'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def info(path):
    result = {'path': str(path.relative_to(ROOT)).replace('\\', '/'), 'bytes': path.stat().st_size, 'sha256': digest(path)}
    if path.suffix == '.npz':
        fields = {}
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                with archive.open(name) as f:
                    version = np.lib.format.read_magic(f)
                    reader = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
                    shape, fortran, dtype = reader(f)
                    fields[name.removesuffix('.npy')] = {'shape': list(shape), 'dtype': str(dtype)}
        result['arrays'] = fields
    if path.suffix == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as f:
            rows = csv.reader(f)
            result['columns'] = next(rows, [])
            result['rows'] = sum(1 for _ in rows)
    return result

def main():
    report = {'schema_version': 1, 'generated_utc': datetime.now(timezone.utc).isoformat(),
              'environment': {'python': sys.version, 'executable': sys.executable, 'numpy': np.__version__, 'platform': platform.platform(),
                              'capability': 'CPU NumPy linear algebra and archive inspection; GPU not needed or probed'},
              'encodings': {}, 'protected_source': {}, 'inputs': [], 'reference_materials': [], 'reference_gaps': [], 'gaps': []}
    protected = json.loads((OLD/'manifests/protected_source.json').read_text())
    for name, record in protected.items():
        actual = digest(ROOT/name)
        report['protected_source'][name] = {'sha256': actual, 'expected': record['archived'], 'matches': actual == record['archived']}
    archive_index = json.loads((ROOT/'handcrafted_ei/artifacts/v2/run/archives.json').read_text())
    for encoding in ['one_hot', 'ring', 'topology']:
        p = OLD/'data'/encoding
        meta = json.loads((p/'metadata.json').read_text())
        report['inputs'].extend(info(x) for x in [p/'recording.npz', p/'metadata.json'])
        with np.load(p/'recording.npz', allow_pickle=False) as z:
            rates, times, outputs = z['rates'], z['times_ms'], z['outputs']
            archive = Path(meta['archive_path'])
            actual_archive_hash = digest(archive)
            raw_match = True
            raw_keys = None
            with zipfile.ZipFile(archive) as source:
                for trial in range(24):
                    with np.load(io.BytesIO(source.read(f'{trial:02d}_rates.npz')), allow_pickle=False) as raw:
                        raw_keys = raw.files
                        raw_match &= np.array_equal(raw['rates'], rates[trial]) and np.array_equal(raw['times_ms'], times)
            conditions = [(x['L'], x['D'], x['S']) for x in meta['tasks']]
            targets = np.array([x['target'] for x in meta['tasks']])
            indices = [i for values in meta['population_indices'].values() for i in values]
            checks = {'rates_shape': rates.shape == (24,663,132), 'finite_rates': bool(np.isfinite(rates).all()),
                      'rates_bounded': bool(np.min(rates)>=0 and np.max(rates)<=1),
                      'dt_5ms': bool(np.array_equal(times, np.arange(0,3315,5))), '24_unique_conditions': len(set(conditions)) == 24,
                      'encoding_identity': meta['encoding_type'] == encoding and meta['config']['location_encoding'] == encoding and all(t['encoding'] == encoding for t in meta['tasks']),
                      'population_partition': sorted(indices) == list(range(132)), 'metadata_events_equal': all(e == meta['events'][0] for e in meta['events']),
                      'labels_unique': len(set(z['neuron_labels'].tolist()))==132,
                      'outputs_match_targets': bool(np.array_equal(outputs,targets)), 'raw_trajectories_equal': bool(raw_match),
                      'archive_hash_matches': actual_archive_hash == meta['archive_sha256'] == archive_index[archive.name]}
            report['encodings'][encoding] = {'checks': checks, 'status': 'PASS' if all(checks.values()) else 'BLOCKED',
                'rates_range': [float(np.min(rates)),float(np.max(rates))], 'types': {k:int(np.sum(z['neuron_types']==k)) for k in ['E','I']},
                'events': meta['events'][0], 'population_indices': meta['population_indices'], 'branch_indices':meta['branch_indices'],
                'conditions':conditions, 'input_current_origin':meta['input_current_origin'], 'archive_path':str(archive.relative_to(ROOT)),
                'archive_sha256':actual_archive_hash, 'raw_npz_keys':raw_keys}
        for folder in [OLD/'metrics'/encoding, REF/encoding]:
            for path in sorted(folder.glob('*')):
                if path.suffix in ['.npz','.csv','.json']:
                    report['inputs'].append(info(path))
        for filename in ['fixed_points.npz','fixed_points.csv','basin_full.npz','basin_active_branch.npz','basin.csv','local_flow.npz','state_perturbation.npz','input_summary.csv']:
            if not (REF/encoding/filename).is_file():
                report['gaps'].append({'encoding':encoding,'missing':str((REF/encoding/filename).relative_to(ROOT))})
    references = json.loads((OLD/'config/references.json').read_text())
    for reference in references['references']:
        record = {k:reference.get(k) for k in ['key','title','doi','caption_checked','visually_checked']}
        record['verification_scope'] = 'Historical manifest claims only; this audit checks local asset identity, not a new caption/visual review.'
        record['assets'] = []
        for name in reference.get('local_evidence',[]):
            path = OLD/name
            item = info(path) if path.is_file() else {'path':str(path.relative_to(ROOT)), 'exists':False}
            if path.is_file() and path.suffix == '.pdf':
                item['pdf_header_valid'] = path.read_bytes()[:5] == b'%PDF-'
                if not item['pdf_header_valid']:
                    report['reference_gaps'].append({'paper':reference.get('key'), 'path':item['path'], 'reason':'Filename ends in PDF but file header is not %PDF-; cannot be used as a local paper PDF.'})
            record['assets'].append(item)
        report['reference_materials'].append(record)
    report['limitations'] = [
        'One deterministic baseline trajectory per task condition; 24 conditions are not independent repeats.',
        'Input currents are reconstructed, not separately recorded measurements.',
        'Historical reference caption/visual verification is not re-certified by this data audit.',
        'Churchland2012.pdf and Gallego2018.pdf reference assets have invalid PDF headers; historical panel images exist separately.',
        'Figure 8 basin slices, Figure 9 stage-matched perturbations and Figure 3 temporal ablations require new independent simulations.',
        'Figure 10 requires a common fitted basis; existing encoding-specific PCA axes are not comparable.',
        'Fixed-point local-flow grids are projected vector fields, not full-state basin classifications.'
    ]
    report['status'] = 'PASS_WITH_LIMITS' if all(v['status']=='PASS' for v in report['encodings'].values()) and all(v['matches'] for v in report['protected_source'].values()) and not report['gaps'] else 'BLOCKED'
    (OUT/'data_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'encodings':{k:v['checks'] for k,v in report['encodings'].items()},'input_files':len(report['inputs']),'gaps':report['gaps']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
