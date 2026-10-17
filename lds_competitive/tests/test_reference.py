from dataclasses import replace
from itertools import product
import unittest
import numpy as np

from lds_competitive import CompressedCode, ModelParameters, RateDecompressor
from lds_competitive.diagnostics import (
    AGGREGATION_TOLERANCE, DT_DIFFERENCE_LIMIT, ODE_COARSE_LIMIT,
    ODE_REFINEMENT_RATIO, packed_trace,
)
from lds_competitive.reference import expanded_euler, ode_reference
from lds_competitive.timeline import build_timeline


class ReferenceTests(unittest.TestCase):
    def compare_expanded(self, model, code):
        initial = model.initialize(code)
        result = model.resume(initial)
        reference = expanded_euler(model, initial)
        for measured, ref in zip(result.transitions, reference):
            np.testing.assert_allclose(packed_trace(measured), ref["rates"], atol=AGGREGATION_TOLERANCE, rtol=0)
        return result

    def test_expanded_four_path_aggregation_all_24_codes(self):
        m = RateDecompressor()
        for l, d, s in product(range(1, 7), (1, -1), (1, 2)):
            with self.subTest(L=l, D=d, S=s):
                self.compare_expanded(m, CompressedCode(l, d, s))

    def test_aggregation_when_multiple_paths_are_active_and_B_is_not_identity(self):
        m = RateDecompressor()
        m.connections.gate_to_branch[:] = 0
        m.connections.branch_to_m[:] = np.array([
            .30 * np.eye(6), .20 * np.roll(np.eye(6), 1, axis=0),
            .25 * np.eye(6), .15 * np.roll(np.eye(6), -1, axis=0),
        ])
        # Compare actual states without decoding the deliberately ambiguous E.
        state = m.initialize(CompressedCode(1, 1, 2))
        refs = expanded_euler(m, state)
        for ref in refs:
            state, trace = m.advance(state)
            self.assertTrue(np.all(trace.branch_target.sum(axis=2) > 0))
            np.testing.assert_allclose(packed_trace(trace), ref["rates"], atol=AGGREGATION_TOLERANCE, rtol=0)

    def test_fixed_A_B_and_gate_connection_interventions_preserve_aggregation(self):
        m = RateDecompressor()
        m.connections.e_to_branch[1] *= .6
        m.connections.branch_to_m[2] *= .8
        m.connections.gate_to_branch[:, :, 1] *= .75
        self.compare_expanded(m, CompressedCode(2, -1, 2))

    def test_dt_halving_all_24_conditions(self):
        a, b = RateDecompressor(), RateDecompressor(ModelParameters(dt=.001))
        for l, d, s in product(range(1, 7), (1, -1), (1, 2)):
            code = CompressedCode(l, d, s)
            coarse, fine = a.decompress(code), b.decompress(code)
            with self.subTest(L=l, D=d, S=s):
                self.assertEqual(coarse.positions, fine.positions)
                error = np.max(np.abs(build_timeline(coarse).rates - build_timeline(fine).rates[::2]))
                self.assertLessEqual(error, DT_DIFFERENCE_LIMIT)

    def test_independent_ode_reference_and_first_order_convergence(self):
        a, b = RateDecompressor(), RateDecompressor(ModelParameters(dt=.001))
        for d, s in product((1, -1), (1, 2)):
            coarse = a.decompress(CompressedCode(1, d, s))
            fine = b.decompress(CompressedCode(1, d, s))
            ref = ode_reference(a, a.encode_angle(0), a.encode_tuning(d, s), .001)
            coarse_error = max(np.max(np.abs(packed_trace(t) - r[::2])) for t, r in zip(coarse.transitions, ref))
            fine_error = max(np.max(np.abs(packed_trace(t) - r)) for t, r in zip(fine.transitions, ref))
            with self.subTest(D=d, S=s):
                self.assertLessEqual(coarse_error, ODE_COARSE_LIMIT)
                self.assertLessEqual(fine_error, ODE_REFINEMENT_RATIO * coarse_error)


if __name__ == "__main__":
    unittest.main()
