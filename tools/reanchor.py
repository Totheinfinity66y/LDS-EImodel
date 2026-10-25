"""Re-anchor a reading.json card onto a different PDF edition of the same paper.

Page numbers and quotes are edition-specific: a card written against one PDF
build may fail to resolve against another printing of the same article. This
helper relocates each annotation to the page where its quote actually occurs
and, when the quote straddles a page break, shortens it to the longest prefix
that still sits on a single page.

Usage:
    python tools/reanchor.py <card.json> <target.pdf> [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pymupdf


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def page_stream(page) -> str:
    return "".join(norm(w[4]) for w in page.get_text("words"))


def occurrences(streams: list[str], needle: str) -> list[tuple[int, int]]:
    hits = []
    for index, stream in enumerate(streams):
        count = stream.count(needle)
        if count:
            hits.append((index + 1, count))
    return hits


def shrink(words: list[str], streams: list[str]) -> tuple[str, int, int] | None:
    """Longest word prefix of the quote that occurs exactly once in the document."""
    for length in range(len(words), 5, -1):
        candidate = " ".join(words[:length])
        needle = norm(candidate)
        if len(needle) < 12:
            continue
        hits = occurrences(streams, needle)
        if len(hits) == 1:
            return candidate, hits[0][0], hits[0][1]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("card")
    parser.add_argument("pdf")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    card_path = Path(args.card)
    card = json.loads(card_path.read_text(encoding="utf-8-sig"))
    doc = pymupdf.open(args.pdf)
    streams = [page_stream(page) for page in doc]

    changed = 0
    for ann in card["annotations"]:
        quote = ann["quote"]
        words = quote.split()
        needle = norm(quote)
        hits = occurrences(streams, needle)
        if len(hits) == 1 and hits[0][0] == ann["page"]:
            continue
        fixed = shrink(words, streams)
        if fixed is None:
            print(f"{ann['id']}: no single-page variant found (hits={hits})")
            continue
        new_quote, page, count = fixed
        print(f"{ann['id']}: p{ann['page']} -> p{page}, {len(words)} -> {len(new_quote.split())} words")
        ann["quote"] = new_quote
        ann["page"] = page
        changed += 1

    if changed and args.write:
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {card_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
