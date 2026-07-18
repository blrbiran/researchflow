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
CANARY_PROMPT=$'Reply with exactly this first line and no preamble.\nRESEARCHFLOW_BOOTSTRAP_ACTIVE'

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

config_get_optional() {
  "$PYTHON_BIN" - "$CONFIG" "$1" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = config
try:
    for part in sys.argv[2].split('.'):
        value = value[part]
except Exception:
    print("")
    raise SystemExit(0)
if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("")
else:
    print(value)
PY
}

case_prompt() {
  "$PYTHON_BIN" - "$HARNESS_DIR/cases.json" "$HARNESS_DIR/scored-prompt.txt" "$1" <<'PY'
import json
import sys
from pathlib import Path

cases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
suffix = Path(sys.argv[2]).read_text(encoding="utf-8").rstrip()
case_id = sys.argv[3]
for item in cases:
    if item.get("case_id") == case_id:
        prompt = item["prompt"].rstrip()
        sys.stdout.write(f"{prompt}\n\n{suffix}\n")
        break
else:
    raise SystemExit(f"unknown case_id: {case_id}")
PY
}

run_capture() {
  local stdout_path="$1"
  local stderr_path="$2"
  local status_path="$3"
  shift 3
  local -a command=("${CLI_CMD[@]}" "$@")
  if [[ -n "$SCENARIO_DIR" ]]; then
    RUN_CWD="${RUN_CWD:-}" FAKE_CLAUDE_SCENARIO_DIR="$SCENARIO_DIR" FAKE_REPO_ROOT="$REPO_ROOT" "$PYTHON_BIN" - "$stdout_path" "$stderr_path" "$status_path" "$TIMEOUT_SECONDS" "${command[@]}" <<'PY'
import os
import subprocess
import sys
from pathlib import Path

stdout_path = Path(sys.argv[1])
stderr_path = Path(sys.argv[2])
status_path = Path(sys.argv[3])
timeout_seconds = int(sys.argv[4])
command = sys.argv[5:]

stdout_path.parent.mkdir(parents=True, exist_ok=True)
stderr_path.parent.mkdir(parents=True, exist_ok=True)
status_path.parent.mkdir(parents=True, exist_ok=True)

cwd = os.environ.get("RUN_CWD") or None
try:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, cwd=cwd)
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    status = completed.returncode
except subprocess.TimeoutExpired as exc:
    stdout = exc.stdout or ""
    stderr = exc.stderr or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    status = 124

stdout_path.write_text(stdout, encoding="utf-8")
stderr_path.write_text(stderr, encoding="utf-8")
status_path.write_text(f"{status}\n", encoding="utf-8")
PY
  else
    RUN_CWD="${RUN_CWD:-}" "$PYTHON_BIN" - "$stdout_path" "$stderr_path" "$status_path" "$TIMEOUT_SECONDS" "${command[@]}" <<'PY'
import os
import subprocess
import sys
from pathlib import Path

stdout_path = Path(sys.argv[1])
stderr_path = Path(sys.argv[2])
status_path = Path(sys.argv[3])
timeout_seconds = int(sys.argv[4])
command = sys.argv[5:]

stdout_path.parent.mkdir(parents=True, exist_ok=True)
stderr_path.parent.mkdir(parents=True, exist_ok=True)
status_path.parent.mkdir(parents=True, exist_ok=True)

cwd = os.environ.get("RUN_CWD") or None
try:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, cwd=cwd)
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    status = completed.returncode
except subprocess.TimeoutExpired as exc:
    stdout = exc.stdout or ""
    stderr = exc.stderr or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    status = 124

stdout_path.write_text(stdout, encoding="utf-8")
stderr_path.write_text(stderr, encoding="utf-8")
status_path.write_text(f"{status}\n", encoding="utf-8")
PY
  fi
}

require_absent() {
  local path="$1"
  if [[ -e "$path" ]]; then
    printf '%s\n' "$path" >&2
    exit 1
  fi
}

