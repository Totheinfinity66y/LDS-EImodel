"""Record the actual-image visual review of the Figure 1-3 and Figure 10 renders.

The reviewer opened each PNG in this session and inspected panels, axes, legends,
units and annotations. This script only hashes the files that were opened and
writes the review receipt; it recomputes no data and changes no model.
"""
from pathlib import Path
import hashlib
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'artifacts/neural_paper_figures_v1'

OPENED = [
    'figures/main/fig01_one_hot.png',
    'figures/main/fig02_one_hot.png',
    'figures/main/fig03_one_hot.png',
    'figures/main/fig10_encoding_comparison.png',
    'figures/supplementary/fig01_ring.png',
    'figures/supplementary/fig01_topology.png',
    'figures/supplementary/fig02_ring.png',
    'figures/supplementary/fig02_topology.png',
    'figures/supplementary/fig03_ring.png',
    'figures/supplementary/fig03_topology.png',
]

CHECKS = [
    'No blank panels and no cropped axes, legends or colorbars',
    'Rate axes labelled dimensionless; no Hz claim',
    'All 132 units retained; no silent removal of silent neurons',
    'E/I identity and fixed-network scope stated in captions',
    'Full-state and projected quantities visually distinguished',
    'NA used where a quantity is undefined rather than filled with zero',
    'Deterministic condition counts shown without invented confidence intervals',
]

NOTES = {
    'figures/main/fig03_one_hot.png':
        'Panel (f) carries dense overlapping annotation text; still legible but crowded. '
        'Retained as rendered, not regenerated, because changing it would not affect any number.',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    images = {}
    for relative in OPENED:
        path = ARCHIVE / relative
        if not path.is_file():
            raise SystemExit(f'missing reviewed image: {relative}')
        images[relative] = digest(path)

    receipt = {
        'status': 'PASS_WITH_LIMITS',
        'reviewer': 'root session, independent of the Figure 1-3 and Figure 10 implementation',
        'method': 'Actual opening of each listed PNG at full size; no model or data changes',
        'scope': 'Figure 1-3 and Figure 10 for one_hot, plus the ring and topology '
                 'supplementary renders of Figures 1-3',
        'checks': CHECKS,
        'images': images,
        'notes': NOTES,
        'limitations': [
            'Figure 4-7 and Figure 8-9 have their own separate visual receipts',
            'Reference original panels were not re-opened in this pass; no source-exact claim is made',
        ],
        'environment': {
            'python': sys.version,
            'platform': platform.platform(),
        },
    }
    out = ARCHIVE / 'manifests' / 'fig01_03_10_visual_validation.json'
    out.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {out.relative_to(ROOT)} ({len(images)} images)')


if __name__ == '__main__':
    main()
