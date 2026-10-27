"""Criteria for affine full-state flow portraits, not clipped PC arrow maps."""
import unittest
import numpy as np
from handcrafted_ei.evaluation.phase_portrait import plane_field, project_path, background_state
from handcrafted_ei.model.ei_network import EINetwork


class PhasePortraitTests(unittest.TestCase):
    def test_dual_coordinates_not_orthogonal_dot(self):
        b=np.array([[1.,.5],[0.,1.],[.2,.3]])
        xy=np.array([[.1,.2],[.3,.4]])
        out=project_path(xy@b.T,np.zeros(3),b)
        np.testing.assert_allclose(out['coordinates'],xy,atol=1e-14)
        np.testing.assert_allclose(out['offplane_distance'],0,atol=1e-14)
        with self.assertRaises(ValueError):project_path(np.zeros((2,3)),np.zeros(3),np.ones((3,2)))

    def test_invalid_states_masked_not_clipped(self):
        m=EINetwork();origin=m.rates.copy();b=np.zeros((len(origin),2));b[0]=[1,1];b[1]=[0,1]
        xy=np.array([[.2,.2],[.8,.8]])
        out=plane_field(m,origin,b,xy)
        np.testing.assert_array_equal(out['valid'],[True,False])
        self.assertEqual(out['states'][1,0],1.6)
        self.assertTrue(np.isnan(out['coordinate_velocity'][1]).all())

    def test_full_field_projection_closure_and_model_preserved(self):
        m=EINetwork();origin=m.rates.copy();b=np.eye(len(origin))[:,:2];before=m.rates.copy()
        out=plane_field(m,origin,b,np.array([[.2,.6],[.8,.4]]))
        full=out['full_velocity'];along=out['coordinate_velocity']@b.T;off=out['offplane_velocity']
        np.testing.assert_allclose(full,along+off,atol=1e-15)
        np.testing.assert_allclose(np.sum(full**2,1),np.sum(along**2,1)+np.sum(off**2,1),atol=1e-15)
        np.testing.assert_array_equal(m.rates,before)

    def test_background_is_integrated_and_retirement_uses_actual_clock(self):
        m=EINetwork();before=m.rates.copy();clock=np.zeros_like(before)
        retired=EINetwork();retired.advance_phase('retire3')
        b=background_state(m,retired.clock)
        self.assertLess(b['residual_max_per_ms'],1e-8)
        self.assertGreater(b['rates'][m.groups['retire'][2]],.99)
        np.testing.assert_array_equal(m.rates,before)


if __name__=='__main__':unittest.main()
