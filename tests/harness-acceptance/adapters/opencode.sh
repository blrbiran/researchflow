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
CLI_BIN="$(config_get opencode.cli_bin)"
SCENARIO_DIR="$(config_get opencode.scenario_dir)"
REPO_ROOT="$(config_get repo_root)"
RAW_ROOT="$(config_get raw_dir)"
if [[ -x "$CLI_BIN" ]]; then
  CLI_CMD=("$CLI_BIN")
else
  CLI_CMD=("bash" "$CLI_BIN")
fi
mkdir -p "$RAW_ROOT"
PROBE_DIR="$(mktemp -d "$RAW_ROOT/opencode-probe.XXXXXX")"

run_probe() {
  run_capture "$PROBE_DIR/version.txt" "$PROBE_DIR/version.stderr" "$PROBE_DIR/version.status" version
  run_capture "$PROBE_DIR/debug-config.json" "$PROBE_DIR/debug-config.stderr" "$PROBE_DIR/debug-config.status" debug config
  run_capture "$PROBE_DIR/debug-paths.json" "$PROBE_DIR/debug-paths.stderr" "$PROBE_DIR/debug-paths.status" debug paths
  run_capture "$PROBE_DIR/debug-skill.json" "$PROBE_DIR/debug-skill.stderr" "$PROBE_DIR/debug-skill.status" debug skill
  run_capture "$PROBE_DIR/canary.jsonl" "$PROBE_DIR/canary.stderr" "$PROBE_DIR/canary.status" canary
}

run_probe

case "$MODE" in
  capability)
    require_absent "$OUTPUT_DIR/opencode.json"
    "$PYTHON_BIN" "$HARNESS_DIR/capabilities.py" normalize-capability \
      --harness opencode \
      --config "$CONFIG" \
      --probe-dir "$PROBE_DIR" \
      --output "$OUTPUT_DIR/opencode.json"
    ;;
  preflight)
    require_absent "$OUTPUT_DIR/opencode.json"
    require_absent "$OUTPUT_DIR/opencode-model-proof.json"
    "$PYTHON_BIN" "$HARNESS_DIR/capabilities.py" normalize-preflight \
      --harness opencode \
      --config "$CONFIG" \
      --probe-dir "$PROBE_DIR" \
      --events "$PROBE_DIR/canary.jsonl" \
      --stderr "$PROBE_DIR/canary.stderr" \
      --status "$PROBE_DIR/canary.status" \
      --output "$OUTPUT_DIR/opencode.json" \
      --model-output "$OUTPUT_DIR/opencode-model-proof.json"
    ;;
  case)
    require_absent "$OUTPUT_DIR/final-response.txt"
    require_absent "$OUTPUT_DIR/invocation.json"
    require_absent "$OUTPUT_DIR/command.json"
    CASE_RAW_DIR="$(mktemp -d "$RAW_ROOT/opencode-case-${CASE_ID}.XXXXXX")"
    run_capture "$CASE_RAW_DIR/events.jsonl" "$CASE_RAW_DIR/stderr.txt" "$CASE_RAW_DIR/status.txt" case "$CASE_ID"
    "$PYTHON_BIN" "$HARNESS_DIR/capabilities.py" normalize-case \
      --harness opencode \
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
