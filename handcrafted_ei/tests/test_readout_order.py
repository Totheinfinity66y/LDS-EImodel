import unittest
import numpy as np
from common import baseline


class OrderTests(unittest.TestCase):
    def test_four_distinct_readouts_before_transitions(self):
        for c,r in baseline():
            for stage in (1,2,3):
                self.assertLess(r.events[f'readout{stage}'],r.events[f'to_R{stage+1}'])
            self.assertEqual(len(set(r.events[f'readout{i}'] for i in range(1,5))),4)
            self.assertEqual(len(r.groups['Y']),6)
            self.assertEqual(r.y.shape,(len(r.times),6))
            for stage in (2,3,4):
                idx=np.argmin(abs(r.times-r.events[f'readout{stage}']))
                for previous in range(1,stage):
                    self.assertLess(r.rates[idx,r.groups[f'R{previous}']].max(), .05)

