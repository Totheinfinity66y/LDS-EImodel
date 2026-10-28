import unittest
import numpy as np
from handcrafted_ei.evaluation.paper_figure_v3_geometry import discriminant_axes, project_energy, temporal_geometry
from handcrafted_ei.evaluation.subspace_geometry import principal_angles, cross_vaf


class GeometryTests(unittest.TestCase):
    def test_angles_rotation_and_orthogonal(self):
        q=np.eye(8)[:,:3]; u=np.linalg.qr(np.random.default_rng(7).normal(size=(3,3)))[0]
        np.testing.assert_allclose(principal_angles(q,q@u),0,atol=2e-6)
        np.testing.assert_allclose(principal_angles(q,np.eye(8)[:,3:6]),90)

    def test_cross_vaf_direct_projection(self):
        x=np.random.default_rng(11).normal(size=(6,8)); q=np.eye(8)[:,:3]; z=x-x.mean(0)
        self.assertAlmostEqual(cross_vaf(x,q),np.sum((z@q@q.T)**2)/np.sum(z*z))

    def test_branch_axes_centered_rank(self):
        x=np.eye(4,8); q,mu,s,explained=discriminant_axes(x)
        self.assertEqual(q.shape,(8,3)); self.assertEqual(len(s),4)
        self.assertAlmostEqual(explained.sum(),1)
        np.testing.assert_allclose(q.T@q,np.eye(3),atol=1e-12)

    def test_energy_decomposition(self):
        x=np.random.default_rng(19).normal(size=(9,8)); q=np.linalg.qr(x.T)[0][:,:3]
        full,inside,outside=project_energy(x,q)
        np.testing.assert_allclose(full,inside+outside,atol=1e-12)

    def test_inactive_subspace_is_na_rank_at_most_five(self):
        x=np.zeros((24,2,8)); ids=[np.arange(k,24,4) for k in range(4)]
        x[:,1]=np.random.default_rng(7).normal(size=(24,8))
        a=temporal_geometry(x,ids)
        self.assertTrue(np.isnan(a['angles_degrees'][0]).all())
        self.assertTrue((a['ranks']<=5).all()); self.assertTrue((a['singular_values'][:, :, 5]<1e-12).all())

if __name__=='__main__': unittest.main()
