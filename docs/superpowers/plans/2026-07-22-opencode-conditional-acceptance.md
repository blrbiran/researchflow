# OpenCode Conditional Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first slice of the dual-track Task 6 / Task 7 contract so ResearchFlow can distinguish strong continuation from OpenCode-conditional continuation, carry OpenCode proof absence as machine-readable proof facts, and report accepted outcomes through `acceptance_class` without claiming strong cross-harness alignment.

**Architecture:** Keep the trusted proof boundary and proof extraction logic unchanged. Add the new semantics at the contract layer only: `preflight.py` classifies Task 6 into strong vs conditional continuation, `run.py` allows scored execution from a conditional baseline, and `summarize.py` reports accepted terminal outcomes with `acceptance_class` plus `proof_facts`. Lock the behavior with focused unit tests before touching implementation, and update handover/spec docs only after the code and tests agree.

**Tech Stack:** Python 3.9, `unittest`, JSON artifact contracts, shell wrapper orchestration via existing harness scripts.

## Global Constraints

- Keep `reference/opencode` reference-only; do not modify it or consume it as authoritative runtime proof input.
- Do not change adapter capture behavior, the trusted current-run proof boundary, or underlying OpenCode proof-unavailable detection in this slice.
- Claude must remain the canonicalized anchor: conditional continuation requires Claude authoritative proof plus allowlisted `canonical_identity`.
- Conditional acceptance counts as `acceptance_passed = true`, but must always disclose that OpenCode runtime identity was not authoritatively proved.
- Use `outcome` only for top-level terminal state and `acceptance_class` for strong vs conditional accepted results.
- Represent OpenCode missing runtime proof as machine-readable `proof_facts`, not only as a terminal `reason_code`.
- Preserve historical evidence directories unchanged.
- Keep changes surgical: only the first implementation slice from `docs/superpowers/specs/2026-07-22-opencode-conditional-acceptance-design.md`.

---

## File map

- `tests/harness-acceptance/preflight.py` — Task 6 contract classification logic; today emits `continuation-ready`, `allowlist-update-needed`, or blocked outcomes.
- `tests/harness-acceptance/run.py` — preflight baseline writer and scored gate; today requires aligned preflight before baseline/scored continuation.
- `tests/harness-acceptance/summarize.py` — final summary/result builder and markdown renderer; today assumes accepted runs are only strong aligned runs.
- `tests/harness-acceptance/test_preflight.py` — unit tests for preflight evaluation and outcome classification.
- `tests/harness-acceptance/test_run.py` — unit tests for baseline writing and scored continuation rules.
- `tests/harness-acceptance/test_summarize.py` — unit tests for final result shapes and markdown output.
- `docs/superpowers/specs/2026-07-22-opencode-conditional-acceptance-design.md` — approved design record; update only if implementation reveals wording drift.
- `docs/handover/researchwork-plugin-handover.md` — operational contract and next-step notes; update after implementation/test semantics are final.

### Planned interface additions

These names are the contract for the implementation tasks below.

- `preflight.determine_preflight_outcome(...) -> dict[str, Any]`
  - Produces keys:
    - `outcome`: one of `blocked`, `allowlist-update-needed`, `continuation-ready-strong`, `continuation-ready-conditional`
    - `reason_code`: `str | None`
    - `canonical_identity`: `str | None`
    - `proof_facts`: `dict[str, str]`
- `preflight.require_continuation_ready(state: dict[str, Any]) -> None`
  - Accepts both `continuation-ready-strong` and `continuation-ready-conditional`
- `run.build_baseline_record(...) -> dict[str, Any]`
  - Adds baseline contract field `continuation_class`: `strong | conditional-opencode`
  - Adds `proof_facts` object keyed by harness fact names used later by scored continuation and summary reconstruction
- `summarize.build_summary(run_dir: Path, cases: list[dict[str, Any]]) -> dict[str, Any]`
  - Produces keys:
    - `outcome`: top-level terminal state such as `accepted`, `blocked`, `failed`, `allowlist-update-needed`, `continuation-ready-strong`, `continuation-ready-conditional`
    - `acceptance_class`: `None | "strong" | "conditional-opencode"`
    - `proof_facts`: `dict[str, str]`
    - `acceptance_disclosure`: `None | list[str]`

