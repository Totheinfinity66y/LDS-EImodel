"""Numerical and information-isolation checks for independent dynamics probes."""
from copy import deepcopy
import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.evaluation.population_dynamics import (
    field, jacobian, evolve_batch, perturbation_targets, state_identity, recovery)


class PopulationDynamicsTests(unittest.TestCase):
    def test_batch_matches_actual_steps_and_preserves_model(self):
        model = EINetwork()
        model.rates = np.random.default_rng(7).uniform(.05, .9, len(model.rates))
        before = deepcopy(model)
        path = evolve_batch(model, model.rates[None], 100)[0]
        actual = [before.rates.copy()]
        for _ in range(20):
            before.step(); actual.append(before.rates.copy())
        np.testing.assert_allclose(path, actual, atol=1e-14)
        np.testing.assert_array_equal(model.rates, path[0])
        np.testing.assert_array_equal(evolve_batch(model, model.rates[None], 100)[0], path)

    def test_jacobian_matches_finite_difference_and_euler(self):
        model = EINetwork()
        model.rates = np.random.default_rng(11).uniform(.1, .9, len(model.rates))
        analytic = jacobian(model)
        numeric = np.zeros_like(analytic)
        for j in range(len(model.rates)):
            delta = np.zeros(len(model.rates)); delta[j] = 1e-7
            numeric[:, j] = (field(model, model.rates + delta) - field(model, model.rates - delta)) / 2e-7
        np.testing.assert_allclose(analytic, numeric, atol=1e-9)
        copied = deepcopy(model); copied.step()
        np.testing.assert_allclose(copied.rates-model.rates, model.config['dt_ms']*field(model), atol=1e-15)

    def test_zero_perturbation_and_identity_not_rest(self):
        model = EINetwork(); model.rates[model.groups['R2'][7]] = 1
        targets = perturbation_targets(model, 2)
        self.assertEqual(set(targets), {'full', 'response', 'active_branch', 'unselected_branch', 'E', 'I'})
        self.assertEqual(state_identity(model, model.rates, 2), (1, 1))
        self.assertTrue(recovery(model, model.rates, model.rates, 2))
        self.assertFalse(recovery(model, model.rates*0, model.rates*0, 2))
        self.assertFalse(recovery(model, model.rates*0, model.rates, 2))

    def test_different_encoding_state_shapes(self):
        for mode in ('one_hot', 'ring', 'topology'):
            model = EINetwork(overrides={'location_encoding': mode})
            self.assertEqual(field(model).shape, model.rates.shape)
            self.assertEqual(evolve_batch(model, model.rates[None], 0).shape, (1, 1, len(model.rates)))


if __name__ == '__main__':
    unittest.main()
