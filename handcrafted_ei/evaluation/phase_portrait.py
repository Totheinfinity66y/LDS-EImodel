"""Paper-style affine state-plane flows computed from the LDS full rate field.

Blue 2D streamlines integrate the projected slice field, not the full system.
Red paths are projections of actual full132-state Euler integrations.
No model weights, task definitions, or parameters are changed.
"""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import argparse
import json
import sys
import platform
import numpy as np
from .population_dynamics import evolve_batch,field,state_identity
from .reference_adapter import load_audited_dataset,extract_snapshots
from .reference_reproduction import ROOT,dump,csvwrite
from ..model.ei_network import EINetwork

DEFAULT=ROOT/'artifacts/phase_portraits_v2'
TITLES=('Autonomous hold','R3 clock held','R3 retired')
KEYS=('autonomous','clock_held','retired')


def dual_basis(basis):
    b=np.asarray(basis,dtype=float)
    if b.ndim!=2 or b.shape[1]!=2 or not np.isfinite(b).all() or np.linalg.matrix_rank(b)!=2:
        raise ValueError('two independent full-state directions required')
    return np.linalg.solve(b.T@b,b.T)


def project_path(states,origin,basis):
    x=np.asarray(states);b=np.asarray(basis);dual=dual_basis(b)
    coordinates=(x-origin)@dual.T;off=x-origin-coordinates@b.T
    return dict(coordinates=coordinates,offplane_distance=np.linalg.norm(off,axis=-1),offplane_state=off)


def plane_field(model,origin,basis,coordinates):
    """Evaluate a regular coefficient grid without clipping or inventing rates."""
    b=np.asarray(basis);xy=np.asarray(coordinates);dual=dual_basis(b)
    if xy.ndim!=2 or xy.shape[1]!=2:raise ValueError('coordinates must be [point,2]')
    states=np.asarray(origin)+xy@b.T
    valid=np.isfinite(states).all(1)&(states>=0).all(1)&(states<=1).all(1)
    full=np.full(states.shape,np.nan);velocity=np.full(xy.shape,np.nan);off=np.full(states.shape,np.nan)
    external=model.tonic+model.stimulus+model.clock-model.theta
    full[valid]=(-states[valid]+np.clip(states[valid]@model.signed_weights.T+external,0,1))/model.tau
    velocity[valid]=full[valid]@dual.T;off[valid]=full[valid]-velocity[valid]@b.T
    norm=np.linalg.norm(full,axis=1);offnorm=np.linalg.norm(off,axis=1)
    fraction=np.divide(offnorm,norm,out=np.full_like(norm,np.nan),where=norm>1e-14)
    return dict(states=states,valid=valid,full_velocity=full,coordinate_velocity=velocity,
                offplane_velocity=off,offplane_norm=offnorm,offplane_fraction=fraction)


def background_state(model,clock,duration_ms=2000):
    """Integrate a content-free initial state under the specified fixed clock."""
    probe=deepcopy(model);probe.initialize();probe.remove_stimulus();probe.clock=np.asarray(clock).copy()
    rates=evolve_batch(probe,probe.rates[None],duration_ms)[0,-1]
    residual=float(np.max(abs(field(probe,rates))))
    if residual>=1e-8:raise ValueError('content-free background has not converged')
    return dict(rates=rates,residual_max_per_ms=residual,duration_ms=duration_ms)


def select_pair(model,endpoints):
    """Observed activity selects a branch and opposing positions; no task labels."""
    identities=[state_identity(model,r,3) for r in endpoints]
    eligible=[q for q in identities if q is not None]
    if not eligible:raise ValueError('no recorded active R3 endpoint')
    branch=min(q[0] for q in eligible)
    positions=sorted(set(q[1] for q in eligible if q[0]==branch))
    first=positions[0];second=(first+3)%6
    if second not in positions:raise ValueError('opposing actual R3 positions not recorded')
    return np.array([identities.index((branch,p)) for p in (first,second)]),[(branch,first),(branch,second)]


