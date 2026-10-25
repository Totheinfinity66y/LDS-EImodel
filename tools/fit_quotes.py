"""Fit each annotation quote to a verbatim, uniquely locatable span in the PDF.

The viewer locates a quote by searching the normalised word stream of a page,
so a quote must appear there as one contiguous run of characters.  PyMuPDF
emits a page block by block and a block line by line, and inside a block the
words of one line of one column stay together, so a quote can span a whole
line of a column but must not cross into the neighbouring column.

That last point matters more than it looks.  On a page that carries a summary
column beside the body text, PyMuPDF merges both into a single block and
interleaves their lines in the flat stream, so a contiguous run of words can
splice the two columns together.  Such a span still locates, but it reads as
nonsense, so this tool refuses to produce one.

The tool therefore labels every line with a column, found by clustering the
left edges of the lines on the page, and requires a quote to stay inside one
column.  Within that column it finds the longest run of the intended quote
that the PDF really does contain, anchors the quote at that run, and grows it
to the end of the sentence.  Line-break hyphenation is healed ("modu-" +
"lated" -> "modulated"), which does not change the normalised text because
normalisation drops punctuation, so uniqueness is unaffected.

The annotation's own page is tried first, so a quote never silently migrates
to a page that merely happens to contain similar words.

The intended quotes are read from ``source-quotes.json`` next to the card when
that file exists, otherwise from the card itself.  Use ``--write`` to store the
fitted quotes back into the card.

Usage:
    python tools/fit_quotes.py <card.json> <pdf> [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pymupdf

SENTENCE_END = re.compile(r'[.!?]["\'’”\)\]]*$')
MAX_WORDS = 45


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def join(words: list[str]) -> str:
    """Rebuild readable text from PDF words, healing line-break hyphenation."""
    out = ""
    for word in words:
        if not out:
            out = word
        elif out.endswith("-"):
            out += word
        else:
            out += " " + word
    return out


class Page:
    """The flat word stream of one page, with every word labelled by column."""

    def __init__(self, page: pymupdf.Page) -> None:
        raw = page.get_text("words")
        self.words = [w[4] for w in raw]
        self.norm_words = [norm(w) for w in self.words]
        self.left = [w[0] for w in raw]
        self.right = [w[2] for w in raw]
        self.stream = "".join(self.norm_words)

        # PyMuPDF sorts words by block then line, so the words of one line are
        # consecutive in the flat stream.
        self.lines: list[tuple[int, int]] = []  # (first index, one past last)
        for index, word in enumerate(raw):
            key = (word[5], word[6])
            if self.lines and raw[self.lines[-1][0]][5] == key[0] and raw[self.lines[-1][0]][6] == key[1]:
                start = self.lines[-1][0]
                self.lines[-1] = (start, index + 1)
            else:
                self.lines.append((index, index + 1))

        # Cluster the left edges of the lines to find the columns.
        edges = sorted({round(self.left[start]) for start, _ in self.lines})
        clusters: list[list[int]] = []
        for edge in edges:
            if clusters and edge - clusters[-1][-1] < 40:
                clusters[-1].append(edge)
            else:
                clusters.append([edge])
        centres = [sum(group) / len(group) for group in clusters]

        self.column_of_word: list[int] = []
        for start, end in self.lines:
            nearest = min(range(len(centres)), key=lambda i: abs(centres[i] - self.left[start]))
            self.column_of_word.extend([nearest] * (end - start))

    def count(self, text: str) -> int:
        return self.stream.count(norm(text))

    def coherent(self, start: int, end: int) -> bool:
        """Reject spans that leave a column or jump backwards on the page."""
        column = self.column_of_word[start]
        for index in range(start + 1, end):
            if self.column_of_word[index] != column:
                return False
            if self.left[index] < self.right[index - 1] - 12:
                return False
        return True


def longest_run(quote_words: list[str], page_words: list[str]) -> tuple[int, int]:
    """Longest contiguous run of the quote found in the page word stream.

    A run that matches the *start* of the quote is preferred, because it keeps
    the excerpt anchored to the wording that was meant to be cited.  Only when
    no such run exists is a run matching the quote at any offset accepted.

    Returns (length of run, index in the stream where it starts).
    """
    best = (0, 0)
    for quote_start in range(len(quote_words)):
        for stream_start in range(len(page_words)):
            length = 0
            while (
                quote_start + length < len(quote_words)
                and stream_start + length < len(page_words)
                and quote_words[quote_start + length]
                and quote_words[quote_start + length] == page_words[stream_start + length]
            ):
                length += 1
            if length > best[0]:
                best = (length, stream_start)
    return best


def prefix_run(quote_words: list[str], page_words: list[str]) -> tuple[int, int]:
    """Longest run matching the start of the quote, anywhere in the stream."""
    best = (0, 0)
    for stream_start in range(len(page_words)):
        length = 0
        while (
            length < len(quote_words)
            and stream_start + length < len(page_words)
            and quote_words[length]
            and quote_words[length] == page_words[stream_start + length]
        ):
            length += 1
        if length > best[0]:
            best = (length, stream_start)
    return best


def ends_sentence(word: str) -> bool:
    return bool(SENTENCE_END.search(word.strip()))


def sentence_end(words: list[str], start: int, stop: int) -> int:
    """Index one past the end of the sentence containing ``start``."""
    index = start
    while index < stop:
        if ends_sentence(words[index]):
            index += 1
            # A sentence may continue over an abbreviation such as "et al.".
            if index < stop and words[index][:1].islower():
                index -= 1
            break
        index += 1
    return index


def grow(page: Page, start: int, length: int) -> int:
    """Index one past the end of the sentence that starts at ``start``."""
    column = page.column_of_word[start]
    stop = start
    while stop < len(page.words) and page.column_of_word[stop] == column:
        stop += 1
    return min(sentence_end(page.words, start + length, stop), start + MAX_WORDS)


def build_text(page: Page, start: int, length: int) -> str | None:
    """Turn a matched run into a unique, coherent quote."""
    stop = grow(page, start, length)
    candidates = [
        (start, stop),
        (start, start + length),
        (start, min(stop, start + length + 30)),
    ]

    for begin, end in candidates:
        if end <= begin or not page.coherent(begin, end):
            continue
        trial = join(page.words[begin:end])
        if len(norm(trial)) >= 12 and page.count(trial) == 1:
            return trial

    # Nothing was unique as grown: trim the bare run until it is.
    for begin, end in candidates:
        while end > begin + 1:
            if not page.coherent(begin, end):
                end -= 1
                continue
            trial = join(page.words[begin:end])
            if page.count(trial) == 1 and len(norm(trial)) >= 12:
                return trial
            end -= 1
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
    pages = [Page(page) for page in doc]

    intended_path = card_path.parent / "source-quotes.json"
    intended = {}
    if intended_path.exists():
        intended = json.loads(intended_path.read_text(encoding="utf-8-sig"))

    changed = 0
    for ann in card["annotations"]:
        want = intended.get(ann["id"], ann["quote"])
        quote_words = [part for part in (norm(w) for w in want.split()) if part]
        if not quote_words:
            continue

        order = [ann["page"] - 1] + [i for i in range(len(pages)) if i != ann["page"] - 1]

        found = None
        for page_index in order:
            page = pages[page_index]
            length, start = prefix_run(quote_words, page.norm_words)
            if length < 3:
                length, start = longest_run(quote_words, page.norm_words)
            if length < 3:
                continue
            text = build_text(page, start, length)
            if text is not None:
                found = (page_index, text)
                break

        if found is None:
            print(f"{ann['id']}: no unique quote found")
            continue

        page_index, text = found
        if text != ann["quote"] or (page_index + 1) != ann["page"]:
            changed += 1
            print(
                f"{ann['id']}: p{ann['page']} -> p{page_index + 1} "
                f"({len(ann['quote'].split())} -> {len(text.split())} words)"
            )
        ann["quote"] = text
        ann["page"] = page_index + 1

    if changed and args.write:
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {card_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
