# Task 6 Real Preflight-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the first real preflight-only gate for the live harness acceptance system, producing either blocked evidence, allowlist-update-needed evidence, or a continuation-ready run for Task 7 without running any scored cases.

**Architecture:** Keep Task 6 narrow and reuse the Task 5 runner shape. First extend the synthetic contract so preflight outcomes are machine-distinguishable and continuation-ready runs can be validated without final summary artifacts. Then run one real `preflight-only` pass, optionally resolve a first-seen allowlist gap in a separate commit and new run, and finish with a committed blocked or continuation-ready evidence set.

**Tech Stack:** Python 3 standard library, Bash, JSON, existing `tests/harness-acceptance` runner/adapters, `unittest`, local non-committed operator config

## Global Constraints

- Task 6 only.
- real `--mode preflight-only` execution using the existing harness acceptance runner;
- real capability, plugin-proof, and model-proof artifact capture;
- real redaction and summary reconstruction against preflight-only artifacts;
- operator workflow for reviewing redacted proof artifacts;
- strict handling of first-seen backing-model allowlist gaps;
- producing one of three outcomes: `blocked`, `allowlist-update-needed`, or `continuation-ready`.
- scored case execution is out of scope.
- proving routing correctness is out of scope.
- retrying or reusing a blocked run is out of scope.
- updating router behavior or workflow contracts is out of scope.
- release readiness claims are out of scope.
- version bump, publish, or push are out of scope.
- Task 6 does not score routing decisions.
- Task 6 does not prove acceptance success.
- Task 6 does not run the seven shared cases.
- The only acceptable source of canonical model identity remains real redacted proof.
- Task 6 passes only if both harnesses prove the same verified canonical `openai/<model>` identity.
- If both harnesses prove the same backing model but that backing model is absent from `model-identities.json`, the run is `allowlist-update-needed`.
- The current run must be stopped and preserved as blocked evidence before any allowlist update.
- The exact `backing_model_id -> openai/<model>` mapping is added in a separate commit.
- A new Task 6 run starts with a new `run-id` after any allowlist update.
- The original run must never continue into Task 7 after an allowlist update.
- Task 6 must reuse the Task 5 monotonic run model.
- If the run is blocked or allowlist-update-needed, it must write `summary.json` and `summary.md`.
- If the run is continuation-ready, it must write `preflight/baseline.json` and must not write final summary artifacts yet.
- `run-config.local.json` must not commit secrets, raw endpoints, or environment dumps.
- The operator must not “just try one scored case” from Task 6.
- Task 6 should add only the synthetic coverage necessary to support the real preflight-only flow.
- Task 6 should not broaden into new scored-routing tests.

---

## File Structure

- `tests/harness-acceptance/preflight.py` — extend preflight outcome logic, run-directory evaluation helpers, and a CLI for validating whether a real preflight run is continuation-ready.
- `tests/harness-acceptance/summarize.py` — emit a machine-readable blocked outcome marker that distinguishes `allowlist-update-needed` from ordinary blocked runs.
- `tests/harness-acceptance/test_preflight.py` — synthetic coverage for Task 6 outcome classification and the new preflight validation CLI.
- `tests/harness-acceptance/test_summarize.py` — synthetic coverage for blocked vs allowlist-update-needed summary outcomes.
- `tests/harness-acceptance/run.py` — existing runner used unchanged or with only the minimum glue needed to support Task 6 real preflight semantics.
- `tests/harness-acceptance/run-config.local.json` — local-only operator config for real preflight; never committed.
- `tests/harness-acceptance/model-identities.json` — committed allowlist; only changes if a real run proves a first-seen backing model.
- `tests/harness-acceptance/results/<run-id>/**` — committed real preflight artifacts and blocked/continuation-ready evidence.
- `tests/harness-acceptance/run-tests.sh` — synthetic harness-acceptance baseline to rerun before and after any allowlist update.
- `tests/run-all.sh` — repository synthetic baseline to rerun before any real preflight and after any allowlist update.

### Task 1: Encode `runtime-proof-unavailable` and machine-readable blocked reasons

**Files:**
- Modify: `tests/harness-acceptance/preflight.py`
- Modify: `tests/harness-acceptance/summarize.py`
- Modify: `tests/harness-acceptance/test_preflight.py`
- Modify: `tests/harness-acceptance/test_summarize.py`