def run_mode(source,reference,out,mode,grid_size=71):
    d=load_audited_dataset(source,mode);model=EINetwork(overrides=d['config'])
    path=reference/'lds_results'/mode/'fixed_points.npz'
    manifest=json.loads((reference/'manifests/result_hashes.json').read_text(encoding='utf-8'))
    relative=str(path.relative_to(reference)).replace('\\','/')
    if manifest.get(relative)!=sha256(path.read_bytes()).hexdigest():raise ValueError('reference endpoint checksum mismatch')
    if json.loads((path.parent/'config.json').read_text(encoding='utf-8'))!=d['config']:raise ValueError('endpoint config mismatch')
    with np.load(path) as z:endpoints=z['endpoints'].copy()
    pair,identities=select_pair(model,endpoints)
    rest=background_state(model,np.zeros(len(model.rates)))['rates'];b=(endpoints[pair]-rest).T;dual=dual_basis(b)
    snapshot=extract_snapshots(d);clock=snapshot['clock'][pair[0]].copy()
    retired=deepcopy(model);retired.clock=clock.copy();retired.advance_phase('retire3')
    clocks=[np.zeros_like(clock),clock,retired.clock.copy()]
    coordinates=np.array([(x,y) for y in np.linspace(0,1,grid_size) for x in np.linspace(0,1,grid_size)])
    seeds=np.array([(x,y) for x in (.1,.5,.95) for y in (.1,.5,.95)])
    rng_seeds=(7,11,19)
    seeds=np.concatenate([seeds,np.array([np.clip([.9,.9]+np.random.default_rng(s).normal(0,.02,2),0,1) for s in rng_seeds])])
    red_indices=np.array([0,2,6,8]);duration=2000;dt=model.config['dt_ms'];times=np.arange(0,duration+dt,dt)
    payload=dict(basis=b,dual=dual,grid_coordinates=coordinates,grid_size=grid_size,
        anchor_rates=endpoints[pair],anchor_trial_indices=pair,anchor_observed_identities=identities,
        anchor_conditions=np.array([[d['tasks'][i][k] for k in ('L','D','S')] for i in pair]),
        seed_coordinates=seeds,red_path_indices=red_indices,times_ms=times,
        neuron_labels=d['labels'],neuron_types=d['neuron_types'],condition_keys=np.array(KEYS),condition_titles=np.array(TITLES))
    metrics=[];end_rows=[]
    for key,clock_values in zip(KEYS,clocks):
        probe=deepcopy(model);probe.remove_stimulus();probe.clock=clock_values.copy()
        background=background_state(probe,clock_values);origin=background['rates']
        grid=plane_field(probe,origin,b,coordinates)
        initial=origin+seeds@b.T
        if not np.all((initial>=0)&(initial<=1)):raise ValueError('predeclared trajectory seed outside valid rate cube')
        paths=evolve_batch(probe,initial,duration);projection=project_path(paths,origin,b)
        # Verify against actual model.step on a deep copy, not just the batch formula.
        checked=deepcopy(probe);checked.rates=initial[0].copy();max_step_error=0.
        for k in range(1,len(times)):
            checked.step();max_step_error=max(max_step_error,float(np.max(abs(checked.rates-paths[0,k]))))
        if max_step_error>1e-12:raise AssertionError('full-state trajectory disagrees with model.step')
        anchors=origin+np.array([[0,0],[1,0],[0,1],[1,1]])@b.T
        anchor_valid=((anchors>=0)&(anchors<=1)).all(1)
        residual=np.array([np.max(abs(field(probe,r))) if good else np.nan for r,good in zip(anchors,anchor_valid)])
        for name,value in grid.items():payload[f'{key}_{name}']=value
        payload.update({f'{key}_origin':origin,f'{key}_clock':clock_values,f'{key}_stimulus':probe.stimulus,
            f'{key}_tonic':probe.tonic,f'{key}_paths':paths,f'{key}_coordinates':projection['coordinates'],
            f'{key}_path_offplane_distance':projection['offplane_distance'],f'{key}_anchor_residual_max_per_ms':residual})
        fraction=grid['offplane_fraction'];finite=fraction[np.isfinite(fraction)]
        metrics.append(dict(encoding=mode,condition=key,valid_grid_fraction=float(grid['valid'].mean()),
            background_residual_max_per_ms=background['residual_max_per_ms'],
            field_offplane_fraction_median=float(np.median(finite)) if len(finite) else None,
            field_offplane_fraction_max=float(finite.max()) if len(finite) else None,
            trajectory_offplane_distance_max=float(projection['offplane_distance'].max()),
            trajectory_step_max_error=max_step_error,grid_size=grid_size,full_state_dimension=len(model.rates)))
        for i,path in enumerate(paths):
            end_rows.append(dict(encoding=mode,condition=key,seed_index=i,initial_lambda1=seeds[i,0],initial_lambda2=seeds[i,1],
                final_lambda1=projection['coordinates'][i,-1,0],final_lambda2=projection['coordinates'][i,-1,1],
                final_offplane_distance=projection['offplane_distance'][i,-1],
                final_full_residual_max_per_ms=float(np.max(abs(field(probe,path[-1])))),
                active_R3_units=';'.join(map(str,np.flatnonzero(path[-1][model.groups['R3']]>.2)))))
    folder=out/mode;folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(folder/'phase_portrait.npz',**payload)
    dump(folder/'config.json',d['config']);csvwrite(folder/'diagnostics.csv',metrics);csvwrite(folder/'endpoints.csv',end_rows)
    dump(folder/'provenance.json',dict(encoding=mode,raw_archive_sha256=d['archive_sha256'],reference_endpoints_sha256=manifest[relative],
        reference_endpoints_file=str(reference/'lds_results'/mode/'fixed_points.npz'),
        protected_source_identity=d['protected_source_identity'],model_parameters_changed=False,training=False,
        coordinate_definition='r = background(condition) + B lambda; B from two activity-selected actual R3 endpoints minus tonic-only rest',
        projection='dual=(B.T B)^(-1) B.T; field evaluated in full132 then projected',
        conditions='all fixed sample-off fields; different integrated content-free origins; original tonic and weights retained',
        invalid_grid='masked, never clipped',blue='streamlines of projected affine slice; not full132 solution',
        red='projections of real full132 Euler paths; offplane displacement saved',seeds=rng_seeds,
        seed_definition='9 fixed coefficient-grid seeds (.1,.5,.95)^2 plus three N(0,.02^2 I) coefficient offsets about (.9,.9), clipped in coefficient coordinates only; not process noise',
        source_figure='Saighi & Rozenberg 2025 Frontiers Figure2, DOI10.3389/fncom.2025.1655701; source u states, LDS r rates; METHOD ADAPTED'))
    return metrics


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=ROOT/'handcrafted_ei/artifacts/v2/run')
    p.add_argument('--reference',type=Path,default=ROOT/'artifacts/paper2agent_reproduction');p.add_argument('--output',type=Path,default=DEFAULT)
    p.add_argument('--encoding',choices=('one_hot','ring','topology','all'),default='all');p.add_argument('--render-only',action='store_true')
    args=p.parse_args(argv);modes=('one_hot','ring','topology') if args.encoding=='all' else (args.encoding,)
    args.output.mkdir(parents=True,exist_ok=True)
    if not args.render_only:
        rows=[]
        for mode in modes:
            print('Affine flow',mode,flush=True);rows+=run_mode(args.input,args.reference,args.output,mode)
        csvwrite(args.output/'diagnostics.csv',rows)
    from ..visualization.phase_portrait import render
    render(args.output,modes)
    from ..visualization.quality_check import check
    check(args.output)
    source_files=[ROOT/p for p in (
        'handcrafted_ei/evaluation/phase_portrait.py','handcrafted_ei/visualization/phase_portrait.py',
        'handcrafted_ei/tests/test_phase_portrait.py','handcrafted_ei/visualization/plot_all.py',
        'handcrafted_ei/visualization/style.py','handcrafted_ei/evaluation/reference_adapter.py',
        'handcrafted_ei/evaluation/reference_reproduction.py','handcrafted_ei/evaluation/population_dynamics.py',
        'handcrafted_ei/visualization/quality_check.py')]
    import scipy,matplotlib
    dump(args.output/'manifest.json',dict(source_hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in source_files},
        output_hashes={str(p.relative_to(args.output)):sha256(p.read_bytes()).hexdigest() for p in args.output.rglob('*') if p.is_file() and p.name!='manifest.json'},
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,platform=platform.platform(),cpu=True),rate_unit='dimensionless',duration_ms=2000,dt_ms=5,
        source_doi='10.3389/fncom.2025.1655701',source_figure='2',scientific_status='METHOD ADAPTED; not pre/post training; no training or weight changes'))


if __name__=='__main__':main()
