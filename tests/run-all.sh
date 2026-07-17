#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)

printf '==> Running OpenCode smoke test\n'
"$ROOT/tests/opencode/run-tests.sh"

printf '\n==> Running Claude Code smoke test\n'
"$ROOT/tests/claude-code/run-tests.sh"

printf '\n==> Running workflow demo contract tests\n'
"$ROOT/tests/demo/test-agent-memory-e2e.sh"
"$ROOT/tests/demo/test-benchmark-ambiguity-e2e.sh"

printf '\nAll ResearchFlow tests passed.\n'
