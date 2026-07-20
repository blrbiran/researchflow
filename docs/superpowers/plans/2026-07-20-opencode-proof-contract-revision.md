# OpenCode Proof Contract Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the revised OpenCode proof contract so capability/plugin proof is evaluated separately from runtime model proof, future OpenCode preflight runs can classify as `runtime-proof-unavailable`, and historical Task 6 blocked evidence remains unchanged.

**Architecture:** Keep the change narrow. Update the OpenCode capability gate in `tests/harness-acceptance/capabilities.py` so repo proof, workspace proof, and canary success decide raw capability pass/fail while debug surfaces remain advisory diagnostics. Then extend synthetic tests and docs so the revised gate feeds into the existing `runtime-proof-unavailable` preflight semantics without changing Claude behavior or rewriting committed Task 6 evidence.

**Tech Stack:** Python 3 standard library, JSON fixtures, existing `tests/harness-acceptance` contract helpers, `unittest`, Markdown docs

## Global Constraints

- implement the revised OpenCode proof contract with capability/plugin proof separated from runtime model proof;
- do not reopen Task 5;
- do not run scored cases;
- do not reclassify or rewrite `tests/harness-acceptance/results/2026-07-19T152433Z/`;
- preserve Claude semantics;
- keep `runtime-proof-unavailable` as the blocked reason when capability passes but authoritative runtime model proof is unavailable;
- update spec/plan/handover/code/tests consistently;
- capability pass must never imply Task 7 is allowed to start;
- debug surfaces stay collected as diagnostics and must not silently disappear from committed evidence;
- rerun synthetic baseline only.

---

## File Structure

- `tests/harness-acceptance/capabilities.py` — revise OpenCode capability gating, branch/profile semantics, and diagnostic field handling without changing Claude logic.
- `tests/harness-acceptance/test_capabilities.py` — update OpenCode capability expectations to match repo/workspace/canary hard-gate semantics and preserve diagnostic-field visibility.
- `tests/harness-acceptance/test_preflight.py` — add a cross-layer regression test proving capability-pass plus missing authoritative model proof lands on `runtime-proof-unavailable`.
- `tests/harness-acceptance/fixtures/capabilities/opencode-strong.json` — adjust or replace as a capability-pass fixture under the revised contract.
- `tests/harness-acceptance/fixtures/capabilities/opencode-fallback.json` — adjust or replace as a capability-pass fixture with weak diagnostics under the revised contract.
- `tests/harness-acceptance/fixtures/capabilities/opencode-unsupported.json` — preserve unsupported capability fixture under the revised contract.
- `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md` — record the revised OpenCode contract and the separation between capability proof and runtime model proof.
- `docs/superpowers/plans/2026-07-19-task6-real-preflight.md` — supersede old OpenCode-gating assumptions and point future implementation work at the revised contract.
- `docs/handover/researchwork-plugin-handover.md` — record that the historical Task 6 blocked run remains valid old-contract evidence and future similar runs should classify as `runtime-proof-unavailable`.
- `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md` — already-written spec to keep aligned if wording needs a final touch during implementation.

### Task 1: Revise the OpenCode capability contract in synthetic tests first

**Files:**
- Modify: `tests/harness-acceptance/test_capabilities.py`
- Modify: `tests/harness-acceptance/fixtures/capabilities/opencode-strong.json`
- Modify: `tests/harness-acceptance/fixtures/capabilities/opencode-fallback.json`
- Modify: `tests/harness-acceptance/fixtures/capabilities/opencode-unsupported.json`

**Interfaces:**
- Consumes: `select_opencode_proof_branch(probe: dict[str, Any]) -> Optional[str]`
- Consumes: `select_isolation_profile(probe: dict[str, Any]) -> Optional[str]`
- Produces: revised OpenCode fixture expectations where repo/workspace/canary are hard gates and debug fields are advisory
- Produces: an explicit synthetic regression for the observed real-world shape (`paths_source_match = false`, `skill_inventory_valid = false`, capability still passable)

- [ ] **Step 1: Replace the old branch/profile expectations with revised contract assertions**

Edit `tests/harness-acceptance/test_capabilities.py` so the OpenCode contract test no longer encodes `strong-runtime-proof` / `fallback-workspace-proof` as required semantics. Replace the current test bodies with assertions like:

