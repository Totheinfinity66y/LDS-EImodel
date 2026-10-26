import ast
import inspect
from pathlib import Path
import unittest
import numpy as np
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import encode
from handcrafted_ei.simulation import run_trial


class BoundaryTests(unittest.TestCase):
    def test_imports_and_runtime_shifts(self):
        root = Path(__file__).parents[1]
        for path in (root / 'model').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for n in ast.walk(tree):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    self.assertNotRegex(ast.unparse(n), r'\b(task|evaluation)\b')
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                    self.assertNotEqual(n.func.attr, 'roll')
                    if n.func.attr == 'argmax':
                        self.fail('model must only expose continuous readout')
        src = inspect.getsource(run_trial)
        self.assertNotRegex(src, r'\b(target|direction|location)\b')

    def test_interface_and_target_isolation(self):
        m = EINetwork()
        self.assertEqual(list(inspect.signature(m.apply_input).parameters), ['x_L','x_D','x_S'])
        for name in ('force_correct_response', 'set_true_D_branch', 'update_S_from_reward'):
            self.assertFalse(hasattr(m, name))
        class ShieldedInput(dict):
            @property
            def target(self):
                raise AssertionError('target accessed during trial')
        result = run_trial(m, ShieldedInput(encode(0, 1, 2)))
        self.assertEqual(result.outputs, (0, 1, 3, 4))
        m = EINetwork()
        before=m.rates.copy()
        m.apply_input(**encode(0, 1, 1))
        np.testing.assert_array_equal(before,m.rates)  # input cannot write rates
        m.integrate(200)
        before = m.rates.copy()
        m.readout()
        np.testing.assert_array_equal(before, m.rates)

    def test_fixed_topology_across_trials_and_phases(self):
        m = EINetwork()
        weights = m.weights.copy()
        run_trial(m, encode(5,-1,2))
        np.testing.assert_array_equal(weights, m.weights)
        self.assertFalse(any('M_L' in s or 'M_DS' in s for s in m.groups))

