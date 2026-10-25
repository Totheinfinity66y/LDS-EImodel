import unittest
import numpy as np
from common import baseline
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import encode
from handcrafted_ei.simulation import run_trial


class GateTests(unittest.TestCase):
    def test_default_closed_and_release_chain(self):
        for c,r in baseline():
            g=r.groups
            first=r.times <= r.events['readout1']
            self.assertLess(r.rates[first][:,g['R2']].max(), .01)
            self.assertGreater(r.rates[first][:,g['gate12']].min(), .49)
            selected=0 if c[1]==1 else 1
            window=(r.times >= r.events['to_R2']+100)&(r.times <= r.events['readout2'])
            self.assertGreater(r.rates[window][:,g['release12'][selected]].max(), .6)
            self.assertLess(r.rates[window][:,g['gate12'][selected]].min(), .05)
            self.assertLess(r.rates[:,g['R2'].reshape(2,6)[1-selected]].max(), .05)
            for stage in (2,3,4):
                idx=np.argmin(abs(r.times-r.events[f'readout{stage}']))
                branches=r.rates[idx,g[f'R{stage}']].reshape(-1,6).max(axis=1)
                self.assertEqual(int((branches>.5).sum()),1)

    def test_no_release_and_no_i_to_i_are_negative_controls(self):
        for intervention in ('A','C','no_i_to_i'):
            r=run_trial(EINetwork(),encode(0,1,2),intervention=intervention)
            self.assertEqual(r.outputs[0],0)
            self.assertNotEqual(r.outputs,(0,1,3,4))
            if intervention=='C': self.assertEqual(r.outputs[:2],(0,1))

