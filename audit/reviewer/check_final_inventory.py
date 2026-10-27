"""Independent hash readback; run after coordinator declares final-ready."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/paper2agent_reproduction'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    failures=[];counts={}; evidence={}
    for label,file,base in (
        ('new_results',OUT/'manifests/result_hashes.json',OUT),
        ('new_sources',OUT/'manifests/source_hashes.json',ROOT),
    ):
        data=json.loads(file.read_text());counts[label]=len(data)
        for name,expected in data.items():
            p=base/name
            if not p.is_file() or h(p)!=expected:failures.append([label,name])
        evidence[str(file.relative_to(ROOT))]=h(file)
    archive=ROOT/'handcrafted_ei/artifacts/v2/run/source_hashes.json'
    protected={k:v for k,v in json.loads(archive.read_text()).items() if any('/'+name+'/' in k.replace('\\','/') for name in ('model','task','simulation','config'))}
    counts['protected_sources']=len(protected)
    for name,expected in protected.items():
        p=ROOT/name
        if not p.is_file() or h(p)!=expected:failures.append(['protected_sources',name])
    old=ROOT/'artifacts/neural_representation_v2/figure_manifest.json'
    figures=json.loads(old.read_text())['figures'];counts['historical_figures']=len(figures);n=0
    for figure in figures:
        for name,expected in figure['output_sha256'].items():
            p=ROOT/name;n+=1
            if not p.is_file() or h(p)!=expected:failures.append(['historical_figures',name])
    counts['historical_figure_files']=n
    report=dict(status='PASS' if not failures else 'FAIL',counts=counts,failures=failures,manifest_sha256=evidence)
    Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    assert not failures
if __name__=='__main__':main()