```python
def test_select_opencode_proof_branch_supports_capability_pass_and_unsupported(self):
    self.assertEqual(
        self.capabilities.select_opencode_proof_branch(self.fixtures["opencode_strong"]),
        "workspace-repo-canary-proof",
    )
    self.assertEqual(
        self.capabilities.select_opencode_proof_branch(self.fixtures["opencode_fallback"]),
        "workspace-repo-canary-proof",
    )
    self.assertIsNone(self.capabilities.select_opencode_proof_branch(self.fixtures["opencode_unsupported"]))


def test_select_isolation_profile_keeps_opencode_profile_consistent_under_revised_gate(self):
    self.assertEqual(
        self.capabilities.select_isolation_profile(self.fixtures["opencode_strong"]),
        "workspace-config-runtime-proof",
    )
    self.assertEqual(
        self.capabilities.select_isolation_profile(self.fixtures["opencode_fallback"]),
        "workspace-config-runtime-proof",
    )
    self.assertIsNone(self.capabilities.select_isolation_profile(self.fixtures["opencode_unsupported"]))
```

- [ ] **Step 2: Add the failing diagnostic-regression test**

Add this new test to `tests/harness-acceptance/test_capabilities.py`:

```python
def test_select_opencode_proof_branch_allows_weak_debug_diagnostics_when_repo_workspace_and_canary_hold(self):
    weak_debug = clone_json(self.fixtures["opencode_fallback"])
    weak_debug["probe_results"]["debug"]["paths_source_match"] = False
    weak_debug["probe_results"]["debug"]["skill_inventory_valid"] = False
    self.assertEqual(
        self.capabilities.select_opencode_proof_branch(weak_debug),
        "workspace-repo-canary-proof",
    )
```

- [ ] **Step 3: Remove the old fail-closed assumptions from the targeted OpenCode test**

Replace the current `test_select_opencode_proof_branch_requires_metadata_inventory_workspace_and_source_evidence` body with a version that only treats repo/workspace/canary failures as hard blockers:

```python
def test_select_opencode_proof_branch_requires_repo_workspace_and_canary_evidence(self):
    missing_plugin_validation = clone_json(self.fixtures["opencode_strong"])
    missing_plugin_validation["probe_results"]["repo_validation"]["plugin_source_file_valid"] = False
    self.assertIsNone(self.capabilities.select_opencode_proof_branch(missing_plugin_validation))

    missing_repo_inventory = clone_json(self.fixtures["opencode_strong"])
    missing_repo_inventory["probe_results"]["repo_validation"]["required_skill_inventory_valid"] = False
    self.assertIsNone(self.capabilities.select_opencode_proof_branch(missing_repo_inventory))

    missing_workspace = clone_json(self.fixtures["opencode_strong"])
    missing_workspace["probe_results"]["repo_validation"]["workspace_config_valid"] = False
    self.assertIsNone(self.capabilities.select_opencode_proof_branch(missing_workspace))

    missing_canary = clone_json(self.fixtures["opencode_strong"])
    missing_canary["probe_results"]["run"]["canary_passed"] = False
    self.assertIsNone(self.capabilities.select_opencode_proof_branch(missing_canary))
```

- [ ] **Step 4: Update the OpenCode fixtures to match the revised semantics**

Make the fixture contents reflect the new contract. The intended shapes are:

`tests/harness-acceptance/fixtures/capabilities/opencode-strong.json`
```json
{
  "harness": "opencode",
  "workspace_plugin_matches_checkout": true,
  "probe_results": {
    "repo_validation": {
      "plugin_source_file_valid": true,
      "required_skill_inventory_valid": true,
      "required_skill_inventory_missing": [],
      "workspace_config_valid": true
    },
    "debug": {
      "config": true,
      "config_source_match": true,
      "paths": true,
      "paths_source_match": true,
      "paths_isolation_supported": true,
      "skill": true,
      "skill_inventory_valid": true
    },
    "run": {
      "canary_passed": true
    }
  }
}
```

`tests/harness-acceptance/fixtures/capabilities/opencode-fallback.json`
```json
{
  "harness": "opencode",
  "workspace_plugin_matches_checkout": true,
  "probe_results": {
    "repo_validation": {
      "plugin_source_file_valid": true,
      "required_skill_inventory_valid": true,
      "required_skill_inventory_missing": [],
      "workspace_config_valid": true
    },
    "debug": {
      "config": false,
      "config_source_match": false,
      "paths": true,
      "paths_source_match": false,
      "paths_isolation_supported": true,
      "skill": false,
      "skill_inventory_valid": false
    },
    "run": {
      "canary_passed": true
    }
  }
}
```

