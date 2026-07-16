#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
DEMO="$ROOT/docs/demos/agent-memory-e2e"

for f in   "$DEMO/01-literature-map.md"   "$DEMO/02-structure-brief.md"   "$DEMO/03-draft-packet.md"   "$DEMO/04-review-packet.md"   "$DEMO/05-submission-packet.md"; do
  test -f "$f"
done

grep -q '^## frozen_question$' "$DEMO/01-literature-map.md"
grep -q '^## paper_type$' "$DEMO/02-structure-brief.md"
grep -q '^## target_scope$' "$DEMO/03-draft-packet.md"
grep -q '^## manuscript_summary$' "$DEMO/04-review-packet.md"
grep -q '^## artifact_inventory$' "$DEMO/05-submission-packet.md"

echo 'ok - end-to-end demo artifacts satisfy the minimum contract headings'
