import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import encode
from handcrafted_ei.simulation import run_trial


class DecayTests(unittest.TestCase):
    def test_handoff_specific_decay(self):
        r=run_trial(EINetwork(),encode(0,1,2)); g=r.groups
        def at(event,group):
            return r.rates[np.argmin(abs(r.times-r.events[event])),g[group]].max()
        self.assertGreater(at('readout1','M_D'),.9)
        self.assertGreater(at('readout2','M_S'),.9)
        self.assertLess(at('readout3','M_D'),.05)
        self.assertLess(at('readout4','M_S'),.05)
        for source,memory,transition in (('R2','M_D','to_R2'),('R3','M_S','to_R3')):
            formed=r.times[np.flatnonzero(r.rates[:,g[source]].max(axis=1)>.9)[0]]
            falling=(r.times>r.events[transition])&(r.rates[:,g[memory]].max(axis=1)<.5)
            self.assertGreater(r.times[np.flatnonzero(falling)[0]],formed)
        self.assertEqual(r.outputs,(0,1,3,4))

    def test_block_feedback_prevents_decay(self):
        m=EINetwork(overrides={'w_response_decay':0})
        r=run_trial(m,encode(0,1,2))
        for name in ('M_D','M_S'):
            self.assertGreater(r.rates[-1,r.groups[name]].max(),.9)

    def test_delayed_response_and_weak_activity_do_not_end_memory(self):
        m=EINetwork(); m.apply_input(**encode(0,1,2)); m.integrate(200); m.remove_stimulus()
        m.integrate(5000)
        self.assertGreater(m.rates[m.groups['M_D']].max(),.9)
        self.assertGreater(m.rates[m.groups['M_S']].max(),.9)
        # Explicit experimental weak-state perturbation; no phase signal.
        m.rates[m.groups['R2']]=.1; m.rates[m.groups['R3']]=.1
        m.integrate(1000)
        self.assertLess(m.rates[m.groups['I_decay_D']].max(),.01)
        self.assertGreater(m.rates[m.groups['M_D']].max(),.9)

    def test_early_loss_damages_only_unused_rule(self):
        for kind,kept in [('early_D',1),('early_S',2)]:
            r=run_trial(EINetwork(),encode(0,1,2),intervention=kind)
            self.assertEqual(r.outputs[:kept],(0,1,3,4)[:kept])
            self.assertNotEqual(r.outputs,(0,1,3,4))

    def test_delayed_handoff_tracks_response_not_elapsed_time(self):
        r=run_trial(EINetwork(),encode(0,1,2),permission_delay_ms=1500)
        self.assertEqual(r.outputs,(0,1,3,4))
        for memory,response in [('M_D','R2'),('M_S','R3')]:
            formation=r.times[np.flatnonzero(r.rates[:,r.groups[response]].max(axis=1)>.9)[0]]
            before=(r.times>=r.events['sample_end'])&(r.times<formation-100)
            self.assertGreater(r.rates[before][:,r.groups[memory]].max(axis=1).min(),.9)

    def test_brief_response_signal_does_not_extinguish_memory(self):
        m=EINetwork(); m.apply_input(**encode(0,1,2)); m.integrate(200); m.remove_stimulus(); m.integrate(1600)
        # An explicitly labeled one-step experimental pulse, isolated from recurrence.
        idx=m.groups['R2']; m.weights[idx,idx]=0
        m.rates[idx[0]]=1.; m.step(); m.integrate(1000)
        self.assertGreater(m.rates[m.groups['M_D']].max(),.9)


