"""Build the reader for one paper: fit the quotes, check them, then build.

This is the single path every paper takes.  It runs the quote fitter, refuses
to continue while any quote still fails to resolve, and only then hands the
card to the viewer builder, so a reader can never ship with a highlight that
does not point at its evidence.

Usage:
    python tools/build_paper.py <paper-directory> [<paper-directory> ...]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".agents" / "skills" / "jzks-pdf-viewer" / "scripts" / "build_viewer.py"


def run(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def build_one(directory: Path) -> bool:
    pdf = directory / f"{directory.name.split('_')[0]}.pdf"
    card_path = directory / "reading.json"
    reader = directory / "reader"

    if not pdf.exists():
        print(f"{directory.name}: missing PDF {pdf.name}")
        return False
    if not card_path.exists():
        print(f"{directory.name}: missing reading.json")
        return False

    code, output = run([sys.executable, str(ROOT / "tools" / "fit_quotes.py"), str(card_path), str(pdf), "--write"])
    print(f"{directory.name}: fit_quotes -> {code}")
    if code != 0:
        print(output.strip()[-2000:])
        return False

    code, output = run([sys.executable, str(ROOT / "tools" / "check_quotes.py"), str(pdf), str(card_path)])
    tail = output.strip().splitlines()[-1] if output.strip() else ""
    print(f"{directory.name}: check_quotes -> {code} ({tail})")
    if code != 0:
        print(output.strip()[-4000:])
        return False

    code, output = run(
        [sys.executable, str(SKILL), "--pdf", str(pdf), "--card", str(card_path), "--out", str(reader)]
    )
    print(f"{directory.name}: build_viewer -> {code}")
    if code != 0:
        print(output.strip()[-3000:])
        return False

    report = json.loads((reader / "build-report.json").read_text(encoding="utf-8-sig"))
    print(
        f"{directory.name}: {report.get('matched')}/{report.get('annotations')} matched, "
        f"unresolved={report.get('unresolved')}"
    )
    return not report.get("unresolved")


def main() -> int:
    ok = True
    for argument in sys.argv[1:]:
        ok = build_one(Path(argument).resolve()) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
