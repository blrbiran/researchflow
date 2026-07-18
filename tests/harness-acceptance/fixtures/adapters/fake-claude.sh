#!/usr/bin/env bash
set -euo pipefail

SCENARIO_DIR="${FAKE_CLAUDE_SCENARIO_DIR:?}"
REPO_ROOT="${FAKE_REPO_ROOT:?}"
CASE_ID="${FAKE_CASE_ID:-R-DIRECT-LIT}"

render_marketplace_list() {
  python3 - "$SCENARIO_DIR/marketplace-list-template.json" "$REPO_ROOT" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for item in payload:
    if item.get("path") == "__REPO_ROOT__":
        item["path"] = sys.argv[2]
    if item.get("source") == "__REPO_ROOT__":
        item["source"] = sys.argv[2]
print(json.dumps(payload, indent=2))
PY
}

if [[ "${1:-}" == "--version" ]]; then
  cat "$SCENARIO_DIR/version.txt"
  exit 0
fi
if [[ "${1:-}" == "--help" ]]; then
  cat "$SCENARIO_DIR/help.txt"
  exit 0
fi
if [[ "${1:-}" == "plugin" && "${2:-}" == "--help" ]]; then
  cat "$SCENARIO_DIR/plugin-help.txt"
  exit 0
fi
if [[ "${1:-}" == "plugin" && "${2:-}" == "list" ]]; then
  if [[ "${3:-}" != "--output-format" || "${4:-}" != "json" ]]; then
    printf 'expected plugin list --output-format json\n' >&2
    exit 2
  fi
  render_marketplace_list
  exit "$(cat "$SCENARIO_DIR/marketplace.exit")"
fi
if [[ "${1:-}" == "plugin" && "${2:-}" == "validate" ]]; then
  if [[ "${3:-}" != "$REPO_ROOT" ]]; then
    printf 'expected plugin validate <repo_root>\n' >&2
    exit 2
  fi
  cat "$SCENARIO_DIR/validate.txt"
  exit "$(cat "$SCENARIO_DIR/validate.exit")"
fi

prompt=""
plugin_dir=""
has_bare=0
has_no_session=0
has_output_json=0
has_model=0
has_effort=0
has_tools=0

index=1
while [[ $index -le $# ]]; do
  arg="${!index}"
  case "$arg" in
    -p)
      index=$((index + 1))
      prompt="${!index}"
      ;;
    --plugin-dir)
      index=$((index + 1))
      plugin_dir="${!index}"
      ;;
    --bare)
      has_bare=1
      ;;
    --no-session-persistence)
      has_no_session=1
      ;;
    --tools)
      index=$((index + 1))
      if [[ "${!index}" == "" ]]; then
        has_tools=1
      fi
      ;;
    --output-format)
      index=$((index + 1))
      if [[ "${!index}" == "json" ]]; then
        has_output_json=1
      fi
      ;;
    --model)
      index=$((index + 1))
      if [[ -n "${!index}" ]]; then
        has_model=1
      fi
      ;;
    --effort)
      index=$((index + 1))
      if [[ -n "${!index}" ]]; then
        has_effort=1
      fi
      ;;
  esac
  index=$((index + 1))
done

if [[ -z "$prompt" || $has_no_session -ne 1 || $has_output_json -ne 1 || $has_model -ne 1 || $has_effort -ne 1 || $has_tools -ne 1 ]]; then
  printf 'unexpected claude invocation\n' >&2
  exit 2
fi

if [[ "$prompt" == *"RESEARCHFLOW_BOOTSTRAP_ACTIVE"* ]]; then
  if [[ -n "$plugin_dir" && "$plugin_dir" != "$REPO_ROOT" ]]; then
    printf 'unexpected --plugin-dir value\n' >&2
    exit 2
  fi
  if [[ $has_bare -eq 1 ]]; then
    cat "$SCENARIO_DIR/full-direct.jsonl"
    exit "$(cat "$SCENARIO_DIR/full-direct.exit")"
  fi
  if [[ -n "$plugin_dir" ]]; then
    cat "$SCENARIO_DIR/direct.jsonl"
    exit "$(cat "$SCENARIO_DIR/direct.exit")"
  fi
  cat "$SCENARIO_DIR/marketplace.jsonl"
  exit "$(cat "$SCENARIO_DIR/marketplace.exit")"
fi

printf '%s' "$prompt" > "$SCENARIO_DIR/last-prompt.txt"
printf '%s\n' "$PWD" > "$SCENARIO_DIR/last-cwd.txt"
cat "$SCENARIO_DIR/cases/${CASE_ID}.jsonl"
exit "$(cat "$SCENARIO_DIR/cases/${CASE_ID}.exit")"
