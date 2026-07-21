# Reference-Only OpenCode Proof Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the current ResearchFlow harness accept OpenCode runtime model proof only from the current run’s trusted preflight artifacts, never from `reference/opencode` or any other non-run path.

**Architecture:** Introduce one shared current-run-only proof loader in `tests/harness-acceptance/lib.py`, route both `preflight.py` and `run.py` through it, and lock the boundary with regression coverage that asserts attempted proof-read path provenance. Update the handover and adjacent proof-contract spec so the reference-only boundary is explicit in current-repo documentation.

**Tech Stack:** Python 3.9, existing `tests/harness-acceptance` harness utilities, `unittest`, Markdown docs

## Global Constraints

- Scope is only the current ResearchFlow repo; do not modify `reference/opencode`.
- Keep `reference/opencode` reference-only and never treat it as authoritative runtime proof input.
- Preserve current fail-closed behavior: missing authoritative OpenCode runtime proof must remain `blocked` with `reason_code = runtime-proof-unavailable`.
- Do not introduce any new proof source, upstream dependency, or Task 7 continuation path.
- Trusted proof provenance is path-based: only current-run artifacts under `tests/harness-acceptance/results/<run-id>/preflight/` are accepted.
- The guard must validate both trusted root path and fixed artifact filenames.
- `preflight.py` and `run.py` must share the same loader so there is one defended boundary.
- Regression coverage must assert attempted proof-read paths, not only the final blocked outcome.
- Keep doc updates narrow: `docs/handover/researchwork-plugin-handover.md` and `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`.

---

## File Structure

- `tests/harness-acceptance/lib.py` — add the shared trusted-root runtime proof loader and the explicit reference-only comment; this is the only accepted proof entrypoint.
- `tests/harness-acceptance/preflight.py` — replace direct model-proof reads with the shared loader; keep outcome semantics unchanged.
- `tests/harness-acceptance/run.py` — replace direct model-proof reads with the same shared loader in both preflight-only and scored continuation paths.
- `tests/harness-acceptance/test_preflight.py` — add path-provenance regression coverage and keep the existing `runtime-proof-unavailable` regression green.
- `docs/handover/researchwork-plugin-handover.md` — clarify that `reference/opencode` is reference-only and not a continuation-proof source.
- `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md` — make the current-repo accepted proof-source boundary explicit and consistent with the new guard.

### Task 1: Add the shared trusted-root proof loader in `lib.py`

**Files:**
- Modify: `tests/harness-acceptance/lib.py`
- Test via later tasks: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Produces: `def load_runtime_model_proof_artifact(run_dir: Path, harness: str, results_root: Path) -> dict[str, Any]`
- Consumes: `run_dir: Path`, `harness in {"claude", "opencode"}`, `results_root: Path`
- Produces for later tasks: one shared loader that validates trusted root provenance and reads exactly `preflight/<harness>-model-proof.json`

- [ ] **Step 1: Write the failing regression test scaffold in `test_preflight.py`**

```python
def test_runtime_model_proof_loader_rejects_run_dir_outside_results_tree(self):
    outside_run_dir = (ROOT / "reference" / "opencode").resolve()
    with self.assertRaises(ValueError):
        self.preflight.lib.load_runtime_model_proof_artifact(
            outside_run_dir,
            "opencode",
            HARNESS_DIR / "results",
        )
```

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
python3 -m unittest tests.harness-acceptance.test_preflight.PreflightTest.test_runtime_model_proof_loader_rejects_run_dir_outside_results_tree -v
```

Expected: FAIL because the helper does not exist yet.

- [ ] **Step 3: Add the minimal helper to `lib.py`**

```python
def load_runtime_model_proof_artifact(run_dir: Path, harness: str, results_root: Path) -> dict[str, Any]:
    if harness not in ("claude", "opencode"):
        raise ValueError(f"unsupported harness: {harness}")

    resolved_run_dir = run_dir.resolve()
    resolved_results_root = results_root.resolve()
    try:
        resolved_run_dir.relative_to(resolved_results_root)
    except ValueError as exc:
        raise ValueError(f"run_dir is outside trusted results tree: {resolved_run_dir}") from exc

    proof_path = resolved_run_dir / "preflight" / f"{harness}-model-proof.json"
    # reference/opencode is reference-only; never widen runtime proof lookup beyond the current run.
    return read_json(proof_path)
