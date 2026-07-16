#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
python3 - <<'PY' "$ROOT"
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
plugin = json.loads((root / '.claude-plugin' / 'plugin.json').read_text())
market = json.loads((root / '.claude-plugin' / 'marketplace.json').read_text())
assert plugin['name'] == 'researchflow'
assert market['plugins'][0]['name'] == 'researchflow'
for rel in [
    'skills/using-researchflow/SKILL.md',
    'skills/figure-support/SKILL.md',
    'skills/submission-readiness/SKILL.md',
    'skills/arxiv/scripts/search_arxiv.py',
    'skills/arxiv-pdf-download/scripts/download_arxiv_refs.py',
    'skills/arxiv-pdf-download/scripts/organize_pdf_titles.py',
    'docs/workflow-contracts.md',
]:
    assert (root / rel).exists(), rel
print('ok - claude manifests point at researchflow and support skills/scripts exist')
PY
