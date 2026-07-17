#!/usr/bin/env python3
import sys
from pathlib import Path

root = Path(sys.argv[1])
using = (root / 'skills' / 'using-researchflow' / 'SKILL.md').read_text(encoding='utf-8')

assert 'docs/workflow-contracts.md' in using
assert 'Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.' in using
assert 'External reference libraries may not introduce new top-level phases in V1.' in using
assert 'Ask exactly one clarifying question only when the request could plausibly belong to two adjacent phases' in using

print('ok - using-researchflow encodes the thin-router invariants')
