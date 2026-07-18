# Task 4 Review-Close Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Review-close Task 4 in a fresh worktree on top of `main`, making only the minimum synthetic fixes needed for the five named review concerns and proving the result with the required adapter syntax checks plus the full synthetic test suite.

**Architecture:** This is a bounded closure pass, not new feature work. Start from a new `.worktrees/` checkout of `main`, lock each named concern with a failing synthetic test first, patch the smallest adapter/capability path that can satisfy the contract, and verify each task before moving on. Keep production harness behavior separate from fake-fixture wiring, and do not start Task 5 or any live harness execution.

**Tech Stack:** git worktree, Bash adapters, Python 3 standard library, `unittest`, JSON fixture scenarios, existing `tests/run-all.sh`

## Global Constraints

- This pass covers only Task 4 review closure on top of repo-root `main`.
- Allowed code changes are limited to the Task 4 surface and the smallest shared files directly required to close one of the five named review concerns.
- Do not start Task 5 preflight/orchestration work.
- Do not modify router behavior, `skills/using-researchflow/SKILL.md`, or `docs/workflow-contracts.md`.
- Do not perform real `claude`, `opencode`, LiteLLM, network, or paid-model invocation.
- Do not clean up `.claude/worktrees/agent-*` directories.
- Do not touch any `.omc/` directory.
- Use a fresh local worktree under `.worktrees/<task4-review-close>`.
- Before any code change, read `docs/handover/researchwork-plugin-handover.md`, `docs/superpowers/specs/2026-07-17-live-harness-acceptance-design.md`, `docs/superpowers/plans/2026-07-17-live-harness-acceptance.md`, `tests/harness-acceptance/scored-prompt.txt`, `tests/harness-acceptance/capabilities.py`, both native adapters, both Task 4 test files, and the relevant Task 4 fixtures.
- Required verification for this pass is:
  - `bash -n tests/harness-acceptance/adapters/claude.sh`
  - `bash -n tests/harness-acceptance/adapters/opencode.sh`
  - `python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v`
  - `./tests/run-all.sh`
- The only acceptable completion claim is: `Task 4 is synthetically review-closed in a fresh clean worktree with synthetic verification passing; no live harness acceptance has been performed.`

---

## File Structure

- `.worktrees/task4-review-close/` — fresh execution checkout rooted at repo `main`; do all implementation and verification in this worktree.
- `tests/harness-acceptance/adapters/claude.sh` — Claude capability, preflight, and case adapter; likely edit sites for shared scored-suffix composition and case workspace isolation.
- `tests/harness-acceptance/adapters/opencode.sh` — OpenCode capability, preflight, and case adapter; likely edit sites for shared scored-suffix composition and fixture-only wiring removal.
- `tests/harness-acceptance/capabilities.py` — probe parsing, branch/profile selection, model/tool normalization, and `normalize-case`; likely edit sites for evidence-derived booleans and fail-closed native event normalization.
- `tests/harness-acceptance/test_adapters.py` — synthetic adapter contract coverage for capability/preflight/case mode and no-overwrite behavior; add tests here for scored suffix composition, Claude workspace isolation, and test-only fixture separation.
- `tests/harness-acceptance/test_capabilities.py` — synthetic coverage for branch/profile selection, tool classification, and fail-closed parsing; add tests here for evidence-derived booleans and native-event normalization.
- `tests/harness-acceptance/scored-prompt.txt` — shared routing-only suffix. Only edit if review proves the checked-in contract text itself is wrong; otherwise leave it unchanged and fix composition in adapters.
- `tests/harness-acceptance/test_contracts.py` — shared contract lock for `cases.json`, `scored-prompt.txt`, and invocation schema; only edit if a shared contract file must change.
- `tests/harness-acceptance/fixtures/adapters/**` — fake CLI scripts and scenario directories used by `test_adapters.py`; only add or adjust fixtures needed to prove one of the five named review concerns.
- `tests/harness-acceptance/fixtures/capabilities/**` — capability probe fixtures used by `test_capabilities.py`; use these to lock evidence-derived booleans and fail-closed probe behavior.
- `tests/run-all.sh` — repo-wide synthetic verification entrypoint; never replace it with a narrower command.

### Task 1: Lock scored-suffix composition and Claude fresh-workspace isolation in a clean worktree

