#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
"$ROOT/tests/claude-code/test-manifests.sh"
python3 "$ROOT/tests/claude-code/test-routing-docs.py" "$ROOT"