`tests/harness-acceptance/fixtures/capabilities/opencode-unsupported.json`
```json
{
  "harness": "opencode",
  "workspace_plugin_matches_checkout": false,
  "probe_results": {
    "repo_validation": {
      "plugin_source_file_valid": false,
      "required_skill_inventory_valid": false,
      "required_skill_inventory_missing": ["using-researchflow"],
      "workspace_config_valid": false
    },
    "debug": {
      "config": true,
      "config_source_match": false,
      "paths": true,
      "paths_source_match": false,
      "paths_isolation_supported": false,
      "skill": true,
      "skill_inventory_valid": false
    },
    "run": {
      "canary_passed": false
    }
  }
}
```

- [ ] **Step 5: Run the focused RED test suite**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_capabilities.py' -v
```

Expected:
- FAIL because `capabilities.py` still requires `paths_source_match` / `skill_inventory_valid` for OpenCode capability selection;
- failures point at the revised `workspace-repo-canary-proof` expectation.

- [ ] **Step 6: Commit the test-only contract update**

```bash
git add tests/harness-acceptance/test_capabilities.py \
        tests/harness-acceptance/fixtures/capabilities/opencode-strong.json \
        tests/harness-acceptance/fixtures/capabilities/opencode-fallback.json \
        tests/harness-acceptance/fixtures/capabilities/opencode-unsupported.json
git commit -m "test: revise opencode capability contract"
```

### Task 2: Implement the revised OpenCode capability gate

**Files:**
- Modify: `tests/harness-acceptance/capabilities.py`
- Test: `tests/harness-acceptance/test_capabilities.py`

**Interfaces:**
- Consumes: `_validate_opencode_repo(repo_root: Path) -> dict[str, Any]`
- Consumes: `_validate_opencode_workspace_config(path: Path, repo_root: str) -> bool`
- Produces: `select_opencode_proof_branch(probe: dict[str, Any]) -> Optional[str]`
- Produces: `select_isolation_profile(probe: dict[str, Any]) -> Optional[str]`
- Produces: `build_capability_record("opencode", cli_version, probe) -> dict[str, Any]`

- [ ] **Step 1: Narrow the OpenCode branch constants to the revised contract**

Edit the OpenCode branch/profile constants near the top of `tests/harness-acceptance/capabilities.py` so the branch name stops implying old strong/fallback debug-surface semantics:

```python
OPENCODE_CAPABILITY_BRANCH = "workspace-repo-canary-proof"
OPENCODE_RUNTIME_PROFILE = "workspace-config-runtime-proof"
```

Delete the old fallback branch constant and its static-profile companion if nothing else uses them:

```python
# Remove:
# OPENCODE_FALLBACK_BRANCH = "fallback-workspace-proof"
# OPENCODE_STATIC_PROFILE = "workspace-config-static-proof"
```

- [ ] **Step 2: Rewrite `select_opencode_proof_branch()` around repo/workspace/canary only**

Replace the current OpenCode-specific body with this minimal version:

```python
def select_opencode_proof_branch(probe: dict[str, Any]) -> Optional[str]:
    probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
    if not isinstance(probe_results, dict):
        return None
    if not _opencode_repo_validation_ok(probe_results):
        return None

    run = probe_results.get("run")
    if not isinstance(run, dict) or run.get("canary_passed") is not True:
        return None

    return OPENCODE_CAPABILITY_BRANCH
```

This keeps debug fields in `probe_results`, but they no longer gate capability success.

- [ ] **Step 3: Keep OpenCode isolation/profile selection aligned with the new branch**

Update the OpenCode part of `select_isolation_profile()` to map the revised branch to the existing runtime profile:

```python
if harness == "opencode":
    branch = select_opencode_proof_branch(probe)
    if branch == OPENCODE_CAPABILITY_BRANCH:
        return OPENCODE_RUNTIME_PROFILE
