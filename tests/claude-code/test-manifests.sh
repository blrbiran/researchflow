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
assert (root / 'skills' / 'using-researchflow' / 'SKILL.md').exists()
print('ok - claude manifests point at researchflow and bootstrap skill exists')
PY