**Files:**
- Modify: `tests/harness-acceptance/adapters/claude.sh`
- Modify: `tests/harness-acceptance/adapters/opencode.sh`
- Modify: `tests/harness-acceptance/test_adapters.py`
- Modify: `tests/harness-acceptance/fixtures/adapters/fake-claude.sh`
- Modify: `tests/harness-acceptance/fixtures/adapters/fake-opencode.sh`
- Modify only if review proves the shared contract text is wrong: `tests/harness-acceptance/scored-prompt.txt`
- Modify only if `scored-prompt.txt` changes: `tests/harness-acceptance/test_contracts.py`

**Interfaces:**
- Consumes: `case_prompt()` in both adapter scripts.
- Consumes: `run_case_command()` in `tests/harness-acceptance/adapters/claude.sh:277` and `tests/harness-acceptance/adapters/opencode.sh:257`.
- Consumes: `run_adapter()` and `make_config()` in `tests/harness-acceptance/test_adapters.py`.
- Produces: both adapters compose `<case prompt> + blank line + contents of scored-prompt.txt` before any case run.
- Produces: Claude case mode executes from a case-local workspace path under the temp raw directory instead of the repository root.
- Produces: fake adapter fixtures write `last-prompt.txt` and `last-cwd.txt` into the cloned scenario directory so tests can assert prompt composition and workspace isolation without touching production paths.

- [ ] **Step 1: Create the clean worktree from repo-root `main`**

Run from the repository root:

```bash
git worktree add -b task4-review-close .worktrees/task4-review-close main
```

Expected: `Preparing worktree` output with no errors.

Then verify the new checkout is clean:

```bash
git -C .worktrees/task4-review-close status --short
```

Expected: no output.

- [ ] **Step 2: Write the failing adapter tests for shared suffix composition and Claude case cwd**

Add these tests to `tests/harness-acceptance/test_adapters.py` inside `AdapterTest`:

```python
def test_case_mode_appends_shared_suffix_for_both_harnesses(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        scored_suffix = (HARNESS_DIR / "scored-prompt.txt").read_text(encoding="utf-8").rstrip()

        cases = [
            ("claude", self.claude_adapter, "claude-direct", self.fake_claude),
            ("opencode", self.opencode_adapter, "opencode-strong", self.fake_opencode),
        ]
        for harness, script, scenario_name, _ in cases:
            scenario_dir = self.clone_scenario(temp_root / harness, scenario_name)
            config_path = self.make_config(temp_root / harness, scenario_name, harness, scenario_dir=scenario_dir)
            output_dir = temp_root / harness / "case"
            result = self.run_adapter(script, "case", config_path, output_dir, case_id="R-DIRECT-LIT")
            self.assertEqual(result.returncode, 0, result.stderr)
            captured_prompt = (scenario_dir / "last-prompt.txt").read_text(encoding="utf-8")
            self.assertTrue(captured_prompt.rstrip().endswith(scored_suffix))


def test_claude_case_mode_runs_in_fresh_workspace(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        scenario_dir = self.clone_scenario(temp_root, "claude-direct")
        config_path = self.make_config(temp_root, "claude-direct", "claude", scenario_dir=scenario_dir)
        output_dir = temp_root / "claude-case"
        result = self.run_adapter(self.claude_adapter, "case", config_path, output_dir, case_id="R-DIRECT-LIT")
        self.assertEqual(result.returncode, 0, result.stderr)
        cwd = Path((scenario_dir / "last-cwd.txt").read_text(encoding="utf-8").strip())
        self.assertNotEqual(cwd, ROOT)
        self.assertTrue(cwd.is_dir())
        self.assertTrue(str(cwd).startswith(str(temp_root)))
```

- [ ] **Step 3: Run the adapter-only suite to prove the new tests fail first**

Run from `.worktrees/task4-review-close/`:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_adapters.py' -v
```

Expected: the two new tests fail because the adapters currently read only `cases.json` and Claude case mode does not execute from a fresh case workspace.

- [ ] **Step 4: Patch both adapters to append the shared suffix, and patch Claude case mode to execute from a case-local workspace**

Update `case_prompt()` in both adapters so it reads `cases.json` and `scored-prompt.txt` together:

```bash
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
        print(f"{prompt}\n\n{suffix}\n")
        break
else:
    raise SystemExit(f"unknown case_id: {case_id}")
