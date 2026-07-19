#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
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


class SummarizeTest(unittest.TestCase):
    def set_allowlist(self, canonical_models: dict[str, str]):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        harness_dir = Path(temp_dir.name)
        allowlist = {
            "allowed_provider": "openai",
            "canonical_models": canonical_models,
            "harness_aliases": {
                "fable": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
                "haiku": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
                "opus": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
                "sonnet": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
            },
        }
        write_json(harness_dir / "model-identities.json", allowlist)
        original = self.summarize.HARNESS_DIR
        self.summarize.HARNESS_DIR = harness_dir
        self.addCleanup(setattr, self.summarize, "HARNESS_DIR", original)

    @classmethod
    def setUpClass(cls):
        cls.lib = load_module("harness_acceptance_lib", HARNESS_DIR / "lib.py")
        cls.summarize = load_module("harness_acceptance_summarize", HARNESS_DIR / "summarize.py")
        cls.cases = cls.lib.load_cases(ROOT)
        cls.case_ids = [case["case_id"] for case in cls.cases]
        cls.base_environment = json.loads((SUMMARY_FIXTURE_DIR / "base-environment.json").read_text(encoding="utf-8"))
        cls.base_capabilities = {
            "claude": json.loads((SUMMARY_FIXTURE_DIR / "base-capability-claude.json").read_text(encoding="utf-8")),
            "opencode": json.loads((SUMMARY_FIXTURE_DIR / "base-capability-opencode.json").read_text(encoding="utf-8")),
        }
        cls.base_preflights = {
            "claude": json.loads((SUMMARY_FIXTURE_DIR / "base-preflight-claude.json").read_text(encoding="utf-8")),
            "opencode": json.loads((SUMMARY_FIXTURE_DIR / "base-preflight-opencode.json").read_text(encoding="utf-8")),
        }
        cls.base_model_proof = json.loads((SUMMARY_FIXTURE_DIR / "base-model-proof.json").read_text(encoding="utf-8"))
        cls.base_invocation = json.loads((JUDGE_FIXTURE_DIR / "base-invocation.json").read_text(encoding="utf-8"))

    def make_run_dir(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        run_dir = Path(temp_dir.name)
        write_json(run_dir / "environment.json", copy.deepcopy(self.base_environment))
        for harness in ("claude", "opencode"):
            write_json(run_dir / "capabilities" / f"{harness}.json", copy.deepcopy(self.base_capabilities[harness]))
            write_json(run_dir / "preflight" / f"{harness}.json", copy.deepcopy(self.base_preflights[harness]))
            model_proof = copy.deepcopy(self.base_model_proof)
            model_proof["harness"] = harness
            model_proof["requested_route"] = "fable" if harness == "claude" else "openai/synthetic-model"
            write_json(run_dir / "preflight" / f"{harness}-model-proof.json", model_proof)
        return run_dir

    def write_attempted_case(
        self,
        run_dir: Path,
        harness: str,
        case_id: str,
        verdict: str = "pass",
        contaminated: bool = False,
        plugin_source_id: str = "researchflow-checkout",
    ):
        case_dir = run_dir / harness / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        observed_phase = next(case["expected_phase"] for case in self.cases if case["case_id"] == case_id)
        response_text = f"ResearchFlow phase: {observed_phase}\n"
        response_sha256 = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        invocation = copy.deepcopy(self.base_invocation)
        invocation["case_id"] = case_id
        invocation["harness"] = harness
        invocation["plugin_source_id"] = plugin_source_id
        invocation["model_request"]["requested_route"] = "fable" if harness == "claude" else "openai/synthetic-model"
        invocation["final_response_sha256"] = response_sha256
        invocation["final_response_path"] = "final-response.txt"
        with (case_dir / "final-response.txt").open("w", encoding="utf-8", newline="") as handle:
            handle.write(response_text)
        write_json(case_dir / "invocation.json", invocation)
        verdict_value = {
            "case_id": case_id,
            "expected_phase": observed_phase,
            "verdict": verdict,
            "observed_phase": observed_phase,
            "marker_count": 1,
            "response_sha256": response_sha256,
            "line_1_evidence": {"line": 1, "sha256": response_sha256, "text": f"ResearchFlow phase: {observed_phase}"},
            "matched_evidence": {"line": 1, "sha256": response_sha256, "text": f"ResearchFlow phase: {observed_phase}"},
            "forbidden_pattern_matches": [],
            "environment_contaminated": False,
            "contamination": {
                "contaminated": contaminated,
                "reasons": ["tool_call_blocked"] if contaminated else [],
            },
            "manual_note": None,
        }
        write_json(case_dir / "verdict.json", verdict_value)

    def test_validate_model_proof_accepts_allowlisted_identity(self):
        identities = {"allowed_provider": "openai", "canonical_models": {"synthetic-model": "openai/synthetic-model"}}
        canonical = self.summarize.validate_model_proof(copy.deepcopy(self.base_model_proof), identities)
        self.assertEqual(canonical, "openai/synthetic-model")

    def test_validate_model_proof_rejects_unverified_and_mismatched_identities(self):
        identities = {"allowed_provider": "openai", "canonical_models": {"synthetic-model": "openai/synthetic-model"}}
        unverified = copy.deepcopy(self.base_model_proof)
        unverified["verified"] = False
        mismatched = copy.deepcopy(self.base_model_proof)
        mismatched["resolved_model_identity"] = "openai/not-synthetic"
        alias_only = copy.deepcopy(self.base_model_proof)
        alias_only["requested_route"] = "fable"
        empty_allowlist = {
            "allowed_provider": "openai",
            "canonical_models": {},
            "harness_aliases": {"fable": {"does_not_prove_backing_model": True}},
        }
        self.assertIsNone(self.summarize.validate_model_proof(unverified, identities))
        self.assertIsNone(self.summarize.validate_model_proof(mismatched, identities))
        self.assertIsNone(self.summarize.validate_model_proof(alias_only, empty_allowlist))

    def test_build_summary_all_passes_and_render_is_deterministic(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
        run_dir = self.make_run_dir()
        for harness in ("claude", "opencode"):
            for case_id in self.case_ids:
                self.write_attempted_case(run_dir, harness, case_id)
        summary = self.summarize.build_summary(run_dir, self.cases)
        markdown_1 = self.summarize.render_summary_markdown(summary)
        markdown_2 = self.summarize.render_summary_markdown(summary)
        self.assertTrue(summary["acceptance_passed"])
        self.assertTrue(summary["release_candidate_eligible"])
        self.assertEqual(len(summary["accounting_rows"]), 14)
        self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["pass"], 7)
        self.assertEqual(summary["harnesses"]["opencode"]["verdict_counts"]["pass"], 7)
        self.assertEqual(summary["harnesses"]["claude"]["contamination"]["contaminated_invocations"], 0)
        self.assertEqual(summary["harnesses"]["claude"]["plugin_source_id"], "researchflow-checkout")
        self.assertEqual(markdown_1, markdown_2)
        self.assertIn(
            "This is single-run fresh-session acceptance evidence, not a stability or repeated-run estimate.",
            markdown_1,
        )
        self.assertIn(
            "- Plugin proof strength: `best_available_source_plus_canary` (source `researchflow-checkout`)",
            markdown_1,
        )
        self.assertEqual(sum(1 for line in markdown_1.splitlines() if line.startswith("| ") and "R-" in line), 14)

    def test_build_summary_tracks_fail_and_contamination_overlay_separately(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
        run_dir = self.make_run_dir()
        for case_id in self.case_ids:
            self.write_attempted_case(
                run_dir,
                "claude",
                case_id,
                verdict="fail" if case_id == "R-BACK-INTRO" else "pass",
                contaminated=(case_id == "R-BACK-INTRO"),
            )
            self.write_attempted_case(run_dir, "opencode", case_id)
        summary = self.summarize.build_summary(run_dir, self.cases)
        self.assertFalse(summary["acceptance_passed"])
        self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["fail"], 1)
        self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["pass"], 6)
        self.assertEqual(summary["harnesses"]["claude"]["contamination"]["contaminated_invocations"], 1)
        self.assertEqual(summary["harnesses"]["claude"]["contamination"]["case_ids"], ["R-BACK-INTRO"])
        self.assertEqual(summary["harnesses"]["opencode"]["verdict_counts"]["pass"], 7)

    def test_build_summary_preflight_block_creates_reason_coded_rows_and_uses_preflight_plugin_source(self):
        run_dir = self.make_run_dir()
        blocked_preflight = copy.deepcopy(self.base_preflights["claude"])
        blocked_preflight["status"] = "blocked"
        write_json(run_dir / "preflight" / "claude.json", blocked_preflight)
        summary = self.summarize.build_summary(run_dir, self.cases)
        claude_rows = [row for row in summary["accounting_rows"] if row["harness"] == "claude"]
        opencode_rows = [row for row in summary["accounting_rows"] if row["harness"] == "opencode"]
        self.assertTrue(all(row["status"] == "unattempted" for row in claude_rows + opencode_rows))
        self.assertEqual({row["reason_code"] for row in claude_rows}, {"claude_preflight_blocked"})
        self.assertEqual({row["reason_code"] for row in opencode_rows}, {"global_hard_gate_blocked"})
        self.assertEqual(summary["harnesses"]["claude"]["plugin_source_id"], "researchflow-checkout")
        self.assertEqual(summary["harnesses"]["opencode"]["plugin_source_id"], "researchflow-checkout")
        self.assertFalse(summary["acceptance_passed"])

    def test_build_summary_uses_evaluated_preflight_when_model_proof_is_malformed(self):
        run_dir = self.make_run_dir()
        malformed_proof = copy.deepcopy(self.base_model_proof)
        malformed_proof.pop("proof_sha256")
        write_json(run_dir / "preflight" / "claude-model-proof.json", malformed_proof)
        summary = self.summarize.build_summary(run_dir, self.cases)
        claude_rows = [row for row in summary["accounting_rows"] if row["harness"] == "claude"]
        opencode_rows = [row for row in summary["accounting_rows"] if row["harness"] == "opencode"]
        self.assertTrue(all(row["status"] == "unattempted" for row in claude_rows + opencode_rows))
        self.assertEqual({row["reason_code"] for row in claude_rows}, {"claude_preflight_blocked"})
        self.assertEqual({row["reason_code"] for row in opencode_rows}, {"global_hard_gate_blocked"})
        self.assertEqual(summary["harnesses"]["claude"]["preflight"], "blocked")
        self.assertEqual(summary["harnesses"]["claude"]["resolved_model_identity"], "openai/synthetic-model")
        self.assertFalse(summary["model_alignment"]["aligned"])
        self.assertTrue(summary["model_alignment"]["blocked"])

    def test_build_summary_blocks_profile_mismatch_between_capability_and_preflight(self):
        run_dir = self.make_run_dir()
        mismatched_preflight = copy.deepcopy(self.base_preflights["claude"])
        mismatched_preflight["isolation_profile"] = "workspace-config-runtime-proof"
        write_json(run_dir / "preflight" / "claude.json", mismatched_preflight)
        summary = self.summarize.build_summary(run_dir, self.cases)
        claude_rows = [row for row in summary["accounting_rows"] if row["harness"] == "claude"]
        opencode_rows = [row for row in summary["accounting_rows"] if row["harness"] == "opencode"]
        self.assertTrue(all(row["status"] == "unattempted" for row in claude_rows + opencode_rows))
        self.assertEqual({row["reason_code"] for row in claude_rows}, {"claude_preflight_blocked"})
        self.assertEqual({row["reason_code"] for row in opencode_rows}, {"global_hard_gate_blocked"})
        self.assertEqual(summary["harnesses"]["claude"]["preflight"], "blocked")
        self.assertIsNone(summary["harnesses"]["claude"]["isolation_profile"])

    def test_build_summary_blocked_run_allows_missing_preflight_metadata_without_attempts(self):
        run_dir = self.make_run_dir()
        blocked_preflight = copy.deepcopy(self.base_preflights["claude"])
        blocked_preflight["status"] = "blocked"
        blocked_preflight.pop("plugin_source_id")
        blocked_preflight.pop("plugin_proof_strength")
        blocked_preflight.pop("isolation_profile")
        write_json(run_dir / "preflight" / "claude.json", blocked_preflight)
        blocked_capability = copy.deepcopy(self.base_capabilities["claude"])
        blocked_capability.pop("plugin_proof_strength")
        blocked_capability.pop("selected_isolation_profile")
        write_json(run_dir / "capabilities" / "claude.json", blocked_capability)
        summary = self.summarize.build_summary(run_dir, self.cases)
        self.assertEqual(len(summary["accounting_rows"]), 14)
        self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))
        self.assertEqual(summary["harnesses"]["claude"]["preflight"], "blocked")
        self.assertIsNone(summary["harnesses"]["claude"]["plugin_source_id"])
        self.assertIsNone(summary["harnesses"]["claude"]["plugin_proof_strength"])
        self.assertIsNone(summary["harnesses"]["claude"]["isolation_profile"])
        self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["unattempted"], 7)

    def test_build_summary_model_block_creates_all_14_unattempted_rows(self):
        self.set_allowlist(
            {
                "synthetic-model": "openai/synthetic-model",
                "other-synthetic-model": "openai/other-synthetic-model",
            }
        )
        run_dir = self.make_run_dir()
        mismatched_model = copy.deepcopy(self.base_model_proof)
        mismatched_model["harness"] = "opencode"
        mismatched_model["backing_model_id"] = "other-synthetic-model"
        mismatched_model["resolved_model_identity"] = "openai/other-synthetic-model"
        write_json(run_dir / "preflight" / "opencode-model-proof.json", mismatched_model)
        summary = self.summarize.build_summary(run_dir, self.cases)
        self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))
        self.assertEqual({row["reason_code"] for row in summary["accounting_rows"]}, {"model_alignment_blocked"})
        self.assertTrue(summary["cross_harness_model_confound"])
        self.assertTrue(summary["model_alignment"]["blocked"])

    def test_build_summary_missing_allowlist_uses_global_hard_gate_block(self):
        run_dir = self.make_run_dir()
        for harness in ("claude", "opencode"):
            model_proof = copy.deepcopy(self.base_model_proof)
            model_proof["harness"] = harness
            model_proof["backing_model_id"] = "gpt-5.5"
            model_proof["resolved_model_identity"] = "openai/gpt-5.5"
            model_proof["requested_route"] = "fable" if harness == "claude" else "openai/gpt-5.5"
            write_json(run_dir / "preflight" / f"{harness}-model-proof.json", model_proof)
        summary = self.summarize.build_summary(run_dir, self.cases)
        self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))
        self.assertEqual({row["reason_code"] for row in summary["accounting_rows"]}, {"global_hard_gate_blocked"})
        self.assertTrue(summary["model_alignment"]["blocked"])

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
        self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))

    def test_build_summary_marks_runtime_proof_unavailable_reason(self):
        run_dir = self.make_run_dir()
        write_json(run_dir / "preflight" / "claude.json", {**self.base_preflights["claude"], "status": "pass"})
        write_json(run_dir / "preflight" / "opencode.json", {**self.base_preflights["opencode"], "status": "pass"})

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
        self.assertEqual(summary["reason_code"], self.summarize.lib.REASON_CODES[5])
        self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))

    def test_build_summary_raw_preflight_block_does_not_use_runtime_proof_unavailable(self):
        run_dir = self.make_run_dir()
        blocked_preflight = copy.deepcopy(self.base_preflights["claude"])
        blocked_preflight["status"] = "blocked"
        write_json(run_dir / "preflight" / "claude.json", blocked_preflight)

        invalid_proof = copy.deepcopy(self.base_model_proof)
        invalid_proof["harness"] = "claude"
        invalid_proof.pop("proof_sha256")
        write_json(run_dir / "preflight" / "claude-model-proof.json", invalid_proof)

        summary = self.summarize.build_summary(run_dir, self.cases)
        claude_rows = [row for row in summary["accounting_rows"] if row["harness"] == "claude"]
        self.assertEqual(summary["outcome"], "blocked")
        self.assertEqual(summary["reason_code"], self.summarize.lib.REASON_CODES[3])
        self.assertEqual({row["reason_code"] for row in claude_rows}, {self.summarize.lib.REASON_CODES[0]})
        self.assertTrue(all(row["status"] == "unattempted" for row in summary["accounting_rows"]))

    def test_build_summary_runtime_stop_marks_remaining_rows(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
        run_dir = self.make_run_dir()
        self.write_attempted_case(run_dir, "claude", self.case_ids[0])
        self.write_attempted_case(run_dir, "claude", self.case_ids[1], verdict="harness_error")
        for case_id in self.case_ids:
            self.write_attempted_case(run_dir, "opencode", case_id)
        summary = self.summarize.build_summary(run_dir, self.cases)
        claude_rows = [row for row in summary["accounting_rows"] if row["harness"] == "claude"]
        self.assertEqual([row["status"] for row in claude_rows[:2]], ["pass", "harness_error"])
        self.assertTrue(all(row["status"] == "unattempted" for row in claude_rows[2:]))
        self.assertEqual({row["reason_code"] for row in claude_rows[2:]}, {"runtime_harness_stopped"})
        self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["unattempted"], 5)

    def test_build_summary_rejects_attempted_case_after_runtime_stop(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
        run_dir = self.make_run_dir()
        self.write_attempted_case(run_dir, "claude", self.case_ids[0])
        self.write_attempted_case(run_dir, "claude", self.case_ids[1], verdict="harness_error")
        self.write_attempted_case(run_dir, "claude", self.case_ids[2])
        for case_id in self.case_ids:
            self.write_attempted_case(run_dir, "opencode", case_id)
        with self.assertRaisesRegex(ValueError, "after harness_error"):
            self.summarize.build_summary(run_dir, self.cases)

    def test_build_summary_rejects_conflicting_plugin_sources(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})

        with self.subTest("attempted invocation sources disagree"):
            run_dir = self.make_run_dir()
            for case_id in self.case_ids:
                plugin_source_id = "researchflow-checkout"
                if case_id == self.case_ids[1]:
                    plugin_source_id = "researchflow-release"
                self.write_attempted_case(run_dir, "claude", case_id, plugin_source_id=plugin_source_id)
                self.write_attempted_case(run_dir, "opencode", case_id)
            with self.assertRaisesRegex(ValueError, "conflicting plugin_source_id"):
                self.summarize.build_summary(run_dir, self.cases)

        with self.subTest("preflight proof conflicts with attempted source"):
            run_dir = self.make_run_dir()
            preflight = copy.deepcopy(self.base_preflights["claude"])
            preflight["plugin_source_id"] = "researchflow-release"
            write_json(run_dir / "preflight" / "claude.json", preflight)
            for harness in ("claude", "opencode"):
                for case_id in self.case_ids:
                    self.write_attempted_case(run_dir, harness, case_id)
            with self.assertRaisesRegex(ValueError, "conflicting plugin_source_id"):
                self.summarize.build_summary(run_dir, self.cases)

    def test_build_summary_rejects_duplicate_missing_and_invalid_partitions(self):
        with self.subTest("duplicate case ids across directories"):
            self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
            run_dir = self.make_run_dir()
            for harness in ("claude", "opencode"):
                for case_id in self.case_ids:
                    self.write_attempted_case(run_dir, harness, case_id)
            duplicate_dir = run_dir / "claude" / "R-DIRECT-LIT-copy"
            duplicate_dir.mkdir(parents=True, exist_ok=True)
            copied_invocation = json.loads((run_dir / "claude" / "R-DIRECT-LIT" / "invocation.json").read_text(encoding="utf-8"))
            copied_verdict = json.loads((run_dir / "claude" / "R-DIRECT-LIT" / "verdict.json").read_text(encoding="utf-8"))
            response_text = (run_dir / "claude" / "R-DIRECT-LIT" / "final-response.txt").read_text(encoding="utf-8")
            write_json(duplicate_dir / "invocation.json", copied_invocation)
            write_json(duplicate_dir / "verdict.json", copied_verdict)
            with (duplicate_dir / "final-response.txt").open("w", encoding="utf-8", newline="") as handle:
                handle.write(response_text)
            with self.assertRaisesRegex(ValueError, "does not match verdict case_id"):
                self.summarize.build_summary(run_dir, self.cases)

        with self.subTest("non-prefix attempted cases are invalid"):
            self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
            run_dir = self.make_run_dir()
            self.write_attempted_case(run_dir, "claude", self.case_ids[0])
            self.write_attempted_case(run_dir, "claude", self.case_ids[2])
            for case_id in self.case_ids:
                self.write_attempted_case(run_dir, "opencode", case_id)
            with self.assertRaisesRegex(ValueError, "manifest prefix"):
                self.summarize.build_summary(run_dir, self.cases)

        with self.subTest("aligned run without attempted artifacts is invalid"):
            self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
            run_dir = self.make_run_dir()
            with self.assertRaisesRegex(ValueError, "aligned run requires attempted case artifacts"):
                self.summarize.build_summary(run_dir, self.cases)

    def test_cli_write_and_check_only_round_trip(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})
        run_dir = self.make_run_dir()
        for harness in ("claude", "opencode"):
            for case_id in self.case_ids:
                self.write_attempted_case(run_dir, harness, case_id)
        env = dict(os.environ)
        env["HARNESS_ACCEPTANCE_DIR"] = str(self.summarize.HARNESS_DIR)
        write_command = [
            sys.executable,
            str(HARNESS_DIR / "summarize.py"),
            "--run-dir",
            str(run_dir),
            "--write",
        ]
        check_command = [
            sys.executable,
            str(HARNESS_DIR / "summarize.py"),
            "--run-dir",
            str(run_dir),
            "--check-only",
        ]
        write_result = subprocess.run(write_command, capture_output=True, text=True, env=env)
        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertTrue((run_dir / "summary.json").exists())
        self.assertTrue((run_dir / "summary.md").exists())
        check_result = subprocess.run(check_command, capture_output=True, text=True, env=env)
        self.assertEqual(check_result.returncode, 0, check_result.stderr)

    def test_cli_write_preflights_both_targets_atomically(self):
        self.set_allowlist({"synthetic-model": "openai/synthetic-model"})

        with self.subTest("existing markdown blocks json creation"):
            run_dir = self.make_run_dir()
            for harness in ("claude", "opencode"):
                for case_id in self.case_ids:
                    self.write_attempted_case(run_dir, harness, case_id)
            summary_md_path = run_dir / "summary.md"
            summary_md_path.write_text("existing markdown\n", encoding="utf-8")
            env = dict(os.environ)
            env["HARNESS_ACCEPTANCE_DIR"] = str(self.summarize.HARNESS_DIR)
            result = subprocess.run(
                [
                    sys.executable,
                    str(HARNESS_DIR / "summarize.py"),
                    "--run-dir",
                    str(run_dir),
                    "--write",
                ],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse((run_dir / "summary.json").exists())
            self.assertEqual(summary_md_path.read_text(encoding="utf-8"), "existing markdown\n")
            self.assertIn("summary.md", result.stderr)

        with self.subTest("existing json blocks markdown creation"):
            run_dir = self.make_run_dir()
            for harness in ("claude", "opencode"):
                for case_id in self.case_ids:
                    self.write_attempted_case(run_dir, harness, case_id)
            summary_json_path = run_dir / "summary.json"
            summary_json_path.write_text('{"existing": true}\n', encoding="utf-8")
            env = dict(os.environ)
            env["HARNESS_ACCEPTANCE_DIR"] = str(self.summarize.HARNESS_DIR)
            result = subprocess.run(
                [
                    sys.executable,
                    str(HARNESS_DIR / "summarize.py"),
                    "--run-dir",
                    str(run_dir),
                    "--write",
                ],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse((run_dir / "summary.md").exists())
            self.assertEqual(summary_json_path.read_text(encoding="utf-8"), '{"existing": true}\n')
            self.assertIn("summary.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
