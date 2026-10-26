import unittest
import numpy as np
from handcrafted_ei.model.location_encoding import LocationEncoding, permutation, rotation


class TransformTests(unittest.TestCase):
    def test_all_positions_directions_steps_and_composition(self):
        a=rotation(1)
        np.testing.assert_allclose(np.linalg.matrix_power(a,6),np.eye(2),atol=2e-15)
        np.testing.assert_allclose(rotation(-1)@a,np.eye(2),atol=1e-15)
        np.testing.assert_allclose(rotation(2),a@a,atol=1e-15)
        for k in range(6):
            for d in (1,-1):
                for s in (1,2):
                    nxt=(k+d*s)%6
                    np.testing.assert_allclose(permutation(d*s)@np.eye(6)[k],np.eye(6)[nxt])
                    enc=LocationEncoding('topology')
                    np.testing.assert_allclose(rotation(d*s)@enc.encode(k),enc.encode(nxt),atol=2e-15)
                    enc=LocationEncoding('ring')
                    angle=(enc.encode(k)[0]+d*s*np.pi/3)%(2*np.pi)
                    np.testing.assert_allclose(enc.to_current([angle]),enc.to_current(enc.encode(nxt)),atol=2e-15)
