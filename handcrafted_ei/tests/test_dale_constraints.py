import unittest
import numpy as np
from handcrafted_ei.model.neuron import ExcitatoryNeuron, InhibitoryNeuron, euler
from handcrafted_ei.model.ei_network import EINetwork


class DaleTests(unittest.TestCase):
    def test_all_four_synapse_types(self):
        m = EINetwork()
        for pre in (1, -1):
            for post in (1, -1):
                indices = np.flatnonzero(m.signs == pre)
                rows = np.flatnonzero(m.signs == post)
                self.assertTrue(np.any(m.weights[np.ix_(rows, indices)] > 0))
                self.assertTrue(np.all(m.signed_weights[:, indices] * pre >= 0))
        self.assertTrue(np.all(m.weights >= 0))
        self.assertLess(m.signed_weights[m.groups['gate12'][0], m.groups['release12'][0]], 0)

    def test_unified_update_and_bounds(self):
        for cls in (ExcitatoryNeuron, InhibitoryNeuron):
            self.assertAlmostEqual(cls(tau_ms=20).step(1, 5), .25)
        self.assertAlmostEqual(float(euler(np.array([.4]), np.array([.8]), np.array([40]), 5)[0]), .45)
        with self.assertRaises(ValueError):
            euler(np.array([0.]), np.array([1.]), np.array([20.]), 20)