```

- [ ] **Step 4: Run the focused test to verify GREEN**

Run:

```bash
python3 -m unittest tests.harness-acceptance.test_preflight.PreflightTest.test_runtime_model_proof_loader_rejects_run_dir_outside_results_tree -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add tests/harness-acceptance/lib.py tests/harness-acceptance/test_preflight.py
git commit -m "test: guard trusted runtime proof root"
```

### Task 2: Route `preflight.py` through the shared loader without changing outcomes

**Files:**
- Modify: `tests/harness-acceptance/preflight.py`
- Test: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Consumes: `lib.load_runtime_model_proof_artifact(run_dir: Path, harness: str, results_root: Path) -> dict[str, Any]`
- Produces: `load_run_preflight_state(run_dir: Path, harness_dir: Path) -> dict[str, Any]` still returns the same schema and reason-code semantics

- [ ] **Step 1: Extend the failing regression to capture attempted proof paths**

```python
def test_load_run_preflight_state_reads_only_current_run_proof_artifacts(self):
    attempted = []
    original = self.preflight.lib.read_json

    def fake_read_json(path: Path):
        attempted.append(path.resolve())
        return original(path)

    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir) / "results" / "run-1"
        (run_dir / "capabilities").mkdir(parents=True)
        (run_dir / "preflight").mkdir(parents=True)
        write_json(run_dir / "capabilities" / "claude.json", copy.deepcopy(self.capability["claude"]))
        write_json(run_dir / "capabilities" / "opencode.json", copy.deepcopy(self.capability["opencode"]))
        write_json(run_dir / "preflight" / "claude.json", copy.deepcopy(self.base_preflight["claude"]))
        write_json(run_dir / "preflight" / "opencode.json", copy.deepcopy(self.base_preflight["opencode"]))
        write_json(run_dir / "preflight" / "claude-model-proof.json", copy.deepcopy(self.base_model_proof))
        broken_opencode_proof = copy.deepcopy(self.base_model_proof)
        broken_opencode_proof["resolved_model_identity"] = None
        broken_opencode_proof["verified"] = False
        write_json(run_dir / "preflight" / "opencode-model-proof.json", broken_opencode_proof)

        try:
            self.preflight.lib.read_json = fake_read_json
            state = self.preflight.load_run_preflight_state(run_dir, HARNESS_DIR)
        finally:
            self.preflight.lib.read_json = original

    proof_reads = [path for path in attempted if path.name.endswith("-model-proof.json")]
    self.assertTrue(all((run_dir / "preflight") in path.parents for path in proof_reads))
    self.assertTrue(all("reference/opencode" not in str(path) for path in proof_reads))
    self.assertEqual(state["outcome"], "blocked")
    self.assertEqual(state["reason_code"], self.preflight.lib.REASON_CODES[5])
```

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
python3 -m unittest tests.harness-acceptance.test_preflight.PreflightTest.test_load_run_preflight_state_reads_only_current_run_proof_artifacts -v
```

Expected: FAIL because `preflight.py` still reads `run_dir / "preflight" / f"{harness}-model-proof.json"` directly.

- [ ] **Step 3: Replace direct reads in `preflight.py` with the shared helper**

```python
def load_run_preflight_state(run_dir: Path, harness_dir: Path) -> dict[str, Any]:
    identities = load_identities(harness_dir)
    results_root = harness_dir / "results"
    evaluations = {}
    for harness in ("claude", "opencode"):
        capability = lib.read_json(run_dir / "capabilities" / f"{harness}.json")
        preflight_record = lib.read_json(run_dir / "preflight" / f"{harness}.json")
        model_proof = lib.load_runtime_model_proof_artifact(run_dir, harness, results_root)
        evaluations[harness] = evaluate_preflight(capability, preflight_record, model_proof, identities)
```