### Recommended task order

1. Preflight classification and proof-fact shape
2. Runner baseline/scored gate updates
3. Summary/result payload and markdown updates
4. Documentation alignment

### Task 1: Preflight contract classification

**Files:**
- Modify: `tests/harness-acceptance/preflight.py:79-159`
- Test: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Consumes: existing `evaluate_preflight(...) -> dict[str, Any]` results with keys `status`, `raw_gate_passed`, `canonical_identity`, `proof_identity`, `proof_valid`, `allowlist_missing`, `backing_model_id`
- Produces:
  - `determine_preflight_outcome(...) -> dict[str, Any]` with:
    ```python
    {
        "outcome": str,
        "reason_code": str | None,
        "canonical_identity": str | None,
        "proof_facts": dict[str, str],
    }
    ```
  - `load_run_preflight_state(...) -> dict[str, Any]` including root-level `proof_facts`
  - `require_continuation_ready(state)` accepting both continuation-ready classes

- [ ] **Step 1: Write the failing tests for the new conditional preflight contract**

```python
    def test_determine_preflight_outcome_marks_conditional_continuation_for_opencode_proof_gap(self):
        claude = {
            "status": "pass",
            "raw_gate_passed": True,
            "canonical_identity": "openai/gpt-5.4",
            "proof_identity": "openai/gpt-5.4",
            "proof_valid": True,
            "allowlist_missing": False,
        }
        opencode = {
            "status": "pass",
            "raw_gate_passed": True,
            "canonical_identity": None,
            "proof_identity": None,
            "proof_valid": False,
            "allowlist_missing": False,
        }
        result = self.preflight.determine_preflight_outcome(claude, opencode)
        self.assertEqual(result["outcome"], "continuation-ready-conditional")
        self.assertIsNone(result["reason_code"])
        self.assertEqual(result["canonical_identity"], "openai/gpt-5.4")
        self.assertEqual(result["proof_facts"], {"opencode_runtime_proof": "unavailable"})

    def test_determine_preflight_outcome_keeps_claude_allowlist_gap_outside_conditional_path(self):
        claude = {
            "status": "pass",
            "raw_gate_passed": True,
            "canonical_identity": None,
            "proof_identity": "openai/gpt-5.4",
            "proof_valid": True,
            "allowlist_missing": True,
        }
        opencode = {
            "status": "pass",
            "raw_gate_passed": True,
            "canonical_identity": None,
            "proof_identity": None,
            "proof_valid": False,
            "allowlist_missing": False,
        }
        result = self.preflight.determine_preflight_outcome(claude, opencode)
        self.assertEqual(result["outcome"], "allowlist-update-needed")
        self.assertEqual(result["reason_code"], self.preflight.lib.REASON_CODES[3])
        self.assertEqual(result["proof_facts"], {"opencode_runtime_proof": "unavailable"})

    def test_require_continuation_ready_accepts_conditional_state(self):
        self.preflight.require_continuation_ready({"outcome": "continuation-ready-conditional"})
```

- [ ] **Step 2: Run the targeted preflight tests to confirm RED**

Run: `python3 -m unittest tests/harness-acceptance/test_preflight.py -v`
Expected: FAIL on the new conditional tests because `determine_preflight_outcome()` still returns `blocked` for OpenCode runtime-proof absence and `require_continuation_ready()` only accepts `continuation-ready`.

- [ ] **Step 3: Implement the minimal outcome-shape changes in `preflight.py`**