**Interfaces:**
- Produces: `determine_preflight_outcome(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]`
- Produces: summary fields `outcome: str` and `reason_code: str | None` for blocked-style preflight runs
- Consumes: `evaluate_preflight(...)`
- Consumes: `evaluate_model_alignment(...)`

- [ ] **Step 1: Write the failing preflight and summary tests**

Add these tests to `tests/harness-acceptance/test_preflight.py`:

```python
def test_determine_preflight_outcome_marks_allowlist_update_needed(self):
    claude = {
        "status": "pass",
        "canonical_identity": None,
        "proof_identity": "openai/gpt-5.5",
        "proof_valid": True,
        "allowlist_missing": True,
    }
    opencode = {
        "status": "pass",
        "canonical_identity": None,
        "proof_identity": "openai/gpt-5.5",
        "proof_valid": True,
        "allowlist_missing": True,
    }
    result = self.preflight.determine_preflight_outcome(claude, opencode)
    self.assertEqual(result["outcome"], "allowlist-update-needed")
    self.assertEqual(result["reason_code"], "global_hard_gate_blocked")


def test_determine_preflight_outcome_marks_runtime_proof_unavailable(self):
    claude = {
        "status": "pass",
        "canonical_identity": "openai/gpt-5.4",
        "proof_identity": "openai/gpt-5.4",
        "proof_valid": True,
        "allowlist_missing": False,
    }
    opencode = {
        "status": "pass",
        "canonical_identity": None,
        "proof_identity": None,
        "proof_valid": False,
        "allowlist_missing": False,
    }
    result = self.preflight.determine_preflight_outcome(claude, opencode)
    self.assertEqual(result["outcome"], "blocked")
    self.assertEqual(result["reason_code"], "runtime-proof-unavailable")
    self.assertIsNone(result["canonical_identity"])


def test_determine_preflight_outcome_marks_continuation_ready(self):
    ready = {
        "status": "pass",
        "canonical_identity": "openai/synthetic-model",
        "proof_identity": "openai/synthetic-model",
        "proof_valid": True,
        "allowlist_missing": False,
    }
    result = self.preflight.determine_preflight_outcome(ready, ready)
    self.assertEqual(result["outcome"], "continuation-ready")
    self.assertEqual(result["canonical_identity"], "openai/synthetic-model")
```

Add these tests to `tests/harness-acceptance/test_summarize.py`:

```python
def test_build_summary_marks_allowlist_update_needed_outcome(self):
    run_dir = self.make_run_dir()
    for harness in ("claude", "opencode"):
        model_proof = copy.deepcopy(self.base_model_proof)
        model_proof["harness"] = harness
        model_proof["backing_model_id"] = "gpt-5.5"
        model_proof["resolved_model_identity"] = "openai/gpt-5.5"
        model_proof["requested_route"] = "fable" if harness == "claude" else "openai/gpt-5.5"
        write_json(run_dir / "preflight" / f"{harness}-model-proof.json", model_proof)
    summary = self.summarize.build_summary(run_dir, self.cases)
    self.assertEqual(summary["outcome"], "allowlist-update-needed")
    self.assertEqual(summary["reason_code"], "global_hard_gate_blocked")


def test_build_summary_marks_runtime_proof_unavailable_reason(self):
    run_dir = self.make_run_dir()
    write_json(run_dir / "preflight" / "claude.json", {**self.base_preflight["claude"], "status": "pass"})
    write_json(run_dir / "preflight" / "opencode.json", {**self.base_preflight["opencode"], "status": "pass"})

    claude_proof = copy.deepcopy(self.base_model_proof)
    claude_proof["harness"] = "claude"
    claude_proof["backing_model_id"] = "gpt-5.4"
    claude_proof["resolved_model_identity"] = "openai/gpt-5.4"
    claude_proof["requested_route"] = "sonnet"
    write_json(run_dir / "preflight" / "claude-model-proof.json", claude_proof)

    opencode_proof = copy.deepcopy(self.base_model_proof)
    opencode_proof["harness"] = "opencode"
    opencode_proof["backing_model_id"] = "unknown"
    opencode_proof["resolved_model_identity"] = None
    opencode_proof["verified"] = False
    opencode_proof["proof_method"] = "missing-model-metadata"
    opencode_proof["requested_route"] = "openai-compatible/gpt-5.4"
    write_json(run_dir / "preflight" / "opencode-model-proof.json", opencode_proof)

    summary = self.summarize.build_summary(run_dir, self.cases)
    self.assertEqual(summary["outcome"], "blocked")
    self.assertEqual(summary["reason_code"], "runtime-proof-unavailable")
    self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))
```

