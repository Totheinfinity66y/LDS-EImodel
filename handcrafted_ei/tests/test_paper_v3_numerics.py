"""Small meaningful numerical controls for the v3 analysis protocol."""
import unittest
from pathlib import Path
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.evaluation.paper_v3_dynamics import classify
from handcrafted_ei.evaluation.population_dynamics import evolve_batch, field, jacobian
from handcrafted_ei.evaluation.reference_dynamics import paired_input_probe, projection_energy


class PaperV3Numerics(unittest.TestCase):
    def setUp(self):
        self.model=EINetwork();self.model.remove_stimulus();self.model.clock[:]=0

    def test_competition_classifier_all_units(self):
        m=self.model;r=np.zeros_like(m.rates);q=m.groups['R3'].reshape(4,6)
        self.assertEqual(classify(m,r,residual=0)['endpoint_class'],'rest')
        r[q[0,1]]=.8
        self.assertEqual(classify(m,r,expected_branch=0,residual=0)['endpoint_class'],'single_position')
        r[q[0,2]]=.7
        self.assertEqual(classify(m,r,expected_branch=0,residual=0)['endpoint_class'],'multiple_positions')
        r[q[1,1]]=.8
        self.assertEqual(classify(m,r,expected_branch=0,residual=0)['endpoint_class'],'outside_branch')
        self.assertEqual(classify(m,r,expected_branch=0,residual=1e-3)['endpoint_class'],'unconverged')
        self.assertEqual(classify(m,r,expected_branch=0,residual=1e-3,require_converged=False)['endpoint_class'],'outside_branch')

    def test_integrator_exact_model_step_and_euler_jacobian(self):
        m=self.model;m.rates=np.random.default_rng(7).uniform(.1,.9,len(m.rates))
        before=m.rates.copy();path=evolve_batch(m,before[None],5)[0]
        m.step();np.testing.assert_allclose(path[-1],m.rates,atol=1e-15)
        np.testing.assert_allclose(path[-1]-before,5*field(m,before),atol=1e-15)
        # Interior random states avoid clip kinks; finite differences independent.
        h=1e-6;j=jacobian(m,before);numeric=np.empty_like(j)
        for k in range(len(before)):
            eps=np.zeros_like(before);eps[k]=h
            numeric[:,k]=(field(m,before+eps)-field(m,before-eps))/(2*h)
        np.testing.assert_allclose(j,numeric,atol=1e-9)

    def test_zero_input_pair_and_shared_history(self):
        m=self.model;t=np.arange(0,105,5);u=np.zeros((len(t),len(m.rates)));r=np.zeros_like(m.rates)
        result=paired_input_probe(m,r,t,u,u,np.ones_like(r),20,50,0)
        np.testing.assert_array_equal(result['control'],result['perturbed'])
        result=paired_input_probe(m,r,t,u,u,np.ones_like(r),20,50,.25)
        np.testing.assert_array_equal(result['control'][t<=20],result['perturbed'][t<=20])
        self.assertEqual(int(result['pulse_mask'].sum()),10)

    def test_projection_energy(self):
        rng=np.random.default_rng(11);q,_=np.linalg.qr(rng.normal(size=(132,3)))
        e=projection_energy(rng.normal(size=(10,132)),q)
        np.testing.assert_allclose(e['full_squared'],e['projected_squared']+e['orthogonal_squared'],atol=1e-12)

    def test_multi_branch_same_location_is_not_single_state(self):
        m=self.model;r=np.zeros_like(m.rates);q=m.groups['R3'].reshape(4,6)
        r[q[0,1]]=r[q[1,1]]=.8
        self.assertEqual(classify(m,r,residual=0)['endpoint_class'],'outside_branch')

    def test_source_time_has_no_fixed_field_convergence_claim(self):
        result=classify(self.model,np.zeros_like(self.model.rates),require_converged=False)
        self.assertIsNone(result['converged'])
        self.assertTrue(np.isnan(result['residual_max_per_ms']))

    def test_archived_kick_preclip_and_postclip_doses_are_distinct(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/paper2agent_reproduction/lds_results/one_hot'
        with np.load(root/'fixed_points.npz') as a:reference=a['endpoints'][0]
        with np.load(root/'basin_full.npz') as a:initial=a['rates'][0,0];amplitude=float(a['amplitude'][0]);seed=int(a['seed'][0])
        direction=np.random.default_rng(seed).normal(size=len(reference));direction/=np.sqrt(np.mean(direction**2))
        raw=reference+amplitude*direction
        np.testing.assert_allclose(initial,np.clip(raw,0,1),atol=1e-15)
        self.assertAlmostEqual(float(np.sqrt(np.mean((raw-reference)**2))),amplitude)
        self.assertLess(float(np.sqrt(np.mean((initial-reference)**2))),amplitude)


if __name__=='__main__': unittest.main()