```

Also update `_plugin_proof_strength_for_probe()` so capability pass no longer overstates weak diagnostic evidence. Add an OpenCode helper that preserves `resolved_runtime_source_inventory_canary` only for full resolved debug evidence and returns `workspace_config_static_inventory_canary` for capability-pass weak-diagnostic cases:

```python
def _opencode_plugin_proof_strength(probe: dict[str, Any]) -> Optional[str]:
    branch = select_opencode_proof_branch(probe)
    if branch != OPENCODE_CAPABILITY_BRANCH:
        return None
    probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
    debug = probe_results.get("debug") if isinstance(probe_results, dict) else None
    if not isinstance(debug, dict):
        return OPENCODE_STATIC_PROOF_STRENGTH
    strong_runtime_debug_evidence = (
        _truthy(debug.get("config"))
        and _truthy(debug.get("config_source_match"))
        and _truthy(debug.get("paths"))
        and _truthy(debug.get("paths_source_match"))
        and _truthy(debug.get("paths_isolation_supported"))
        and _truthy(debug.get("skill"))
        and _truthy(debug.get("skill_inventory_valid"))
    )
    if strong_runtime_debug_evidence:
        return OPENCODE_RUNTIME_PROOF_STRENGTH
    return OPENCODE_STATIC_PROOF_STRENGTH

if harness == "opencode":
    return _opencode_plugin_proof_strength(probe)
```

- [ ] **Step 4: Preserve diagnostic fields without promoting them back to hard gates**

Keep `_probe_from_opencode_dir()` computing these fields exactly as diagnostics:

```python
config_source_match = debug_config_status and (
    _plugin_path_matches(debug_config_payload, str(repo_root))
    or _plugin_path_matches_text(debug_config_text, str(repo_root))
)
paths_source_match = debug_paths_status and _opencode_paths_source_match(
    debug_paths_payload,
    debug_paths_text,
    str(repo_root),
)
skill_inventory_valid = debug_skill_status and _runtime_skill_inventory_valid(
    debug_skill_payload or debug_skill_text
)
```

Do not delete them from `probe_results["debug"]`; only stop consuming them in the hard gate.

- [ ] **Step 5: Run the focused GREEN test suite**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_capabilities.py' -v
```

Expected:
- PASS;
- OpenCode capability tests now pass when repo/workspace/canary hold even with weak diagnostics;
- Claude tests remain green.

- [ ] **Step 6: Commit the capability-gate implementation**

```bash
git add tests/harness-acceptance/capabilities.py tests/harness-acceptance/test_capabilities.py
git commit -m "fix: separate opencode capability from model proof"
```

### Task 3: Prove the revised gate feeds into `runtime-proof-unavailable`

**Files:**
- Modify: `tests/harness-acceptance/test_preflight.py`
- Test: `tests/harness-acceptance/test_capabilities.py`
- Test: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Consumes: `evaluate_preflight(capability: dict[str, Any], preflight: dict[str, Any], model_proof: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]`
- Consumes: `determine_preflight_outcome(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]`
- Produces: a cross-layer regression proving capability-pass plus missing runtime proof becomes `runtime-proof-unavailable`

- [ ] **Step 1: Add the failing cross-layer regression test**

Append this test to `tests/harness-acceptance/test_preflight.py`:

```python
def test_revised_opencode_capability_pass_still_blocks_on_runtime_proof_unavailable(self):
    claude_capability = copy.deepcopy(self.capability["claude"])
    claude_preflight = copy.deepcopy(self.base_preflight["claude"])
    claude_model_proof = copy.deepcopy(self.base_model_proof)

    opencode_capability = copy.deepcopy(self.capability["opencode"])
    opencode_capability["selected_proof_branch"] = "workspace-repo-canary-proof"
    opencode_capability["selected_isolation_profile"] = "workspace-config-runtime-proof"
    opencode_capability["probe_results"]["debug"]["paths_source_match"] = False
    opencode_capability["probe_results"]["debug"]["skill_inventory_valid"] = False

    opencode_preflight = copy.deepcopy(self.base_preflight["opencode"])
    opencode_preflight["status"] = "pass"
    opencode_preflight["isolation_profile"] = "workspace-config-runtime-proof"
    opencode_preflight["plugin_proof_strength"] = "workspace_config_static_inventory_canary"

    opencode_model_proof = copy.deepcopy(self.base_model_proof)
    opencode_model_proof["harness"] = "opencode"
    opencode_model_proof["requested_route"] = "openai-compatible/gpt-5.4"
    opencode_model_proof["backing_model_id"] = "unknown"
    opencode_model_proof["resolved_model_identity"] = None
    opencode_model_proof["proof_method"] = "missing-model-metadata"
    opencode_model_proof["verified"] = False

    claude_result = self.preflight.evaluate_preflight(
        claude_capability,
        claude_preflight,
        claude_model_proof,
        self.identities,
    )
    opencode_result = self.preflight.evaluate_preflight(
        opencode_capability,
        opencode_preflight,
        opencode_model_proof,
        self.identities,
    )
    outcome = self.preflight.determine_preflight_outcome(claude_result, opencode_result)

    self.assertTrue(opencode_result["raw_gate_passed"])
    self.assertEqual(opencode_result["status"], "pass")
    self.assertEqual(opencode_result["plugin_proof_strength"], "workspace_config_static_inventory_canary")
    self.assertFalse(opencode_result["proof_valid"])
    self.assertEqual(outcome["outcome"], "blocked")
    self.assertEqual(outcome["reason_code"], self.preflight.lib.REASON_CODES[5])
```

