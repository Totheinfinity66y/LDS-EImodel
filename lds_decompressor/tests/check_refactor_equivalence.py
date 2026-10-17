"""Compare every original array against the immutable pre-refactor Git source.

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

    def compare(before, after, name="result"):
        nonlocal arrays
        if isinstance(before, np.ndarray):
            np.testing.assert_array_equal(before, after, err_msg=name)
            arrays += 1
        elif is_dataclass(before):
            # Compare all baseline fields, including recordings when available.
            for field in fields(before):
                compare(getattr(before, field.name), getattr(after, field.name),
                        f"{name}.{field.name}")
        elif isinstance(before, (tuple, list)):
            assert len(before) == len(after), name
            for index, (a, b) in enumerate(zip(before, after)):
                compare(a, b, f"{name}[{index}]")
        else:
            assert before == after, (name, before, after)

    def compare_result(before, after):
        compare(before, after)
        if hasattr(before, "recording"):
            compare(before.recording, after.recording, "result.recording")

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
        for code in product(range(1, 7), (1, -1), (1, 2)):
            compare_result(before.decompress(original.CompressedCode(*code)),
                           after.decompress(current.CompressedCode(*code)))
    print(f"EXACT: 96 full sequences, {arrays} original arrays, zero differences")

    before, after = original.RateDecompressor(), current.RateDecompressor()
    for angle in (np.arange(72) + 0.173) * 2 * np.pi / 72:
        for direction, step in product((1, -1), (1, 2)):
            a = before.initialize_population(before.encode_angle(float(angle)),
                                             before.encode_tuning(direction, step))
            b = after.initialize_population(after.encode_angle(float(angle)),
                                            after.encode_tuning(direction, step))
            compare_result(before.resume(a), after.resume(b))
    print(f"EXACT: 288 off-site sequences; cumulative original arrays: {arrays}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE_COMMIT,
                        help="Immutable Git revision; use " + ARCHITECTURE_BASELINE_COMMIT
                             + " to include pre-architecture recordings")
    args = parser.parse_args()
    with baseline_model(args.baseline) as original:
        compare_models(original)
    print(f"Baseline: {args.baseline}")


if __name__ == "__main__":
    main()
