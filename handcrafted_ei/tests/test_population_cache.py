"""Output integrity must determine whether experiment caches are reusable."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from handcrafted_ei.evaluation import population_dynamics as dynamics


class PopulationCacheTests(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder); source=root/'source'; source.mkdir(); traces=source/'attractor_trajectories'; traces.mkdir()
        original=traces/'one_hot_L0_R1.npz'; np.savez(original,one_hot_L0_R1_initial_rates=np.zeros(132))
        checksum=lambda p:sha256(p.read_bytes()).hexdigest()
        (traces/'index.json').write_text(json.dumps({original.name:{'sha256':checksum(original)}})); (source/'config.json').write_text('{}')
        out=root/'output'; data=out/'data/dynamics'; data.mkdir(parents=True); metrics=out/'metrics'; metrics.mkdir()
        artifact=data/original.name; artifact.write_bytes(b'cache payload'); csv=metrics/'dynamics_fixed_points.csv'; csv.write_text('value\n1\n')
        module=Path(dynamics.__file__)
        signature={'analysis_sha256':checksum(module),'inputs':{str(original):checksum(original)},'config_sha256':checksum(source/'config.json'),
                   'model_source_hashes':{str(p):checksum(p) for p in sorted((module.parents[1]/'model').glob('*.py'))}}
        cached={'signature':signature,'output_sha256':{str(p.relative_to(out)).replace('\\','/'):checksum(p) for p in (artifact,csv)},'test_marker':'cache hit'}
        (data/'summary.json').write_text(json.dumps(cached))
        return source,out,original,artifact,csv

    def test_valid_cache_skips_model_but_missing_csv_recomputes(self):
        with tempfile.TemporaryDirectory() as folder:
            source,out,_,_,csv=self.fixture(folder)
            with patch.object(dynamics,'EINetwork',side_effect=RuntimeError('recomputation reached')):
                self.assertEqual(dynamics.run(source,out)['test_marker'],'cache hit')
                csv.unlink()
                with self.assertRaisesRegex(RuntimeError,'recomputation reached'): dynamics.run(source,out)

    def test_corrupt_output_recomputes_and_corrupt_source_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            source,out,original,artifact,_=self.fixture(folder); artifact.write_bytes(b'corrupted output')
            with patch.object(dynamics,'EINetwork',side_effect=RuntimeError('recomputation reached')):
                with self.assertRaisesRegex(RuntimeError,'recomputation reached'): dynamics.run(source,out)
            original.write_bytes(b'corrupted source')
            with self.assertRaisesRegex(ValueError,'source snapshot checksum'): dynamics.run(source,out)


if __name__=='__main__': unittest.main()