- [ ] **Step 2: Run the focused RED tests**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_preflight.py' -v
python3 -m unittest discover -s tests/harness-acceptance -p 'test_summarize.py' -v
```

Expected:
- `test_preflight.py` fails with missing `determine_preflight_outcome`
- `test_summarize.py` fails because `summary["outcome"]` is missing or incorrect

- [ ] **Step 3: Implement the minimal outcome helper and summary outcome field**

Add this helper to `tests/harness-acceptance/preflight.py`:

```python
def determine_preflight_outcome(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]:
    alignment = evaluate_model_alignment(claude_result, opencode_result)
    if claude_result.get("status") != "pass" or opencode_result.get("status") != "pass":
        return {
            "outcome": "blocked",
            "reason_code": alignment["reason_code"] or "global_hard_gate_blocked",
            "canonical_identity": None,
        }
    if alignment["aligned"]:
        return {
            "outcome": "continuation-ready",
            "reason_code": None,
            "canonical_identity": alignment["canonical_identity"],
        }
    if (
        alignment["reason_code"] == "global_hard_gate_blocked"
        and claude_result.get("proof_valid")
        and opencode_result.get("proof_valid")
        and claude_result.get("proof_identity") == opencode_result.get("proof_identity")
        and (claude_result.get("allowlist_missing") or opencode_result.get("allowlist_missing"))
    ):
        return {
            "outcome": "allowlist-update-needed",
            "reason_code": "global_hard_gate_blocked",
            "canonical_identity": None,
        }
    if claude_result.get("proof_valid") != opencode_result.get("proof_valid"):
        return {
            "outcome": "blocked",
            "reason_code": "runtime-proof-unavailable",
            "canonical_identity": None,
        }
    return {
        "outcome": "blocked",
        "reason_code": alignment["reason_code"] or "model_alignment_blocked",
        "canonical_identity": None,
    }
```

In `tests/harness-acceptance/summarize.py`, derive and expose blocked-style `outcome` and `reason_code` from the shared helper:

```python
    outcome = None
    reason_code = None
    if any(status != "pass" for status in preflight_statuses.values()):
        derived = preflight_contract.determine_preflight_outcome(
            states["claude"]["evaluated_preflight"],
            states["opencode"]["evaluated_preflight"],
        )
        outcome = derived["outcome"]
        reason_code = derived["reason_code"]
    elif not aligned:
        derived = preflight_contract.determine_preflight_outcome(
            states["claude"]["evaluated_preflight"],
            states["opencode"]["evaluated_preflight"],
        )
        outcome = derived["outcome"]
        reason_code = derived["reason_code"]
```

and include both fields in the returned summary payload:

```python
        "outcome": outcome,
        "reason_code": reason_code,
```

Do not add a continuation-ready summary file path here; Task 6 continuation-ready runs still stop at preflight artifacts plus baseline.

- [ ] **Step 4: Run focused GREEN tests**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_preflight.py' -v
python3 -m unittest discover -s tests/harness-acceptance -p 'test_summarize.py' -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add tests/harness-acceptance/preflight.py \
        tests/harness-acceptance/summarize.py \
        tests/harness-acceptance/test_preflight.py \
        tests/harness-acceptance/test_summarize.py
git commit -m "test: encode Task 6 preflight outcomes"
```

### Task 2: Add continuation-ready preflight validation helpers and CLI

**Files:**
- Modify: `tests/harness-acceptance/preflight.py`
- Modify: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Produces: `load_run_preflight_state(run_dir: Path, harness_dir: Path) -> dict[str, Any]`
- Produces: `require_continuation_ready(state: dict[str, Any]) -> None`
- Produces CLI: `python3 tests/harness-acceptance/preflight.py --run-dir PATH [--require-aligned]`

- [ ] **Step 1: Add failing tests for run-directory validation and CLI alignment checking**

Add these tests to `tests/harness-acceptance/test_preflight.py`:

