"""Dump per-page text of a PDF so a reader can quote exact sentences with page numbers.

Usage:
    python tools/dump_text.py <pdf> [--out <txt>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("--out", default=None)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=0, help="0 means last page")
    args = parser.parse_args()

    doc = pymupdf.open(args.pdf)
    end = args.end or doc.page_count
    chunks = []
    for index in range(args.start - 1, min(end, doc.page_count)):
        page = doc[index]
        chunks.append(f"\n===== PDF PAGE {index + 1} =====\n")
        chunks.append(page.get_text())
    text = "".join(chunks)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"{args.out} ({len(text)} chars, {doc.page_count} pages)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