PY
}
```

In `tests/harness-acceptance/adapters/claude.sh`, make `run_capture()` honor a case-local cwd and make `run_case_command()` create and use a workspace directory:

```bash
cwd = os.environ.get("RUN_CWD") or None
completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, cwd=cwd)
```

```bash
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
  args+=(--no-session-persistence --tools "" --output-format json --model "$MODEL_VALUE" --effort "$EFFORT_VALUE")
  RUN_CWD="$workspace_dir" run_capture "$stdout_path" "$stderr_path" "$status_path" "${args[@]}"
}
```

Update Claude case mode to pass the new workspace argument:

```bash
CASE_RAW_DIR="$(mktemp -d "$RAW_ROOT/claude-case-${CASE_ID}.XXXXXX")"
prompt="$(case_prompt "$CASE_ID")"
run_case_command "$prompt" "$CASE_RAW_DIR/events.jsonl" "$CASE_RAW_DIR/stderr.txt" "$CASE_RAW_DIR/status.txt" "$profile" "$CASE_RAW_DIR/workspace"
```

Do not edit `tests/harness-acceptance/scored-prompt.txt` unless the checked-in text itself is wrong. If you do change it, update `EXPECTED_SUFFIX` in `tests/harness-acceptance/test_contracts.py` in the same task.

- [ ] **Step 5: Make the fake fixture scripts capture the prompt and cwd for test inspection**

Add these two lines to both `tests/harness-acceptance/fixtures/adapters/fake-claude.sh` and `tests/harness-acceptance/fixtures/adapters/fake-opencode.sh` after the prompt has been parsed and validated:

```bash
printf '%s' "$prompt" > "$SCENARIO_DIR/last-prompt.txt"
printf '%s\n' "$PWD" > "$SCENARIO_DIR/last-cwd.txt"
```

Do not make the production adapters read these files. They are test-only artifacts written by the fake CLIs.

- [ ] **Step 6: Re-run the adapter-only suite and the shared contract test if the suffix file changed**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_adapters.py' -v
```

Expected: PASS for the two new adapter tests and all pre-existing adapter tests.

Only if you edited `tests/harness-acceptance/scored-prompt.txt`, also run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_contracts.py' -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 1**

Run from `.worktrees/task4-review-close/`:

```bash
git add tests/harness-acceptance/adapters/claude.sh \
        tests/harness-acceptance/adapters/opencode.sh \
        tests/harness-acceptance/test_adapters.py \
        tests/harness-acceptance/fixtures/adapters/fake-claude.sh \
        tests/harness-acceptance/fixtures/adapters/fake-opencode.sh \
        tests/harness-acceptance/scored-prompt.txt \
        tests/harness-acceptance/test_contracts.py
git commit -m "fix: lock Task 4 prompt and workspace contract"
```

Expected: a new commit on `task4-review-close`.

### Task 2: Fail-close native event normalization and derive capability booleans from probe evidence

**Files:**
- Modify: `tests/harness-acceptance/capabilities.py`
- Modify: `tests/harness-acceptance/test_capabilities.py`
- Modify only if the current committed capability fixtures do not cover the reviewed branch: `tests/harness-acceptance/fixtures/capabilities/*.json`
- Modify only if adapter-case fixtures are needed to pin the exact accepted native event shape: `tests/harness-acceptance/fixtures/adapters/**`

**Interfaces:**
- Consumes: `build_capability_record()` in `tests/harness-acceptance/capabilities.py:508`.
- Consumes: `_response_text()`, `_extract_model_event()`, `classify_tool_execution()`, and `build_invocation_record()` in `tests/harness-acceptance/capabilities.py`.
- Produces: capability booleans in the exported capability JSON are derived from actual probe evidence, not constant `True` values.
- Produces: `build_invocation_record()` recognizes only the native event shapes explicitly locked by tests and otherwise fails closed.
- Produces: unknown or malformed native event shapes still yield empty response / unverified model / `unknown` tool status rather than optimistic success.

- [ ] **Step 1: Write the failing capability test for evidence-derived booleans**

Add this test to `tests/harness-acceptance/test_capabilities.py`:

```python
def test_build_capability_record_derives_boolean_fields_from_probe_evidence(self):
    probe = clone_json(self.fixtures["claude_direct"])
    probe["probe_results"]["environment_validation"]["structured_output_supported"] = False
    probe["probe_results"]["environment_validation"]["session_persistence_disable_supported"] = False
    record = self.capabilities.build_capability_record("claude", "2.1.212", probe)
    self.assertFalse(record["structured_output"])
    self.assertFalse(record["session_persistence_disable"])
    self.assertIsNone(record["selected_load_branch"])
    self.assertIsNone(record["selected_isolation_profile"])
```

