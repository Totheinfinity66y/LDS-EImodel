from dataclasses import fields, replace
from itertools import product
from pathlib import Path
import ast
import unittest
import numpy as np

from lds_competitive import CompressedCode, ModelParameters, NeuralState, Population, RateDecompressor
from lds_competitive.diagnostics import transition_metrics
from lds_competitive.model import PATH_NAMES, SHIFTS


class CircuitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = RateDecompressor()
        cls.results = {(l, d, s): cls.model.decompress(CompressedCode(l, d, s))
                       for l, d, s in product(range(1, 7), (1, -1), (1, 2))}

    def test_all_24_actual_four_rank_outputs(self):
        for (l, d, s), result in self.results.items():
            expected = tuple(1 + (l - 1 + d * k) % 6 for k in (0, 1, 1 + s, 2 + s))
            with self.subTest(L=l, D=d, S=s):
                self.assertEqual(result.positions, expected)
                self.assertTrue(all(transition_metrics(t)["position_peak_margin"] > 1e-8
                                    for t in result.transitions))

    def test_terminal_control_and_switching_contract_all_conditions(self):
        for key, result in self.results.items():
            for t in result.transitions:
                with self.subTest(condition=key, rank=t.from_rank):
                    self.assertTrue(transition_metrics(t)["control_pass"], transition_metrics(t))

    def test_coordinate_and_tuning_equations(self):
        m = self.model
        np.testing.assert_allclose(m.site_coordinates[0], (1, 0))
        self.assertLess(m.site_coordinates[1, 1], 0)
        for k, (d, s) in enumerate(product((1, -1), (1, 2))):
            enc = m.encode_tuning(d, s)
            self.assertEqual(np.argmax(enc.joint.activity), k)
            np.testing.assert_allclose(enc.joint.raw_drive,
                                      np.outer(enc.direction.activity, enc.step.activity).ravel())
            for pop in (enc.direction, enc.step, enc.joint):
                np.testing.assert_allclose(pop.activity, pop.rates / pop.rates.sum())

    def test_four_shared_paths_and_independent_rank_slices(self):
        c = self.model.connections
        for k, shift in enumerate(SHIFTS):
            for j in range(6):
                np.testing.assert_array_equal(c.e_to_branch[k] @ np.eye(6)[j], np.eye(6)[(j + shift) % 6])
        self.assertFalse(np.shares_memory(c.rank_to_readout[0], c.rank_to_readout[2]))
        np.testing.assert_array_equal(c.rank_to_readout.sum(axis=1), np.ones((3, 4)))

    def test_every_euler_update_uses_old_synchronous_state(self):
        t = self.results[1, 1, 2].transitions[1]
        p, c = self.model.params, self.model.connections
        k = 17
        np.testing.assert_allclose(t.v_rates[k + 1], t.v_rates[k] + p.dt / p.tau_v *
                                  (-t.v_rates[k] + np.maximum(t.readout_drive + c.gate_to_readout @ t.g_rates[k], 0)))
        np.testing.assert_allclose(t.g_rates[k + 1], t.g_rates[k] + p.dt / p.tau_g *
                                  (-t.g_rates[k] + c.readout_to_gate @ t.v_rates[k]))
        np.testing.assert_allclose(t.e_rates[k + 1], t.e_rates[k] + p.dt / p.tau_e *
                                  (-t.e_rates[k] + np.maximum(t.m_rates[k] + p.w_ee * t.e_rates[k] - p.w_ei * t.i_rates[k], 0)))

    def test_control_continuity_relay_reset_and_real_transient_leakage(self):
        traces = self.results[1, 1, 2].transitions
        self.assertGreater(transition_metrics(traces[0])["leakage_peak"], 0)
        self.assertGreater(transition_metrics(traces[1])["leakage_integral"], 0)
        for index, t in enumerate(traces):
            np.testing.assert_array_equal(t.m_rates[0], 0)
            if index:
                for key in ("e_rates", "i_rates", "v_rates", "g_rates"):
                    np.testing.assert_array_equal(getattr(t, key)[0], getattr(traces[index - 1], key)[-1])

    def test_joint_intervention_changes_actual_sequence(self):
        m = RateDecompressor()
        state = m.initialize(CompressedCode(1, 1, 2))
        joint = Population(state.encoding.joint.names, [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1])
        altered = replace(state, encoding=replace(state.encoding, joint=joint))
        self.assertEqual(m.resume(altered).positions, (1, 6, 4, 3))

    def test_rank_intervention_is_causal_and_local(self):
        m = RateDecompressor()
        m.connections.rank_to_readout[1] = 0
        m.connections.rank_to_readout[1, 2] = 1
        result = m.decompress(CompressedCode(1, 1, 2))
        self.assertEqual(result.positions, (1, 2, 1, 2))

    def test_selected_path_disconnection_breaks_sequence(self):
        m = RateDecompressor()
        m.connections.e_to_branch[1] = 0
        self.assertNotEqual(m.decompress(CompressedCode(1, 1, 2)).positions, (1, 2, 4, 5))

    def test_path_gate_ablation_removes_directional_transmission(self):
        m = RateDecompressor()
        m.connections.gate_to_branch[:] = 0
        a, b = m.initialize(CompressedCode(1, 1, 2)), m.initialize(CompressedCode(1, -1, 2))
        for _ in range(3):
            a, _ = m.advance(a)
            b, _ = m.advance(b)
            np.testing.assert_array_equal(a.e_rates, b.e_rates)
        with self.assertRaisesRegex(ValueError, "unique"):
            m.decompress(CompressedCode(1, 1, 2))

    def test_competitive_feedback_and_gate_excitation_have_causal_effects(self):
        baseline = self.results[1, 1, 2].transitions[1]
        m = RateDecompressor()
        m.connections.gate_to_readout[:] = 0
        changed = m.decompress(CompressedCode(1, 1, 2)).transitions[1]
        self.assertGreater(np.max(np.abs(changed.v_rates - baseline.v_rates)), 1e-4)
        self.assertGreater(np.sort(changed.v_rates[-1])[-2], 1e-4)
        m = RateDecompressor()
        m.connections.readout_to_gate[:] = 0
        _, trace = m.advance(m.initialize(CompressedCode(1, 1, 2)))
        np.testing.assert_array_equal(trace.g_rates, 0)
        self.assertGreater(transition_metrics(trace)["terminal_blocked_drive"], 0)

    def test_symbols_read_once_and_never_retained(self):
        class Once:
            def __init__(self):
                self.counts = dict(location=0, direction=0, step=0)
            def __getattr__(self, name):
                self.counts[name] += 1
                if self.counts[name] > 1:
                    raise AssertionError("Symbol reread")
                return dict(location=2, direction=-1, step=2)[name]
        code = Once()
        self.assertEqual(RateDecompressor().decompress(code).positions, (2, 1, 5, 4))
        self.assertEqual(code.counts, dict(location=1, direction=1, step=1))
        self.assertEqual({f.name for f in fields(NeuralState)},
                         {"e_rates", "i_rate", "v_rates", "g_rates", "m_rates", "encoding", "rank"})

    def test_model_has_no_oracle_import_or_symbolic_gating(self):
        import lds_competitive.model as module
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        imports = [x.module or "" for x in ast.walk(tree) if isinstance(x, ast.ImportFrom)]
        self.assertFalse(any(any(bad in x for bad in ("evaluation", "reference", "lds_decompressor", "hennequin")) for x in imports))
        advance = next(x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef) and x.name == "advance")
        self.assertFalse(any(isinstance(x, ast.Attribute) and x.attr == "argmax" for x in ast.walk(advance)))

    def test_no_hidden_history_arrays_readonly_and_instances_independent(self):
        m = RateDecompressor()
        code = CompressedCode(6, -1, 2)
        before = m.decompress(code)
        m.decompress(CompressedCode(2, 1, 1))
        np.testing.assert_array_equal(before.position_activity, m.decompress(code).position_activity)
        other = RateDecompressor()
        other.connections.e_to_branch[:] = 0
        self.assertGreater(m.connections.e_to_branch.sum(), 0)
        with self.assertRaises(ValueError):
            before.transitions[0].v_rates[0, 0] = 2

    def test_rotational_equivariance_for_noncentral_input(self):
        m = RateDecompressor()
        enc = m.encode_tuning(-1, 2)
        base = m.resume(m.initialize_population(m.encode_angle(0.19), enc))
        for k in range(1, 6):
            shifted = m.resume(m.initialize_population(m.encode_angle(0.19 + k * np.pi / 3), enc))
            np.testing.assert_allclose(shifted.position_activity, np.roll(base.position_activity, k, axis=1), atol=1e-12)

    def test_invalid_parameters_silent_tied_drive_and_sign_violation(self):
        for args in ((0, 1, 1), (1, 0, 1), (1, 1, 3), (True, 1, 1), (1.0, 1, 1)):
            with self.assertRaises(ValueError):
                CompressedCode(*args)
        for kw in (dict(dt=.1), dict(tau_v=0), dict(w_ee=1), dict(rank_duration=.8001)):
            with self.assertRaises(ValueError):
                ModelParameters(**kw)
        m = RateDecompressor()
        with self.assertRaises(ValueError):
            m.initialize_population(np.zeros(6), m.encode_tuning(1, 1))
        state = m.initialize(CompressedCode(1, 1, 1))
        m.connections.rank_to_readout[0] = 0
        with self.assertRaisesRegex(ValueError, "unique"):
            m.advance(state)
        m.connections.rank_to_readout[0] = 1
        with self.assertRaisesRegex(ValueError, "unique"):
            m.advance(state)
        m.connections.gate_to_readout[0, 0] = 1
        with self.assertRaisesRegex(ValueError, "sign"):
            m.connections.validate()


if __name__ == "__main__":
    unittest.main()
