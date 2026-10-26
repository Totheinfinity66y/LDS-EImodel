"""Independent noise realization is a different split from unseen conditions."""
from copy import deepcopy
from pathlib import Path
import unittest
import numpy as np
from handcrafted_ei.evaluation.population_data import load_dataset
from handcrafted_ei.evaluation.decoding import independent_seed_probe


class PopulationNoiseProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).parents[1]/'artifacts/v2/run'
        if not root.exists(): raise unittest.SkipTest('research archive unavailable')
        cls.data=[load_dataset(root,'one_hot',f'noise_0.03_{s}') for s in (7,11,19)]

    def test_no_seed_overlap_and_response_readability(self):
        result=independent_seed_probe(self.data,max_times=3)
        for fold in result['splits']:
            test=set(fold['test_trial_noise_seeds']); training=set(sum(fold['training_trial_noise_seeds_by_seed'].values(),[]))
            self.assertFalse(test&training); self.assertNotIn(fold['heldout_seed'],fold['training_seeds'])
        for time,key in ((2370,('R2','D')),(2840,('R3','S'))):
            i=int(np.flatnonzero(result['times_ms']==time)[0]); self.assertEqual(result['curves'][key][i],1.)
        i=int(np.flatnonzero(result['times_ms']==2370)[0]); self.assertEqual(result['curves'][('M_D','D')][i],1.)

    def test_duplicate_realization_rejected(self):
        with self.assertRaisesRegex(ValueError,'seed identities.*overlap'): independent_seed_probe([self.data[0]]*3)

    def test_mismatched_coordinate_or_condition_order_rejected(self):
        d=deepcopy(self.data[2]); d['labels']=d['labels'][::-1]
        with self.assertRaisesRegex(ValueError,'coordinates'): independent_seed_probe([*self.data[:2],d])
        d=deepcopy(self.data[2]); d['tasks']=d['tasks'][::-1]
        with self.assertRaisesRegex(ValueError,'ordered complete'): independent_seed_probe([*self.data[:2],d])


if __name__=='__main__': unittest.main()