This test is allowed to force the selected branch/profile to `None`; that is the fail-closed behavior you want when the required evidence disappears.

- [ ] **Step 2: Write the failing normalization test for unknown-or-native event shapes**

Add one fail-closed test that writes an event stream with no recognized response/model fields and proves the normalized record does not claim success:

```python
def test_build_invocation_record_fail_closes_on_unrecognized_event_shapes(self):
    config = {
        "run_id": "2026-07-17T120000Z",
        "repo_commit_sha": "c" * 40,
        "timeout_seconds": 120,
        "endpoint_identity": "https://proxy.example.com/v1?token=secret",
        "claude": {
            "harness_model_value": "fable",
            "effort_or_variant": "high",
        },
    }
    capability = self.capabilities.build_capability_record("claude", "2.1.212", self.fixtures["claude_direct"])
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        events_path = temp_root / "events.jsonl"
        stderr_path = temp_root / "stderr.txt"
        events_path.write_text(json.dumps({"type": "unknown", "payload": "x"}) + "\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        invocation, command, final_response = self.capabilities.build_invocation_record(
            "claude",
            config,
            capability,
            "R-DIRECT-LIT",
            "2.1.212",
            events_path,
            stderr_path,
            0,
        )
    self.assertEqual(final_response, "")
    self.assertFalse(invocation["model_identity_verified"])
    self.assertEqual(invocation["tool_execution"]["side_effect_status"], "none")
```

If your review shows that a real committed Task 4 fixture already contains a second native event shape that should be accepted, add one more test using that exact fixture shape. Do not invent a new accepted schema that is not already present in the reviewed Task 4 fixtures.

- [ ] **Step 3: Run the capability-only suite to prove the new tests fail first**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_capabilities.py' -v
```

Expected: the new boolean-derivation test fails because `build_capability_record()` currently hard-codes several capability booleans to `True`.

- [ ] **Step 4: Replace hard-coded capability booleans with evidence-derived values and keep normalization fail-closed**

In `build_capability_record()`, replace constant booleans with values derived from the probe results already parsed by `_probe_from_claude_dir()` / `_probe_from_opencode_dir()`. For Claude, use `environment_validation` directly:

```python
environment = probe.get("probe_results", {}).get("environment_validation", {})
record = {
    "schema_version": 1,
    "harness": harness,
    "cli_version": cli_version,
    "noninteractive": True,
    "structured_output": bool(environment.get("structured_output_supported")) if harness == "claude" else True,
    "local_plugin_loading": selected_profile is not None,
    "session_persistence_disable": bool(environment.get("session_persistence_disable_supported")) if harness == "claude" else True,
    "settings_isolation": selected_profile is not None,
    ...
}
```

Do not make unknown probe fields truthy by default.

For native event normalization, keep the default behavior fail-closed. Only add explicit branches for event shapes you can point to in the committed Task 4 fixtures you just reviewed. The pattern for an accepted branch is:

```python
if event.get("event") == "response" and isinstance(event.get("text"), str):
    parts.append(event["text"])
    continue
if event.get("type") == "response.output_text.delta" and isinstance(event.get("delta"), str):
    parts.append(event["delta"])
```

Apply the same rule to model and tool extraction: add a branch only for the exact fixture-backed shape you are preserving, and leave all other unknown shapes on the current fail-closed path.

- [ ] **Step 5: Re-run the capability-only suite**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_capabilities.py' -v
```

Expected: PASS for the new evidence-derivation and fail-closed normalization tests plus all pre-existing capability tests.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add tests/harness-acceptance/capabilities.py \
        tests/harness-acceptance/test_capabilities.py \
        tests/harness-acceptance/fixtures/capabilities \
        tests/harness-acceptance/fixtures/adapters
