"""Mathematical controls for the independent population analysis workflow."""
import unittest
import numpy as np
from handcrafted_ei.evaluation.subspace_geometry import pca,principal_angles,cross_vaf,compare,independent_seed_stability
from handcrafted_ei.evaluation.representational_similarity import rdm,ring_distance,topology_metrics,classical_mds
from handcrafted_ei.evaluation.neuron_selectivity import factorial_effects,support_similarity
from handcrafted_ei.evaluation.decoding import condition_folds,centroid_accuracy
from handcrafted_ei.evaluation.population_activity import validate_dataset


class PopulationGeometryTests(unittest.TestCase):
    def test_pca_energy_rank_and_reconstruction(self):
        x=np.array([[1,2,0],[2,4,0],[3,6,0.]])
        result=pca(x); self.assertEqual(result['rank'],1)
        np.testing.assert_allclose(result['scores']@result['components']+result['mean'],x,atol=1e-12)
        self.assertAlmostEqual(result['evr'].sum(),1); self.assertAlmostEqual(result['effective_dimension'],1)

    def test_angles_shared_coordinates(self):
        eye=np.eye(4); np.testing.assert_allclose(principal_angles(eye[:,:2],eye[:,2:]),90)
        np.testing.assert_allclose(principal_angles(eye[:,:2],eye[:,:2]),0)
        with self.assertRaises(ValueError): principal_angles(np.eye(3),np.eye(4))

    def test_cross_vaf_and_empty(self):
        x=np.array([[1.,0],[-1,0]])
        self.assertAlmostEqual(cross_vaf(x,np.array([[1.],[0.]])),1)
        self.assertAlmostEqual(cross_vaf(x,np.array([[0.],[1.]])),0)
        self.assertTrue(np.isnan(cross_vaf(np.zeros((3,2)),np.eye(2))))

    def test_rdms_and_ring(self):
        ring=ring_distance(); np.testing.assert_array_equal(ring[0],[0,1,2,3,2,1])
        theta=np.arange(6)*np.pi/3; x=np.c_[np.cos(theta),np.sin(theta)]
        distance=rdm(x); np.testing.assert_allclose(distance,distance.T); np.testing.assert_allclose(np.diag(distance),0)
        xy,stress,_=classical_mds(distance); self.assertLess(stress,1e-10)
        result=topology_metrics(distance); self.assertGreater(result['ring_spearman'],.99); self.assertEqual(result['permutation_count'],720)
        np.testing.assert_allclose(rdm(xy),distance,atol=1e-10)

    def test_onehot_degeneracy(self):
        result=topology_metrics(rdm(np.eye(6)))
        self.assertTrue(np.isnan(result['ring_spearman'])); self.assertTrue(np.isnan(result['permutation_p']))
        self.assertAlmostEqual(result['adjacency_accuracy'],.4)
        self.assertTrue(np.isnan(rdm(np.zeros((6,3)),'cosine')[0,1]))

    def test_factorial_variance_partition(self):
        tasks=[{'L':l,'D':d,'S':s} for l in range(6) for d in (1,-1) for s in (1,2)]
        x=np.array([[t['L']+2*t['D']+3*t['D']*t['S'],t['S']] for t in tasks])
        result=factorial_effects(x,tasks)
        np.testing.assert_allclose(sum(result['energy'].values()),result['total'],atol=1e-12)
        self.assertAlmostEqual(result['fraction']['S'][1],1)

    def test_split_leakage_and_ties(self):
        tasks=[{'L':l,'D':d,'S':s} for l in range(6) for d in (1,-1) for s in (1,2)]*2
        y=np.array([t['D'] for t in tasks])
        for train,test in condition_folds(tasks,y):
            keys=lambda idx:{tuple(tasks[i].values()) for i in idx}
            self.assertFalse(keys(train)&keys(test)); self.assertEqual(set(y[train]),set(y[test]))
        self.assertAlmostEqual(centroid_accuracy(np.zeros((4,2)),np.array([0,0,1,1]),np.zeros((2,2)),np.array([0,1])),.5)

    def test_support_jaccard(self):
        x=np.array([[1,0],[0,1]],bool); np.testing.assert_allclose(support_similarity(x),np.eye(2))

    def test_dataset_missing_shapes(self):
        with self.assertRaises(ValueError): validate_dataset({'rates':np.zeros((2,3)), 'times_ms':np.arange(3),'labels':[]})

    def test_dataset_types_and_branch_layout(self):
        groups={}; start=0
        for s,n in enumerate((6,12,24,24),1): groups[f'R{s}']=np.arange(start,start+n); start+=n
        d={'rates':np.zeros((24,3,start)), 'times_ms':np.arange(3.),'labels':[str(i) for i in range(start)],
           'tasks':[{}]*24,'neuron_types':['E']*start,'groups':groups}
        self.assertTrue(validate_dataset(d)); d['neuron_types'][0]='unknown'
        with self.assertRaises(ValueError): validate_dataset(d)
        d['neuron_types'][0]='I'; d['groups']['R2']=np.arange(11)
        with self.assertRaises(ValueError): validate_dataset(d)

    def test_noise_stability_rejects_unmatched_coordinates(self):
        with self.assertRaises(ValueError): independent_seed_stability([{'labels':['a']},{'labels':['b']}])

    def test_factorial_missing_condition(self):
        with self.assertRaises(ValueError): factorial_effects(np.zeros((1,2)),[{'L':0,'D':1,'S':1}])


if __name__=='__main__': unittest.main()
