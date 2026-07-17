#!/usr/bin/env python3
import sys
from pathlib import Path

root = Path(sys.argv[1])
using = (root / 'skills' / 'using-researchflow' / 'SKILL.md').read_text(encoding='utf-8')

assert 'docs/workflow-contracts.md' in using
assert 'Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.' in using
assert 'External reference libraries may not introduce new top-level phases in V1.' in using
assert 'Ask exactly one clarifying question only when the request could plausibly belong to two adjacent phases' in using

readme = (root / 'README.md').read_text(encoding='utf-8')
claude = (root / 'CLAUDE.md').read_text(encoding='utf-8')
claude_doc = (root / 'docs' / 'README.claude.md').read_text(encoding='utf-8')
handover = (root / 'docs' / 'handover' / 'researchwork-plugin-handover.md').read_text(encoding='utf-8')

assert 'thin router' in readme
assert 'Surface intent proposes a phase; artifact stability confirms it or routes earlier.' in readme
assert 'Keep `using-researchflow` as a thin router over the existing five-phase workflow.' in claude
assert 'Do not turn support skills or external references into peer top-level routes.' in claude
assert 'If the user asks to write an introduction without a stable literature-backed gap, the router should still start at `literature-discovery`.' in claude_doc
assert 'If the user asks to export a PDF from a still-unreviewed manuscript, the router should still start at `paper-review`.' in claude_doc
assert 'Router model: thin router;' in handover
assert 'repo-local routing-doc smoke coverage' in handover

print('ok - using-researchflow encodes the thin-router invariants')
