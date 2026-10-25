"""Post-implementation falsification checks, distinct from the initial import-red log."""
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
from handcrafted_ei.model import ei_network
from common import baseline


def main():
    original=ei_network.build
    variants=[
        ('Dale sign error','test_dale_constraints.DaleTests.test_all_four_synapse_types','sign'),
        ('no internal memory','test_memory_delay.MemoryTests.test_pulse_removed_memory_at_both_delays',{'w_rec':0}),
        ('no I-to-I release','test_disinhibition.GateTests.test_default_closed_and_release_chain',{'w_release':0}),
        ('early routing','test_disinhibition.GateTests.test_default_closed_and_release_chain',{'theta_release':0}),
        ('broken branch inheritance','test_pathway_inheritance.InheritanceTests.test_memory_output_cuts_preserve_downstream_responses','inheritance'),
    ]
    for name,test,variant in variants:
        def mutant(config):
            values=dict(config)
            if isinstance(variant,dict): values.update(variant)
            data=original(values)
            groups,_,_,weights,*_=data
            if variant=='sign': weights[groups['R1'][0],groups['R1'][0]]=-1
            if variant=='inheritance': weights[groups['R4'],:]=0
            return data
        baseline.cache_clear()
        with patch.object(ei_network,'build',mutant):
            capture=io.StringIO()
            red=unittest.TextTestRunner(stream=capture).run(unittest.defaultTestLoader.loadTestsFromName(test))
        if red.wasSuccessful(): raise AssertionError(f'mutant escaped: {name}')
        print(f'RED {name}: {len(red.failures)} failures, {len(red.errors)} errors')
        print(capture.getvalue())
        baseline.cache_clear()
        healthy=unittest.TextTestRunner(stream=sys.stdout).run(unittest.defaultTestLoader.loadTestsFromName(test))
        if not healthy.wasSuccessful(): raise AssertionError(f'healthy model failed: {name}')
        print(f'GREEN restored: {name}',flush=True)


if __name__=='__main__': main()
