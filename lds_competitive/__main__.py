import argparse
import json
from pathlib import Path
from .evaluation import run


def main():
    parser = argparse.ArgumentParser(description="Evaluate and plot the independent 29-rate competitive circuit")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    summary = run(args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