- [ ] **Step 4: Re-run the focused regression and the existing revised-contract regression**

Run:

```bash
python3 -m unittest \
  tests.harness-acceptance.test_preflight.PreflightTest.test_load_run_preflight_state_reads_only_current_run_proof_artifacts \
  tests.harness-acceptance.test_preflight.PreflightTest.test_revised_opencode_capability_pass_still_blocks_on_runtime_proof_unavailable -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add tests/harness-acceptance/preflight.py tests/harness-acceptance/test_preflight.py
git commit -m "fix: keep preflight proof reads current-run only"
```

### Task 3: Route `run.py` through the same loader and preserve orchestration behavior

**Files:**
- Modify: `tests/harness-acceptance/run.py`
- Test: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Consumes: `lib.load_runtime_model_proof_artifact(run_dir: Path, harness: str, results_root: Path) -> dict[str, Any]`
- Produces: unchanged preflight-only/scored orchestration semantics; no new proof source

- [ ] **Step 1: Write the failing orchestration-level regression**

```python
def test_run_module_uses_shared_runtime_model_proof_loader_contract(self):
    source = (HARNESS_DIR / "run.py").read_text(encoding="utf-8")
    self.assertIn("load_runtime_model_proof_artifact", source)
    self.assertNotIn('lib.read_json(preflight_dir / f"{harness}-model-proof.json")', source)
```

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
python3 -m unittest tests.harness-acceptance.test_preflight.PreflightTest.test_run_module_uses_shared_runtime_model_proof_loader_contract -v
```

Expected: FAIL because `run.py` still reads the model-proof artifacts directly.

- [ ] **Step 3: Replace direct model-proof reads in `run.py`**

```python
model_proof = lib.load_runtime_model_proof_artifact(run_dir, harness, HARNESS_DIR / "results")
```

Apply that replacement in:
- the preflight-only loop
- the scored-phase evaluation dict
- the expected-baseline model-proof dict builder

Do not change outcome logic, scoring logic, or baseline fingerprint structure.

- [ ] **Step 4: Run the focused tests to verify GREEN**

Run:

```bash
python3 -m unittest \
  tests.harness-acceptance.test_preflight.PreflightTest.test_run_module_uses_shared_runtime_model_proof_loader_contract \
  tests.harness-acceptance.test_preflight.PreflightTest.test_load_run_preflight_state_reads_only_current_run_proof_artifacts -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

```bash
git add tests/harness-acceptance/run.py tests/harness-acceptance/test_preflight.py
git commit -m "refactor: share trusted proof loader"
```

### Task 4: Update handover and adjacent proof-contract spec narrowly

**Files:**
- Modify: `docs/handover/researchwork-plugin-handover.md`
- Modify: `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`

**Interfaces:**
- Consumes: approved design in `docs/superpowers/specs/2026-07-21-reference-opencode-proof-boundary-design.md`
- Produces: current-repo documentation that explicitly treats `reference/opencode` as reference-only and current-run preflight artifacts as the only accepted runtime-proof source

- [ ] **Step 1: Add the failing documentation assertions in a temporary focused check**

```python
handover = (ROOT / "docs" / "handover" / "researchwork-plugin-handover.md").read_text(encoding="utf-8")
proof_spec = (ROOT / "docs" / "superpowers" / "specs" / "2026-07-20-opencode-proof-contract-revision-design.md").read_text(encoding="utf-8")
assert "reference/opencode" in handover
assert "reference-only" in handover
assert "tests/harness-acceptance/results" in proof_spec
```

Use an ad hoc local check only while editing; do not create a permanent new test file for this doc wording.

- [ ] **Step 2: Update the handover text narrowly**

Add wording that says, in substance:

