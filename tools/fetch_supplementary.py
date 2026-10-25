"""Fetch supplementary PDF(s) for a PMC article, reusing the PoW-capable Fetcher.

Usage:
    python tools/fetch_supplementary.py <PMCID> <out_dir>
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_papers import Fetcher  # noqa: E402

LINK_RE = re.compile(r'href="([^"]*(?:supplement|MOESM)[^"]*\.pdf[^"]*)"', re.I)


def main() -> int:
    pmcid = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    fetcher = Fetcher()
    page = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    _, _, body = fetcher.get(page)
    html = body.decode("utf-8", "replace")

    links = sorted(set(LINK_RE.findall(html)))
    if not links:
        # Retry once: PMC's HTML is not always identical between requests.
        time.sleep(2)
        _, _, body = fetcher.get(page)
        html = body.decode("utf-8", "replace")
        links = sorted(set(LINK_RE.findall(html)))

    if not links:
        print(f"{pmcid}: NO SUPPLEMENTARY LINK FOUND")
        return 2

    print(f"{pmcid}: {len(links)} candidate link(s)")
    ok = 0
    for link in links:
        url = link.replace("&amp;", "&")
        if url.startswith("/"):
            url = "https://pmc.ncbi.nlm.nih.gov" + url
        name = url.rsplit("/", 1)[-1] or f"{pmcid}-suppl.pdf"
        target = out_dir / name
        if target.exists() and target.stat().st_size > 1000:
            print(f"  cached {name} ({target.stat().st_size} bytes)")
            ok += 1
            continue
        data = fetcher.fetch_pdf(url, referer=page)
        if data and data.startswith(b"%PDF"):
            target.write_bytes(data)
            print(f"  saved {name} ({len(data)} bytes)")
            ok += 1
        else:
            print(f"  FAILED {name}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