selected_value() {
  local field="$1"
  "$PYTHON_BIN" - "$HARNESS_DIR" "$CONFIG" "$PROBE_DIR" "$field" <<'PY'
import importlib.util
import sys
from pathlib import Path

harness_dir = Path(sys.argv[1])
config_path = Path(sys.argv[2])
probe_dir = Path(sys.argv[3])
field = sys.argv[4]
module_path = harness_dir / "capabilities.py"
spec = importlib.util.spec_from_file_location("caps", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.read_config(config_path)
_, probe = module.probe_from_dir("claude", config, probe_dir)
if field == "branch":
    print(module.select_claude_load_branch(probe) or "")
elif field == "profile":
    print(module.select_isolation_profile(probe) or "")
else:
    raise SystemExit(f"unsupported field: {field}")
PY
}

mkdir -p "$OUTPUT_DIR"
CLI_BIN="$(config_get claude.cli_bin)"
REPO_ROOT="$(config_get repo_root)"
RAW_ROOT="$(config_get raw_dir)"
MODEL_VALUE="$(config_get claude.harness_model_value)"
EFFORT_VALUE="$(config_get claude.effort_or_variant)"
TIMEOUT_SECONDS="$(config_get timeout_seconds)"
SCENARIO_DIR="$(config_get_optional claude.scenario_dir)"
if [[ -x "$CLI_BIN" ]]; then
  CLI_CMD=("$CLI_BIN")
else
  CLI_CMD=("bash" "$CLI_BIN")
fi
mkdir -p "$RAW_ROOT"
PROBE_DIR="$(mktemp -d "$RAW_ROOT/claude-probe.XXXXXX")"

run_probe() {
  run_capture "$PROBE_DIR/version.txt" "$PROBE_DIR/version.stderr" "$PROBE_DIR/version.status" --version
  run_capture "$PROBE_DIR/help.txt" "$PROBE_DIR/help.stderr" "$PROBE_DIR/help.status" --help
  run_capture "$PROBE_DIR/plugin-help.txt" "$PROBE_DIR/plugin-help.stderr" "$PROBE_DIR/plugin-help.status" plugin --help

  if grep -q 'list' "$PROBE_DIR/plugin-help.txt"; then
    run_capture "$PROBE_DIR/marketplace-list.json" "$PROBE_DIR/marketplace-list.stderr" "$PROBE_DIR/marketplace-list.status" plugin list --output-format json
  fi
  if grep -q 'validate' "$PROBE_DIR/plugin-help.txt"; then
    run_capture "$PROBE_DIR/validate.txt" "$PROBE_DIR/validate.stderr" "$PROBE_DIR/validate.status" plugin validate "$REPO_ROOT"
  fi
  if grep -q -- '--plugin-dir' "$PROBE_DIR/help.txt"; then
    run_capture "$PROBE_DIR/direct-canary.jsonl" "$PROBE_DIR/direct-canary.stderr" "$PROBE_DIR/direct-canary.status" \
      -p "$CANARY_PROMPT" \
      --plugin-dir "$REPO_ROOT" \
      --no-session-persistence \
      --tools "" \
      --output-format json \
      --model "$MODEL_VALUE" \
      --effort "$EFFORT_VALUE"
  fi
  if grep -q 'list' "$PROBE_DIR/plugin-help.txt"; then
    run_capture "$PROBE_DIR/marketplace-canary.jsonl" "$PROBE_DIR/marketplace-canary.stderr" "$PROBE_DIR/marketplace-canary.status" \
      -p "$CANARY_PROMPT" \
      --no-session-persistence \
      --tools "" \
      --output-format json \
      --model "$MODEL_VALUE" \
      --effort "$EFFORT_VALUE"
  fi
  if grep -q -- '--plugin-dir' "$PROBE_DIR/help.txt" && grep -q -- '--bare' "$PROBE_DIR/help.txt"; then
    run_capture "$PROBE_DIR/full-direct-canary.jsonl" "$PROBE_DIR/full-direct-canary.stderr" "$PROBE_DIR/full-direct-canary.status" \
      -p "$CANARY_PROMPT" \
      --plugin-dir "$REPO_ROOT" \
      --bare \
      --no-session-persistence \
      --tools "" \
      --output-format json \
      --model "$MODEL_VALUE" \
      --effort "$EFFORT_VALUE"
  fi
}

run_case_command() {
  local prompt="$1"
  local stdout_path="$2"
  local stderr_path="$3"
  local status_path="$4"
  local profile="$5"
  local workspace_dir="$6"
  mkdir -p "$workspace_dir"
  local -a args=(-p "$prompt")
  if [[ "$profile" == "auth-preserving-direct-plugin-dir" || "$profile" == "full-direct-plugin-dir" ]]; then
    args+=(--plugin-dir "$REPO_ROOT")
  fi
  if [[ "$profile" == "full-direct-plugin-dir" ]]; then
    args+=(--bare)
  fi
  args+=(
    --no-session-persistence
    --tools ""
    --output-format json
    --model "$MODEL_VALUE"
    --effort "$EFFORT_VALUE"
  )
  RUN_CWD="$workspace_dir" run_capture "$stdout_path" "$stderr_path" "$status_path" "${args[@]}"
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
    profile="$(selected_value profile)"
    if [[ -z "$profile" ]]; then
      : > "$PROBE_DIR/preflight-events.jsonl"
      : > "$PROBE_DIR/preflight.stderr"
      printf '1\n' > "$PROBE_DIR/preflight.status"
      events_path="$PROBE_DIR/preflight-events.jsonl"
      stderr_path="$PROBE_DIR/preflight.stderr"
      status_path="$PROBE_DIR/preflight.status"
    else
      branch="$(selected_value branch)"
      events_path="$PROBE_DIR/direct-canary.jsonl"
      stderr_path="$PROBE_DIR/direct-canary.stderr"
      status_path="$PROBE_DIR/direct-canary.status"
      if [[ "$branch" == "local-marketplace" ]]; then
        events_path="$PROBE_DIR/marketplace-canary.jsonl"
        stderr_path="$PROBE_DIR/marketplace-canary.stderr"
        status_path="$PROBE_DIR/marketplace-canary.status"
      elif [[ "$profile" == "full-direct-plugin-dir" ]]; then
        events_path="$PROBE_DIR/full-direct-canary.jsonl"
        stderr_path="$PROBE_DIR/full-direct-canary.stderr"
        status_path="$PROBE_DIR/full-direct-canary.status"
      fi
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
    profile="$(selected_value profile)"
    if [[ -z "$profile" ]]; then
      printf 'blocked: no supported claude capability profile\n' >&2
      exit 1
    fi
    CASE_RAW_DIR="$(mktemp -d "$RAW_ROOT/claude-case-${CASE_ID}.XXXXXX")"
    prompt="$(case_prompt "$CASE_ID"; printf '__RESEARCHFLOW_PROMPT_END__')"
    prompt="${prompt%__RESEARCHFLOW_PROMPT_END__}"
    run_case_command "$prompt" "$CASE_RAW_DIR/events.jsonl" "$CASE_RAW_DIR/stderr.txt" "$CASE_RAW_DIR/status.txt" "$profile" "$CASE_RAW_DIR/workspace"
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
