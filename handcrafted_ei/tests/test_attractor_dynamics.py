import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.evaluation.attractors import free_evolution, local_stability, basin_probe
from handcrafted_ei.task import encode


class AttractorTests(unittest.TestCase):
    def test_free_state_recovery_and_decaying_control(self):
        m=EINetwork(); m.apply_input(**encode(0,1,2)); m.integrate(200); m.remove_stimulus(); m.integrate(1600)
        original=m.rates.copy(); clock=m.clock.copy()
        free,rates=free_evolution(m,duration_ms=2000)
        np.testing.assert_array_equal(m.rates,original); np.testing.assert_array_equal(m.clock,clock)
        self.assertEqual(float(free.clock.sum()),0)
        self.assertLess(local_stability(free)['field_residual_per_ms'],1e-8)
        self.assertLess(local_stability(free)['euler_spectral_radius'],1)
        # A recovery assertion at large RMS noise would pre-impose an attractor basin.
        p=basin_probe(free,amplitudes=(.02,),seeds=(7,),duration_ms=2000)
        self.assertTrue(all(x['recovered'] for x in p))
        no=EINetwork(overrides={'w_rec':0}); no.rates=original.copy()
        decayed,_=free_evolution(no,duration_ms=2000)
        self.assertLess(decayed.rates[no.groups['R1']].max(),.01)

    def test_zero_input_stability(self):
        m,_=free_evolution(EINetwork(),duration_ms=2000)
        self.assertLess(m.rates[m.groups['R1']].max(),.01)
        self.assertLess(local_stability(m)['field_residual_per_ms'],1e-8)

