#!/usr/bin/env bash
set -euo pipefail

SCENARIO_DIR="${FAKE_OPENCODE_SCENARIO_DIR:?}"
REPO_ROOT="${FAKE_REPO_ROOT:?}"
CASE_ID="${FAKE_CASE_ID:-R-DIRECT-LIT}"

render_json() {
  local path="$1"
  python3 - "$path" "$REPO_ROOT" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("plugin_path") == "__REPO_ROOT__":
    payload["plugin_path"] = sys.argv[2]
print(json.dumps(payload, indent=2))
PY
}

if [[ "${1:-}" == "--version" ]]; then
  cat "$SCENARIO_DIR/version.txt"
  exit 0
fi
if [[ "${1:-}" == "debug" && "${2:-}" == "config" ]]; then
  render_json "$SCENARIO_DIR/debug-config.json"
  exit "$(cat "$SCENARIO_DIR/debug-config.exit")"
fi
if [[ "${1:-}" == "debug" && "${2:-}" == "paths" ]]; then
  render_json "$SCENARIO_DIR/debug-paths-template.json"
  exit "$(cat "$SCENARIO_DIR/debug-paths.exit")"
fi
if [[ "${1:-}" == "debug" && "${2:-}" == "skill" ]]; then
  cat "$SCENARIO_DIR/debug-skill.json"
  exit "$(cat "$SCENARIO_DIR/debug-skill.exit")"
fi
if [[ "${1:-}" != "run" ]]; then
  printf 'unexpected opencode invocation\n' >&2
  exit 2
fi

format=""
model=""
variant=""
workspace_dir=""
prompt=""

index=2
while [[ $index -le $# ]]; do
  arg="${!index}"
  case "$arg" in
    --format)
      index=$((index + 1))
      format="${!index}"
      ;;
    --model)
      index=$((index + 1))
      model="${!index}"
      ;;
    --variant)
      index=$((index + 1))
      variant="${!index}"
      ;;
    --dir)
      index=$((index + 1))
      workspace_dir="${!index}"
      ;;
    *)
      prompt="$arg"
      ;;
  esac
  index=$((index + 1))
done

if [[ "$format" != "json" || -z "$model" || -z "$variant" || -z "$workspace_dir" || -z "$prompt" ]]; then
  printf 'unexpected opencode run invocation\n' >&2
  exit 2
fi
if [[ ! -f "$workspace_dir/opencode.json" ]]; then
  printf 'missing workspace config\n' >&2
  exit 2
fi

if [[ "$prompt" == *"RESEARCHFLOW_BOOTSTRAP_ACTIVE"* ]]; then
  cat "$SCENARIO_DIR/canary.jsonl"
  exit "$(cat "$SCENARIO_DIR/canary.exit")"
fi

cat "$SCENARIO_DIR/cases/${CASE_ID}.jsonl"
exit "$(cat "$SCENARIO_DIR/cases/${CASE_ID}.exit")"
