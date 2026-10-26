"""Read archived full activity, compute metrics, and export the research figures."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np
from .style import configure,save_figure
from . import population_figures as figures
from .dynamics_figures import fixed_points,perturbation
from .comparison_figures import comparison
from . import supplementary
from ..evaluation.population_data import MODES,load_dataset,save_dataset,source_identity
from ..evaluation import population_activity,neuron_selectivity,subspace_geometry,representational_similarity,decoding,memory_transfer

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_INPUT=ROOT/'handcrafted_ei/artifacts/v2/run'
DEFAULT_OUTPUT=ROOT/'artifacts/neural_representation_v2'


def file_hash(p): return sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=DEFAULT_INPUT)
    p.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    p.add_argument('--formats',default='png,svg,pdf')
    p.add_argument('--figures',default='1,2,3,4,5,6,7,8,9,10',help='Comma-separated Figure numbers')
    p.add_argument('--encoding',choices=(*MODES,'all'),default='all')
    p.add_argument('--force',action='store_true',help='Re-export unchanged figures; source/data cache is otherwise reused')
    args=p.parse_args(argv); requested={int(x) for x in args.figures.split(',')}; formats=args.formats.split(',')
    if requested-set(range(1,11)): p.error('Figure numbers must be 1..10')
    if set(formats)-{'png','svg','pdf'}: p.error('formats must be png,svg,pdf')
    out=args.output; out.mkdir(parents=True,exist_ok=True); (out/'config').mkdir(exist_ok=True); (out/'manifests').mkdir(exist_ok=True)
    identity=source_identity(args.input); configure()
    if requested & {8,9,10}:
        from ..evaluation.population_dynamics import run
        run(args.input,out)
    sources={str(x.relative_to(ROOT)):file_hash(x) for directory in (ROOT/'handcrafted_ei/evaluation',ROOT/'handcrafted_ei/visualization') for x in directory.glob('*.py')}
    dynamics_summary=out/'data/dynamics/summary.json'
    signature=sha256(json.dumps({'source':sources,'data':file_hash(args.input/'archives.json'),'formats':formats,
        'dynamics':file_hash(dynamics_summary) if dynamics_summary.exists() else None,
        'references':file_hash(out/'config/references.json') if (out/'config/references.json').exists() else None},sort_keys=True).encode()).hexdigest()
    manifest_path=out/'figure_manifest.json'; old=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'figures':[]}
    records={r['id']:r for r in old['figures']}; data={}; results={}; modes=MODES if args.encoding=='all' else (args.encoding,)
    def export(key,mode,number,make,metrics):
        folder=out/'figures'/mode
        if key in records and records[key].get('signature')==signature and not args.force and all(Path(f).exists() and file_hash(f)==records[key]['output_sha256'][f] for f in records[key]['paths']):
            print('cached figure',key,flush=True); return
        paths=save_figure(make(),folder,key,formats)
        records[key]={'id':key,'figure_number':number,'encoding':mode,'paths':paths,
                      'output_sha256':{path:file_hash(path) for path in paths},'signature':signature,
                      'reference_ids':{1:['A','F'],2:['A'],3:['G'],4:['B','C','A'],5:['D','A'],6:['E','F'],7:['C','A'],8:['G','I'],9:['G','H'],10:['A','D','E','G']}[number],
                      'reference_catalog':'config/references.json','data_source':str(args.input.resolve()),
                      'metrics':[str(x) for x in metrics],'code':sources,'preprocessing':'t=0 baseline for activity/recruitment; centered within samples for SVD; full-state unnormalized Euclidean metrics',
                      'stage_window':'(readout-decision_ms, readout], decision_ms=20','seed':[7,11,19],
                      'plotting_config':'config/analysis.json','dpi':300,'pca_scope':'all 24 conditions, all neural units; uniform stride 4; no per-trial fit'}
        if number in (8,9) or key=='figure_10_dynamics':
            records[key].update({'metrics':[str(x) for x in (out/'metrics').glob('dynamics_*.csv')],
                'raw_data':[str(x) for x in (out/'data/dynamics').glob(mode+'_*.npz')] if mode!='comparison' else str(out/'data/dynamics'),
                'preprocessing':'full-state distances; independent clipped rate-state perturbations at autonomous endpoints; no task-time averaging',
                'stage_window':'sampled readout states extended 2000 ms, dt=5 ms',
                'pca_scope':'display-only top 2 PCs of six same-stage autonomous endpoints; fixed-input vector slice; off-plane field saved'})
        print('exported',key,flush=True)
        manifest_path.write_text(json.dumps({'schema':1,'figures':list(records.values()),'protected_sources':identity},indent=2)+'\n',encoding='utf-8')
    for mode in modes:
        d=load_dataset(args.input,mode); data[mode]=d; save_dataset(d,out/'data'/mode)
        met=out/'metrics'/mode; met.mkdir(parents=True,exist_ok=True)
        print('analyzing',mode,flush=True)
        r={'activity':population_activity.analyze(d,met),'recruitment':neuron_selectivity.analyze(d,met),
           'memory':memory_transfer.analyze(d,args.input,met),'subspaces':subspace_geometry.analyze(d,met),
           'rsa':representational_similarity.analyze(d,met),'decoding':decoding.analyze(d,met)}
        noisy=[load_dataset(args.input,mode,f'noise_0.03_{seed}') for seed in (7,11,19)]
        r['seed_stability']=subspace_geometry.independent_seed_stability(noisy,met); results[mode]=r
        r['noise_decoding']=decoding.independent_seed_probe(noisy,met)
        np.savez_compressed(met/'noise_mean_trajectories.npz',mean_rates=np.mean([x['rates'] for x in noisy],axis=0),
                            individual_seed_rates=np.array([x['rates'] for x in noisy]),times_ms=d['times_ms'],seeds=[7,11,19])
        makers={1:lambda:figures.activity(d,r['activity']),2:lambda:figures.recruitment(d,r['recruitment']),
                3:lambda:figures.memory(d,r['memory']),4:lambda:figures.trajectories(d,r['subspaces']),
                5:lambda:figures.subspaces(d,r['subspaces']),6:lambda:figures.ring_geometry(d,r['rsa']),
                7:lambda:figures.decoding(d,r['decoding']),8:lambda:fixed_points(mode,out),9:lambda:perturbation(mode,out)}
        for number,make in makers.items():
            if number in requested: export(f'figure_{number:02d}_{mode}',mode,number,make,list(met.glob('*')))
        if 2 in requested: export(f'figure_02_selectivity_{mode}',mode,2,lambda:figures.selectivity(d,r['recruitment']),[met/'selectivity.csv'])
        if 3 in requested: export(f'figure_03_controls_{mode}',mode,3,lambda:supplementary.memory_controls(d,r),[met/'memory_controls.csv'])
        if 7 in requested: export(f'figure_07_noise_{mode}',mode,7,lambda:supplementary.noise_decoding(d,r),[met/'decoding_noise_seed.csv',met/'decoding_noise_seed.npz'])
        if 6 in requested:
            from ..model.location_encoding import LocationEncoding
            (met/'input_geometry.json').write_text(json.dumps(LocationEncoding(mode).geometry(),indent=2)+'\n',encoding='utf-8')
            export(f'figure_06_input_{mode}',mode,6,lambda:supplementary.input_geometry(d,r),[met/'input_geometry.json',met/'rsa_response.csv'])
        supplements={1:lambda:supplementary.population_metrics(d,r),4:lambda:supplementary.noisy_trajectories(d,r,np.array([x['rates'] for x in noisy])),5:lambda:supplementary.geometry_metrics(d,r),6:lambda:supplementary.position_controls(d,r)}
        for number,make in supplements.items():
            if number in requested: export(f'figure_{number:02d}_supplement_{mode}',mode,number,make,list(met.glob('*')))
    if 10 in requested:
        if len(modes)!=3: print('Figure 10 requires --encoding all; skipped',flush=True)
        else:
            for kind in ('localization','geometry','dynamics'): export('figure_10_'+kind,'comparison',10,lambda:comparison(data,results,out,kind),list((out/'metrics').rglob('*.csv')))
    if len(modes)==3:
        from .reporting import write_reports,quantitative_summary
        summary=write_reports(data,results,args.input,out)
        if 10 in requested: export('figure_10_quantitative','comparison',10,lambda:quantitative_summary(summary),[out/'metrics/encoding_summary.csv'])
    (out/'config/analysis.json').write_text(json.dumps({'active_threshold':.1,'baseline':'actual t=0 rates','stage_window_ms':20,
        'pca_fit_stride':4,'pca_all_conditions':24,'pca_all_neurons':True,'svd':'centered samples','topology_permutations':720,
        'decoding':'two disjoint stratified LDS-condition folds; fractional tie credit','noise_stability_sigma_L':.03,
        'seeds':[7,11,19],'formats':formats,'rate_unit':'dimensionless, not Hz','model_parameters_changed':False},indent=2)+'\n',encoding='utf-8')
    (out/'manifests/analysis_source_hashes.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
    manifest_path.write_text(json.dumps({'schema':1,'figures':list(records.values()),'protected_sources':identity},indent=2)+'\n',encoding='utf-8')
    print('figure manifest:',manifest_path,flush=True)


if __name__=='__main__': main()
