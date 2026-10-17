"""Compare downstream dynamics and projected relay state to immutable Git models.

Run from the repository root using the verified analysis interpreter:
python -m lds_decompressor.tests.check_refactor_equivalence
"""

import argparse
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
import importlib
from itertools import product
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

import numpy as np

from lds_decompressor import model as current


BASELINE_COMMIT = "4424b97d8b4f5ff30b0fedc2d6a2ccb7ac9efd34"
ARCHITECTURE_BASELINE_COMMIT = "c56c80d2972da7689425aaf85b910db2d8287d41"
AGGREGATION_BASELINE_COMMIT = "9b984877909f2e25809c7e801865d48935912f94"


@contextmanager
def baseline_model(revision):
    """Import a read-only Git snapshot as an isolated temporary package.

    Relative imports follow that snapshot, never the working model. This also
    supports baselines with neuron-owned state and transition recordings.
    """
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git executable is required to read the immutable baseline")
    root = Path(__file__).parents[2]

    def git_read(*args):
        return subprocess.run([git, *args], cwd=root, check=True,
                              capture_output=True, encoding="utf-8").stdout

    name = "_original_lds_refactor_reference"
    with tempfile.TemporaryDirectory(prefix=".lds-equivalence-", dir=root) as folder:
        for filename in git_read("ls-tree", "--name-only",
                                 f"{revision}:lds_decompressor").splitlines():
            if filename.endswith(".py"):
                Path(folder, filename).write_text(
                    git_read("show", f"{revision}:lds_decompressor/{filename}"),
                    encoding="utf-8")
        package = types.ModuleType(name)
        package.__path__ = [folder]
        sys.modules[name] = package
        try:
            yield importlib.import_module(f"{name}.model")
        finally:
            for key in tuple(sys.modules):
                if key == name or key.startswith(name + "."):
                    del sys.modules[key]


def compare_models(original):
    arrays = 0
    projection = None
    max_error = 0.0

    def project(values):
        return np.einsum("pij,...pj->...i", projection, values)

    def compare_recording(before, after, name):
        compare(before.time, after.time, name + ".time")
        if len(before.labels) == 47:
            mapped = np.c_[before.rates[:, :22],
                           project(before.rates[:, 22:46].reshape(-1, 4, 6)),
                           before.rates[:, -1]]
            compare(mapped, after.rates, name + ".rates")
            compare(np.r_[before.labels[:22], [f"M{k}" for k in range(1, 7)], before.labels[-1:]],
                    after.labels, name + ".labels")
            compare(np.r_[before.groups[:22], ["Relay"] * 6, before.groups[-1:]],
                    after.groups, name + ".groups")
            compare(np.r_[before.modes[:22], ["integrated"] * 6, before.modes[-1:]],
                    after.modes, name + ".modes")
        else:
            for key in ("rates", "labels", "groups", "modes"):
                compare(getattr(before, key), getattr(after, key), name + "." + key)

    def compare(before, after, name="result"):
        nonlocal arrays, max_error
        if isinstance(before, np.ndarray):
            if before.dtype.kind == "f":
                # Summation and Euler updating commute algebraically; their
                # floating-point operation order need not be bit-identical.
                np.testing.assert_allclose(before, after, rtol=2e-13, atol=2e-13, err_msg=name)
                max_error = max(max_error, float(np.max(np.abs(before - after))))
            else:
                np.testing.assert_array_equal(before, after, err_msg=name)
            arrays += 1
        elif is_dataclass(before):
            for field in fields(before):
                value = getattr(before, field.name)
                other = getattr(after, field.name)
                if field.name == "recording":
                    compare_recording(value, other, f"{name}.recording")
                else:
                    if field.name in {"relay_rates", "relay_target"} and value.ndim > other.ndim:
                        if field.name == "relay_target":
                            compare(value, after.relay_path_targets, name + ".relay_path_targets")
                        value = project(value)
                    compare(value, other, f"{name}.{field.name}")
        elif isinstance(before, (tuple, list)):
            assert len(before) == len(after), name
            for index, (a, b) in enumerate(zip(before, after)):
                compare(a, b, f"{name}[{index}]")
        elif isinstance(before, (float, np.floating)):
            np.testing.assert_allclose(before, after, rtol=2e-13, atol=2e-13, err_msg=name)
            max_error = max(max_error, abs(float(before) - float(after)))
        else:
            assert before == after, (name, before, after)

    def compare_result(before, after):
        compare(before, after)
        if hasattr(before, "recording"):
            compare_recording(before.recording, after.recording, "result.recording")

    settings = [
        {}, {"dt": 0.001},
        {"direction_slope": 2, "step_slope": 3, "joint_gains": (2, 1, 0.7, 1.2),
         "readout_gains": (1.1, 0.8, 1.4, 0.9)},
        {"encoding_duration": 0.07, "readout_duration": 0.09, "gate_duration": 0.11,
         "w_ee": 0.08, "w_ei": 0.3, "w_ie": 0.4, "gate_strength": 1.7},
    ]
    for config in settings:
        before = original.RateDecompressor(original.ModelParameters(**config))
        after = current.RateDecompressor(current.ModelParameters(**config))
        projection = before.connections.relay_to_e
        for code in product(range(1, 7), (1, -1), (1, 2)):
            compare_result(before.decompress(original.CompressedCode(*code)),
                           after.decompress(current.CompressedCode(*code)))
    print(f"PASS: 96 full sequences, {arrays} compared arrays")

    before, after = original.RateDecompressor(), current.RateDecompressor()
    projection = before.connections.relay_to_e
    for angle in (np.arange(72) + 0.173) * 2 * np.pi / 72:
        for direction, step in product((1, -1), (1, 2)):
            a = before.initialize_population(before.encode_angle(float(angle)),
                                             before.encode_tuning(direction, step))
            b = after.initialize_population(after.encode_angle(float(angle)),
                                            after.encode_tuning(direction, step))
            compare_result(before.resume(a), after.resume(b))
    print(f"PASS: 288 off-site sequences; cumulative arrays: {arrays}")
    rng = np.random.default_rng(724)
    for variant in ("no-gates", "broken-path", "weighted-output"):
        before, after = original.RateDecompressor(), current.RateDecompressor()
        if variant == "no-gates":
            before.connections.gate_to_relay[:] = 0
        elif variant == "broken-path":
            before.connections.e_to_relay[1] = 0
        else:
            before.connections.relay_to_e[:] = rng.random((4, 6, 6))
        for key in vars(before.connections):
            getattr(after.connections, key)[:] = getattr(before.connections, key)
        projection = before.connections.relay_to_e
        for code in product(range(1, 7), (1, -1), (1, 2)):
            a = before.initialize(original.CompressedCode(*code))
            b = after.initialize(current.CompressedCode(*code))
            state_a, trace_a = before.advance(a)
            state_b, trace_b = after.advance(b)
            compare(state_a, state_b)
            compare(trace_a, trace_b, "transition")
    print(f"PASS: 72 intervention transitions; total arrays: {arrays}")
    print(f"Maximum absolute array error: {max_error:.17g}; rtol=atol=2e-13")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=AGGREGATION_BASELINE_COMMIT,
                        help="Immutable Git revision; use " + ARCHITECTURE_BASELINE_COMMIT
                             + " to include pre-architecture recordings")
    args = parser.parse_args()
    with baseline_model(args.baseline) as original:
        compare_models(original)
    print(f"Baseline: {args.baseline}")


if __name__ == "__main__":
    main()