```python
def test_load_run_preflight_state_reports_continuation_ready(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        (run_dir / "capabilities").mkdir()
        (run_dir / "preflight").mkdir()
        write_json(run_dir / "capabilities" / "claude.json", self.capability["claude"])
        write_json(run_dir / "capabilities" / "opencode.json", self.capability["opencode"])
        write_json(run_dir / "preflight" / "claude.json", self.base_preflight["claude"])
        write_json(run_dir / "preflight" / "opencode.json", self.base_preflight["opencode"])
        claude_proof = copy.deepcopy(self.base_model_proof)
        claude_proof["harness"] = "claude"
        claude_proof["requested_route"] = "fable"
        opencode_proof = copy.deepcopy(self.base_model_proof)
        opencode_proof["harness"] = "opencode"
        opencode_proof["requested_route"] = "openai/synthetic-model"
        write_json(run_dir / "preflight" / "claude-model-proof.json", claude_proof)
        write_json(run_dir / "preflight" / "opencode-model-proof.json", opencode_proof)
        state = self.preflight.load_run_preflight_state(run_dir, HARNESS_DIR)
        self.assertEqual(state["outcome"], "continuation-ready")
        self.assertEqual(state["canonical_identity"], "openai/synthetic-model")


def test_require_continuation_ready_rejects_allowlist_update_needed(self):
    state = {
        "outcome": "allowlist-update-needed",
        "reason_code": "global_hard_gate_blocked",
        "canonical_identity": None,
    }
    with self.assertRaisesRegex(ValueError, "continuation-ready"):
        self.preflight.require_continuation_ready(state)
```

- [ ] **Step 2: Run the focused RED test**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_preflight.py' -v
```

Expected: FAIL because the new helpers/CLI do not exist yet.

- [ ] **Step 3: Implement the run-directory validation helpers and CLI**

Add this code to `tests/harness-acceptance/preflight.py`:

```python
import argparse
import json
from pathlib import Path


def load_run_preflight_state(run_dir: Path, harness_dir: Path) -> dict[str, Any]:
    identities = load_identities(harness_dir)
    evaluations = {}
    for harness in ("claude", "opencode"):
        capability = lib.read_json(run_dir / "capabilities" / f"{harness}.json")
        preflight_record = lib.read_json(run_dir / "preflight" / f"{harness}.json")
        model_proof = lib.read_json(run_dir / "preflight" / f"{harness}-model-proof.json")
        evaluations[harness] = evaluate_preflight(capability, preflight_record, model_proof, identities)
    outcome = determine_preflight_outcome(evaluations["claude"], evaluations["opencode"])
    return {
        "outcome": outcome["outcome"],
        "reason_code": outcome["reason_code"],
        "canonical_identity": outcome["canonical_identity"],
        "harnesses": evaluations,
    }


def require_continuation_ready(state: dict[str, Any]) -> None:
    if state.get("outcome") != "continuation-ready":
        raise ValueError(f"run is not continuation-ready: {state.get('outcome')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--require-aligned", action="store_true")
    args = parser.parse_args(argv)
    state = load_run_preflight_state(Path(args.run_dir), HERE)
    if args.require_aligned:
        require_continuation_ready(state)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Keep the CLI read-only. It validates an existing run directory; it does not execute any harness commands.

