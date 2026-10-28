"""Guard scientific comparison assumptions, independently of rendering."""
import unittest
import numpy as np
from handcrafted_ei.evaluation.figure_data_comparison import common_pca


class CommonProjectionTests(unittest.TestCase):
    def test_shared_axes_preserve_full_state_distances(self):
        rng=np.random.default_rng(7)
        a=rng.normal(size=(4,9,6));b=a+np.array([3,0,0,0,0,0])
        center,basis,evr=common_pca([a,b],stride=1)
        expected=np.linalg.norm(a-b,axis=-1)
        observed=np.linalg.norm((a-center)@basis-(b-center)@basis,axis=-1)
        np.testing.assert_allclose(observed,expected,atol=1e-12)
        # Independently fitted/centered coordinates would erase this displacement.
        self.assertGreater(np.linalg.norm(a.mean((0,1))-center),1)
        self.assertAlmostEqual(float(evr.sum()),1)

    def test_incompatible_sampling_fails_before_comparison(self):
        with self.assertRaises(ValueError):
            common_pca([np.ones((4,8,6)),np.ones((4,7,6))])


if __name__=='__main__':unittest.main()
