"""Run unmodified author task code; reconstruct only explicit distance formulas.

This is not author Figure7 execution and does not train any neural network.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'artifacts/paper2agent_reproduction/references/zhou/author-source/Timing-WM_RNN_2022-main'


def cross_euclidean(control, perturbed):
    control = np.asarray(control, dtype=float)
    perturbed = np.asarray(perturbed, dtype=float)
    if control.ndim != 2 or perturbed.ndim != 2 or control.shape[1] != perturbed.shape[1]:
        raise ValueError('Expected [time, recurrent_unit] matrices')
    return np.linalg.norm(control[:, None, :] - perturbed[None, :, :], axis=-1)


def main():
    # Defaults extracted from actual author AST, without importing TF/train.py.
    tree = ast.parse((SOURCE / 'train.py').read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'get_default_hp')
    hp_ast = next(n.value for n in function.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'hp' for t in n.targets))
    hp = {}
    for key, value in zip(hp_ast.keys, hp_ast.values):
        try:
            hp[ast.literal_eval(key)] = ast.literal_eval(value)
        except ValueError:
            pass
    hp.update(n_input=33, n_output=2, rng=np.random.RandomState(7))
    spec = importlib.util.spec_from_file_location('zhou_author_task', SOURCE / 'task.py')
    task = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(task)
    trial = task.generate_trials('ITdDNMS', hp, mode='test', noise_on=False)
    out = Path(__file__).parent
    np.savez_compressed(out / 'author_task_inputs.npz', x=trial.x, y=trial.y, c_mask=trial.c_mask)
    t = np.arange(12.)
    trajectory = np.column_stack((t, np.zeros_like(t)))
    d = cross_euclidean(trajectory, trajectory)
    np.testing.assert_allclose(np.diag(d), 0)
    shifted = cross_euclidean(trajectory, np.column_stack((t+1, t*0)))
    assert np.argmin(shifted[4]) == 3
    offset = cross_euclidean(trajectory, trajectory + [0, 2])
    np.testing.assert_allclose(np.diag(offset), 2)
    decay = np.exp(-t)
    same_endpoint = cross_euclidean(np.column_stack((decay,t*0)), np.column_stack((-decay,t*0)))
    assert same_endpoint[-1,-1] < same_endpoint[0,0]
    other_endpoint = cross_euclidean(trajectory*0, trajectory*0 + [0, 1])
    np.testing.assert_allclose(other_endpoint, 1)
    report = {
        'status':'PARTIAL: author task generator executed; Figure7 unavailable',
        'source_task_sha256':hashlib.sha256((SOURCE/'task.py').read_bytes()).hexdigest(),
        'source_train_sha256':hashlib.sha256((SOURCE/'train.py').read_bytes()).hexdigest(),
        'executed_author_function':'task.generate_trials(ITdDNMS, defaults, test, noise_on=False)',
        'x_shape':list(trial.x.shape), 'y_shape':list(trial.y.shape),
        'no_recurrent_activity_generated':True,
        'synthetic_formula_checks':['identical','time shifted','parallel offset','same endpoint convergence','different fixed endpoints'],
        'synthetic_is_original_data':False,
        'numpy':np.__version__,
    }
    (out/'source_execution.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
