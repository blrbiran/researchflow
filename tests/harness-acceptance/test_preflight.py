#!/usr/bin/env python3
import copy
import importlib.util
import json
import tempfile
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


def write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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

    def test_load_identities_uses_shared_lib_reader(self):
        sentinel = {"allowed_provider": "openai"}
        captured = {}
        original = self.preflight.lib.read_json
        try:
            def fake_read_json(path: Path):
                captured["path"] = path
                return sentinel

            self.preflight.lib.read_json = fake_read_json
            result = self.preflight.load_identities(HARNESS_DIR)
        finally:
            self.preflight.lib.read_json = original
        self.assertIs(result, sentinel)
        self.assertEqual(captured["path"], HARNESS_DIR / "model-identities.json")

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

    def test_evaluate_preflight_rejects_model_proof_missing_summary_required_fields(self):
        capability = copy.deepcopy(self.capability["claude"])
        preflight = copy.deepcopy(self.base_preflight["claude"])
        model_proof = copy.deepcopy(self.base_model_proof)
        model_proof.pop("proof_sha256")
        result = self.preflight.evaluate_preflight(capability, preflight, model_proof, self.identities)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["proof_valid"])

    def test_evaluate_preflight_blocks_on_capability_preflight_profile_mismatch(self):
        capability = copy.deepcopy(self.capability["claude"])
        preflight = copy.deepcopy(self.base_preflight["claude"])
        model_proof = copy.deepcopy(self.base_model_proof)
        preflight["isolation_profile"] = "workspace-config-runtime-proof"
        result = self.preflight.evaluate_preflight(capability, preflight, model_proof, self.identities)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["canonical_identity"])
        self.assertIsNone(result["isolation_profile"])
        self.assertEqual(result["plugin_proof_strength"], "best_available_source_plus_canary")

    def test_evaluate_preflight_blocks_on_capability_preflight_plugin_proof_strength_mismatch(self):
        capability = copy.deepcopy(self.capability["claude"])
        preflight = copy.deepcopy(self.base_preflight["claude"])
        model_proof = copy.deepcopy(self.base_model_proof)
        preflight["plugin_proof_strength"] = "workspace_config_static_inventory_canary"
        result = self.preflight.evaluate_preflight(capability, preflight, model_proof, self.identities)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["canonical_identity"])
        self.assertIsNone(result["plugin_proof_strength"])
        self.assertEqual(result["isolation_profile"], "auth-preserving-direct-plugin-dir")

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
        self.assertEqual(allowlist_gap["reason_code"], self.preflight.lib.REASON_CODES[3])

        mismatched = copy.deepcopy(opencode)
        mismatched["proof_identity"] = "openai/other-synthetic-model"
        mismatch = self.preflight.evaluate_model_alignment(claude, mismatched)
        self.assertFalse(mismatch["aligned"])
        self.assertEqual(mismatch["reason_code"], self.preflight.lib.REASON_CODES[2])

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

    def test_load_run_preflight_state_reports_continuation_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            harness_dir = run_dir / "harness"
            (run_dir / "capabilities").mkdir()
            (run_dir / "preflight").mkdir()
            write_json(
                harness_dir / "model-identities.json",
                {
                    "allowed_provider": "openai",
                    "canonical_models": {"synthetic-model": "openai/synthetic-model"},
                    "harness_aliases": {"fable": {"does_not_prove_backing_model": True, "may_route_via": "litellm"}},
                },
            )
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
            state = self.preflight.load_run_preflight_state(run_dir, harness_dir)
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

    def test_main_require_aligned_rejects_non_ready_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            (run_dir / "capabilities").mkdir()
            (run_dir / "preflight").mkdir()
            write_json(run_dir / "capabilities" / "claude.json", self.capability["claude"])
            write_json(run_dir / "capabilities" / "opencode.json", self.capability["opencode"])
            write_json(run_dir / "preflight" / "claude.json", self.base_preflight["claude"])
            write_json(run_dir / "preflight" / "opencode.json", self.base_preflight["opencode"])
            for harness in ("claude", "opencode"):
                model_proof = copy.deepcopy(self.base_model_proof)
                model_proof["harness"] = harness
                model_proof["backing_model_id"] = "gpt-5.5"
                model_proof["resolved_model_identity"] = "openai/gpt-5.5"
                model_proof["requested_route"] = "fable" if harness == "claude" else "openai/gpt-5.5"
                write_json(run_dir / "preflight" / f"{harness}-model-proof.json", model_proof)
            with self.assertRaisesRegex(ValueError, "continuation-ready"):
                self.preflight.main(["--run-dir", str(run_dir), "--require-aligned"])
