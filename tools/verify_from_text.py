"""Check that every annotation quote appears verbatim on its stated page of text.txt.

``tools/check_quotes.py`` proves that a quote locates uniquely inside the PDF,
which is what the viewer needs.  This tool proves the complementary thing: that
the quote really was copied out of the extracted text of that physical page,
so a mis-transcribed page number or a quote invented from the abstract cannot
slip through.

Both checks are normalised the same way, so a hyphenated line break in the
extracted text still matches the healed quote.

Usage:
    python tools/verify_from_text.py <text.txt> <card.json>
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def split_pages(text: str) -> dict[int, str]:
    pages: dict[int, str] = {}
    parts = re.split(r"===== PDF PAGE (\d+) =====", text)
    for index in range(1, len(parts), 2):
        pages[int(parts[index])] = parts[index + 1]
    return pages


def main() -> int:
    text_path, card_path = Path(sys.argv[1]), Path(sys.argv[2])
    pages = split_pages(text_path.read_text(encoding="utf-8"))
    card = json.loads(card_path.read_text(encoding="utf-8-sig"))

    problems = 0
    for ann in card["annotations"]:
        page = ann["page"]
        if page not in pages:
            print(f"{ann['id']}: page {page} is not in the extracted text")
            problems += 1
            continue
        needle = norm(ann["quote"])
        if not needle:
            print(f"{ann['id']}: empty quote")
            problems += 1
            continue
        if needle not in norm(pages[page]):
            print(f"{ann['id']} (p{page}): quote not found in the text of that page")
            print(f"  quote: {ann['quote'][:140]}")
            problems += 1

    print(f"\n{len(card['annotations']) - problems}/{len(card['annotations'])} quotes present in text.txt; {problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
