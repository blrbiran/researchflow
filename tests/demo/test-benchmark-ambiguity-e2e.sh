#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEMO="$ROOT/docs/demos/benchmark-ambiguity-e2e"

python3 - <<'PY2' "$DEMO"
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
required = {
    '01-literature-map.md': [
        'frozen_question',
        'retrieval_axes',
        'closest_works',
        'taxonomy_or_clusters',
        'likely_gap',
        'confidence_and_uncertainty',
    ],
    '02-structure-brief.md': [
        'paper_type',
        'thesis_or_goal',
        'logic_chain',
        'section_skeleton',
        'contribution_list',
        'structural_risks',
    ],
    '03-draft-packet.md': [
        'target_scope',
        'evidence_basis',
        'draft_text_or_path',
        'unresolved_gaps',
        'real_vs_planned_status',
    ],
    '04-review-packet.md': [
        'manuscript_summary',
        'critical_issues',
        'major_issues',
        'minor_issues',
        'revision_order',
        'recommended_next_phase',
    ],
    '05-submission-packet.md': [
        'artifact_inventory',
        'export_paths',
        'figure_status',
        'supplement_status',
        'go_no_go',
        'remaining_manual_checks',
    ],
}

heading_re = re.compile(r'^##\s+([a-zA-Z0-9_]+)\s*$', flags=re.MULTILINE)
for filename, headings in required.items():
    path = root / filename
    assert path.exists(), f'missing artifact: {filename}'
    text = path.read_text()
    matches = list(heading_re.finditer(text))
    found = {m.group(1): m for m in matches}
    missing = [heading for heading in headings if heading not in found]
    assert not missing, f'{filename} missing headings: {", ".join(missing)}'

    for heading in headings:
        start = found[heading].end()
        later = [m.start() for m in matches if m.start() > found[heading].start()]
        end = min(later) if later else len(text)
        body = text[start:end].strip()
        assert body, f'{filename} has empty section: {heading}'

print('ok - benchmark ambiguity demo satisfies required workflow contract fields and non-empty sections')
PY2
