"""Compare every original array against the immutable pre-refactor Git source.

Run from the repository root using the verified analysis interpreter:
python -m lds_decompressor.tests.check_refactor_equivalence
"""

from dataclasses import fields, is_dataclass
from itertools import product
from pathlib import Path
import shutil
import subprocess
import sys
import types

import numpy as np

from lds_decompressor import model as current


BASELINE_COMMIT = "4424b97d8b4f5ff30b0fedc2d6a2ccb7ac9efd34"


def main():
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git executable is required to read the immutable baseline")
    source = subprocess.run(
        [git, "show", f"{BASELINE_COMMIT}:lds_decompressor/model.py"],
        cwd=Path(__file__).parents[2], check=True, capture_output=True, encoding="utf-8",
    ).stdout
    original = types.ModuleType("_original_lds_refactor_reference")
    sys.modules[original.__name__] = original
    exec(compile(source, f"{BASELINE_COMMIT}:lds_decompressor/model.py", "exec"),
         original.__dict__)
    arrays = 0

    def compare(before, after, name="result"):
        nonlocal arrays
        if isinstance(before, np.ndarray):
            np.testing.assert_array_equal(before, after, err_msg=name)
            arrays += 1
        elif is_dataclass(before):
            # Compare every pre-existing field; recordings are new inspection data.
            for field in fields(before):
                compare(getattr(before, field.name), getattr(after, field.name),
                        f"{name}.{field.name}")
        elif isinstance(before, (tuple, list)):
            assert len(before) == len(after), name
            for index, (a, b) in enumerate(zip(before, after)):
                compare(a, b, f"{name}[{index}]")
        else:
            assert before == after, (name, before, after)

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
            compare(before.decompress(original.CompressedCode(*code)),
                    after.decompress(current.CompressedCode(*code)))
    print(f"EXACT: 96 full sequences, {arrays} original arrays, zero differences")

    before, after = original.RateDecompressor(), current.RateDecompressor()
    for angle in (np.arange(72) + 0.173) * 2 * np.pi / 72:
        for direction, step in product((1, -1), (1, 2)):
            a = before.initialize_population(before.encode_angle(float(angle)),
                                             before.encode_tuning(direction, step))
            b = after.initialize_population(after.encode_angle(float(angle)),
                                            after.encode_tuning(direction, step))
            compare(before.resume(a), after.resume(b))
    print(f"EXACT: 288 off-site sequences; cumulative original arrays: {arrays}")
    print(f"Baseline: {BASELINE_COMMIT}")


if __name__ == "__main__":
    main()
