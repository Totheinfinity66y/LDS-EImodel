"""Verify every downloaded paper: title match, page count, and text-layer presence.

Writes artifacts/papers/verification.json so that later reading stages can rely
on a known page range for each PDF.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = ROOT / "artifacts" / "papers"

STOPWORDS = {"the", "of", "and", "in", "a", "for", "to", "with", "on", "by"}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def title_match(pdf_title: str, expected: str) -> float:
    """Fraction of expected title content words present in the PDF's first page."""
    pdf_words = set(normalize(pdf_title).split())
    want = [w for w in normalize(expected).split() if w not in STOPWORDS]
    if not want:
        return 0.0
    hit = sum(1 for w in want if w in pdf_words)
    return hit / len(want)


def main() -> int:
    manifest = json.loads((PAPERS_DIR / "download-manifest.json").read_text(encoding="utf-8"))
    results = []

    for entry in manifest:
        record = dict(entry)
        record.pop("attempts", None)
        pdf_path = ROOT / entry["pdf"]
        if not pdf_path.exists():
            record["verification"] = {"ok": False, "error": "missing file"}
            results.append(record)
            continue

        doc = pymupdf.open(pdf_path)
        first_page_text = doc[0].get_text().strip()
        full_text = "".join(page.get_text() for page in doc)
        text_chars = len(full_text.strip())
        record["verification"] = {
            "ok": True,
            "pages": doc.page_count,
            "text_chars": text_chars,
            "text_layer": text_chars > 500 * max(1, doc.page_count // 10),
            "first_page_head": re.sub(r"\s+", " ", first_page_text[:200]),
            "title_match": round(title_match(first_page_text[:1500], entry["title"]), 3),
        }
        record["verification"]["ok"] = bool(
            doc.page_count >= 2 and record["verification"]["title_match"] >= 0.45
        )
        doc.close()
        results.append(record)
        print(f'{entry["id"]}: pages={record["verification"]["pages"]} '
              f'chars={record["verification"]["text_chars"]} '
              f'match={record["verification"]["title_match"]} '
              f'{"OK" if record["verification"]["ok"] else "CHECK"}')

    out = PAPERS_DIR / "verification.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in results if r["verification"].get("ok"))
    print(f"\n{ok}/{len(results)} verified -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
