"""Find which PDF page(s) of a text dump contain a candidate quote.

Usage:
    python tools/find_quote.py <text.txt> "<quote>" ["<quote>" ...]
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def load_pages(text_path: Path) -> list[tuple[int, str]]:
    raw = text_path.read_text(encoding="utf-8")
    parts = re.split(r"===== PDF PAGE (\d+) =====", raw)
    pages = []
    for i in range(1, len(parts), 2):
        pages.append((int(parts[i]), parts[i + 1]))
    return pages


def main() -> int:
    text_path = Path(sys.argv[1])
    pages = load_pages(text_path)
    normalized = [(num, norm(body)) for num, body in pages]

    for quote in sys.argv[2:]:
        needle = norm(quote)
        hits = [num for num, body in normalized if needle and needle in body]
        # A quote is safely page-unique when exactly one page contains it.
        print(f"{len(hits)} hit(s) {hits} :: {quote[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
