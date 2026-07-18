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