- [ ] **Step 2: Run the focused RED preflight suite**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_preflight.py' -v
```

Expected:
- FAIL until the capability gate and selected branch semantics are aligned with the revised contract.

- [ ] **Step 3: Adjust the synthetic OpenCode base capability fixture assumptions in the new test only**

If the new test still relies on old fixture semantics after Task 2, keep the adjustment local to the test body rather than changing unrelated summary fixtures. The final shape in the test should continue to use:

```python
opencode_capability["selected_proof_branch"] = "workspace-repo-canary-proof"
opencode_capability["selected_isolation_profile"] = "workspace-config-runtime-proof"
```

Do not mutate historical result artifacts or any committed real-run JSON under `tests/harness-acceptance/results/`.

- [ ] **Step 4: Run the focused GREEN suites**

Run:

```bash
python3 -m unittest discover -s tests/harness-acceptance -p 'test_capabilities.py' -v
python3 -m unittest discover -s tests/harness-acceptance -p 'test_preflight.py' -v
```

Expected:
- PASS;
- the new regression proves capability pass plus missing model proof reaches `runtime-proof-unavailable`.

- [ ] **Step 5: Commit the cross-layer regression coverage**

```bash
git add tests/harness-acceptance/test_preflight.py tests/harness-acceptance/test_capabilities.py
git commit -m "test: lock revised opencode proof outcome"
```

### Task 4: Update the active Task 6 docs and handover to the revised contract

**Files:**
- Modify: `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md`
- Modify: `docs/superpowers/plans/2026-07-19-task6-real-preflight.md`
- Modify: `docs/handover/researchwork-plugin-handover.md`
- Modify: `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md` (only if implementation wording must be synchronized)

**Interfaces:**
- Consumes: the approved revision spec at `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`
- Produces: updated Task 6/handver docs that explain future `runtime-proof-unavailable` classification without reinterpreting the historical blocked run

- [ ] **Step 1: Add the revised OpenCode contract text to the Task 6 spec**

In `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md`, add a short subsection near the existing OpenCode proof discussion that states:

```md
For OpenCode, capability/plugin proof and runtime model proof are separate gates.

- repo static proof, workspace proof, and canary success determine whether OpenCode passes the capability/plugin gate;
- `debug config`, `debug paths`, and `debug skill` remain diagnostic evidence only;
- `run --format json` is not an accepted authoritative runtime model-proof surface on the current non-interactive path;
- therefore a future OpenCode run that passes capability/plugin proof but cannot emit authoritative runtime model proof must classify as `blocked` with `reason_code = runtime-proof-unavailable`.
```

- [ ] **Step 2: Add the revised contract note to the Task 6 plan**

In `docs/superpowers/plans/2026-07-19-task6-real-preflight.md`, add a bounded note near the OpenCode proof steps that says future implementation must not use `paths_source_match` or `skill_inventory_valid` as hard gates and must not reinterpret the historical `2026-07-19T152433Z` run.

Use wording like:

```md
Revision note (2026-07-20): the OpenCode capability gate is now defined by repo proof, workspace proof, and canary success. Weak `debug paths` or `debug skill` evidence does not by itself keep OpenCode in raw capability-blocked state. Historical blocked evidence remains unchanged.
```

- [ ] **Step 3: Update the handover so the next agent sees old-contract vs new-contract semantics clearly**

Add a short paragraph in `docs/handover/researchwork-plugin-handover.md` near the current Task 6 status section:

```md
Contract revision note: `tests/harness-acceptance/results/2026-07-19T152433Z/` remains valid blocked evidence under the old OpenCode capability contract. After the 2026-07-20 proof-contract revision lands, comparable future runs should be expected to pass capability/plugin proof and classify as `runtime-proof-unavailable` if authoritative runtime model proof is still unavailable.
```

- [ ] **Step 4: Run a docs-only consistency check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
paths = [
    Path('docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md'),
    Path('docs/superpowers/plans/2026-07-19-task6-real-preflight.md'),
    Path('docs/handover/researchwork-plugin-handover.md'),
    Path('docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md'),
]
for path in paths:
    text = path.read_text(encoding='utf-8')
    assert 'runtime-proof-unavailable' in text
print('docs contract strings present')
PY
```

