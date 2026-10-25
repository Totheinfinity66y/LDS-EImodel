"""Structural self-check for a reading.json card, per tools/READING_TASK.md's delivery checklist.

Checks schema, the five step titles, paragraph counts, layer/kind vocabularies,
annotation uniqueness, and that every refs id resolves.  Quote wording is checked
separately by tools/check_quotes.py and tools/verify_from_text.py.

Usage:
    python tools/check_card.py <card.json>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

STEP_TITLES = [
    "作者想解决什么问题",
    "用了什么方法",
    "得到了什么结果",
    "结果能否支持结论",
    "有哪些局限与启发",
]
LAYERS = {"author", "analysis"}
KINDS = {"background", "method", "result", "question", "implication"}


def main() -> int:
    card = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    problems = 0

    if card.get("schema") != "jzks-pdf-viewer/v1":
        print(f"schema is {card.get('schema')!r}, expected 'jzks-pdf-viewer/v1'")
        problems += 1
    for field in ("title", "authors", "doi"):
        if field not in card.get("paper", {}):
            print(f"paper.{field} missing")
            problems += 1
    if len(card.get("summary", "")) < 200:
        print("summary is shorter than 200 characters")
        problems += 1

    steps = card.get("steps", [])
    if len(steps) != 5:
        print(f"{len(steps)} steps, expected 5")
        problems += 1
    for index, step in enumerate(steps):
        if step.get("id") != index + 1:
            print(f"step {step.get('id')} has wrong id, expected {index + 1}")
            problems += 1
        if step.get("title") != STEP_TITLES[index]:
            print(f"step {step.get('id')} title is {step.get('title')!r}, expected {STEP_TITLES[index]!r}")
            problems += 1
        paragraphs = step.get("paragraphs", [])
        if len(paragraphs) < 2:
            print(f"step {step.get('id')} has {len(paragraphs)} paragraphs, expected >= 2")
            problems += 1
        for para in paragraphs:
            for field in ("title", "text", "layer", "refs"):
                if field not in para:
                    print(f"step {step.get('id')} paragraph missing {field}")
                    problems += 1
            if para.get("layer") not in LAYERS:
                print(f"step {step.get('id')} paragraph layer {para.get('layer')!r} invalid")
                problems += 1
            if not para.get("refs"):
                print(f"step {step.get('id')} paragraph {para.get('title')!r} has empty refs")
                problems += 1

    annotations = card.get("annotations", [])
    if len(annotations) < 10:
        print(f"{len(annotations)} annotations, expected >= 10")
        problems += 1
    ids = [a["id"] for a in annotations]
    for duplicate in [i for i, n in Counter(ids).items() if n > 1]:
        print(f"duplicate annotation id {duplicate}")
        problems += 1
    known = set(ids)
    for ann in annotations:
        for field in ("id", "step", "page", "title", "kind", "quote", "explanation", "layer"):
            if field not in ann:
                print(f"annotation {ann.get('id')} missing {field}")
                problems += 1
        if ann.get("kind") not in KINDS:
            print(f"annotation {ann.get('id')} kind {ann.get('kind')!r} invalid")
            problems += 1
        if ann.get("layer") not in LAYERS:
            print(f"annotation {ann.get('id')} layer {ann.get('layer')!r} invalid")
            problems += 1
        if ann.get("step") not in range(1, 6):
            print(f"annotation {ann.get('id')} step {ann.get('step')} invalid")
            problems += 1
        if not ann.get("explanation"):
            print(f"annotation {ann.get('id')} has empty explanation")
            problems += 1

    for step in steps:
        for para in step.get("paragraphs", []):
            for ref in para.get("refs", []):
                if ref not in known:
                    print(f"step {step.get('id')} references unknown id {ref}")
                    problems += 1

    print("\n--- structure ---")
    print("steps:", len(steps))
    for step in steps:
        layers = Counter(p["layer"] for p in step["paragraphs"])
        print(f"  step {step['id']}: {len(step['paragraphs'])} paragraphs  {dict(layers)}")
    print("annotations:", len(annotations))
    print("  per step:", dict(sorted(Counter(a["step"] for a in annotations).items())))
    print("  kinds:  ", dict(Counter(a["kind"] for a in annotations)))
    print("  layers: ", dict(Counter(a["layer"] for a in annotations)))
    print("  pages:  ", sorted(set(a["page"] for a in annotations)))
    print("  summary:", len(card.get("summary", "")), "characters")
    print(f"\n{len(problems)} structural problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
