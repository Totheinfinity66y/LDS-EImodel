import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.simulation import run_trial, lesion_edges
from handcrafted_ei.task import encode


class InterventionTests(unittest.TestCase):
    def test_recurrence_cut_preserves_all_feedforward_edges(self):
        m=EINetwork(); original=m.weights.copy()
        lesion_edges(m,'recurrence')
        offdiag=~np.eye(len(m.labels),dtype=bool)
        np.testing.assert_array_equal(m.weights[offdiag],original[offdiag])
        for kind in ('early_D','early_S','feedback_D','feedback_S','tonic','recurrence','gate_D','gate_S'):
            m=EINetwork(); specific=lesion_edges(m,kind)
            m=EINetwork(); random=lesion_edges(m,kind,7)
            self.assertEqual(specific['magnitudes'],random['magnitudes'])
            self.assertEqual(specific['presynaptic_signs'],random['presynaptic_signs'])

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
