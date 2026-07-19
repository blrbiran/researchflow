# Task 5 Synthetic Preflight / Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the minimum Task 5 code needed to evaluate synthetic preflight gates, block or allow scored continuation correctly, and orchestrate runs without ever launching real harness/model/network work from the repository test baseline.

**Architecture:** Keep Task 5 narrow. `preflight.py` owns single-harness preflight and cross-harness model-alignment judgment, while `run.py` owns run lifecycle, baseline fingerprinting, blocked-summary generation, and scored gating. Reuse the existing Task 4 adapters plus the existing `judge.py` and `summarize.py` contracts instead of introducing a new orchestration layer.

**Tech Stack:** Python 3 standard library, Bash, JSON, existing `unittest` suite, existing Task 4 adapters, existing `judge.py` and `summarize.py`

## Global Constraints

- Task 4 is synthetically review-closed on `main`.
- Router behavior and workflow contracts are already settled.
- No real Claude Code, OpenCode, LiteLLM, network, or paid-model run is authorized in Task 5.
- add `tests/harness-acceptance/preflight.py`;
- add `tests/harness-acceptance/run.py` and `run.sh`;
- add `tests/harness-acceptance/run-config.example.json`;
- add `test_preflight.py`, `test_run.py`, and `tests/harness-acceptance/run-tests.sh`;
- wire Task 5 synthetic tests into `tests/run-all.sh`;
- reuse Task 4 capability and adapter outputs as the upstream proof inputs.
- changing `skills/using-researchflow/SKILL.md` is out of scope.
- changing `docs/workflow-contracts.md` is out of scope.
- reopening Task 4 unless a concrete regression appears is out of scope.
- introducing real harness runs is out of scope.
- redesigning the Task 4 adapter boundary is out of scope.
- adding abstractions aimed mainly at Task 6 or Task 7 is out of scope.
- version bumps, release work, publish, or push are out of scope.
- Prefer minimum change over elegance.
- `preflight-only` must not invoke a scored case under any circumstance.
- Blocked runs must produce complete 14-row accounting.
- Aligned `preflight-only` runs must write capability/preflight/model-proof artifacts plus stored baseline metadata, but not final `summary.json`, final `summary.md`, or 14 `unattempted` rows.
- The stored scored-continuation baseline must include selected profile IDs, proof hashes, canonical model identities, non-secret config fields, `repo_commit_sha`, the hash of `tests/harness-acceptance/cases.json`, and the hash of `tests/harness-acceptance/scored-prompt.txt`.
- `tests/harness-acceptance/run-tests.sh` and `tests/run-all.sh` must remain synthetic-only commands.
- The checked-in `tests/harness-acceptance/run-config.example.json` must stay minimal: route values, effort/variant, and timeout only. `repo_root`, `repo_commit_sha`, and `endpoint_identity` are derived or injected outside the checked-in example.

---

## File Structure

- `tests/harness-acceptance/preflight.py` — evaluates one harness preflight result plus cross-harness model alignment without invoking cases.
- `tests/harness-acceptance/test_preflight.py` — synthetic tests for blocked/pass preflight outcomes, allowlist behavior, and model-alignment reason selection.
- `tests/harness-acceptance/run.py` — creates run directories, writes environment/baseline metadata, invokes adapters in fixed order, blocks scored continuation when required, judges scored cases, and writes blocked/final summaries.
- `tests/harness-acceptance/test_run.py` — state-machine tests for `preflight-only`, blocked summaries, aligned baseline persistence, scored gating, fixed case order, and no-overwrite behavior.
- `tests/harness-acceptance/run.sh` — thin shell wrapper for `run.py`.
- `tests/harness-acceptance/run-config.example.json` — non-secret sample config for operators.
- `tests/harness-acceptance/run-tests.sh` — unittest discovery entrypoint for the harness-acceptance synthetic suite.
- `tests/run-all.sh` — repository-wide synthetic baseline; append Task 5 synthetic acceptance tests here.
- `tests/harness-acceptance/lib.py` — existing shared JSON/hash/schema helpers used by Task 5.
- `tests/harness-acceptance/judge.py` — existing deterministic verdict generator used by `run.py` after each scored case.
- `tests/harness-acceptance/summarize.py` — existing deterministic summary builder used by `run.py` for blocked and scored-final summaries.
- `tests/harness-acceptance/fixtures/summary/*.json` — existing reusable base fixtures for preflight/model/environment artifacts.
- `tests/harness-acceptance/results/<run-id>/environment.json` — run metadata written by `run.py` for both blocked and later-scored runs.
- `tests/harness-acceptance/results/<run-id>/preflight/baseline.json` — stored scored-continuation baseline metadata written only for aligned `preflight-only` runs.

