"""Run from repository root: python -m lds_decompressor --output ..."""

import argparse
from pathlib import Path

from .evaluation import run


def main():
    parser = argparse.ArgumentParser(description="Evaluate the independent six-site L/D/S rate circuit")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "artifacts")
    parser.add_argument("--probe-angles", type=int, default=72)
    args = parser.parse_args()
    summary, passed = run(args.output, n_angles=args.probe_angles)
    print(f"Discrete conditions: {summary['correct']}/{summary['conditions']}")
    print(f"Spatial probes: {summary['spatial_probe_correct']}/{summary['spatial_probe_conditions']}")
    print(f"Artifacts: {args.output.resolve()}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