```python
def determine_preflight_outcome(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]:
    alignment = evaluate_model_alignment(claude_result, opencode_result)
    proof_facts: dict[str, str] = {}
    if not opencode_result.get("proof_valid"):
        proof_facts["opencode_runtime_proof"] = "unavailable"
    if alignment["aligned"]:
        return {
            "outcome": "continuation-ready-strong",
            "reason_code": None,
            "canonical_identity": alignment["canonical_identity"],
            "proof_facts": proof_facts,
        }
    raw_gate_passed = bool(claude_result.get("raw_gate_passed")) and bool(opencode_result.get("raw_gate_passed"))
    if (
        raw_gate_passed
        and alignment["reason_code"] == GLOBAL_HARD_GATE_BLOCKED
        and claude_result.get("proof_valid")
        and opencode_result.get("proof_valid")
        and claude_result.get("proof_identity") == opencode_result.get("proof_identity")
        and (claude_result.get("allowlist_missing") or opencode_result.get("allowlist_missing"))
    ):
        return {
            "outcome": "allowlist-update-needed",
            "reason_code": GLOBAL_HARD_GATE_BLOCKED,
            "canonical_identity": None,
            "proof_facts": proof_facts,
        }
    if (
        raw_gate_passed
        and claude_result.get("proof_valid")
        and isinstance(claude_result.get("canonical_identity"), str)
        and not opencode_result.get("proof_valid")
    ):
        return {
            "outcome": "continuation-ready-conditional",
            "reason_code": None,
            "canonical_identity": claude_result["canonical_identity"],
            "proof_facts": proof_facts,
        }
    if raw_gate_passed and (not claude_result.get("proof_valid") or not opencode_result.get("proof_valid")):
        return {
            "outcome": "blocked",
            "reason_code": RUNTIME_PROOF_UNAVAILABLE,
            "canonical_identity": None,
            "proof_facts": proof_facts,
        }
    if claude_result.get("status") != "pass" or opencode_result.get("status") != "pass":
        return {
            "outcome": "blocked",
            "reason_code": alignment["reason_code"] or GLOBAL_HARD_GATE_BLOCKED,
            "canonical_identity": None,
            "proof_facts": proof_facts,
        }
    return {
        "outcome": "blocked",
        "reason_code": alignment["reason_code"] or MODEL_ALIGNMENT_BLOCKED,
        "canonical_identity": None,
        "proof_facts": proof_facts,
    }


def require_continuation_ready(state: dict[str, Any]) -> None:
    if state.get("outcome") not in {"continuation-ready-strong", "continuation-ready-conditional"}:
        raise ValueError(f"run is not continuation-ready: {state.get('outcome')}")
```

- [ ] **Step 4: Extend `load_run_preflight_state()` to carry the proof facts through**

```python
    outcome = determine_preflight_outcome(evaluations["claude"], evaluations["opencode"])
    return {
        "outcome": outcome["outcome"],
        "reason_code": outcome["reason_code"],
        "canonical_identity": outcome["canonical_identity"],
        "proof_facts": outcome["proof_facts"],
        "harnesses": evaluations,
    }
```

- [ ] **Step 5: Re-run the targeted preflight tests to confirm GREEN**

Run: `python3 -m unittest tests/harness-acceptance/test_preflight.py -v`
Expected: PASS, including the new conditional continuation and allowlist-gap guard tests.

- [ ] **Step 6: Commit the preflight contract slice**

```bash
git add tests/harness-acceptance/preflight.py tests/harness-acceptance/test_preflight.py
git commit -m "fix: classify opencode conditional continuation"
```

### Task 2: Runner baseline and scored continuation gate

**Files:**
- Modify: `tests/harness-acceptance/run.py:58-90`
- Modify: `tests/harness-acceptance/run.py:267-329`
- Test: `tests/harness-acceptance/test_run.py`

**Interfaces:**
- Consumes:
  - `preflight.determine_preflight_outcome(...) -> {outcome, reason_code, canonical_identity, proof_facts}`
  - `preflight.require_continuation_ready(state)`
- Produces:
  - `build_baseline_record(...) -> dict[str, Any]` with added keys:
    ```python
    {
        "continuation_class": "strong" | "conditional-opencode",
        "proof_facts": dict[str, str],
    }
    ```
  - `run_original(..., mode="preflight-only")` writing `preflight/baseline.json` for both strong and conditional continuation
  - `run_original(..., mode="scored")` accepting either continuation class while still blocking raw preflight failures

- [ ] **Step 1: Add RED tests for conditional baseline writing and scored continuation**