### Task 1: Add synthetic preflight and model-alignment evaluation

**Files:**
- Create: `tests/harness-acceptance/preflight.py`
- Create: `tests/harness-acceptance/test_preflight.py`

**Interfaces:**
- Consumes: `lib.read_json(path: Path) -> dict`
- Consumes: `lib.REASON_CODES`
- Produces: `evaluate_preflight(capability: dict[str, Any], preflight: dict[str, Any], model_proof: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]`
- Produces: `evaluate_model_alignment(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]`
- Produces: `load_identities(harness_dir: Path) -> dict[str, Any]`

- [ ] **Step 1: Write the failing preflight tests**

Create `tests/harness-acceptance/test_preflight.py` with this structure and these tests:

```python
#!/usr/bin/env python3
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
SUMMARY_FIXTURE_DIR = HARNESS_DIR / "fixtures" / "summary"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preflight = load_module("harness_acceptance_preflight", HARNESS_DIR / "preflight.py")
        cls.capability = {
            "claude": read_json(SUMMARY_FIXTURE_DIR / "base-capability-claude.json"),
            "opencode": read_json(SUMMARY_FIXTURE_DIR / "base-capability-opencode.json"),
        }
        cls.base_preflight = {
            "claude": read_json(SUMMARY_FIXTURE_DIR / "base-preflight-claude.json"),
            "opencode": read_json(SUMMARY_FIXTURE_DIR / "base-preflight-opencode.json"),
        }
        cls.base_model_proof = read_json(SUMMARY_FIXTURE_DIR / "base-model-proof.json")
        cls.identities = {
            "allowed_provider": "openai",
            "canonical_models": {"synthetic-model": "openai/synthetic-model"},
            "harness_aliases": {"fable": {"does_not_prove_backing_model": True, "may_route_via": "litellm"}},
        }

    def test_evaluate_preflight_blocks_when_profile_or_plugin_proof_is_missing(self):
        capability = copy.deepcopy(self.capability["claude"])
        preflight = copy.deepcopy(self.base_preflight["claude"])
        model_proof = copy.deepcopy(self.base_model_proof)
        capability["selected_isolation_profile"] = None
        preflight["status"] = "blocked"
        result = self.preflight.evaluate_preflight(capability, preflight, model_proof, self.identities)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["canonical_identity"])
        self.assertEqual(result["plugin_source_id"], "researchflow-checkout")

    def test_evaluate_preflight_accepts_verified_allowlisted_model(self):
        capability = copy.deepcopy(self.capability["claude"])
        preflight = copy.deepcopy(self.base_preflight["claude"])
        model_proof = copy.deepcopy(self.base_model_proof)
        result = self.preflight.evaluate_preflight(capability, preflight, model_proof, self.identities)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["canonical_identity"], "openai/synthetic-model")
        self.assertFalse(result["allowlist_missing"])

    def test_evaluate_model_alignment_distinguishes_allowlist_gap_from_true_mismatch(self):
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
        allowlist_gap = self.preflight.evaluate_model_alignment(claude, opencode)
        self.assertFalse(allowlist_gap["aligned"])
        self.assertEqual(allowlist_gap["reason_code"], "global_hard_gate_blocked")

        mismatched = copy.deepcopy(opencode)
        mismatched["proof_identity"] = "openai/other-synthetic-model"
        mismatch = self.preflight.evaluate_model_alignment(claude, mismatched)
        self.assertFalse(mismatch["aligned"])
        self.assertEqual(mismatch["reason_code"], "model_alignment_blocked")
```

- [ ] **Step 2: Run the preflight test file to verify RED**

Run:

```bash
python3 -m unittest tests/harness-acceptance/test_preflight.py -v
```

Expected: FAIL with `FileNotFoundError`, `ImportError`, or missing `evaluate_preflight` / `evaluate_model_alignment` symbols because `preflight.py` does not exist yet.

- [ ] **Step 3: Implement the minimal evaluator in `preflight.py`**

