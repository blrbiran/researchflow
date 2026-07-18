#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./cleanup-useless-worktrees.sh        # preview only
  ./cleanup-useless-worktrees.sh --apply
EOF
}

MODE="preview"
if [[ ${1:-} == "--apply" ]]; then
  MODE="apply"
  shift
fi

if [[ $# -ne 0 ]]; then
  usage >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
COMMON_DIR="$(git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir)"

TARGETS=$(cat <<EOF
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a1311d6298e971812|worktree-agent-a1311d6298e971812|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a1410fa16d57a24bf|task-2-deterministic-judge|?? .omc/
?? .superpowers/
?? tests/harness-acceptance/__pycache__/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a17a832b50d36bb90|worktree-agent-a17a832b50d36bb90|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a7736fbb967635b09|worktree-agent-a7736fbb967635b09|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a8dd9bce148b00609|worktree-agent-a8dd9bce148b00609|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a97ab6645db0b4d9e|worktree-agent-a97ab6645db0b4d9e|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-a9df27e7dac2ecb52|worktree-agent-a9df27e7dac2ecb52|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-abc359137f6354660|worktree-agent-abc359137f6354660|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-abf07b06dd69bfd02|worktree-agent-abf07b06dd69bfd02|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-af1cbbad43699f3cb|fix-task2-blocked-incomplete-audit|?? .omc/
?? .superpowers/
?? tests/harness-acceptance/__pycache__/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-af8739365e988d63a|worktree-agent-af8739365e988d63a|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-af9233548b417596f|worktree-agent-af9233548b417596f|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-afdc5676267039dcb|worktree-agent-afdc5676267039dcb|?? .omc/
COMMON_AGENT|$COMMON_DIR/.claude/worktrees/agent-afe92ac362d33b745|worktree-agent-afe92ac362d33b745|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a12c0c78be564d14a|worktree-agent-a12c0c78be564d14a|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a36b780c422a33b8a|worktree-agent-a36b780c422a33b8a|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a3e4996bd5dcedf40|worktree-agent-a3e4996bd5dcedf40|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a764f22c46f2eac7c|worktree-agent-a764f22c46f2eac7c|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a7653394c6a080328|worktree-agent-a7653394c6a080328|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a9219941e7079bef6|worktree-agent-a9219941e7079bef6|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-a926d81c875b3a52e|worktree-agent-a926d81c875b3a52e|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-ae3bfcb6471fbef9f|worktree-agent-ae3bfcb6471fbef9f|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-ae852081cb4904302|worktree-agent-ae852081cb4904302|?? .omc/
REPO_AGENT|$REPO_ROOT/.claude/worktrees/agent-afdd06af93e397eb3|worktree-agent-afdd06af93e397eb3|?? .omc/
MANUAL_WORKTREE|$REPO_ROOT/.worktrees/live-harness-acceptance|main-preserved|?? .omc/
?? tests/harness-acceptance/__pycache__/
EOF
)

is_registered() {
  local path="$1"
  git -C "$REPO_ROOT" worktree list --porcelain | grep -Fxq "worktree $path"
}

branch_exists() {
  local branch="$1"
  git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$branch"
}

print_block() {
  local prefix="$1"
  local text="$2"
  if [[ -z "$text" ]]; then
    printf '%s<empty>\n' "$prefix"
    return
  fi
  while IFS= read -r line; do
    printf '%s%s\n' "$prefix" "$line"
  done <<< "$text"
}

remove_target() {
  local path="$1"
  local branch="$2"
  local registered="$3"

  if [[ "$registered" == "yes" ]]; then
    git -C "$REPO_ROOT" worktree remove --force "$path"
  else
    rm -rf -- "$path"
  fi

  if branch_exists "$branch"; then
    git -C "$REPO_ROOT" branch -D "$branch"
  else
    printf 'branch already absent: %s\n' "$branch"
  fi

  printf 'removed: %s (%s)\n' "$path" "$branch"
}

removed_any="no"
record_kind=""
record_path=""
record_branch=""
record_status=""

flush_record() {
  if [[ -z "$record_kind" ]]; then
    return
  fi

  local exists="no"
  local registered="no"
  local current_status=""
  local status_match="no"

  if [[ -d "$record_path" ]]; then
    exists="yes"
    if is_registered "$record_path"; then
      registered="yes"
    fi
    current_status="$(git -C "$record_path" status --short 2>/dev/null || true)"
    current_status="${current_status%$'\n'}"
    if [[ "$current_status" == "$record_status" ]]; then
      status_match="yes"
    fi
  fi

  printf '\n[%s]\n' "$record_branch"
  printf 'kind: %s\n' "$record_kind"
  printf 'path: %s\n' "$record_path"
  printf 'exists: %s\n' "$exists"
  printf 'registered: %s\n' "$registered"
  print_block 'expected: ' "$record_status"
  print_block 'current:  ' "$current_status"
  printf 'status_match: %s\n' "$status_match"

  if [[ "$record_kind" == "MANUAL_WORKTREE" ]]; then
    printf 'warning: manual preserved worktree candidate\n'
  fi

  if [[ "$MODE" == "apply" ]]; then
    if [[ "$exists" != "yes" ]]; then
      printf 'skip: path missing\n'
    elif [[ "$status_match" != "yes" ]]; then
      printf 'skip: current status differs from confirmed snapshot\n'
    else
      remove_target "$record_path" "$record_branch" "$registered"
      removed_any="yes"
    fi
  fi

  record_kind=""
  record_path=""
  record_branch=""
  record_status=""
}

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" == *'|'* ]]; then
    flush_record
    IFS='|' read -r record_kind record_path record_branch record_status <<< "$line"
  elif [[ -n "$record_kind" ]]; then
    record_status+=$'\n'
    record_status+="$line"
  fi
done <<< "$TARGETS"

flush_record

if [[ "$MODE" == "apply" ]]; then
  if [[ "$removed_any" == "yes" ]]; then
    git -C "$REPO_ROOT" worktree prune
    printf '\npruned stale worktree metadata\n'
  else
    printf '\nno matching targets were removed; skipped prune\n'
  fi
else
  printf '\npreview only: re-run with --apply to perform removals\n'
fi
