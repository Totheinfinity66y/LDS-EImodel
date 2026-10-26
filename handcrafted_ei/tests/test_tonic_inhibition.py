import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.simulation import run_trial
from handcrafted_ei.task import encode


class TonicTests(unittest.TestCase):
    def test_real_inhibitory_background_and_necessary_silence(self):
        m=EINetwork(); i=m.groups['I_tonic_R']
        self.assertTrue(np.all(m.signs[i]==-1))
        self.assertTrue(np.all(m.signed_weights[np.ix_(m.groups['R2'],i)]<0))
        r=run_trial(m,encode(0,1,2))
        no=run_trial(EINetwork(overrides={'w_tonic_response':0}),encode(0,1,2))
        before=r.times<=r.events['readout1']
        self.assertLess(r.rates[before][:,r.groups['R2']].max(),.01)
        self.assertGreater(no.rates[before][:,no.groups['R2']].max(),.5)

