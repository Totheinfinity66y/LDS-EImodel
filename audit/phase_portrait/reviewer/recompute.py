"""Independent verification using model.step; no phase-portrait calculation imports."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork

OUT = Path(__file__).parent
archive_root=ROOT/'artifacts/phase_portraits_v2'
manifest=json.loads((archive_root/'manifest.json').read_text(encoding='utf-8'))
for name,expected in manifest['source_hashes'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, name
for name,expected in manifest['output_hashes'].items():
    assert hashlib.sha256((archive_root/name).read_bytes()).hexdigest()==expected, name
for mode in ('one_hot','ring','topology'):
    provenance=json.loads((archive_root/mode/'provenance.json').read_text(encoding='utf-8'))
    assert len(provenance['protected_source_identity'])==8
    for name,identity in provenance['protected_source_identity'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==identity['archived']==identity['current']
rows = []
hashes = {}
for mode in ('one_hot', 'ring', 'topology'):
    folder = ROOT/'artifacts/phase_portraits_v2'/mode
    config = json.loads((folder/'config.json').read_text(encoding='utf-8'))
    with np.load(folder/'phase_portrait.npz') as z:
        b = z['basis']; dual = np.linalg.pinv(b)
        assert b.shape == (132, 2)
        np.testing.assert_allclose(z['dual'], dual, atol=1e-14)
        np.testing.assert_allclose(dual@b, np.eye(2), atol=1e-14)
        for key in z['condition_keys']:
            model = EINetwork(overrides=config)
            model.clock = z[f'{key}_clock'].copy()
            assert not z[f'{key}_stimulus'].any()
            np.testing.assert_array_equal(model.tonic,z[f'{key}_tonic'])
            initial_background = model.rates.copy()
            model.integrate(2000)
            origin = z[f'{key}_origin']
            np.testing.assert_allclose(model.rates, origin, atol=1e-14)
            grid = origin+z['grid_coordinates']@b.T
            valid = ((grid>=0)&(grid<=1)).all(1)
            np.testing.assert_array_equal(valid, z[f'{key}_valid'])
            np.testing.assert_allclose(grid,z[f'{key}_states'],atol=1e-14)
            external=model.tonic+model.clock-model.theta
            full=(-grid[valid]+np.minimum(1,np.maximum(0,grid[valid]@model.signed_weights.T+external)))/model.tau
            coordinates=full@dual.T
            parallel=coordinates@b.T
            perpendicular=full-parallel
            np.testing.assert_allclose(full,z[f'{key}_full_velocity'][valid],atol=1e-14)
            np.testing.assert_allclose(coordinates,z[f'{key}_coordinate_velocity'][valid],atol=1e-14)
            np.testing.assert_allclose(perpendicular,z[f'{key}_offplane_velocity'][valid],atol=1e-14)
            energy_error=np.max(abs((full**2).sum(1)-(parallel**2).sum(1)-(perpendicular**2).sum(1)))
            assert energy_error<1e-15
            actual=z[f'{key}_paths']
            assert actual.shape==(12,401,132)
            max_step_error=0.
            for i,path in enumerate(actual):
                model.rates=path[0].copy()
                np.testing.assert_allclose(path[0],origin+z['seed_coordinates'][i]@b.T,atol=1e-14)
                for state in path[1:]:
                    model.step()
                    max_step_error=max(max_step_error,float(abs(model.rates-state).max()))
            assert max_step_error<1e-12
            # Verification refinement only; canonical config and saved dt5 paths stay unchanged.
            fine_model=EINetwork(overrides={**config,'dt_ms':2.5})
            fine_model.clock=z[f'{key}_clock'].copy()
            fine_max=0.;fine_endpoint=0.;identity_match=True
            response=model.groups['R3']
            for path in actual:
                fine_model.rates=path[0].copy()
                for state in path[1:]:
                    fine_model.step();fine_model.step()
                    fine_max=max(fine_max,float(abs(fine_model.rates-state).max()))
                fine_endpoint=max(fine_endpoint,float(abs(fine_model.rates-path[-1]).max()))
                identity_match &= np.array_equal(fine_model.rates[response]>.2,path[-1,response]>.2)
            # 36-point field shares every other 71-point coordinate: no interpolation.
            coarse_indices=np.arange(71*71).reshape(71,71)[::2,::2].ravel()
            coarse_grid=origin+z['grid_coordinates'][coarse_indices]@b.T
            coarse_f=(-coarse_grid+np.clip(coarse_grid@model.signed_weights.T+external,0,1))/model.tau
            grid_error=float(abs(coarse_f-z[f'{key}_full_velocity'][coarse_indices]).max())
            assert grid_error<1e-14
            coefficients=(actual-origin)@dual.T
            off=actual-origin-coefficients@b.T
            np.testing.assert_allclose(coefficients,z[f'{key}_coordinates'],atol=1e-13)
            np.testing.assert_allclose(np.linalg.norm(off,axis=-1),z[f'{key}_path_offplane_distance'],atol=1e-13)
            rows.append(dict(encoding=mode,condition=str(key),full_dimension=132,grid_points=len(grid),valid_fraction=float(valid.mean()),
                basis_condition_number=float(np.linalg.cond(b)),dual_inverse_error=float(abs(dual@b-np.eye(2)).max()),
                energy_identity_error=float(energy_error),all_12_paths_max_step_error=max_step_error,
                refinement_dt_ms=2.5,refinement_full_trajectory_max_abs_difference=fine_max,
                refinement_endpoint_max_abs_difference=fine_endpoint,refinement_R3_active_identity_all_match=bool(identity_match),
                common_grid_36_vs_71_max_field_error=grid_error,
                maximum_offplane_distance=float(np.linalg.norm(off,axis=-1).max()),
                initial_background_nonzero_count=int(np.count_nonzero(initial_background)),
                sample_current_nonzero_count=0,tonic_current_nonzero_count=int(np.count_nonzero(model.tonic))))
    for name in ('phase_portrait.npz','phase_portrait.png','projection_diagnostics.png'):
        p=folder/name;hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(status='PASS_WITH_LIMITS',checks=rows,reviewed_hashes=hashes,
    manifest_source_hashes_verified=len(manifest['source_hashes']),manifest_output_hashes_verified=len(manifest['output_hashes']),protected_source_hashes_verified_per_encoding=8,
    scope='Independent full-state reconstruction, backgrounds, dual, grid domain, full field, energy decomposition, all 108 paths',
    limits=['Projected slice is not invariant','No pre/post training experiment','Three encodings share this internal-state dynamics'])
(OUT/'independent_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
