"""Independent full-path reference and limits of the six-state observable."""

import unittest

import numpy as np

from lds_decompressor import CompressedCode, ModelParameters, RateDecompressor, RelayNeurons


class RelayAggregationTests(unittest.TestCase):
    def test_random_time_varying_inputs_match_24_state_reference(self):
        rng = np.random.default_rng(2831)
        p = ModelParameters()
        relay = RelayNeurons(p)
        # Include nonzero initial conditions and nonidentity output projections.
        full = rng.random((4, 6))
        weights = rng.random((4, 6, 6))
        relay.initialize(np.einsum("pij,pj->i", weights, full))
        for _ in range(200):
            inputs = rng.random((4, 6))
            full = full + p.dt / p.tau_relay * (inputs - full)
            target = np.einsum("pij,pj->i", weights, inputs)
            relay.step(target, p.dt)
            np.testing.assert_allclose(relay.rates, np.einsum("pij,pj->i", weights, full),
                                       rtol=2e-14, atol=2e-14)
        self.assertEqual(relay.history.shape, (201, 6))

    def test_rectification_happens_before_path_sum(self):
        model = RateDecompressor()
        source = np.eye(6)[0]
        raw_weights = np.zeros((4, 6, 6))
        raw_weights[0, 0, 0] = 2
        gates = np.zeros((4, 6, 4))
        gates[1, 0, 0] = -3
        raw, inhibition, paths, target = model.relay.target(
            source, raw_weights, np.ones(4), gates, model.connections.relay_to_e)
        self.assertEqual(paths[0, 0], 2)
        self.assertEqual(target[0], 2)
        self.assertEqual(np.maximum((raw + inhibition).sum(axis=0), 0)[0], 0)

    def test_equal_total_loses_path_identity_and_unequal_taus_break_closure(self):
        a, b = np.zeros((4, 6)), np.zeros((4, 6))
        a[0, 0] = b[1, 0] = 1
        np.testing.assert_array_equal(a.sum(axis=0), b.sum(axis=0))
        tau = np.array([0.03, 0.06, 0.03, 0.03])[:, None]
        self.assertNotEqual((-a / tau).sum(axis=0)[0], (-b / tau).sum(axis=0)[0])

    def test_model_has_only_six_relay_rates_and_resets_them_at_rank_switches(self):
        model = RateDecompressor()
        result = model.decompress(CompressedCode(1, 1, 2))
        self.assertEqual(model.relay.names, tuple(f"M{k}" for k in range(1, 7)))
        self.assertEqual(model.relay.rates.shape, (6,))
        self.assertEqual(result.recording.rates.shape, (1201, 29))
        self.assertFalse(any(str(name).startswith("R_") for name in result.recording.labels))
        for trace in result.transitions:
            np.testing.assert_array_equal(trace.relay_rates[0], np.zeros(6))
            np.testing.assert_array_equal(trace.relay_target, trace.relay_path_targets.sum(axis=0))
            np.testing.assert_array_equal(trace.e_drive, trace.relay_rates)
        np.testing.assert_array_equal(result.recording.rates[-1], model.rate_potentials)


if __name__ == "__main__":
    unittest.main()
