"""Behavioral tests: supplied grammar, real routing, and information boundaries."""

from dataclasses import fields, replace
from itertools import product
from pathlib import Path
import ast
import unittest

import numpy as np

from lds_decompressor import (
    CompressedCode, ModelParameters, NeuralState, Population, RateDecompressor,
)


class RateCircuitTests(unittest.TestCase):
    def test_six_sites_and_clockwise_geometry_are_defined(self):
        m = RateDecompressor()
        self.assertEqual(m.position_names, ("E1", "E2", "E3", "E4", "E5", "E6"))
        np.testing.assert_allclose(np.linalg.norm(m.site_coordinates, axis=1), 1)
        np.testing.assert_allclose(m.site_coordinates[0], (1, 0))
        self.assertLess(m.site_coordinates[1, 1], 0)
        for label in range(1, 7):
            state = m.initialize(CompressedCode(label, 1, 1))
            self.assertEqual(np.argmax(state.e_rates) + 1, label)

    def test_all_24_conditions_and_all_four_ranks(self):
        m = RateDecompressor()
        for location, direction, step in product(range(1, 7), (1, -1), (1, 2)):
            with self.subTest(L=location, D=direction, S=step):
                result = m.decompress(CompressedCode(location, direction, step))
                # Independent modular-arithmetic oracle, outside inference.
                expected = tuple(1 + (location - 1 + direction * offset) % 6
                                 for offset in (0, 1, 1 + step, 2 + step))
                self.assertEqual(result.positions, expected)
                self.assertEqual(tuple(t.selected_shift for t in result.transitions),
                                 (direction, direction * step, direction))
                self.assertTrue(np.isfinite(result.position_activity).all())
                np.testing.assert_allclose(result.position_activity.sum(axis=1), 1)

    def test_four_tuning_peaks_and_joint_multiplication(self):
        m = RateDecompressor()
        for index, (direction, step) in enumerate(product((1, -1), (1, 2))):
            encoding = m.encode_tuning(direction, step)
            self.assertEqual(np.argmax(encoding.direction.activity), int(direction == -1))
            self.assertEqual(np.argmax(encoding.step.activity), step - 1)
            self.assertEqual(np.argmax(encoding.joint.activity), index)
            np.testing.assert_allclose(encoding.joint.raw_drive,
                                      np.outer(encoding.direction.activity, encoding.step.activity).ravel())
            for pop in (encoding.direction, encoding.step, encoding.joint):
                self.assertGreater(float(pop.rates.sum()), 0)
                np.testing.assert_allclose(pop.activity, pop.rates / pop.rates.sum())
        response = np.stack([m.encode_tuning(d, s).joint.activity
                             for d, s in product((1, -1), (1, 2))])
        self.assertTrue(np.all(np.argmax(response, axis=0) == np.arange(4)))
        self.assertFalse(np.allclose(response[0], response[1]))  # change S
        self.assertFalse(np.allclose(response[0], response[2]))  # change D

    def test_every_joint_is_connected_at_every_rank_and_paths_are_shared(self):
        m = RateDecompressor()
        c = m.connections
        c.validate()
        for transition in range(3):
            np.testing.assert_array_equal(c.rank_to_displacement[transition].sum(axis=0), 1)
        for path, shift in enumerate((1, 2, -1, -2)):
            for start in range(6):
                impulse = np.eye(6)[start]
                expected = np.eye(6)[(start + shift) % 6]
                np.testing.assert_array_equal(c.e_to_relay[path] @ impulse, expected)
                np.testing.assert_array_equal(c.relay_to_e[path] @ expected, expected)

    def test_neural_joint_state_controls_routing_after_initialization(self):
        m = RateDecompressor()
        state = m.initialize(CompressedCode(1, 1, 2))
        joint = Population(state.encoding.joint.names, [0, 0, 0, 1],
                           [0, 0, 0, 1], [0, 0, 0, 1])
        changed = replace(state, encoding=replace(state.encoding, joint=joint))
        result = m.resume(changed)
        self.assertEqual(result.positions, (1, 6, 4, 3))
        self.assertEqual(tuple(t.selected_shift for t in result.transitions), (-1, -2, -1))

    def test_changed_rank_connections_change_actual_generated_positions(self):
        m = RateDecompressor()
        m.connections.rank_to_displacement[:] = 0
        m.connections.rank_to_displacement[:, 2, :] = 1  # force CCW1
        result = m.decompress(CompressedCode(1, 1, 2))
        self.assertEqual(result.positions, (1, 6, 5, 4))

    def test_inhibitory_drive_is_negative_and_unselected_relays_are_silent(self):
        m = RateDecompressor()
        result = m.decompress(CompressedCode(3, -1, 2))
        for t in result.transitions:
            winner = ("CW1", "CW2", "CCW1", "CCW2").index(t.selected_path)
            self.assertEqual(t.gate_i_rates[winner], 0)
            self.assertTrue(np.all(t.gate_i_rates[np.arange(4) != winner] > 0.99))
            self.assertTrue(np.all(t.relay_inhibitory_drive <= 0))
            np.testing.assert_array_equal(t.relay_target[np.arange(4) != winner], 0)
            self.assertGreater(float(t.relay_rates[-1, winner].sum()), 0)
            np.testing.assert_allclose(t.e_drive[-1],
                np.einsum("pij,pj->i", m.connections.relay_to_e, t.relay_rates[-1]))
            self.assertTrue(np.all(t.e_rates >= 0))
            self.assertTrue(np.all(t.i_rates >= 0))
            self.assertGreater(float(t.i_rates.max()), 0)

    def test_breaking_selected_relay_breaks_behavior(self):
        m = RateDecompressor()
        m.connections.e_to_relay[1] = 0  # no CW2 transmission
        result = m.decompress(CompressedCode(1, 1, 2))
        self.assertNotEqual(result.positions, (1, 2, 4, 5))

    def test_removing_gate_inhibition_breaks_selective_transmission(self):
        m = RateDecompressor()
        m.connections.gate_to_relay[:] = 0
        state = m.initialize(CompressedCode(1, 1, 2))
        following, trace = m.advance(state)
        self.assertTrue(np.all(trace.relay_target.sum(axis=1) > 0))
        opposite, _ = m.advance(m.initialize(CompressedCode(1, -1, 2)))
        # With gates disconnected D cannot affect transmission. A residual
        # numerical peak can accidentally match one command, but not both.
        np.testing.assert_array_equal(following.e_rates, opposite.e_rates)
        self.assertFalse(int(np.argmax(following.e_rates)) + 1 == 2 and
                         int(np.argmax(opposite.e_rates)) + 1 == 6)

    def test_no_code_fields_in_runtime_state_or_target_imports(self):
        self.assertEqual({f.name for f in fields(NeuralState)},
                         {"e_rates", "i_rate", "encoding", "rank"})
        import lds_decompressor.model as module
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any("evaluation" in name or "hennequin" in name or "handcrafted" in name
                             for name in imports))

    def test_symbolic_input_is_read_once_and_never_stored(self):
        class OneReadCode:
            def __init__(self):
                self.counts = dict(location=0, direction=0, step=0)

            def __getattr__(self, name):
                values = dict(location=2, direction=-1, step=2)
                if name not in values:
                    raise AttributeError(name)
                self.counts[name] += 1
                if self.counts[name] > 1:
                    raise AssertionError("Symbolic code was reread")
                return values[name]

        code = OneReadCode()
        result = RateDecompressor().decompress(code)
        self.assertEqual(result.positions, (2, 1, 5, 4))
        self.assertEqual(code.counts, dict(location=1, direction=1, step=1))

    def test_previous_runs_and_other_instances_cannot_supply_hidden_state(self):
        m = RateDecompressor()
        code = CompressedCode(6, -1, 2)
        before = m.decompress(code)
        m.decompress(CompressedCode(2, 1, 1))
        after = m.decompress(code)
        np.testing.assert_array_equal(before.position_activity, after.position_activity)
        other = RateDecompressor()
        other.connections.e_to_relay[:] = 0
        self.assertGreater(float(m.connections.e_to_relay.sum()), 0)
        self.assertFalse(before.position_activity.flags.writeable)

    def test_per_instance_tuning_and_integration_parameters(self):
        default = RateDecompressor()
        custom = RateDecompressor(ModelParameters(direction_slope=2, joint_gains=(2, 1, 1, 1)))
        first = default.encode_tuning(1, 1)
        changed = custom.encode_tuning(1, 1)
        self.assertFalse(np.allclose(first.direction.rates, changed.direction.rates))
        self.assertFalse(np.allclose(first.joint.rates, changed.joint.rates))
        code = CompressedCode(4, -1, 2)
        a = default.decompress(code)
        b = RateDecompressor(ModelParameters(dt=0.001)).decompress(code)
        self.assertEqual(a.positions, b.positions)
        np.testing.assert_allclose(a.position_activity, b.position_activity, atol=0.002, rtol=0)

    def test_off_site_population_probes_are_shift_equivariant(self):
        m = RateDecompressor()
        # Not used to fit weights; arbitrary soft spatial states, away from ties.
        for direction, step in product((1, -1), (1, 2)):
            encoding = m.encode_tuning(direction, step)
            base = m.resume(m.initialize_population(m.encode_angle(0.19), encoding))
            for shift in range(1, 6):
                probe = m.resume(m.initialize_population(m.encode_angle(0.19 + shift * np.pi / 3), encoding))
                np.testing.assert_allclose(probe.position_activity,
                    np.roll(base.position_activity, shift, axis=1), atol=1e-12)
                self.assertEqual(probe.positions,
                    tuple(1 + (position - 1 + shift) % 6 for position in base.positions))

    def test_invalid_and_silent_inputs_fail_explicitly(self):
        for args in ((0, 1, 1), (7, 1, 1), (1, 0, 1), (1, 1, 3), (True, 1, 1), (1.0, 1, 1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                CompressedCode(*args)
        for params in (dict(dt=1), dict(tau_e=0), dict(w_ee=1), dict(location_kappa=np.nan),
                       dict(joint_gains=(1, 1)), dict(rank_duration=0.8001)):
            with self.subTest(params=params), self.assertRaises(ValueError):
                ModelParameters(**params)
        m = RateDecompressor()
        with self.assertRaises(ValueError):
            m.initialize_population(np.zeros(6), m.encode_tuning(1, 1))
        state = m.initialize(CompressedCode(1, 1, 1))
        m.connections.rank_to_displacement[:] = 0
        with self.assertRaises(ValueError):
            m.advance(state)
        m.connections.gate_to_relay[:] = 1
        with self.assertRaises(ValueError):
            m.connections.validate()


if __name__ == "__main__":
    unittest.main()