- [ ] **Step 4: Run focused GREEN tests**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_preflight.py' -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add tests/harness-acceptance/preflight.py tests/harness-acceptance/test_preflight.py
git commit -m "test: add Task 6 preflight validation cli"
```

### Task 3: Execute the first real preflight-only run and resolve the allowlist gap path if needed

**Files:**
- Local only: `tests/harness-acceptance/run-config.local.json`
- Local raw only: `.harness-acceptance-local/<run-id>/raw/**`
- Create: `tests/harness-acceptance/results/<run-id>/**`
- Modify only if first real proof reveals a new backing model: `tests/harness-acceptance/model-identities.json`

**Interfaces:**
- Consumes CLI: `./tests/harness-acceptance/run.sh --mode preflight-only --config PATH --run-id ID`
- Consumes CLI: `python3 tests/harness-acceptance/preflight.py --run-dir PATH [--require-aligned]`
- Consumes CLI: `python3 tests/harness-acceptance/redact.py --tree PATH`
- Consumes CLI: `python3 tests/harness-acceptance/summarize.py --run-dir PATH --write|--check-only`
- Produces: one committed real preflight result in state `blocked`, `allowlist-update-needed`, or `continuation-ready`

- [ ] **Step 1: Re-run the full synthetic baseline before any real preflight**

Run:

```bash
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
```

Expected: PASS.

- [ ] **Step 2: Create the local-only real preflight config**

Create `tests/harness-acceptance/run-config.local.json` with this local-only shape:

```json
{
  "claude": {
    "cli_bin": "claude",
    "harness_model_value": "fable",
    "effort_or_variant": "high"
  },
  "opencode": {
    "cli_bin": "opencode",
    "harness_model_value": "openai/proxy-route",
    "effort_or_variant": "high"
  },
  "timeout_seconds": 120,
  "endpoint_identity": "https://api.example.invalid/v1"
}
```

Notes:
- This file is local-only and must not be committed.
- Replace `https://api.example.invalid/v1` with the real non-secret endpoint identity if the runner needs the actual endpoint hash source.
- Do not add credentials or raw environment dumps.

- [ ] **Step 3: Allocate a fresh run ID and verify the result directory is absent**

Run:

```bash
RUN_ID=$(date -u +%Y-%m-%dT%H%M%SZ)
test ! -e "tests/harness-acceptance/results/$RUN_ID"
printf '%s\n' "$RUN_ID"
```

Expected: prints a fresh UTC run id and no failure.

- [ ] **Step 4: Execute the real preflight-only run**

Run:

```bash
./tests/harness-acceptance/run.sh --mode preflight-only \
  --config tests/harness-acceptance/run-config.local.json \
  --run-id "$RUN_ID"
```

Expected: the command exits successfully and writes capability/preflight/model-proof/environment artifacts for the run.

- [ ] **Step 5: Run redaction and classify the run outcome**

Run:

```bash
python3 tests/harness-acceptance/redact.py --tree "tests/harness-acceptance/results/$RUN_ID"
python3 tests/harness-acceptance/preflight.py --run-dir "tests/harness-acceptance/results/$RUN_ID"
```

Expected:
- redaction passes
- the preflight CLI prints JSON with `outcome` equal to one of:
  - `blocked`
  - `allowlist-update-needed`
  - `continuation-ready`
- when `outcome` is `blocked`, the JSON also carries a machine-readable `reason_code`; one allowed blocked sub-reason is `runtime-proof-unavailable`

- [ ] **Step 6: If the outcome is blocked or allowlist-update-needed, write and verify the blocked summary**

Run only when the printed outcome is `blocked` or `allowlist-update-needed`:

```bash
python3 tests/harness-acceptance/summarize.py --run-dir "tests/harness-acceptance/results/$RUN_ID" --write
python3 tests/harness-acceptance/summarize.py --run-dir "tests/harness-acceptance/results/$RUN_ID" --check-only
python3 -m json.tool "tests/harness-acceptance/results/$RUN_ID/summary.json"
python3 -m json.tool "tests/harness-acceptance/results/$RUN_ID/preflight/claude-model-proof.json"
python3 -m json.tool "tests/harness-acceptance/results/$RUN_ID/preflight/opencode-model-proof.json"
```

Expected:
- summary write/check succeeds
- summary includes the correct blocked outcome marker and blocked `reason_code`
- redacted model proofs are readable and self-consistent
- if Claude proves a canonical identity while OpenCode passes capability/preflight but lacks authoritative runtime model proof, the run remains `blocked` with `reason_code = runtime-proof-unavailable`

> Revision note (2026-07-20): the OpenCode capability gate is now defined by repo proof, workspace proof, and canary success. Future implementation must not use `paths_source_match` or `skill_inventory_valid` as hard gates. `debug config`, `debug paths`, and `debug skill` stay committed diagnostics only, and weak debug evidence does not by itself keep OpenCode in raw capability-blocked state. Do not reinterpret the historical blocked evidence at `tests/harness-acceptance/results/2026-07-19T152433Z/`; it remains unchanged old-contract evidence.

- [ ] **Step 7: If the outcome is continuation-ready, validate the preflight basis without final summary artifacts**

Run only when the printed outcome is `continuation-ready`:

```bash
python3 tests/harness-acceptance/preflight.py \
  --run-dir "tests/harness-acceptance/results/$RUN_ID" \
  --require-aligned
python3 -m json.tool "tests/harness-acceptance/results/$RUN_ID/preflight/baseline.json"
python3 -m json.tool "tests/harness-acceptance/results/$RUN_ID/preflight/claude-model-proof.json"
python3 -m json.tool "tests/harness-acceptance/results/$RUN_ID/preflight/opencode-model-proof.json"
```

Expected:
- `--require-aligned` exits 0
- `baseline.json` exists
- no final summary artifacts are required for this branch

- [ ] **Step 8: If the outcome is allowlist-update-needed, commit the blocked evidence first, update the allowlist in a separate commit, then rerun preflight with a new run ID**

`runtime-proof-unavailable` does not enter the allowlist path. It is a final blocked evidence state unless later code changes create a new authoritative runtime proof surface and a brand new Task 6 run is started.

When outcome is `allowlist-update-needed`, first commit the blocked evidence:

```bash
git add "tests/harness-acceptance/results/$RUN_ID"
git commit -m "test: record allowlist-gated real harness preflight"
```

Then add the newly proved mapping using the actual redacted proof values from that run:

```bash
python3 - "$RUN_ID" <<'PY'
import json
import sys
from pathlib import Path

run_dir = Path("tests/harness-acceptance/results") / sys.argv[1]
claude = json.loads((run_dir / "preflight/claude-model-proof.json").read_text(encoding="utf-8"))
opencode = json.loads((run_dir / "preflight/opencode-model-proof.json").read_text(encoding="utf-8"))
assert claude["backing_model_id"] == opencode["backing_model_id"]
assert claude["resolved_model_identity"] == opencode["resolved_model_identity"]
path = Path("tests/harness-acceptance/model-identities.json")
identities = json.loads(path.read_text(encoding="utf-8"))
identities["canonical_models"][claude["backing_model_id"]] = claude["resolved_model_identity"]
path.write_text(json.dumps(identities, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
git add tests/harness-acceptance/model-identities.json
git commit -m "test: allow verified harness backing model"
```

Then rerun Task 3 with a new run id:

```bash
NEW_RUN_ID=$(date -u +%Y-%m-%dT%H%M%SZ)
test ! -e "tests/harness-acceptance/results/$NEW_RUN_ID"
./tests/harness-acceptance/run.sh --mode preflight-only \
  --config tests/harness-acceptance/run-config.local.json \
  --run-id "$NEW_RUN_ID"
python3 tests/harness-acceptance/redact.py --tree "tests/harness-acceptance/results/$NEW_RUN_ID"
python3 tests/harness-acceptance/preflight.py --run-dir "tests/harness-acceptance/results/$NEW_RUN_ID"
```

From that point on, use `NEW_RUN_ID` as the active run and repeat Step 6 or Step 7 depending on the new outcome.

- [ ] **Step 9: Commit the final Task 6 evidence state**

If the final outcome is blocked:

```bash
git add "tests/harness-acceptance/results/$RUN_ID"
git commit -m "test: record blocked real harness preflight"
```

If the final outcome is continuation-ready:

```bash
git add "tests/harness-acceptance/results/$RUN_ID"
git commit -m "test: record real harness preflight baseline"
```

If the allowlist path used `NEW_RUN_ID`, substitute that final run id in the commands above.

## Self-Review

### Spec coverage

- Task 1 preserves the three Task 6 terminal outcomes, adds the required `runtime-proof-unavailable` blocked sub-reason, and keeps blocked-vs-allowlist distinction machine-readable.
- Task 2 adds a read-only validation path for continuation-ready preflight runs that do not write final summaries.
- Task 3 covers the real operator workflow, redaction, blocked summary writing, manual proof review, `runtime-proof-unavailable` blocked handling, strict allowlist rerun handling, and final evidence commit.
- No task introduces scored case execution, router changes, workflow-contract changes, or push/release work.

### Placeholder scan

- No `TODO`/`TBD` placeholders remain.
- Conditional real-run branches are spelled out explicitly rather than deferred.
- Local-only config uses a concrete synthetic endpoint example rather than a placeholder token.

### Type consistency

- `determine_preflight_outcome(...)` is defined in Task 1 and consumed in Task 2 and Task 3 semantics.
- `load_run_preflight_state(...)` and `require_continuation_ready(...)` are defined in Task 2 and used in Task 3.
- The blocked summary `outcome` field introduced in Task 1 is the same field Task 3 reads for operator branching.

Plan complete and saved to `docs/superpowers/plans/2026-07-19-task6-real-preflight.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**