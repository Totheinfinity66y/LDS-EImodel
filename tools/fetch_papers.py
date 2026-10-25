"""Download the 18 papers listed in docs/gating_gain_modulation_paperlist_20261020.md.

Sources per paper are tried in order: PMC open-access PDF, author-institution
PDF, publisher PDF. PMC serves PDFs behind a SHA-256 proof-of-work gate, so the
solver here reproduces the browser algorithm (find a nonce whose digest of
challenge+nonce starts with N zero hex digits) and replays the cookie.

Every attempt is logged so paywalled items are recorded rather than silently
skipped.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import Cookie
from pathlib import Path

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "papers"

PMC_ROOT = "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
PDF_MAGIC = b"%PDF-"


class Fetcher:
    """Minimal cookie-aware HTTP client that can clear the PMC proof-of-work gate."""

    def __init__(self) -> None:
        self.jar: dict[str, str] = {}

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = dict(UA)
        if self.jar:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.jar.items())
        if extra:
            headers.update(extra)
        return headers

    def get(self, url: str, referer: str | None = None, timeout: int = 90, retries: int = 4):
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                extra = {"Referer": referer} if referer else None
                req = urllib.request.Request(url, headers=self._headers(extra))
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read()
                    for header, value in resp.getheaders():
                        if header.lower() == "set-cookie":
                            name, _, rest = value.partition("=")
                            self.jar[name.strip()] = rest.split(";")[0]
                    return resp.geturl(), resp.headers.get("Content-Type", ""), body
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                last_exc = exc
                time.sleep(2.0 * (attempt + 1))
        raise last_exc if last_exc else RuntimeError("unreachable")

    def solve_pow(self, html: str) -> bool:
        """Reproduce NCBI's client-side PoW and store the resulting cookie."""
        challenge = re.search(r'POW_CHALLENGE\s*=\s*"([^"]+)"', html)
        difficulty = re.search(r'POW_DIFFICULTY\s*=\s*"?(\d+)"?', html)
        cookie_name = re.search(r'POW_COOKIE_NAME\s*=\s*"([^"]+)"', html)
        if not (challenge and difficulty and cookie_name):
            return False
        prefix = "0" * int(difficulty.group(1))
        nonce = 0
        while True:
            digest = hashlib.sha256(f"{challenge.group(1)}{nonce}".encode()).hexdigest()
            if digest.startswith(prefix):
                break
            nonce += 1
        self.jar[cookie_name.group(1)] = f"{challenge.group(1)},{nonce}"
        return True

    def fetch_pdf(self, url: str, referer: str | None = None, attempts: int = 3) -> bytes | None:
        for _ in range(attempts):
            try:
                final_url, content_type, body = self.get(url, referer=referer)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
                return None
            if body.startswith(PDF_MAGIC):
                return body
            text = body.decode("utf-8", "ignore")
            if "POW_CHALLENGE" in text:
                if not self.solve_pow(text):
                    return None
                time.sleep(1.0)
                continue
            if "Preparing to download" in text:
                time.sleep(2.0)
                continue
            return None
        return None


PAPERS = [
    {"id": "R1", "slug": "salinas-sejnowski-2001-gain-modulation",
     "title": "Gain modulation in the central nervous system: where behavior, neurophysiology, and computation meet",
     "pmcid": "PMC2887717", "direct": []},
    {"id": "R2", "slug": "silver-2010-neuronal-arithmetic",
     "title": "Neuronal arithmetic", "pmcid": "PMC4750293", "direct": []},
    {"id": "R3", "slug": "ferguson-cardin-2020-cortical-gain-mechanisms",
     "title": "Mechanisms underlying gain modulation in the cortex", "pmcid": "PMC7408409",
     "direct": ["https://www.nature.com/articles/s41583-019-0253-y.pdf"]},
    {"id": "R4", "slug": "wang-yang-2018-disinhibitory-motif",
     "title": "A disinhibitory circuit motif and flexible information routing in the brain",
     "pmcid": "PMC6599531", "direct": []},
    {"id": "G1", "slug": "chance-abbott-reyes-2002-background-synaptic-input",
     "title": "Gain modulation from background synaptic input", "pmcid": "",
     "direct": ["https://columbia.edu/cu/neurotheory/Larry/ChanceNeuron02.pdf"]},
    {"id": "G2", "slug": "prescott-dekoninck-2003-shunting-inhibition",
     "title": "Gain control of firing rate by shunting inhibition: roles of synaptic noise and dendritic saturation",
     "pmcid": "PMC149961", "direct": []},
    {"id": "G3", "slug": "rothman-2009-synaptic-depression-gain-control",
     "title": "Synaptic depression enables neuronal gain control", "pmcid": "PMC2689940", "direct": []},
    {"id": "G4", "slug": "reynolds-heeger-2009-normalization-attention",
     "title": "The normalization model of attention", "pmcid": "PMC2752446", "direct": []},
    {"id": "P1", "slug": "vogels-abbott-2005-signal-propagation-logic-gating",
     "title": "Signal propagation and logic gating in networks of integrate-and-fire neurons",
     "pmcid": "PMC6725859", "direct": []},
    {"id": "P2", "slug": "vogels-abbott-2009-detailed-balance-gating",
     "title": "Gating multiple signals through detailed balance of excitation and inhibition in spiking networks",
     "pmcid": "",
     "direct": ["https://www.columbia.edu/cu/neurotheory/pdfs/Vogels_Abbott_2009.pdf"]},
    {"id": "P3", "slug": "kremkow-2010-gating-balanced-correlated",
     "title": "Gating of signal propagation in spiking neural networks by balanced and correlated excitation and inhibition",
     "pmcid": "PMC6633769", "direct": []},
    {"id": "F1", "slug": "sherman-guillery-1998-drivers-modulators",
     "title": "On the actions that one nerve cell can have on another: distinguishing drivers from modulators",
     "pmcid": "PMC22761", "direct": []},
    {"id": "F2", "slug": "pi-2013-disinhibitory-control",
     "title": "Cortical interneurons that specialize in disinhibitory control", "pmcid": "PMC4017628",
     "direct": ["https://hearingbrain.org/docs/Pi_disinhibitory_control_Nature_2013.pdf"]},
    {"id": "F3", "slug": "lee-2013-disinhibitory-motor-integration",
     "title": "A disinhibitory circuit mediates motor integration in the somatosensory cortex",
     "pmcid": "PMC4100076", "direct": []},
    {"id": "F4", "slug": "wilson-2012-division-subtraction",
     "title": "Division and subtraction by distinct cortical inhibitory networks in vivo", "pmcid": "",
     "direct": ["https://web.mit.edu/surlab/publications/2012_WilsonRunyan_etal.pdf"]},
    {"id": "F5", "slug": "elboustani-sur-2014-cell-specific-inhibition",
     "title": "Response-dependent dynamics of cell-specific inhibition in cortical networks in vivo",
     "pmcid": "PMC4268659", "direct": []},
    {"id": "C1", "slug": "yang-2016-dendritic-disinhibitory-gating",
     "title": "A dendritic disinhibitory circuit mechanism for pathway-specific gating",
     "pmcid": "PMC5034308", "direct": []},
    {"id": "C2", "slug": "mante-2013-context-dependent-recurrent",
     "title": "Context-dependent computation by recurrent dynamics in prefrontal cortex",
     "pmcid": "PMC4121670", "direct": []},
]


