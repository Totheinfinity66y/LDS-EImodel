import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import conditions, encode


class MemoryTests(unittest.TestCase):
    def test_pulse_removed_memory_at_both_delays(self):
        for delay in (1600, 4000):
            for l,d,s in conditions():
                m = EINetwork()
                m.apply_input(**encode(l,d,s)); m.integrate(200); m.remove_stimulus()
                self.assertEqual(float(m.stimulus.sum()), 0.)
                m.integrate(delay)
                for group, selected in [('R1',l), ('M_D',0 if d==1 else 1), ('M_S',s-1)]:
                    r=m.rates[m.groups[group]]
                    self.assertGreater(r[selected], .9)
                    self.assertLess(float(np.delete(r,selected).max()), .05)

    def test_no_recurrence_cannot_pass_as_memory(self):
        m=EINetwork(overrides={'w_rec':0})
        m.apply_input(**encode(2,-1,2)); m.integrate(200); m.remove_stimulus(); m.integrate(1600)
        self.assertLess(m.rates[m.groups['M_D']].max(), .05)
        self.assertLess(m.rates[m.groups['R1']].max(), .05)

