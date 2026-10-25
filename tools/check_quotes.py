"""Check that every annotation quote in a reading.json uniquely locates on its page.

Mirrors the locator used by the jzks-pdf-viewer build script so that a card can
be validated before the full viewer is built. Prints the offending entries and,
for near-misses, the candidate sentences that could replace them.

Usage:
    python tools/check_quotes.py <pdf> <card.json>
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def locate(page, quote: str):
    words = page.get_text("words")
    chars: list[str] = []
    mapping: list[int] = []
    for i, word in enumerate(words):
        s = norm(word[4])
        chars.extend(s)
        mapping.extend([i] * len(s))
    stream = "".join(chars)
    needle = norm(quote)
    if len(needle) < 12:
        return "quote_too_short"
    starts = [m.start() for m in re.finditer(re.escape(needle), stream)]
    if len(starts) != 1:
        return "ambiguous" if starts else "not_found"
    return "matched"


def sentences(page) -> list[str]:
    text = re.sub(r"\s+", " ", page.get_text()).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if len(norm(p)) >= 30]


def main() -> int:
    pdf_path, card_path = Path(sys.argv[1]), Path(sys.argv[2])
    doc = pymupdf.open(pdf_path)
    card = json.loads(card_path.read_text(encoding="utf-8-sig"))
    annotations = card["annotations"]

    problems = 0
    for ann in annotations:
        page_no = ann["page"]
        if not 1 <= page_no <= doc.page_count:
            print(f"{ann['id']}: page {page_no} out of range")
            problems += 1
            continue
        page = doc[page_no - 1]
        status = locate(page, ann["quote"])
        if status == "matched":
            continue
        problems += 1
        print(f"\n{ann['id']} (p{page_no}) status={status}")
        print(f"  quote: {ann['quote'][:160]}")
        print("  candidates on that page:")
        for cand in sentences(page)[:12]:
            print(f"    - {cand[:170]}")

    ids = [a["id"] for a in annotations]
    if len(ids) != len(set(ids)):
        print("duplicate annotation ids")
        problems += 1
    by_id = {a["id"]: a for a in annotations}
    for step in card["steps"]:
        for para in step["paragraphs"]:
            for ref in para["refs"]:
                if ref not in by_id:
                    print(f"step {step['id']} references unknown id {ref}")
                    problems += 1

    print(f"\n{len(annotations) - problems}/{len(annotations)} quotes resolvable; {problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
