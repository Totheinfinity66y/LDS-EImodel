import unittest
import numpy as np
from handcrafted_ei.model.location_encoding import LocationEncoding
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import encode,conditions,target
from handcrafted_ei.simulation import run_trial


class EncodingTests(unittest.TestCase):
    def test_dimensions_continuity_and_energy(self):
        for mode,n in [('one_hot',6),('ring',1),('topology',2)]:
            enc=LocationEncoding(mode)
            for k in range(6):
                x=enc.encode(k); self.assertEqual(x.shape,(n,))
                current=enc.to_current(x)
                self.assertAlmostEqual(np.linalg.norm(current),1)
                self.assertEqual(int(current.argmax()),k)
                if mode!='one_hot': self.assertGreater(current[(k+1)%6],.01)
            self.assertAlmostEqual(enc.circular_distance(0,5),np.pi/3)
        ring=LocationEncoding('ring')
        np.testing.assert_allclose(ring.to_current([0]),ring.to_current([2*np.pi]),atol=1e-14)
        self.assertLess(np.linalg.norm(ring.to_current([.001])-ring.to_current([0])),.01)

    def test_all_encodings_all_conditions(self):
        for mode in ('one_hot','ring','topology'):
            for c in conditions():
                self.assertEqual(run_trial(EINetwork(overrides={'location_encoding':mode}),
                                 encode(*c,mode=mode)).outputs,target(*c),(mode,c))

    def test_config_and_input_validation(self):
        for config in ({'location_encoding':'bad'},{'dt_ms':0},{'tau_decay_ms':0},{'w_rec':'2'}):
            with self.assertRaises(ValueError): EINetwork(overrides=config)