```markdown
- `reference/opencode` is reference-only in the current workflow and must not be consumed as authoritative runtime proof input for Task 6 / Task 7 continuation decisions.
- Current ResearchFlow harness evaluation accepts runtime model proof only from the current run's preflight artifacts under `tests/harness-acceptance/results/<run-id>/preflight/`.
```

- [ ] **Step 3: Update the adjacent proof-contract spec narrowly**

Add wording that says, in substance:

```markdown
For the current ResearchFlow repo, accepted runtime-proof input is limited to the current run's preflight model-proof artifacts under `tests/harness-acceptance/results/<run-id>/preflight/`. Reference checkouts such as `reference/opencode` remain diagnostic/reference material and must not be promoted into authoritative runtime proof.
```

- [ ] **Step 4: Run a narrow documentation check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
root = Path("docs")
handover = (root / "handover" / "researchwork-plugin-handover.md").read_text(encoding="utf-8")
proof_spec = (root / "superpowers" / "specs" / "2026-07-20-opencode-proof-contract-revision-design.md").read_text(encoding="utf-8")
assert "reference/opencode" in handover and "reference-only" in handover
assert "tests/harness-acceptance/results" in proof_spec and "reference/opencode" in proof_spec
print("docs-ok")
PY
```

Expected: `docs-ok`

- [ ] **Step 5: Commit Task 4**

```bash
git add docs/handover/researchwork-plugin-handover.md docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md
git commit -m "docs: clarify reference-only opencode proof boundary"
```

### Task 5: Run the focused harness baseline and confirm scope

**Files:**
- Verify: `tests/harness-acceptance/lib.py`
- Verify: `tests/harness-acceptance/preflight.py`
- Verify: `tests/harness-acceptance/run.py`
- Verify: `tests/harness-acceptance/test_preflight.py`
- Verify: `docs/handover/researchwork-plugin-handover.md`
- Verify: `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`

**Interfaces:**
- Consumes: Tasks 1-4
- Produces: final confirmation that the change is current-repo-only, fail-closed, and introduces no new proof source

- [ ] **Step 1: Run the focused harness tests**

Run:

```bash
python3 -m unittest tests.harness-acceptance.test_preflight -v
```

Expected: PASS, including the new provenance regression and the existing `runtime-proof-unavailable` regression.

- [ ] **Step 2: Run the broader harness baseline**

Run:

```bash
./tests/harness-acceptance/run-tests.sh
```

Expected: PASS.

- [ ] **Step 3: Confirm no non-current-repo implementation surface was touched**

Run:

```bash
git diff --name-only HEAD~4..HEAD
```

Expected:
- only `tests/harness-acceptance/**`
- `docs/handover/researchwork-plugin-handover.md`
- `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`
- no `reference/opencode/**` paths

- [ ] **Step 4: Commit any final cleanup only if needed**

If the focused and broad tests pass with no further edits, skip this step.

If one tiny cleanup is required after the full baseline, use:

```bash
git add <exact-paths>
git commit -m "fix: tighten proof boundary guard"
```

## Self-Review

### Spec coverage
- Task 1 adds the narrow shared loader and trusted-root guard in `lib.py`.
- Task 2 moves `preflight.py` onto that loader and preserves `runtime-proof-unavailable` behavior.
- Task 3 moves `run.py` onto the same loader so there is one defended boundary.
- Task 4 updates the two specified docs narrowly.
- Task 5 runs the focused and broader harness baselines and confirms no `reference/opencode` implementation changes were introduced.

### Placeholder scan
- No `TODO` / `TBD` placeholders remain.
- Every task includes exact files, explicit code snippets, concrete commands, and expected outcomes.
- The documentation check is narrow and temporary; no unnecessary permanent doc-test file was added.

### Type consistency
- The shared helper name is consistently `load_runtime_model_proof_artifact`.
- The trusted root is consistently `tests/harness-acceptance/results/`.
- The preserved blocked outcome is consistently `runtime-proof-unavailable`.

Plan complete and saved to `docs/superpowers/plans/2026-07-21-reference-opencode-proof-boundary.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**