git commit -m "fix: fail-close Task 4 capability normalization"
```

Expected: a second commit on `task4-review-close`.

### Task 3: Remove fixture-only production wiring, rerun the full synthetic suite, and close the review loop

**Files:**
- Modify: `tests/harness-acceptance/adapters/claude.sh`
- Modify: `tests/harness-acceptance/adapters/opencode.sh`
- Modify: `tests/harness-acceptance/test_adapters.py`
- Modify only if needed to keep fake scripts aligned with the new test-only env path: `tests/harness-acceptance/fixtures/adapters/fake-claude.sh`
- Modify only if needed to keep fake scripts aligned with the new test-only env path: `tests/harness-acceptance/fixtures/adapters/fake-opencode.sh`

**Interfaces:**
- Consumes: `SCENARIO_DIR` handling in both adapters.
- Consumes: `make_config()` and `run_adapter()` in `tests/harness-acceptance/test_adapters.py`.
- Produces: fake-fixture scenario selection is test-only wiring supplied by the tests, not a production config key consumed by real adapter config.
- Produces: the final verification set required by the spec runs cleanly from the fresh worktree.

- [ ] **Step 1: Write the failing adapter test that removes `scenario_dir` from production config**

Add this test to `tests/harness-acceptance/test_adapters.py`:

```python
def test_make_config_does_not_embed_test_only_scenario_dir(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        scenario_dir = self.clone_scenario(temp_root, "claude-direct")
        config_path = self.make_config(temp_root, "claude-direct", "claude", scenario_dir=scenario_dir)
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertNotIn("scenario_dir", payload["claude"])
        self.assertNotIn("scenario_dir", payload["opencode"])
```

Then change one existing case-mode test to pass the cloned scenario directory into `run_adapter()` explicitly rather than expecting it to come from config.

- [ ] **Step 2: Run the adapter-only suite to prove the config-separation test fails first**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_adapters.py' -v
```

Expected: the new config-separation test fails because `make_config()` currently serializes `scenario_dir` into the adapter config.

- [ ] **Step 3: Move fake-fixture scenario wiring out of production config and into the test env**

In `tests/harness-acceptance/test_adapters.py`, remove `scenario_dir` from the config JSON written by `make_config()` and teach `run_adapter()` to inject test-only env vars instead:

```python
def run_adapter(self, script: Path, mode: str, config_path: Path, output_dir: Path, case_id: Optional[str] = None, scenario_dir: Optional[Path] = None):
    command = ["bash", str(script), "--mode", mode, "--config", str(config_path), "--output-dir", str(output_dir)]
    if case_id is not None:
        command.extend(["--case-id", case_id])
    env = os.environ.copy()
    env["ECC_GATEGUARD"] = "off"
    if scenario_dir is not None:
        if script == self.claude_adapter:
            env["FAKE_CLAUDE_SCENARIO_DIR"] = str(scenario_dir)
        if script == self.opencode_adapter:
            env["FAKE_OPENCODE_SCENARIO_DIR"] = str(scenario_dir)
    return subprocess.run(command, capture_output=True, text=True, env=env)
```

In both adapters, stop reading `scenario_dir` from config and read only the test-only env var instead:

```bash
SCENARIO_DIR="${FAKE_CLAUDE_SCENARIO_DIR:-}"
```

```bash
SCENARIO_DIR="${FAKE_OPENCODE_SCENARIO_DIR:-}"
```

This keeps the production config schema free of fixture-only fields while preserving the synthetic fake-CLI path used by `test_adapters.py`.

- [ ] **Step 4: Re-run the adapter-only suite**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_adapters.py' -v
```

Expected: PASS for the new config-separation test and all existing adapter tests.

- [ ] **Step 5: Run the full required verification set from the fresh worktree**

Run exactly these commands from `.worktrees/task4-review-close/`:

```bash
bash -n tests/harness-acceptance/adapters/claude.sh
bash -n tests/harness-acceptance/adapters/opencode.sh
python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v
./tests/run-all.sh
```

Expected:
- both `bash -n` commands exit 0 with no output;
- the `unittest discover` run reports all Task 4 synthetic tests passing;
- `./tests/run-all.sh` ends with `All ResearchFlow tests passed.`

- [ ] **Step 6: Re-check the five named review concerns before the final commit**

Use this exact checklist and do not proceed until every line is `meets contract`:

```text
[ ] scored suffix composition
[ ] native JSON event-shape normalization
[ ] Claude fresh-workspace isolation
[ ] evidence-derived capability booleans
[ ] production vs test-only wiring separation
```

If any line is still `needs fix`, go back to the matching task and add the missing test + minimal patch before claiming closure.

- [ ] **Step 7: Commit Task 3**

Run:

```bash
git add tests/harness-acceptance/adapters/claude.sh \
        tests/harness-acceptance/adapters/opencode.sh \
        tests/harness-acceptance/capabilities.py \
        tests/harness-acceptance/test_adapters.py \
        tests/harness-acceptance/test_capabilities.py \
        tests/harness-acceptance/fixtures/adapters \
        tests/harness-acceptance/fixtures/capabilities
git commit -m "fix: close Task 4 synthetic review gaps"
```

Expected: a final Task 4 review-close commit on `task4-review-close`.
