"""Repair a reading.json whose string values contain bare ASCII double quotes.

Chinese prose often quotes terms with ASCII ". Such quotes are illegal inside a
JSON string, so the file fails to parse. This tool rewrites those inner quotes
as full-width curly quotes (" ") while leaving JSON structural quotes intact.

A quote inside a string closes the string only when the next non-whitespace
character is one of , } ] : -- exactly the characters that may legally follow a
JSON string (a value or a key). Any other quote is an inner quotation mark and
is rewritten. Pairing is tracked per string so that opening and closing marks
alternate correctly.

Usage:
    python tools/fix_json.py <card.json> [--check]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

STRUCTURAL_FOLLOWERS = set(",}]:")
OPENING = "“"
CLOSING = "”"


def repair(text: str) -> tuple[str, int]:
    out: list[str] = []
    in_string = False
    escaped = False
    expect_opening = True
    changed = 0
    index = 0
    length = len(text)

    while index < length:
        char = text[index]
        if not in_string:
            out.append(char)
            if char == '"':
                in_string = True
                expect_opening = True
            index += 1
            continue

        if escaped:
            out.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            out.append(char)
            escaped = True
            index += 1
            continue
        if char == '"':
            lookahead = index + 1
            while lookahead < length and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < length and text[lookahead] in STRUCTURAL_FOLLOWERS:
                out.append(char)
                in_string = False
            else:
                out.append(OPENING if expect_opening else CLOSING)
                expect_opening = not expect_opening
                changed += 1
            index += 1
            continue

        out.append(char)
        index += 1

    return "".join(out), changed


def main() -> int:
    path = Path(sys.argv[1])
    check_only = "--check" in sys.argv[2:]
    original = path.read_text(encoding="utf-8")

    try:
        json.loads(original)
        print(f"{path}: already valid JSON")
        return 0
    except json.JSONDecodeError as exc:
        print(f"{path}: invalid as written ({exc.msg} at line {exc.lineno})")

    repaired, changed = repair(original)
    try:
        json.loads(repaired)
    except json.JSONDecodeError as exc:
        print(f"{path}: repair failed, still invalid ({exc.msg} at line {exc.lineno})")
        return 1

    if check_only:
        print(f"{path}: would rewrite {changed} inner quotes")
        return 0

    path.write_text(repaired, encoding="utf-8")
    print(f"{path}: rewrote {changed} inner quotes; file now valid JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())
