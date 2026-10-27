"""Closed-pair dynamics and full-state fixed-point classification criteria."""
import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.evaluation.local_fixed_points import closed_pair,find_nodes,triangular_classification
from handcrafted_ei.evaluation.population_dynamics import field


class LocalFixedPointTests(unittest.TestCase):
    def test_closed_pair_matches_full_field_despite_readout_changes(self):
        m=EINetwork();q=m.groups['R3'][0];z=m.groups['I_decay_S'][0]
        xy=np.array([[.2,.7],[.9,.76],[1.,1.]])
        out=closed_pair(m,q,z,xy)
        self.assertLess(out['nuisance_field_max'],1e-14)
        np.testing.assert_allclose(out['velocity'][1],0,atol=1e-16)
        for i,point in enumerate(xy):
            r=m.rates.copy();r[[q,z]]=point;r[m.groups['Y']]=.3
            np.testing.assert_allclose(field(m,r)[[q,z]],out['velocity'][i],atol=1e-15)

    def test_full_roots_have_two_stable_nodes_and_actual_saddle(self):
        m=EINetwork();q=m.groups['R3'][0];z=m.groups['I_decay_S'][0]
        guess=m.rates.copy();guess[q]=1;guess[z]=1;guess[m.groups['Y'][0]]=.5
        nodes,rows=find_nodes(m,q,z,guess)
        np.testing.assert_allclose(nodes[:,[q,z]],[[0,0],[.9,.76],[1,1]],atol=1e-10)
        self.assertEqual([r['classification'] for r in rows],['stable','saddle','stable'])
        self.assertTrue(all(r['full_residual_max_per_ms']<1e-11 for r in rows))
        self.assertEqual(rows[1]['positive_eigenvalue_count'],1)
        self.assertAlmostEqual(rows[1]['max_real_eigenvalue_per_ms'],.025)

    def test_classifier_rejects_coupled_cycle_not_proven_triangular(self):
        m=EINetwork();r=m.rates.copy();r[m.groups['R1'][:2]]=.3
        idx=m.groups['R1'][:2];m.weights[idx[0],idx[1]]=1;m.weights[idx[1],idx[0]]=1
        self.assertFalse(triangular_classification(m,r)['offdiagonal_union_acyclic'])


if __name__=='__main__':unittest.main()
