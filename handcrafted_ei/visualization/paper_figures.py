"""Orchestrate independent redesigned figures without changing historical archives."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np
from ..evaluation.population_data import source_identity

ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'artifacts/neural_paper_figures_v1'


def finalize(output):
    output=Path(output)
    records=[]
    for p in sorted((output/'manifests').glob('fig*.json')):
        records.append({'path':str(p.relative_to(output)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ('evaluation','visualization') for p in (ROOT/'handcrafted_ei'/folder).glob('*.py')}
    result={'schema':1,'figure_records':records,'analysis_sources':sources,
        'environment':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform()},
        'protected_sources':source_identity(ROOT/'handcrafted_ei/artifacts/v2/run'),
        'rate_unit':'dimensionless','independent_repeats':'baseline: none; 24 deterministic conditions',
        'validation':'See individual figure records and validation report; manifest presence is not scientific acceptance.'}
    def streaming_digest(path):
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1048576),b''):h.update(block)
        return h.hexdigest()
    result['files']={str(p.relative_to(output)).replace('\\','/'):streaming_digest(p)
        for p in sorted(output.rglob('*')) if p.is_file() and p.name!='figure_manifest.json' and '__pycache__' not in p.parts}
    documents=[ROOT/n for n in ('README.md','architecture.md','todo.md','AGENTS.md')]
    documents+=list((ROOT/'docs/figure_redraw').glob('*.md'))
    result['project_documents']={str(p.relative_to(ROOT)).replace('\\','/'):streaming_digest(p) for p in documents}
    (output/'figure_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


def run(figures=range(1,11),encodings=('one_hot','ring','topology'),output=DEFAULT):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);(output/'manifests').mkdir(exist_ok=True)
    source_identity(ROOT/'handcrafted_ei/artifacts/v2/run')
    requested=set(figures)
    if requested & {1,2,3}:
        from .paper_figures_early import run as early
        early(figures=tuple(sorted(requested & {1,2,3})),encodings=encodings,output=output)
    if requested & {4,5,6,7}:
        from .paper_figures_geometry import run as geometry
        geometry(figures=tuple(sorted(requested & {4,5,6,7})),encodings=encodings,output=output)
    if requested & {8,9}:
        from .paper_figures_dynamics import run as dynamics
        dynamics(figures=tuple(sorted(requested & {8,9})),encodings=encodings,output=output)
    if 10 in requested:
        if set(encodings)!={'one_hot','ring','topology'}:
            raise ValueError('Figure10 requires all three encodings')
        from .paper_figures_comparison import run as comparison
        comparison(output=output)
    finalize(output)