```python
    def test_preflight_only_conditional_writes_baseline_without_summary(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
            opencode_proof = copy.deepcopy(self.base_model_proof)
            opencode_proof["harness"] = "opencode"
            opencode_proof["backing_model_id"] = "unknown"
            opencode_proof["resolved_model_identity"] = None
            opencode_proof["verified"] = False
            opencode_proof["proof_method"] = "missing-model-metadata"
            self.base_model_proof = copy.deepcopy(self.base_model_proof)
            run_dir = self.run_module.run_original(config, "2026-07-22T160000Z", "preflight-only")
            baseline = json.loads((run_dir / "preflight" / "baseline.json").read_text(encoding="utf-8"))
            self.assertEqual(baseline["continuation_class"], "conditional-opencode")
            self.assertEqual(baseline["proof_facts"], {"opencode_runtime_proof": "unavailable"})
            self.assertFalse((run_dir / "summary.json").exists())

    def test_scored_accepts_conditional_baseline(self):
        case_calls: list[tuple[str, str]] = []
        self.install_fake_adapter(case_calls=case_calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
            self.run_module.run_original(config, "2026-07-22T160500Z", "preflight-only")
            self.run_module.run_original(config, "2026-07-22T160500Z", "scored")
            self.assertTrue(case_calls)
            summary = json.loads((self.trusted_results_root / "2026-07-22T160500Z" / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["outcome"], "accepted")
            self.assertEqual(summary["acceptance_class"], "conditional-opencode")
```

- [ ] **Step 2: Run the targeted run-module tests to confirm RED**

Run: `python3 -m unittest tests/harness-acceptance/test_run.py -v`
Expected: FAIL because `run_original()` only writes baseline for aligned preflight and still rejects scored continuation when alignment is not strong.

- [ ] **Step 3: Refactor `build_baseline_record()` to carry continuation class and proof facts**

```python
def build_baseline_record(
    repo_root: Path,
    config: dict[str, Any],
    evaluations: dict[str, dict[str, Any]],
    model_proofs: dict[str, dict[str, Any]],
    continuation_state: dict[str, Any],
) -> dict[str, Any]:
    continuation_class = "strong" if continuation_state["outcome"] == "continuation-ready-strong" else "conditional-opencode"
    record = {
        "schema_version": 1,
        "repo_commit_sha": config["repo_commit_sha"],
        "cases_sha256": lib.sha256_path(repo_root / "tests" / "harness-acceptance" / "cases.json"),
        "scored_prompt_sha256": lib.sha256_path(repo_root / "tests" / "harness-acceptance" / "scored-prompt.txt"),
        "timeout_seconds": int(config["timeout_seconds"]),
        "plugin_source_id": config["plugin_source_id"],
        "residual_categories": list(config["residual_categories"]),
        "continuation_class": continuation_class,
        "proof_facts": dict(continuation_state["proof_facts"]),
        "harnesses": {
            # existing per-harness payload unchanged
        },
    }
```

- [ ] **Step 4: Update `run_original()` preflight-only path to branch on continuation class instead of only raw alignment**

```python
            continuation_state = preflight.determine_preflight_outcome(evaluations["claude"], evaluations["opencode"])
            if continuation_state["outcome"] in {"continuation-ready-strong", "continuation-ready-conditional"}:
                lib.write_json(
                    baseline_path,
                    build_baseline_record(target_root, config_with_run, evaluations, model_proofs, continuation_state),
                )
                return run_dir
            _write_summary_outputs(run_dir, cases)
            return run_dir
```

- [ ] **Step 5: Update the scored gate to respect the baseline continuation class**

```python
        continuation_class = baseline.get("continuation_class")
        if any(result["status"] != "pass" for result in evaluations.values()):
            raise ValueError("scored phase requires passing preflight")
        continuation_state = preflight.determine_preflight_outcome(evaluations["claude"], evaluations["opencode"])
        if continuation_state["outcome"] not in {"continuation-ready-strong", "continuation-ready-conditional"}:
            raise ValueError("scored phase requires continuation-ready preflight")
        expected_baseline = build_baseline_record(
            target_root,
            config_with_run,
            evaluations,
            {harness: lib.load_runtime_model_proof_artifact(run_dir, harness, HARNESS_DIR / "results") for harness in HARNESSES},
            continuation_state,
        )
        if baseline != expected_baseline:
            raise ValueError("baseline fingerprint mismatch")
        if continuation_class not in {"strong", "conditional-opencode"}:
            raise ValueError("unknown continuation class")
```

- [ ] **Step 6: Re-run the targeted runner tests to confirm GREEN**

Run: `python3 -m unittest tests/harness-acceptance/test_run.py -v`
Expected: PASS, including the new conditional-baseline and conditional-scored tests.

- [ ] **Step 7: Commit the runner gate changes**

