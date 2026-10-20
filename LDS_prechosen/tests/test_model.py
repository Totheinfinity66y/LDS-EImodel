import ast
from dataclasses import replace
from pathlib import Path
import unittest
import numpy as np
from LDS_prechosen import BranchModel, Code, Parameters, State, decode
from LDS_prechosen.evaluate import conditions, expected, geometry, evaluate


class BranchTests(unittest.TestCase):
    def test_all_conditions_and_geometry(self):
        runs = []
        for code in conditions():
            states, _ = BranchModel().run(code)
            self.assertEqual(tuple(map(decode, states)), expected(code))
            runs.append(states)
        result = geometry(runs)
        self.assertEqual(result["measured_orientation_counts"], [1, 2, 4, 4])
        self.assertEqual(result["centered_spatial_dimensions"], [[2]*4]*4)
        for angles in result["principal_angles_degrees"]:
            self.assertTrue(np.all(np.isclose(angles, 0, atol=1e-5) | np.isclose(angles, 90, atol=1e-5)))

    def test_consumed_codes_absent_and_forbidden(self):
        states, _ = BranchModel().run(Code(1, 1, 2))
        self.assertIsNone(states[1].direction_cue)
        for state in states[2:]:
            self.assertIsNone(state.direction_cue)
            self.assertIsNone(state.step_cue)
            with self.assertRaises(ValueError):
                replace(state, step_cue=[1, 0])
        with self.assertRaises(ValueError):
            replace(states[1], direction_cue=[0, 1])

    def test_restart_in_fresh_model_every_boundary(self):
        for code in conditions():
            states, _ = BranchModel().run(code)
            for rank in range(4):
                suffix, _ = BranchModel().resume(states[rank])
                for actual, want in zip(suffix, states[rank:]):
                    np.testing.assert_array_equal(actual.response, want.response)

    def test_gate_truth_table_and_input_sweep(self):
        for content in np.linspace(0, 1, 21):
            x = np.full((2, 6), content)
            np.testing.assert_array_equal(BranchModel.activate(x, [0, 0]), 0)
            np.testing.assert_allclose(BranchModel.activate(x, [1, 1]), x, atol=1e-15)
        np.testing.assert_array_equal(BranchModel.activate(np.zeros((2, 6)), [1, 1]), 0)

    def test_remove_direction_blocks_r2_and_downstream(self):
        model = BranchModel()
        state = replace(model.initialize(Code(1, 1, 2)), direction_cue=[0, 0])
        states, _ = model.resume(state)
        self.assertTrue(all(decode(s) is None for s in states[1:]))

    def test_step_is_only_needed_before_r3(self):
        model = BranchModel()
        r2, _ = model.advance(model.initialize(Code(1, 1, 2)))
        r3, _ = model.advance(replace(r2, step_cue=[0, 0]))
        self.assertIsNone(decode(r3))
        intact, _ = model.run(Code(1, 1, 2))
        self.assertEqual(decode(BranchModel().advance(intact[2])[0]), 5)

    def test_no_content_no_output(self):
        model = BranchModel()
        state = replace(model.initialize(Code(1, 1, 2)), response=np.zeros((1, 6)))
        states, _ = model.resume(state)
        self.assertTrue(all(decode(s) is None for s in states))

    def test_branch_relocation_changes_future_without_direction_code(self):
        model = BranchModel()
        r2 = model.run(Code(1, 1, 2))[0][1]
        moved = replace(r2, response=r2.response[::-1])
        states, _ = BranchModel().resume(moved)
        self.assertEqual(tuple(map(decode, states)), (2, 6, 5))

    def test_step_branch_relocation_changes_r4(self):
        r3 = BranchModel().run(Code(1, 1, 2))[0][2]
        moved = np.zeros_like(r3.response)
        moved[3] = r3.response[1]
        final, _ = BranchModel().advance(replace(r3, response=moved))
        self.assertEqual(decode(final), 3)

    def test_mixed_response_uses_all_branches_no_winner(self):
        model = BranchModel()
        x = np.zeros((4, 6))
        x[0, 0], x[2, 3] = .3, .7
        state = State(3, x)
        _, trace = model.advance(state)
        self.assertEqual(trace.drive[0, 1], .3)
        self.assertEqual(trace.drive[2, 2], .7)
        self.assertAlmostEqual(trace.drive.sum(), 1)

    def test_connection_cut_and_wrong_wiring_fail(self):
        model = BranchModel()
        model.weights[2][:] = 0
        self.assertIsNone(decode(model.run(Code(1, 1, 2))[0][-1]))
        model = BranchModel()
        model.weights[0][:] = 0
        model.weights[0][:, 0] = np.eye(6)
        self.assertNotEqual(tuple(map(decode, model.run(Code(1, 1, 2))[0])), (1, 2, 4, 5))

    def test_time_step_and_analytic_solution(self):
        first = BranchModel()
        second = BranchModel(Parameters(dt=.001))
        for code in conditions():
            a, traces = first.run(code)
            b, _ = second.run(code)
            self.assertEqual(tuple(map(decode, a)), tuple(map(decode, b)))
            np.testing.assert_allclose(a[-1].response, b[-1].response, atol=1e-4)
            for trace in traces:
                analytic = trace.drive * (1-np.exp(-first.params.duration/first.params.tau))
                np.testing.assert_allclose(trace.target_rates[-1], analytic, atol=1e-5)

    def test_immutability_and_history_independence(self):
        model = BranchModel()
        states, traces = model.run(Code(1, 1, 2))
        with self.assertRaises(ValueError):
            states[1].response[0, 0] = 0
        model.run(Code(6, -1, 1))
        fresh = BranchModel().run(Code(1, 1, 2))
        np.testing.assert_array_equal(states[-1].response, fresh[0][-1].response)
        self.assertFalse(traces[0].target_rates.flags.writeable)

    def test_invalid_inputs_and_weights(self):
        for args in ((True, 1, 1), (0, 1, 1), (1, 0, 1), (1, 1, 3), (1., 1, 1)):
            with self.assertRaises(ValueError):
                Code(*args)
        for params in ({"dt": .1}, {"tau": 0}, {"duration": .501}, {"dt": float('nan')}):
            with self.assertRaises(ValueError):
                Parameters(**params)
        with self.assertRaises(ValueError):
            State(3, np.full((4, 6), float('nan')))
        model = BranchModel()
        model.weights[0][0, 0, 0, 0] = -1
        with self.assertRaises(ValueError):
            model.run(Code(1, 1, 1))
        with self.assertRaises(ValueError):
            model.advance(BranchModel().run(Code(1, 1, 1))[0][-1])

    def test_no_old_model_or_evaluation_dependency(self):
        text = (Path(__file__).parents[1] / 'model.py').read_text(encoding='utf8')
        tree = ast.parse(text)
        imports = [n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertFalse(any('lds_decompressor' in x or 'evaluate' in x for x in imports))
        # Peak decoding is output-only, never used in advance/resume/run.
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'BranchModel')
        self.assertFalse(any(isinstance(n, ast.Name) and n.id == 'decode' for n in ast.walk(cls)))

    def test_evaluation_controls(self):
        summary, _, _ = evaluate()
        self.assertEqual(summary['correct'], 24)
        self.assertTrue(all(x < 24 for x in summary['negative_controls_correct'].values()))


if __name__ == '__main__':
    unittest.main()
