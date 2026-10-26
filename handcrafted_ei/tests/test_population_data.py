"""Recording contract: independent of numerical conclusions."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from handcrafted_ei.evaluation.population_data import load_dataset, validate_dataset


class PopulationDataTests(unittest.TestCase):
    def test_three_encoding_archives_and_types(self):
        root=Path(__file__).parents[1]/'artifacts/v2/run'
        if not root.exists(): self.skipTest('external research archives unavailable')
        for mode in ('one_hot','ring','topology'):
            d=load_dataset(root,mode)
            self.assertEqual(d['rates'].shape,(24,663,132))
            self.assertEqual(set(d['neuron_types']),{'E','I'})
            self.assertEqual(sum(d['neuron_types']=='E'),81)
            self.assertEqual(len(set(d['labels'])),132)
            self.assertEqual(d['input_currents'].shape,d['rates'].shape)
            self.assertTrue(np.all(d['input_currents'][:,d['times_ms']>200]==0))
            for e in d['events']:
                for s in range(1,4): self.assertLess(e[f'readout{s}'],e[f'to_R{s+1}'])
            validate_dataset(d)

    def test_missing_archive_fails_clearly(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaises(FileNotFoundError): load_dataset(p,'ring')

    def test_bad_mode_fails(self):
        with self.assertRaises(ValueError): load_dataset('.', 'fake')


if __name__=='__main__': unittest.main()
