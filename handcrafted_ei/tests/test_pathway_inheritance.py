import unittest
import numpy as np
from common import baseline
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import encode, target
from handcrafted_ei.simulation import run_trial


class InheritanceTests(unittest.TestCase):
    def test_memory_output_cuts_preserve_downstream_responses(self):
        for c,control in baseline():
            self.assertEqual(control.outputs,target(*c))
            for intervention in ('B','D'):
                cut=run_trial(EINetwork(),encode(*c),intervention=intervention)
                self.assertEqual(cut.outputs,target(*c))
                np.testing.assert_allclose(cut.decisions,control.decisions,atol=.03)

    def test_relocating_response_changes_inherited_output(self):
        # A position perturbation after R3 must propagate through its own fixed pathway.
        m=EINetwork()
        def relocate(network,stage):
            if stage==3:
                indices=network.groups['R3'].reshape(4,6)[1]
                network.rates[indices]=[0,0,0,0,1,0]
        r=run_trial(m,encode(0,1,2),after_readout=relocate)
        self.assertEqual(r.outputs[:3],(0,1,3))
        self.assertEqual(r.outputs[3],5)