Create `tests/harness-acceptance/preflight.py` with these functions and no orchestration logic:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_identities(harness_dir: Path) -> dict[str, Any]:
    value = json.loads((harness_dir / "model-identities.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("model-identities.json must be an object")
    return value


def _inspect_model_proof(value: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "proof_valid": False,
            "canonical_identity": None,
            "proof_identity": None,
            "backing_model_id": None,
            "allowlist_missing": False,
        }
    canonical_models = identities.get("canonical_models")
    if not isinstance(canonical_models, dict):
        canonical_models = {}
    resolved = value.get("resolved_model_identity")
    backing_model_id = value.get("backing_model_id")
    proof_valid = (
        value.get("schema_version") == 1
        and value.get("proxy_kind") == "litellm"
        and value.get("upstream_provider") == identities.get("allowed_provider")
        and value.get("verified") is True
        and value.get("redaction_passed") is True
        and isinstance(resolved, str)
        and resolved.startswith("openai/")
        and isinstance(backing_model_id, str)
        and bool(backing_model_id)
    )
    canonical_identity = canonical_models.get(backing_model_id) if proof_valid else None
    allowlist_missing = proof_valid and not isinstance(canonical_identity, str)
    if canonical_identity != resolved:
        canonical_identity = None
    return {
        "proof_valid": proof_valid,
        "canonical_identity": canonical_identity,
        "proof_identity": resolved if isinstance(resolved, str) else None,
        "backing_model_id": backing_model_id if isinstance(backing_model_id, str) else None,
        "allowlist_missing": allowlist_missing,
    }


def evaluate_preflight(capability: dict[str, Any], preflight: dict[str, Any], model_proof: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]:
    inspected = _inspect_model_proof(model_proof, identities)
    isolation_profile = preflight.get("isolation_profile") or capability.get("selected_isolation_profile")
    plugin_proof_strength = preflight.get("plugin_proof_strength") or capability.get("plugin_proof_strength")
    plugin_source_id = preflight.get("plugin_source_id")
    passed = (
        preflight.get("status") == "pass"
        and isinstance(isolation_profile, str)
        and bool(isolation_profile)
        and isinstance(plugin_proof_strength, str)
        and bool(plugin_proof_strength)
        and isinstance(plugin_source_id, str)
        and bool(plugin_source_id)
        and inspected["proof_valid"]
    )
    return {
        "status": "pass" if passed and isinstance(inspected["canonical_identity"], str) else "blocked",
        "plugin_source_id": plugin_source_id,
        "plugin_proof_strength": plugin_proof_strength,
        "isolation_profile": isolation_profile,
        "canonical_identity": inspected["canonical_identity"],
        "proof_identity": inspected["proof_identity"],
        "proof_valid": inspected["proof_valid"],
        "allowlist_missing": inspected["allowlist_missing"],
        "backing_model_id": inspected["backing_model_id"],
    }


def evaluate_model_alignment(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]:
    if claude_result.get("status") != "pass" or opencode_result.get("status") != "pass":
        return {"aligned": False, "canonical_identity": None, "reason_code": "global_hard_gate_blocked"}
    claude_identity = claude_result.get("canonical_identity")
    opencode_identity = opencode_result.get("canonical_identity")
    if isinstance(claude_identity, str) and claude_identity == opencode_identity:
        return {"aligned": True, "canonical_identity": claude_identity, "reason_code": None}
    proofs_same_openai = (
        claude_result.get("proof_valid")
        and opencode_result.get("proof_valid")
        and isinstance(claude_result.get("proof_identity"), str)
        and claude_result.get("proof_identity") == opencode_result.get("proof_identity")
    )
    if proofs_same_openai and (claude_result.get("allowlist_missing") or opencode_result.get("allowlist_missing")):
        return {"aligned": False, "canonical_identity": None, "reason_code": "global_hard_gate_blocked"}
    return {"aligned": False, "canonical_identity": None, "reason_code": "model_alignment_blocked"}
```

Do not add run-directory code, adapter invocation, or summary writing here.

- [ ] **Step 4: Re-run the preflight tests to verify GREEN**

Run:

```bash
python3 -m unittest tests/harness-acceptance/test_preflight.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add tests/harness-acceptance/preflight.py tests/harness-acceptance/test_preflight.py
git commit -m "test: add synthetic preflight gate evaluator"
```

### Task 2: Add run lifecycle, blocked summaries, baseline persistence, and scored gating

**Files:**
- Create: `tests/harness-acceptance/run.py`
- Create: `tests/harness-acceptance/test_run.py`

**Interfaces:**
- Consumes: `preflight.evaluate_preflight(capability, preflight, model_proof, identities) -> dict[str, Any]`
- Consumes: `preflight.evaluate_model_alignment(claude_result, opencode_result) -> dict[str, Any]`
- Consumes: `judge.judge(case: dict, invocation: dict, response: str) -> dict[str, Any]`
- Consumes: `summarize.build_summary(run_dir: Path, cases: list[dict]) -> dict[str, Any]`
- Consumes: `summarize.render_summary_markdown(summary: dict[str, Any]) -> str`
- Consumes: `lib.load_cases(root: Path) -> list[dict[str, Any]]`
- Consumes: `lib.write_json(path: Path, value: dict[str, Any], overwrite: bool = False) -> None`
- Produces: `build_environment_record(run_id: str) -> dict[str, Any]`
- Produces: `build_baseline_record(repo_root: Path, config: dict[str, Any], evaluations: dict[str, dict[str, Any]], model_proofs: dict[str, dict[str, Any]]) -> dict[str, Any]`
- Produces: `run_original(config: dict[str, Any], run_id: str, mode: str) -> Path`
- Produces: `_run_adapter(harness: str, mode: str, config_path: Path, output_dir: Path, case_id: str | None = None) -> None`

- [ ] **Step 1: Write the failing run-state tests**

Create `tests/harness-acceptance/test_run.py` with these helpers and tests:

```python
#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
SUMMARY_FIXTURE_DIR = HARNESS_DIR / "fixtures" / "summary"
JUDGE_FIXTURE_DIR = HARNESS_DIR / "fixtures" / "judge"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class RunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run = load_module("harness_acceptance_run", HARNESS_DIR / "run.py")
        cls.lib = load_module("harness_acceptance_lib", HARNESS_DIR / "lib.py")
        cls.case_ids = [case["case_id"] for case in cls.lib.load_cases(ROOT)]
        cls.base_capability = {
            "claude": json.loads((SUMMARY_FIXTURE_DIR / "base-capability-claude.json").read_text(encoding="utf-8")),
            "opencode": json.loads((SUMMARY_FIXTURE_DIR / "base-capability-opencode.json").read_text(encoding="utf-8")),
        }
        cls.base_preflight = {
            "claude": json.loads((SUMMARY_FIXTURE_DIR / "base-preflight-claude.json").read_text(encoding="utf-8")),
            "opencode": json.loads((SUMMARY_FIXTURE_DIR / "base-preflight-opencode.json").read_text(encoding="utf-8")),
        }
        cls.base_model_proof = json.loads((SUMMARY_FIXTURE_DIR / "base-model-proof.json").read_text(encoding="utf-8"))
        cls.base_invocation = json.loads((JUDGE_FIXTURE_DIR / "base-invocation.json").read_text(encoding="utf-8"))

    def make_config(self) -> dict:
        return {
            "repo_root": str(ROOT),
            "repo_commit_sha": "c" * 40,
            "endpoint_identity": "https://proxy.example.com/v1?token=secret",
            "timeout_seconds": 120,
            "plugin_source_id": "researchflow-checkout",
            "residual_categories": ["auth", "admin-policy"],
            "claude": {"cli_bin": "/bin/true", "harness_model_value": "fable", "effort_or_variant": "high"},
            "opencode": {"cli_bin": "/bin/true", "harness_model_value": "openai/synthetic-model", "effort_or_variant": "high"},
        }

    def write_case_artifacts(self, case_dir: Path, harness: str, case_id: str, observed_phase: str):
        invocation = copy.deepcopy(self.base_invocation)
        invocation["harness"] = harness
        invocation["case_id"] = case_id
        response_text = f"ResearchFlow phase: {observed_phase}\n"
        response_sha = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        invocation["final_response_sha256"] = response_sha
        (case_dir / "final-response.txt").write_text(response_text, encoding="utf-8")
        write_json(case_dir / "invocation.json", invocation)
        write_json(case_dir / "command.json", {
            "schema_version": 1,
            "harness": harness,
            "cli_version": invocation["cli_version"],
            "model_request": invocation["model_request"],
            "resolved_model_identity": invocation["resolved_model_identity"],
            "effort_or_variant": invocation["effort_or_variant"],
            "timeout_seconds": invocation["timeout_seconds"],
            "repo_commit_sha": invocation["repo_commit_sha"],
            "plugin_source_id": invocation["plugin_source_id"],
            "plugin_proof_strength": invocation["plugin_proof_strength"],
            "isolation_profile": invocation["isolation_profile"],
            "residual_categories": invocation["residual_categories"],
            "started_at_utc": invocation["started_at_utc"],
            "finished_at_utc": invocation["finished_at_utc"],
            "exit_code": 0,
            "tool_execution": invocation["tool_execution"],
            "raw_artifact_hashes": invocation["raw_artifact_hashes"],
        })

    def install_fake_adapter(self, blocked_harness: str | None = None, case_calls: list[tuple[str, str]] | None = None):
        original = self.run._run_adapter

        def fake_run_adapter(harness: str, mode: str, config_path: Path, output_dir: Path, case_id: str | None = None):
            output_dir.mkdir(parents=True, exist_ok=True)
            if mode == "capability":
                write_json(output_dir / f"{harness}.json", copy.deepcopy(self.base_capability[harness]))
                return
            if mode == "preflight":
                preflight = copy.deepcopy(self.base_preflight[harness])
                if harness == blocked_harness:
                    preflight["status"] = "blocked"
                proof = copy.deepcopy(self.base_model_proof)
                proof["harness"] = harness
                proof["requested_route"] = "fable" if harness == "claude" else "openai/synthetic-model"
                write_json(output_dir / f"{harness}.json", preflight)
                write_json(output_dir / f"{harness}-model-proof.json", proof)
                return
            if mode == "case":
                assert case_id is not None
                if case_calls is not None:
                    case_calls.append((harness, case_id))
                observed_phase = next(case["expected_phase"] for case in self.lib.load_cases(ROOT) if case["case_id"] == case_id)
                self.write_case_artifacts(output_dir, harness, case_id, observed_phase)
                return
            raise AssertionError(f"unexpected mode: {mode}")

        self.run._run_adapter = fake_run_adapter
        self.addCleanup(setattr, self.run, "_run_adapter", original)

    def test_preflight_only_blocked_writes_summary_and_never_runs_cases(self):
        case_calls: list[tuple[str, str]] = []
        self.install_fake_adapter(blocked_harness="claude", case_calls=case_calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run.run_original(config, "2026-07-18T120000Z", "preflight-only")
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(case_calls, [])
            self.assertEqual(len(summary["accounting_rows"]), 14)
            self.assertFalse((run_dir / "preflight" / "baseline.json").exists())

    def test_preflight_only_aligned_writes_baseline_without_final_summary(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run.run_original(config, "2026-07-18T121500Z", "preflight-only")
            self.assertTrue((run_dir / "preflight" / "baseline.json").exists())
            self.assertFalse((run_dir / "summary.json").exists())
            self.assertFalse((run_dir / "summary.md").exists())

    def test_scored_requires_aligned_baseline_and_runs_cases_in_fixed_order(self):
        case_calls: list[tuple[str, str]] = []
        self.install_fake_adapter(case_calls=case_calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run.run_original(config, "2026-07-18T123000Z", "preflight-only")
            rerun_dir = self.run.run_original(config, "2026-07-18T123000Z", "scored")
            self.assertEqual(run_dir, rerun_dir)
            expected = [("claude", case_id) for case_id in self.case_ids] + [("opencode", case_id) for case_id in self.case_ids]
            self.assertEqual(case_calls, expected)
            self.assertTrue((run_dir / "summary.json").exists())

    def test_scored_rejects_changed_baseline_or_existing_case_artifacts(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run.run_original(config, "2026-07-18T124500Z", "preflight-only")
            changed = copy.deepcopy(config)
            changed["timeout_seconds"] = 300
            with self.assertRaisesRegex(ValueError, "baseline"):
                self.run.run_original(changed, "2026-07-18T124500Z", "scored")
            case_dir = run_dir / "claude" / self.case_ids[0]
            case_dir.mkdir(parents=True, exist_ok=True)
            with self.assertRaisesRegex(ValueError, "existing case artifact"):
                self.run.run_original(config, "2026-07-18T124500Z", "scored")
```

- [ ] **Step 2: Run the run-state test file to verify RED**

Run:

```bash
python3 -m unittest tests/harness-acceptance/test_run.py -v
```

Expected: FAIL because `run.py` does not exist yet.

- [ ] **Step 3: Implement `run.py` with a monotonic lifecycle and baseline fingerprinting**

Create `tests/harness-acceptance/run.py` with these pieces:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import judge
import lib
import preflight
import summarize

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
HARNESSES = ("claude", "opencode")


def _repo_commit_sha() -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_environment_record(run_id: str) -> dict[str, Any]:
    raw_relative_id = f"local-raw/{run_id}"
    raw_sha256 = hashlib.sha256(raw_relative_id.encode("utf-8")).hexdigest()
    return {
        "run_id": run_id,
        "run_kind": "original",
        "redaction_passed": True,
        "raw_artifacts": {
            "relative_id": raw_relative_id,
            "sha256": raw_sha256,
            "manual_review_status": "pending",
            "reason_not_committed": "raw event streams remain local",
        },
        "manual_notes": [],
        "deviations": [],
    }


def build_baseline_record(repo_root: Path, config: dict[str, Any], evaluations: dict[str, dict[str, Any]], model_proofs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    record = {
        "schema_version": 1,
        "repo_commit_sha": config["repo_commit_sha"],
        "cases_sha256": lib.sha256_path(HARNESS_DIR / "cases.json"),
        "scored_prompt_sha256": lib.sha256_path(HARNESS_DIR / "scored-prompt.txt"),
        "timeout_seconds": int(config["timeout_seconds"]),
        "harnesses": {
            harness: {
                "harness_model_value": config[harness]["harness_model_value"],
                "effort_or_variant": config[harness]["effort_or_variant"],
                "plugin_source_id": evaluations[harness]["plugin_source_id"],
                "plugin_proof_strength": evaluations[harness]["plugin_proof_strength"],
                "selected_isolation_profile": evaluations[harness]["isolation_profile"],
                "canonical_identity": evaluations[harness]["canonical_identity"],
                "proof_sha256": model_proofs[harness]["proof_sha256"],
                "endpoint_identity_sha256": model_proofs[harness]["endpoint_identity_sha256"],
            }
            for harness in HARNESSES
        },
    }
    fingerprint_input = json.dumps(record, sort_keys=True).encode("utf-8")
    record["fingerprint_sha256"] = hashlib.sha256(fingerprint_input).hexdigest()
    return record


def _run_adapter(harness: str, mode: str, config_path: Path, output_dir: Path, case_id: str | None = None) -> None:
    adapter = HARNESS_DIR / "adapters" / f"{harness}.sh"
    command = ["bash", str(adapter), "--mode", mode, "--config", str(config_path), "--output-dir", str(output_dir)]
    if case_id is not None:
        command.extend(["--case-id", case_id])
    subprocess.run(command, check=True)


def _write_summary_outputs(run_dir: Path, cases: list[dict[str, Any]]) -> None:
    summary = summarize.build_summary(run_dir, cases)
    lib.write_json(run_dir / "summary.json", summary)
    (run_dir / "summary.md").write_text(summarize.render_summary_markdown(summary), encoding="utf-8")


def _write_verdict(case: dict[str, Any], case_dir: Path) -> None:
    invocation = lib.read_json(case_dir / "invocation.json")
    response = (case_dir / "final-response.txt").read_text(encoding="utf-8")
    verdict = judge.judge(case, invocation, response)
    lib.write_json(case_dir / "verdict.json", verdict)


def run_original(config: dict[str, Any], run_id: str, mode: str) -> Path:
    if mode not in {"preflight-only", "scored"}:
        raise ValueError(f"unsupported mode: {mode}")
    results_root = Path(config.get("results_root", HARNESS_DIR / "results"))
    run_dir = results_root / run_id
    preflight_dir = run_dir / "preflight"
    capabilities_dir = run_dir / "capabilities"
    baseline_path = preflight_dir / "baseline.json"
    cases = lib.load_cases(ROOT)
    identities = preflight.load_identities(HARNESS_DIR)

    if mode == "preflight-only":
        if run_dir.exists():
            raise FileExistsError(run_dir)
        lib.write_json(run_dir / "environment.json", build_environment_record(run_id))
    elif not run_dir.exists():
        raise FileNotFoundError(run_dir)

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "run-config.json"
        config_with_run = dict(config)
        config_with_run.setdefault("repo_root", str(ROOT))
        config_with_run.setdefault("repo_commit_sha", _repo_commit_sha())
        config_with_run.setdefault("endpoint_identity", "https://redacted.invalid/v1")
        config_with_run["run_id"] = run_id
        config_path.write_text(json.dumps(config_with_run, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if mode == "preflight-only":
            evaluations: dict[str, dict[str, Any]] = {}
            model_proofs: dict[str, dict[str, Any]] = {}
            for harness in HARNESSES:
                _run_adapter(harness, "capability", config_path, capabilities_dir)
                _run_adapter(harness, "preflight", config_path, preflight_dir)
                capability = lib.read_json(capabilities_dir / f"{harness}.json")
                preflight_record = lib.read_json(preflight_dir / f"{harness}.json")
                model_proof = lib.read_json(preflight_dir / f"{harness}-model-proof.json")
                evaluations[harness] = preflight.evaluate_preflight(capability, preflight_record, model_proof, identities)
                model_proofs[harness] = model_proof
            alignment = preflight.evaluate_model_alignment(evaluations["claude"], evaluations["opencode"])
            if alignment["aligned"]:
                lib.write_json(baseline_path, build_baseline_record(ROOT, config_with_run, evaluations, model_proofs))
                return run_dir
            _write_summary_outputs(run_dir, cases)
            return run_dir

        baseline = lib.read_json(baseline_path)
        expected_baseline = build_baseline_record(
            ROOT,
            config_with_run,
            {
                harness: preflight.evaluate_preflight(
                    lib.read_json(capabilities_dir / f"{harness}.json"),
                    lib.read_json(preflight_dir / f"{harness}.json"),
                    lib.read_json(preflight_dir / f"{harness}-model-proof.json"),
                    identities,
                )
                for harness in HARNESSES
            },
            {harness: lib.read_json(preflight_dir / f"{harness}-model-proof.json") for harness in HARNESSES},
        )
        if baseline != expected_baseline:
            raise ValueError("baseline fingerprint mismatch")
        if (run_dir / "summary.json").exists():
            raise ValueError("scored phase already completed")
        for harness in HARNESSES:
            harness_dir = run_dir / harness
            if harness_dir.exists() and any(path.is_dir() for path in harness_dir.iterdir()):
                raise ValueError("existing case artifact prevents scored continuation")
            for case in cases:
                case_dir = harness_dir / case["case_id"]
                _run_adapter(harness, "case", config_path, case_dir, case["case_id"])
                _write_verdict(case, case_dir)
        _write_summary_outputs(run_dir, cases)
        return run_dir
```

Keep the implementation thin. Do not add retry loops, alternative orchestration paths, or real-run conveniences.

- [ ] **Step 4: Re-run the run-state test file to verify GREEN**

Run:

```bash
python3 -m unittest tests/harness-acceptance/test_run.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add tests/harness-acceptance/run.py tests/harness-acceptance/test_run.py
git commit -m "test: gate synthetic harness run lifecycle"
```

### Task 3: Add CLI entrypoints, operator config example, and synthetic-suite wiring

**Files:**
- Modify: `tests/harness-acceptance/run.py`
- Create: `tests/harness-acceptance/run.sh`
- Create: `tests/harness-acceptance/run-config.example.json`
- Create: `tests/harness-acceptance/run-tests.sh`
- Modify: `tests/harness-acceptance/test_run.py`
- Modify: `tests/run-all.sh`

**Interfaces:**
- Consumes: `run_original(config: dict[str, Any], run_id: str, mode: str) -> Path`
- Produces: `load_run_config(path: Path) -> dict[str, Any]`
- Produces: `main(argv: list[str] | None = None) -> int`
- Produces CLI: `./tests/harness-acceptance/run.sh --mode preflight-only|scored --config PATH --run-id YYYY-MM-DDTHHMMSSZ`

- [ ] **Step 1: Add a failing CLI/parser smoke test**

Extend `tests/harness-acceptance/test_run.py` with this test:

```python
def test_main_parses_cli_arguments_and_invokes_run_original(self):
    calls = {}
    original = self.run.run_original

    def fake_run_original(config, run_id, mode):
        calls["config"] = config
        calls["run_id"] = run_id
        calls["mode"] = mode
        return Path("/tmp/synthetic-run")

    self.run.run_original = fake_run_original
    self.addCleanup(setattr, self.run, "run_original", original)

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "run-config.json"
        config_path.write_text(json.dumps(self.make_config(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        exit_code = self.run.main([
            "--mode",
            "preflight-only",
            "--config",
            str(config_path),
            "--run-id",
            "2026-07-18T130000Z",
        ])
    self.assertEqual(exit_code, 0)
    self.assertEqual(calls["mode"], "preflight-only")
    self.assertEqual(calls["run_id"], "2026-07-18T130000Z")
    self.assertEqual(calls["config"]["timeout_seconds"], 120)
```

- [ ] **Step 2: Run the run tests again to verify RED on the missing CLI entrypoint**

Run:

```bash
python3 -m unittest tests/harness-acceptance/test_run.py -v
```

Expected: FAIL because `main()` and/or `load_run_config()` do not exist yet.

- [ ] **Step 3: Add the CLI entrypoint, shell wrapper, sample config, and synthetic runner wiring**

Append these functions to `tests/harness-acceptance/run.py`:

```python
def load_run_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("config must be an object")
    for key in ("claude", "opencode", "timeout_seconds"):
        if key not in value:
            raise ValueError(f"missing config key: {key}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("preflight-only", "scored"))
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    config = load_run_config(Path(args.config))
    config.setdefault("repo_root", str(ROOT))
    config.setdefault("repo_commit_sha", _repo_commit_sha())
    config.setdefault("endpoint_identity", "https://redacted.invalid/v1")
    run_original(config, args.run_id, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `tests/harness-acceptance/run.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
python3 "$ROOT/run.py" "$@"
```

Create `tests/harness-acceptance/run-config.example.json` with the approved minimal non-secret shape. Do not include `repo_root`, `repo_commit_sha`, or `endpoint_identity` in the checked-in example:

```json
{
  "claude": {
    "harness_model_value": "fable",
    "effort_or_variant": "high"
  },
  "opencode": {
    "harness_model_value": "openai/proxy-route",
    "effort_or_variant": "high"
  },
  "timeout_seconds": 120
}
```

Create `tests/harness-acceptance/run-tests.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
python3 -m unittest discover -s "$ROOT/tests/harness-acceptance" -p 'test_*.py' -v
```

Modify `tests/run-all.sh` to prepend the harness-acceptance synthetic suite:

```bash
printf '==> Running harness acceptance synthetic tests\n'
"$ROOT/tests/harness-acceptance/run-tests.sh"

printf '\n==> Running OpenCode smoke test\n'
"$ROOT/tests/opencode/run-tests.sh"
```

Do not add any command here that launches a real harness acceptance run.

- [ ] **Step 4: Run the targeted and full synthetic suites**

Run:

```bash
python3 -m unittest tests/harness-acceptance/test_run.py -v
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
```

Expected:
- `test_run.py` PASS
- `run-tests.sh` PASS across the full harness-acceptance synthetic suite
- `tests/run-all.sh` PASS and still end with `All ResearchFlow tests passed.`

- [ ] **Step 5: Commit Task 3**

```bash
git add tests/harness-acceptance/run.py \
        tests/harness-acceptance/run.sh \
        tests/harness-acceptance/run-config.example.json \
        tests/harness-acceptance/run-tests.sh \
        tests/harness-acceptance/test_run.py \
        tests/run-all.sh
git commit -m "test: wire Task 5 synthetic acceptance runner"
```

## Self-Review

### Spec coverage

- `preflight.py` owns preflight and alignment judgment in Task 1.
- `run.py` owns monotonic lifecycle, blocked summary behavior, aligned baseline persistence, and scored gating in Task 2.
- The scored-continuation baseline explicitly includes `repo_commit_sha`, `cases.json` hash, and `scored-prompt.txt` hash in Task 2.
- Blocked runs produce full 14-row accounting through `summarize.build_summary()` in Task 2.
- Aligned `preflight-only` runs skip final summary and 14-row accounting in Task 2.
- Shell/config/test-runner wiring stays synthetic-only in Task 3.
- No task modifies router behavior, workflow contracts, or introduces real harness runs.

### Placeholder scan

- No `TODO`, `TBD`, or deferred implementation placeholders remain.
- Every code-writing step includes concrete code.
- Every verification step includes an exact command and expected outcome.

### Type consistency

- `evaluate_preflight()` and `evaluate_model_alignment()` are defined in Task 1 and consumed by `run.py` in Task 2.
- `run_original(config, run_id, mode)` is defined in Task 2 and consumed by `main()` in Task 3.
- The baseline record fields named in the spec (`repo_commit_sha`, `cases_sha256`, `scored_prompt_sha256`) are the same names used in Task 2.
- `run.sh` shells into `run.py` and does not add alternate argument names.

Plan complete and saved to `docs/superpowers/plans/2026-07-18-task5-synthetic-preflight-orchestration.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**