Expected:
- PASS with `docs contract strings present`.

- [ ] **Step 5: Commit the documentation updates**

```bash
git add docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md \
        docs/superpowers/plans/2026-07-19-task6-real-preflight.md \
        docs/handover/researchwork-plugin-handover.md \
        docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md
git commit -m "docs: record revised opencode proof contract"
```

### Task 5: Run the synthetic baseline and confirm historical evidence is untouched

**Files:**
- Verify: `tests/harness-acceptance/results/2026-07-19T152433Z/**`
- Verify: `tests/harness-acceptance/run-tests.sh`
- Verify: `tests/run-all.sh`

**Interfaces:**
- Consumes: all earlier tasks
- Produces: final verification that the revised contract is green in synthetic tests and that the historical Task 6 evidence tree was not modified

- [ ] **Step 1: Snapshot the historical evidence tree status before running tests**

Run:

```bash
git status --short -- tests/harness-acceptance/results/2026-07-19T152433Z
```

Expected:
- no output.

- [ ] **Step 2: Run the harness synthetic baseline**

Run:

```bash
./tests/harness-acceptance/run-tests.sh
```

Expected:
- PASS;
- harness acceptance tests complete without scored-case execution.

- [ ] **Step 3: Run the repository synthetic baseline**

Run:

```bash
./tests/run-all.sh
```

Expected:
- PASS;
- repository smoke/demo baseline still succeeds.

- [ ] **Step 4: Re-check the historical evidence tree remains untouched**

Run:

```bash
git status --short -- tests/harness-acceptance/results/2026-07-19T152433Z
```

Expected:
- no output.

- [ ] **Step 5: Commit the final implementation state**

```bash
git add tests/harness-acceptance/capabilities.py \
        tests/harness-acceptance/test_capabilities.py \
        tests/harness-acceptance/test_preflight.py \
        tests/harness-acceptance/fixtures/capabilities/opencode-strong.json \
        tests/harness-acceptance/fixtures/capabilities/opencode-fallback.json \
        tests/harness-acceptance/fixtures/capabilities/opencode-unsupported.json \
        docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md \
        docs/superpowers/plans/2026-07-19-task6-real-preflight.md \
        docs/handover/researchwork-plugin-handover.md \
        docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md \
        docs/superpowers/plans/2026-07-20-opencode-proof-contract-revision.md
git commit -m "fix: revise opencode proof contract"
```

## Self-Review

### Spec coverage

- Task 1 rewrites the OpenCode fixture/test contract so repo/workspace/canary become the hard gate and weak diagnostics no longer fail-close the capability path.
- Task 2 updates the actual OpenCode capability gate in `capabilities.py` while preserving diagnostic field collection and leaving Claude untouched.
- Task 3 adds the cross-layer regression proving the revised capability pass still resolves to `runtime-proof-unavailable` when authoritative runtime model proof is absent.
- Task 4 updates the active Task 6 spec, Task 6 plan, handover, and revision spec so future workers understand old-contract versus new-contract semantics.
- Task 5 reruns only synthetic baselines and explicitly checks that `tests/harness-acceptance/results/2026-07-19T152433Z/` remains untouched.

### Placeholder scan

- No `TODO`/`TBD` placeholders remain.
- Every task includes concrete file paths, test bodies, and commands.
- Historical evidence preservation is encoded as explicit verification commands rather than prose-only guidance.

### Type consistency

- The plan consistently uses `select_opencode_proof_branch(...)` as the capability-gate selector and `select_isolation_profile(...)` as the derived profile selector.
- The revised branch name is consistently `workspace-repo-canary-proof` across tests and implementation steps.
- The runtime-proof blocked reason remains `runtime-proof-unavailable` and is never replaced by a new reason-code family.

Plan complete and saved to `docs/superpowers/plans/2026-07-20-opencode-proof-contract-revision.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**