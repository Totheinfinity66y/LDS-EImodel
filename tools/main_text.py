"""Print the main-text portion of a paper's text dump, stopping at the references.

Reference lists occupy a large share of a paper's pages but carry no content
for the five-step reading. This helper cuts the dump at the first reference
heading so the reader can spend context on the article body.

Usage:
    python tools/main_text.py <text.txt> [--refs] [--page N] [--from N] [--to N]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REFERENCE_HEADINGS = re.compile(
    r"^\s*(references|reference list|literature cited|bibliography)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def load_pages(text_path: Path) -> list[tuple[int, str]]:
    raw = text_path.read_text(encoding="utf-8")
    parts = re.split(r"===== PDF PAGE (\d+) =====", raw)
    pages = []
    for i in range(1, len(parts), 2):
        pages.append((int(parts[i]), parts[i + 1]))
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("--refs", action="store_true", help="print the reference section instead")
    parser.add_argument("--page", type=int, default=0, help="print one page")
    parser.add_argument("--from", dest="start", type=int, default=1)
    parser.add_argument("--to", dest="end", type=int, default=0)
    args = parser.parse_args()

    pages = load_pages(Path(args.text))

    if args.page:
        for num, body in pages:
            if num == args.page:
                sys.stdout.write(body)
        return 0

    selected = [
        (num, body)
        for num, body in pages
        if num >= args.start and (args.end == 0 or num <= args.end)
    ]

    if args.refs:
        sys.stdout.write("".join(body for _, body in selected))
        return 0

    cut = None
    for index, (num, body) in enumerate(selected):
        if REFERENCE_HEADINGS.search(body):
            cut = index
            break

    if cut is None:
        sys.stdout.write("".join(body for _, body in selected))
    else:
        sys.stdout.write("".join(body for _, body in selected[:cut]))
        print(f"\n[references start on PDF page {selected[cut][0]}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