```bash
git add tests/harness-acceptance/run.py tests/harness-acceptance/test_run.py
git commit -m "fix: allow scored runs from conditional baseline"
```

### Task 3: Summary/result payload and markdown disclosure

**Files:**
- Modify: `tests/harness-acceptance/summarize.py:270-541`
- Test: `tests/harness-acceptance/test_summarize.py`

**Interfaces:**
- Consumes:
  - `preflight.determine_preflight_outcome(...) -> {outcome, reason_code, canonical_identity, proof_facts}`
  - baseline `continuation_class` from `preflight/baseline.json`
- Produces:
  - `build_summary(...) -> dict[str, Any]` with keys:
    ```python
    {
        "outcome": str,
        "reason_code": str | None,
        "acceptance_passed": bool,
        "acceptance_class": str | None,
        "proof_facts": dict[str, str],
        "acceptance_disclosure": list[str],
    }
    ```
  - `render_summary_markdown(summary)` including conditional disclosure when `acceptance_class == "conditional-opencode"`

- [ ] **Step 1: Add RED tests for accepted + acceptance_class + proof_facts semantics**

```python
    def test_build_summary_marks_conditional_acceptance_with_disclosure(self):
        self.set_allowlist({"gpt-5.4": "openai/gpt-5.4"})
        run_dir = self.make_run_dir()
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
        for harness in ("claude", "opencode"):
            for case_id in self.case_ids:
                self.write_attempted_case(run_dir, harness, case_id)
        summary = self.summarize.build_summary(run_dir, self.cases)
        self.assertEqual(summary["outcome"], "accepted")
        self.assertTrue(summary["acceptance_passed"])
        self.assertEqual(summary["acceptance_class"], "conditional-opencode")
        self.assertEqual(summary["proof_facts"], {"opencode_runtime_proof": "unavailable"})
        self.assertIn("OpenCode runtime model identity was not authoritatively proved", summary["acceptance_disclosure"]) 

    def test_build_summary_strong_acceptance_has_strong_class_without_conditional_disclosure(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
        run_dir = self.make_run_dir()
        for harness in ("claude", "opencode"):
            for case_id in self.case_ids:
                self.write_attempted_case(run_dir, harness, case_id)
        summary = self.summarize.build_summary(run_dir, self.cases)
        self.assertEqual(summary["outcome"], "accepted")
        self.assertEqual(summary["acceptance_class"], "strong")
        self.assertEqual(summary["proof_facts"], {})
        self.assertEqual(summary["acceptance_disclosure"], [])
```

- [ ] **Step 2: Run the targeted summary tests to confirm RED**

Run: `python3 -m unittest tests/harness-acceptance/test_summarize.py -v`
Expected: FAIL because `build_summary()` still treats OpenCode proof absence as blocked and has no `acceptance_class`, `proof_facts`, or `acceptance_disclosure` fields.

- [ ] **Step 3: Implement the minimal summary-shape split in `summarize.py`**

```python
    derived = preflight_contract.determine_preflight_outcome(
        states["claude"]["evaluated_preflight"],
        states["opencode"]["evaluated_preflight"],
    )
    proof_facts = dict(derived.get("proof_facts") or {})
    acceptance_class = None
    acceptance_disclosure: list[str] = []
```

```python
    acceptance_passed = (
        all(harness_summaries[h]["preflight"] == "pass" for h in HARNESSES)
        and all(row["status"] == "pass" for row in accounting_rows)
        and contamination_total == 0
        and environment["redaction_passed"]
        and outcome == "accepted"
    )
    if all(row["status"] == "pass" for row in accounting_rows) and environment["redaction_passed"]:
        if derived["outcome"] == "continuation-ready-strong":
            outcome = "accepted"
            acceptance_class = "strong"
        elif derived["outcome"] == "continuation-ready-conditional":
            outcome = "accepted"
            acceptance_class = "conditional-opencode"
            acceptance_disclosure = [
                "Claude runtime model identity was authoritatively proved.",
                "OpenCode capability / preflight and scored routing behavior passed.",
                "OpenCode runtime model identity was not authoritatively proved.",
                "This result is not strong cross-harness same-model acceptance.",
            ]
```

- [ ] **Step 4: Render the conditional disclosure in markdown only for conditional accepted runs**

