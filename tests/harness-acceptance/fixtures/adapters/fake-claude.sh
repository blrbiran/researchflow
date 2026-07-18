#!/usr/bin/env bash
set -euo pipefail

SCENARIO_DIR="${RF_SCENARIO_DIR:?}"
REPO_ROOT="${RF_REPO_ROOT:?}"

command="${1:-}"
case "$command" in
  version)
    cat "$SCENARIO_DIR/version.txt"
    ;;
  help)
    cat "$SCENARIO_DIR/help.txt"
    ;;
  plugin)
    subcommand="${2:-}"
    case "$subcommand" in
      help)
        cat "$SCENARIO_DIR/plugin-help.txt"
        ;;
      list)
        python3 - "$SCENARIO_DIR/marketplace-list-template.json" "$REPO_ROOT" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for item in payload:
    if item.get("path") == "__REPO_ROOT__":
        item["path"] = sys.argv[2]
print(json.dumps(payload, indent=2))
PY
        ;;
      validate)
        cat "$SCENARIO_DIR/validate.txt"
        exit "$(cat "$SCENARIO_DIR/validate.exit")"
        ;;
      *)
        printf 'unknown plugin subcommand: %s\n' "$subcommand" >&2
        exit 2
        ;;
    esac
    ;;
  canary)
    mode="${2:-}"
    file="$SCENARIO_DIR/${mode}.jsonl"
    cat "$file"
    exit "$(cat "$SCENARIO_DIR/${mode}.exit")"
    ;;
  case)
    case_id="${2:?}"
    cat "$SCENARIO_DIR/cases/${case_id}.jsonl"
    exit "$(cat "$SCENARIO_DIR/cases/${case_id}.exit")"
    ;;
  *)
    printf 'unknown command: %s\n' "$command" >&2
    exit 2
    ;;
esac
