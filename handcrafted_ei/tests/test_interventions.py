import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.simulation import run_trial
from handcrafted_ei.task import encode


class InterventionTests(unittest.TestCase):
    def test_matched_lesions_same_count_magnitude_and_window(self):
        for kind in 'ABCD':
            specific=run_trial(EINetwork(),encode(0,1,2),intervention=kind).lesions[0]
            for seed in (7,11,19):
                random=run_trial(EINetwork(),encode(0,1,2),intervention=kind,random_seed=seed).lesions[0]
                self.assertEqual(len(random['edges']),len(specific['edges']))
                self.assertEqual(random['magnitudes'],specific['magnitudes'])
                self.assertEqual(random['start_ms'],specific['start_ms'])
                self.assertEqual(random['end_ms'],specific['end_ms'])

    def test_projection_permutations_and_composition(self):
        m=EINetwork(); g=m.groups; w=m.weights/m.config['w_projection']
        plus=w[np.ix_(g['R2'][:6],g['R1'])]
        minus=w[np.ix_(g['R2'][6:],g['R1'])]
        double=w[np.ix_(g['R3'][6:12],g['R2'][:6])]
        np.testing.assert_array_equal(plus.sum(axis=0),np.ones(6))
        np.testing.assert_array_equal(plus.sum(axis=1),np.ones(6))
        np.testing.assert_array_equal(plus@minus,np.eye(6))
        np.testing.assert_array_equal(plus@plus,double)
