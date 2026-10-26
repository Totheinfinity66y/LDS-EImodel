import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import encode
from handcrafted_ei.simulation import run_trial


class DirectTests(unittest.TestCase):
    def test_excitatory_gate_and_unselected_silence(self):
        m=EINetwork()
        self.assertNotIn('release12',m.groups)
        for name in ('E_gate_D','E_gate_S','E_gate_34'):
            self.assertTrue(np.all(m.signs[m.groups[name]]==1))
        r=run_trial(m,encode(0,1,2))
        self.assertEqual(r.outputs,(0,1,3,4))
        self.assertLess(r.rates[:,r.groups['R2'][6:]].max(),.01)
        self.assertGreater(r.rates[:,r.groups['E_gate_D'][0]].max(),.6)
        self.assertLess(r.rates[:,r.groups['E_gate_D'][1]].max(),.01)

    def test_source_gate_clock_require_coincidence(self):
        for absent in ('source','memory','clock'):
            m=EINetwork(); x=encode(0,1,2)
            if absent=='source': x['x_L']=np.zeros(6)
            if absent=='memory': x['x_D']=np.zeros(2)
            m.apply_input(**x); m.integrate(200); m.remove_stimulus(); m.integrate(1600)
            if absent!='clock': m.advance_phase('to_R2')
            m.integrate(360)
            self.assertLess(m.rates[m.groups['R2']].max(),.01,absent)
        # Clock only, with neither source nor memory.
        m=EINetwork(); m.advance_phase('to_R2'); m.integrate(500)
        self.assertLess(m.rates[m.groups['R2']].max(),.01)

