#!/usr/bin/env bash
set -euo pipefail

MODE=""
CONFIG=""
OUTPUT_DIR=""
CASE_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --case-id)
      CASE_ID="$2"
      shift 2
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$MODE" || -z "$CONFIG" || -z "$OUTPUT_DIR" ]]; then
  printf 'usage: %s --mode capability|preflight|case --config PATH --output-dir PATH [--case-id ID]\n' "$0" >&2
  exit 2
fi
if [[ "$MODE" == "case" && -z "$CASE_ID" ]]; then
  printf '--case-id is required for case mode\n' >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

config_get() {
  "$PYTHON_BIN" - "$CONFIG" "$1" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = config
for part in sys.argv[2].split('.'):
    value = value[part]
if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("")
else:
    print(value)
PY
}

run_capture() {
  local stdout_path="$1"
  local stderr_path="$2"
  local status_path="$3"
  shift 3
  local -a command=("${CLI_CMD[@]}" "$@")
  set +e
  RF_SCENARIO_DIR="$SCENARIO_DIR" RF_REPO_ROOT="$REPO_ROOT" "${command[@]}" >"$stdout_path" 2>"$stderr_path"
  local status=$?
  set -e
  printf '%s\n' "$status" >"$status_path"
}

require_absent() {
  local path="$1"
  if [[ -e "$path" ]]; then
    printf '%s\n' "$path" >&2
    exit 1
  fi
}

mkdir -p "$OUTPUT_DIR"
CLI_BIN="$(config_get claude.cli_bin)"
SCENARIO_DIR="$(config_get claude.scenario_dir)"
REPO_ROOT="$(config_get repo_root)"
RAW_ROOT="$(config_get raw_dir)"
if [[ -x "$CLI_BIN" ]]; then
  CLI_CMD=("$CLI_BIN")
else
  CLI_CMD=("bash" "$CLI_BIN")
fi
mkdir -p "$RAW_ROOT"
PROBE_DIR="$(mktemp -d "$RAW_ROOT/claude-probe.XXXXXX")"

run_probe() {
  run_capture "$PROBE_DIR/version.txt" "$PROBE_DIR/version.stderr" "$PROBE_DIR/version.status" version
  run_capture "$PROBE_DIR/help.txt" "$PROBE_DIR/help.stderr" "$PROBE_DIR/help.status" help
  run_capture "$PROBE_DIR/plugin-help.txt" "$PROBE_DIR/plugin-help.stderr" "$PROBE_DIR/plugin-help.status" plugin help
  run_capture "$PROBE_DIR/marketplace-list.json" "$PROBE_DIR/marketplace-list.stderr" "$PROBE_DIR/marketplace-list.status" plugin list
  run_capture "$PROBE_DIR/validate.txt" "$PROBE_DIR/validate.stderr" "$PROBE_DIR/validate.status" plugin validate
  run_capture "$PROBE_DIR/direct-canary.jsonl" "$PROBE_DIR/direct-canary.stderr" "$PROBE_DIR/direct-canary.status" canary direct
  run_capture "$PROBE_DIR/marketplace-canary.jsonl" "$PROBE_DIR/marketplace-canary.stderr" "$PROBE_DIR/marketplace-canary.status" canary marketplace
  run_capture "$PROBE_DIR/full-direct-canary.jsonl" "$PROBE_DIR/full-direct-canary.stderr" "$PROBE_DIR/full-direct-canary.status" canary full-direct
}

selected_branch() {
  "$PYTHON_BIN" - "$HARNESS_DIR" "$CONFIG" "$PROBE_DIR" <<'PY'
import importlib.util
import sys
from pathlib import Path

harness_dir = Path(sys.argv[1])
config_path = Path(sys.argv[2])
probe_dir = Path(sys.argv[3])
module_path = harness_dir / "capabilities.py"
spec = importlib.util.spec_from_file_location("caps", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.read_config(config_path)
_, probe = module.probe_from_dir("claude", config, probe_dir)
print(module.select_claude_load_branch(probe) or "")
PY
}

run_probe

case "$MODE" in
  capability)
    require_absent "$OUTPUT_DIR/claude.json"
    "$PYTHON_BIN" "$HARNESS_DIR/capabilities.py" normalize-capability \
      --harness claude \
      --config "$CONFIG" \
      --probe-dir "$PROBE_DIR" \
      --output "$OUTPUT_DIR/claude.json"
    ;;
  preflight)
    require_absent "$OUTPUT_DIR/claude.json"
    require_absent "$OUTPUT_DIR/claude-model-proof.json"
    branch="$(selected_branch)"
    events_path="$PROBE_DIR/direct-canary.jsonl"
    stderr_path="$PROBE_DIR/direct-canary.stderr"
    status_path="$PROBE_DIR/direct-canary.status"
    if [[ "$branch" == "local-marketplace" ]]; then
      events_path="$PROBE_DIR/marketplace-canary.jsonl"
      stderr_path="$PROBE_DIR/marketplace-canary.stderr"
      status_path="$PROBE_DIR/marketplace-canary.status"
    fi
    "$PYTHON_BIN" "$HARNESS_DIR/capabilities.py" normalize-preflight \
      --harness claude \
      --config "$CONFIG" \
      --probe-dir "$PROBE_DIR" \
      --events "$events_path" \
      --stderr "$stderr_path" \
      --status "$status_path" \
      --output "$OUTPUT_DIR/claude.json" \
      --model-output "$OUTPUT_DIR/claude-model-proof.json"
    ;;
  case)
    require_absent "$OUTPUT_DIR/final-response.txt"
    require_absent "$OUTPUT_DIR/invocation.json"
    require_absent "$OUTPUT_DIR/command.json"
    CASE_RAW_DIR="$(mktemp -d "$RAW_ROOT/claude-case-${CASE_ID}.XXXXXX")"
    run_capture "$CASE_RAW_DIR/events.jsonl" "$CASE_RAW_DIR/stderr.txt" "$CASE_RAW_DIR/status.txt" case "$CASE_ID"
    "$PYTHON_BIN" "$HARNESS_DIR/capabilities.py" normalize-case \
      --harness claude \
      --config "$CONFIG" \
      --probe-dir "$PROBE_DIR" \
      --events "$CASE_RAW_DIR/events.jsonl" \
      --stderr "$CASE_RAW_DIR/stderr.txt" \
      --status "$CASE_RAW_DIR/status.txt" \
      --output-dir "$OUTPUT_DIR" \
      --case-id "$CASE_ID"
    ;;
  *)
    printf 'unsupported mode: %s\n' "$MODE" >&2
    exit 2
    ;;
esac
