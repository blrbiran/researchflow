#!/usr/bin/env bash
set -euo pipefail

SCENARIO_DIR="${RF_SCENARIO_DIR:?}"
REPO_ROOT="${RF_REPO_ROOT:?}"

command="${1:-}"
case "$command" in
  version)
    cat "$SCENARIO_DIR/version.txt"
    ;;
  debug)
    subcommand="${2:-}"
    case "$subcommand" in
      config)
        python3 - "$SCENARIO_DIR/debug-config.json" "$REPO_ROOT" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("plugin_path") == "__REPO_ROOT__":
    payload["plugin_path"] = sys.argv[2]
print(json.dumps(payload, indent=2))
PY
        exit "$(cat "$SCENARIO_DIR/debug-config.exit")"
        ;;
      paths)
        python3 - "$SCENARIO_DIR/debug-paths-template.json" "$REPO_ROOT" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("plugin_path") == "__REPO_ROOT__":
    payload["plugin_path"] = sys.argv[2]
print(json.dumps(payload, indent=2))
PY
        exit "$(cat "$SCENARIO_DIR/debug-paths.exit")"
        ;;
      skill)
        cat "$SCENARIO_DIR/debug-skill.json"
        exit "$(cat "$SCENARIO_DIR/debug-skill.exit")"
        ;;
      *)
        printf 'unknown debug subcommand: %s\n' "$subcommand" >&2
        exit 2
        ;;
    esac
    ;;
  canary)
    cat "$SCENARIO_DIR/canary.jsonl"
    exit "$(cat "$SCENARIO_DIR/canary.exit")"
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