```python
    if summary.get("acceptance_class") is not None:
        lines.extend(
            [
                "",
                "## Acceptance",
                f"- Outcome: `{summary['outcome']}`",
                f"- Acceptance class: `{summary['acceptance_class']}`",
            ]
        )
        for item in summary.get("acceptance_disclosure", []):
            lines.append(f"- {item}")
```

- [ ] **Step 5: Re-run the targeted summary tests to confirm GREEN**

Run: `python3 -m unittest tests/harness-acceptance/test_summarize.py -v`
Expected: PASS, including the new strong-vs-conditional accepted-shape tests.

- [ ] **Step 6: Commit the summary/result contract changes**

```bash
git add tests/harness-acceptance/summarize.py tests/harness-acceptance/test_summarize.py
git commit -m "fix: report conditional acceptance separately"
```

### Task 4: Documentation alignment for the new contract

**Files:**
- Modify: `docs/handover/researchwork-plugin-handover.md`
- Modify: `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md`
- Modify: `docs/superpowers/specs/2026-07-22-opencode-conditional-acceptance-design.md`

**Interfaces:**
- Consumes:
  - implemented outcome names from `preflight.py`
  - implemented baseline/result field names from `run.py` and `summarize.py`
- Produces:
  - docs that describe the new dual-track contract without contradicting machine-readable artifact names

- [ ] **Step 1: Add a failing doc checklist in the plan branch notes before editing prose**

```text
Verify all three docs answer these questions with the implemented names:
- What are the Task 6 continuation states?
- When does OpenCode conditional acceptance apply?
- Does conditional acceptance count as acceptance_passed?
- Why does Claude allowlist gap still block/route to allowlist-update-needed?
```

- [ ] **Step 2: Update handover status language to stop saying Task 7 requires only a single continuation-ready state**

```markdown
- Task 7: may begin from either `continuation-ready-strong` or `continuation-ready-conditional`; only the strong path supports verified cross-harness same-model acceptance.
- OpenCode conditional acceptance is a weaker accepted class that still requires Claude canonicalized authoritative proof.
```

- [ ] **Step 3: Update the older Task 6 spec so it no longer contradicts the new dual-track contract**

```markdown
Add a short contract-revision note near the continuation-ready sections stating that the original single continuation-ready concept has been split into strong vs conditional continuation in the later 2026-07-22 design.
```

- [ ] **Step 4: Update the new conditional-acceptance spec only if field names drifted during implementation**

```markdown
Normalize the spec text to the actual implemented field names:
- `acceptance_class`
- `proof_facts`
- `continuation-ready-strong`
- `continuation-ready-conditional`
- `accepted`
```

- [ ] **Step 5: Run focused validation to ensure docs and code agree**

Run: `python3 -m unittest tests/harness-acceptance/test_preflight.py tests/harness-acceptance/test_run.py tests/harness-acceptance/test_summarize.py -v`
Expected: PASS, with docs updated to use the same contract names that now pass in tests.

- [ ] **Step 6: Commit the docs alignment**

```bash
git add docs/handover/researchwork-plugin-handover.md docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md docs/superpowers/specs/2026-07-22-opencode-conditional-acceptance-design.md
git commit -m "docs: align task 6 and 7 acceptance contract"
```

## Self-review

### Spec coverage

- Task 1 covers Task 6 outcome split, `proof_facts`, and Claude allowlist-gap precedence.
- Task 2 covers `run.py` first-slice requirement: baseline writing and scored continuation from conditional preflight.
- Task 3 covers final accepted outcome shape, `acceptance_class`, `acceptance_passed`, and the fixed conditional disclosure.
- Task 4 covers the required handover/spec alignment.
- No spec requirement in the approved first slice is left without a task.

### Placeholder scan

- No `TODO`/`TBD` placeholders remain.
- Every code step includes concrete code blocks.
- Every validation step includes an exact command and expected outcome.

### Type consistency

- Task 1 defines `proof_facts` and the two continuation-ready names.
- Task 2 reuses those exact names in `baseline.json` and scored gating.
- Task 3 reuses `proof_facts` and maps accepted terminal state to `acceptance_class = strong | conditional-opencode`.
- Task 4 only documents names already established in Tasks 1–3.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-22-opencode-conditional-acceptance.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
