import unittest

import numpy as np

from hennequin_rate_model import (
    RateParameters,
    gain,
    optimize_inhibition,
    preferred_initial_states,
    random_balanced_weights,
    rate_rhs,
    simulate,
)


class RateModelTests(unittest.TestCase):
    def test_gain_reaches_baseline_and_saturations(self):
        p = RateParameters()
        x = np.array([-1e6, 0.0, 1e6])
        np.testing.assert_allclose(p.r0 + gain(x, p), [0, 5, 100], atol=1e-10)
        self.assertAlmostEqual((gain(np.array([1e-5]), p)[0] - gain(np.array([-1e-5]), p)[0]) / 2e-5, 1, places=8)

    def test_uncoupled_linear_dynamics_and_energy(self):
        w = np.zeros((4, 4))
        x0 = np.array([1.0, -2.0, 0.5, 3.0])
        out = simulate(w, 0.2, dt=0.01, initial_potential=x0, linear=True)
        np.testing.assert_allclose(out.potential[-1], x0 * np.exp(-1), rtol=1e-7)
        np.testing.assert_allclose(out.firing_rate, 5 + out.rate_deviation)
        np.testing.assert_allclose(rate_rhs(x0, w, linear=True), -x0 / 0.2)
        states, energies = preferred_initial_states(w)
        np.testing.assert_allclose(states.T @ states, np.eye(4), atol=1e-12)
        np.testing.assert_allclose(energies, 1, atol=1e-12)

    def test_initial_connectivity_respects_dale_and_paper_weights(self):
        w = random_balanced_weights(n=40, seed=12)
        self.assertTrue(np.all(w[:, :20] >= 0))
        self.assertTrue(np.all(w[:, 20:] <= 0))
        positive = np.unique(w[w > 0])
        negative = np.unique(w[w < 0])
        self.assertEqual(len(positive), 1)
        self.assertEqual(len(negative), 1)
        self.assertAlmostEqual(negative[0] / positive[0], -3)

    def test_inhibitory_step_freezes_excitation_and_preserves_block_means(self):
        w0 = random_balanced_weights(n=40, seed=7)
        result = optimize_inhibition(w0, max_iterations=1, seed=8)
        w = result.weights
        np.testing.assert_array_equal(w[:, :20], w0[:, :20])
        self.assertTrue(np.all(w[:, 20:] <= 0))
        self.assertEqual(len(result.spectral_abscissa), 2)
        for rows in (slice(0, 20), slice(20, 40)):
            self.assertAlmostEqual(w[rows, 20:].mean(), -3 * w[rows, :20].mean())
        self.assertTrue(np.all(np.count_nonzero(w[:, 20:], axis=1) <= 8))

    def test_small_soc_reaches_linear_stability_and_has_preferred_states(self):
        w0 = random_balanced_weights(n=40, seed=7)
        result = optimize_inhibition(w0, max_iterations=100, seed=8)
        self.assertLess(result.spectral_abscissa[-1], 1)
        states, energies = preferred_initial_states(result.weights)
        np.testing.assert_allclose(states.T @ states, np.eye(40), atol=1e-11)
        self.assertGreater(energies[0], energies[-1])


if __name__ == "__main__":
    unittest.main()
