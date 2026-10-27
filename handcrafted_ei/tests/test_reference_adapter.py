import unittest
from copy import deepcopy
from pathlib import Path
import numpy as np

from handcrafted_ei.evaluation.reference_adapter import (
    load_audited_dataset, reference_axes, extract_snapshots, reconstruct_currents,
)
from handcrafted_ei.model.ei_network import EINetwork


class ReferenceAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).parents[1] / 'artifacts/v2/run'
        cls.datasets = [load_audited_dataset(source, mode) for mode in ('one_hot', 'ring', 'topology')]

    def test_axes_preserve_actual_conditions_without_repetitions(self):
        for d in self.datasets:
            adapted = reference_axes(d)
            self.assertEqual(adapted['rates'].shape, (663, 24, 132))
            np.testing.assert_array_equal(adapted['rates'][:, 3], d['rates'][3])
            self.assertEqual(adapted['repetitions_per_condition'], 1)
            self.assertEqual(adapted['axis_semantics'], ['time', 'condition', 'neuron'])

    def test_snapshots_use_all_24_recorded_states(self):
        for d in self.datasets:
            result = extract_snapshots(d, 3)
            self.assertEqual(result['rates'].shape, (24, 132))
            self.assertEqual(len(set(map(tuple, result['conditions']))), 24)
            np.testing.assert_array_equal(result['rates'], d['rates'][:, 568])
            self.assertTrue(np.all(result['times_ms'] == 2840))

    def test_reconstructed_currents_reproduce_every_step(self):
        for d in self.datasets:
            currents = reconstruct_currents(d)
            m = EINetwork(overrides=d['config'])
            m.initialize()
            np.testing.assert_array_equal(currents['stimulus'], d['input_currents'])
            for trial in range(24):
                # Re-evaluate every actual recorded Euler transition, independently
                # of simulation's event orchestration and labels.
                r = d['rates'][trial, :-1]
                drive = r @ m.signed_weights.T + currents['tonic'][trial, 1:] + currents['stimulus'][trial, 1:] + currents['clock'][trial, 1:] - m.theta
                expected = r + d['config']['dt_ms'] / m.tau * (-r + np.clip(drive, 0, 1))
                np.testing.assert_allclose(expected, d['rates'][trial, 1:], atol=3e-15, rtol=0)

    def test_encoding_metadata_and_conditions_must_be_consistent(self):
        d = deepcopy(self.datasets[0])
        d['encoding_type'] = 'ring'
        with self.assertRaises(ValueError): reference_axes(d)
        d = deepcopy(self.datasets[0])
        d['tasks'][1]['L'] = d['tasks'][0]['L']
        d['tasks'][1]['D'] = d['tasks'][0]['D']
        d['tasks'][1]['S'] = d['tasks'][0]['S']
        with self.assertRaises(ValueError): extract_snapshots(d)

    def test_missing_event_sample_and_state_axis_are_rejected(self):
        d = deepcopy(self.datasets[0]); del d['events'][0]['readout3']
        with self.assertRaises(ValueError): extract_snapshots(d)
        d = deepcopy(self.datasets[0]); d['rates'] = d['rates'].transpose(1, 0, 2)
        with self.assertRaises(ValueError): reference_axes(d)


if __name__ == '__main__': unittest.main()
