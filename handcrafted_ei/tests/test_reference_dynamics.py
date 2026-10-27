"""Independent numerical contracts for source-adapted dynamical analyses."""
import unittest
import numpy as np
from handcrafted_ei.evaluation.reference_dynamics import (
    projection_energy, cross_temporal_distance, endpoint_clusters,
    paired_input_probe, phase_drift, piecewise_cascade_certificate)
from handcrafted_ei.model.ei_network import EINetwork


class ReferenceDynamicsTests(unittest.TestCase):
    def test_piecewise_certificate_does_not_certify_active_recurrent_loop(self):
        m=EINetwork();m.rates[:]=0
        m.rates[m.groups['R1'][0]]=.5
        self.assertFalse(piecewise_cascade_certificate(m,m.rates)['acyclic_union'])

    def test_projection_pythagorean_and_reject_nonorthogonal(self):
        delta=np.array([[3.,4.,12.],[0.,0.,2.]])
        basis=np.eye(3)[:,:2]
        r=projection_energy(delta,basis)
        np.testing.assert_allclose(r['full_squared'],r['projected_squared']+r['orthogonal_squared'])
        np.testing.assert_allclose(r['orthogonal_squared'],[144,4])
        with self.assertRaises(ValueError): projection_energy(delta,basis*2)

    def test_cross_temporal_synthetic_cases(self):
        x=np.column_stack((np.arange(8.),np.zeros(8)))
        np.testing.assert_allclose(np.diag(cross_temporal_distance(x,x)),0)
        shifted=np.roll(x,1,axis=0)
        self.assertEqual(np.argmin(cross_temporal_distance(x,shifted)[2]),3)
        parallel=x+[0,3]
        np.testing.assert_allclose(np.diag(cross_temporal_distance(x,parallel)),3)
        t=np.arange(20.)[:,None]
        control=np.exp(-t)*np.array([[1.,0.]])
        same=np.exp(-t)*np.array([[0.,2.]])
        different=same+[0,1]
        self.assertLess(cross_temporal_distance(control,same)[-1,-1],1e-7)
        self.assertGreater(cross_temporal_distance(control,different)[-1,-1],.99)

    def test_clusters_and_phase_units(self):
        np.testing.assert_array_equal(endpoint_clusters(np.array([[0,0],[0,.001],[1,0]]),.01),[0,0,1])
        t=np.arange(0,101,5.)
        np.testing.assert_allclose(phase_drift(t*.002,t),.002)

    def test_input_pulse_is_not_state_jump_and_zero_noise_pair(self):
        m=EINetwork(); times=np.arange(0,106,5.)
        currents=np.zeros((len(times),len(m.rates)))
        direction=np.ones(len(m.rates))
        before=m.rates.copy()
        out=paired_input_probe(m,before,times,currents,currents,direction,20,50,.25)
        np.testing.assert_array_equal(out['control'][:5],out['perturbed'][:5])
        self.assertGreater(np.linalg.norm(out['perturbed'][5]-out['control'][5]),0)
        np.testing.assert_array_equal(out['perturbed'][0],before)
        np.testing.assert_array_equal(m.rates,before)
        self.assertEqual(np.count_nonzero(out['pulse_mask']),10)
        np.testing.assert_allclose(out['noise_control'],out['noise_perturbed'])


if __name__=='__main__': unittest.main()
