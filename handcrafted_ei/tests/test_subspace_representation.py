import unittest
from common import baseline
from handcrafted_ei.evaluation.representation import analyze


class RepresentationTests(unittest.TestCase):
    def test_report_real_geometry_and_trajectories(self):
        report=analyze([r for _,r in baseline()])
        for stage in range(1,5):
            r=report[f'R{stage}']
            self.assertEqual(r['position_units'],6)
            self.assertEqual(len(r['position_distances']),6)
            self.assertGreater(r['response_spectrum']['rank'],0)
            self.assertGreater(r['branch_selectivity'],.9)
            self.assertIn('post_memory_decay_stability',r)
            self.assertIn('trial_averaged_trajectory',r)
