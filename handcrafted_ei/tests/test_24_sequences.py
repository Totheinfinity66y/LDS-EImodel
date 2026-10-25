import unittest
from common import baseline
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import conditions,encode,target
from handcrafted_ei.simulation import run_trial


class SequenceTests(unittest.TestCase):
    def test_all_24_and_each_stage(self):
        results=baseline()
        self.assertEqual(len(results),24)
        for c,r in results: self.assertEqual(r.outputs,target(*c),str(c))

    def test_zero_noise_seed_independence(self):
        for c,control in baseline():
            for seed in (7,11,19):
                r=run_trial(EINetwork(),encode(*c,seed=seed))
                self.assertEqual(r.outputs,control.outputs)