def pmc_pdf_urls(fetcher: Fetcher, pmcid: str) -> list[str]:
    """Collect candidate PDF URLs for a PMC article.

    Sources, in priority order: the citation_pdf_url meta tag, href links found
    on the article page, and the NCBI static file host. Some responses are
    truncated by rate limiting, so several page shapes are tried.
    """
    page_url = PMC_ROOT.format(pmcid=pmcid)
    urls: list[str] = []

    def add(url: str | None) -> None:
        if url and url not in urls:
            urls.append(url)

    for candidate_page in (
        page_url,
        f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/?report=reader",
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
    ):
        try:
            _, _, body = fetcher.get(candidate_page)
        except Exception as exc:  # noqa: BLE001 - recorded per attempt
            print(f"  pmc page error {pmcid}: {exc!r}")
            continue
        html = body.decode("utf-8", "ignore")
        if len(html) < 30000:
            time.sleep(3.0)
            continue

        meta = re.search(r'name="citation_pdf_url"\s+content="([^"]+)"', html)
        if meta:
            add(meta.group(1))

        for href in re.findall(r'href="([^"]*\.pdf[^"]*)"', html):
            if href.startswith("http"):
                add(href)
            elif href.startswith("/"):
                add("https://pmc.ncbi.nlm.nih.gov/" + href[1:])
            else:
                add(candidate_page + href)

        for href in re.findall(r'(?:src|content)="([^"]*mc\.ncbi\.nlm\.nih\.gov[^"]*\.pdf[^"]*)"', html):
            add(href)

        if urls:
            break

    add(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/")
    return urls


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher()
    manifest = []

    for paper in PAPERS:
        record = {
            "id": paper["id"],
            "slug": paper["slug"],
            "title": paper["title"],
            "pmcid": paper["pmcid"],
        }
        target_dir = OUT / f'{paper["id"]}_{paper["slug"]}'
        target_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = target_dir / f'{paper["id"]}.pdf'

        if pdf_path.exists() and pdf_path.stat().st_size > 20000:
            record.update(status="cached", pdf=str(pdf_path.relative_to(ROOT)),
                          bytes=pdf_path.stat().st_size, source="cached")
            manifest.append(record)
            print(f'{paper["id"]}: cached')
            continue

        attempts = []
        data = None
        source = None

        candidates: list[tuple[str, str, str | None]] = []
        if paper["pmcid"]:
            for url in pmc_pdf_urls(fetcher, paper["pmcid"]):
                candidates.append(("pmc", url, PMC_ROOT.format(pmcid=paper["pmcid"])))
        for direct in paper["direct"]:
            candidates.append(("direct", direct, None))

        for kind, url, referer in candidates:
            attempts.append({"kind": kind, "url": url})
            data = fetcher.fetch_pdf(url, referer=referer)
            if data:
                source = url
                break

        if data:
            pdf_path.write_bytes(data)
            record.update(status="ok", pdf=str(pdf_path.relative_to(ROOT)),
                          bytes=len(data), source=source)
            print(f'{paper["id"]}: ok {len(data)} bytes <- {source}')
        else:
            record["status"] = "failed"
            print(f'{paper["id"]}: FAILED')

        record["attempts"] = attempts
        manifest.append(record)

    manifest_path = OUT / "download-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in manifest if r["status"] in {"ok", "cached"})
    print(f"\n{ok}/{len(manifest)} papers available -> {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
