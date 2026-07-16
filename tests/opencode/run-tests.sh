#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
node "$ROOT/tests/opencode/test-bootstrap.mjs"
