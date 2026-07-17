#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
EXPECTED_PHASES = (
    "literature-discovery",
    "paper-structuring",
    "paper-drafting",
    "paper-review",
    "artifact-packaging",
)
EXPECTED_VERDICTS = ("pass", "fail", "indeterminate", "harness_error")
EXPECTED_REASON_CODES = (
    "claude_preflight_blocked",
    "opencode_preflight_blocked",
    "model_alignment_blocked",
    "global_hard_gate_blocked",
    "runtime_harness_stopped",
)
EXPECTED_CASES = [
    ("R-DIRECT-LIT", "direct", "literature-discovery"),
    ("R-DIRECT-STRUCT", "direct", "paper-structuring"),
    ("R-DIRECT-DRAFT", "direct", "paper-drafting"),
    ("R-DIRECT-REVIEW", "direct", "paper-review"),
    ("R-DIRECT-PACK", "direct", "artifact-packaging"),
    ("R-BACK-INTRO", "backward", "literature-discovery"),
    ("R-BACK-PDF", "backward", "paper-review"),
]
EXPECTED_SUFFIX = (
    "Before doing any research, writing, review, or packaging work, identify\n"
    "the single ResearchFlow phase to enter first. Do not execute that phase.\n"
    "\n"
    "Your response must begin with exactly one line in this format:\n"
    "ResearchFlow phase: <phase-id>\n"
    "\n"
    "After that line, you may give at most two non-empty single-line explanations.\n"
    "Do not use headings, lists, blockquotes, or code fences.\n"
)


def load_lib():
    lib_path = HARNESS_DIR / "lib.py"
    spec = importlib.util.spec_from_file_location("harness_acceptance_lib", lib_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {lib_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = load_lib()

    def test_constants_are_frozen(self):
        self.assertEqual(self.lib.PHASES, EXPECTED_PHASES)
        self.assertEqual(self.lib.VERDICTS, EXPECTED_VERDICTS)
        self.assertEqual(self.lib.REASON_CODES, EXPECTED_REASON_CODES)

    def test_cases_manifest_matches_shared_contract(self):
        cases = self.lib.load_cases(ROOT)
        self.assertEqual(
            [(case["case_id"], case["kind"], case["expected_phase"]) for case in cases],
            EXPECTED_CASES,
        )
        self.assertEqual(len({case["case_id"] for case in cases}), 7)
        for case in cases:
            self.assertEqual(case["required_marker"], "ResearchFlow phase:")
            self.assertIsInstance(case["prompt"], str)
            self.assertGreater(len(case["prompt"]), 80)
            self.assertIsInstance(case["forbidden_patterns"], list)
            self.assertTrue(case["forbidden_patterns"])
            self.assertTrue(all(isinstance(pattern, str) and pattern for pattern in case["forbidden_patterns"]))
            if case["kind"] == "direct":
                self.assertTrue(
                    case["case_id"] == "R-DIRECT-LIT" or "stable" in case["prompt"].lower(),
                    msg=case["case_id"],
                )
            else:
                lowered = case["prompt"].lower()
                self.assertTrue(
                    "missing" in lowered or "unresolved" in lowered or "no stable" in lowered,
                    msg=case["case_id"],
                )

    def test_scored_suffix_is_exact_and_harness_neutral(self):
        scored_path = HARNESS_DIR / "scored-prompt.txt"
        self.assertEqual(scored_path.read_text(encoding="utf-8"), EXPECTED_SUFFIX)
        self.assertNotIn("claude", EXPECTED_SUFFIX.lower())
        self.assertNotIn("opencode", EXPECTED_SUFFIX.lower())

    def test_model_allowlist_starts_empty_and_aliases_do_not_prove_backing_model(self):
        identities = self.lib.read_json(HARNESS_DIR / "model-identities.json")
        self.assertEqual(identities["allowed_provider"], "openai")
        self.assertEqual(identities["canonical_models"], {})
        aliases = identities["harness_aliases"]
        for alias in ("fable", "opus", "sonnet", "haiku"):
            with self.subTest(alias=alias):
                self.assertEqual(aliases[alias]["may_route_via"], "litellm")
                self.assertIs(aliases[alias]["does_not_prove_backing_model"], True)

    def test_json_io_hashing_and_invocation_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            json_path = temp_root / "sample.json"
            self.lib.write_json(json_path, {"b": 1, "a": 2})
            self.assertEqual(
                json_path.read_text(encoding="utf-8"),
                '{\n  "a": 2,\n  "b": 1\n}\n',
            )
            with self.assertRaises(FileExistsError):
                self.lib.write_json(json_path, {"a": 3})

            hash_path = temp_root / "hash.txt"
            hash_path.write_text("routing only\n", encoding="utf-8")
            self.assertEqual(
                self.lib.sha256_path(hash_path),
                hashlib.sha256(b"routing only\n").hexdigest(),
            )

        invocation = {
            "schema_version": 1,
            "run_id": "2026-07-17T120000Z",
            "case_id": "R-DIRECT-LIT",
            "harness": "claude",
            "cli_version": "2.1.212",
            "model_request": {
                "harness_value": "fable",
                "proxy_kind": "litellm",
                "endpoint_identity_sha256": "a" * 64,
                "requested_route": "fable",
            },
            "model_resolution": {
                "upstream_provider": "openai",
                "backing_model_id": "gpt-5.5",
                "proof_source": "litellm-response-metadata",
                "proof_sha256": "b" * 64,
            },
            "resolved_model_identity": "openai/gpt-5.5",
            "model_identity_verified": True,
            "effort_or_variant": "high",
            "timeout_seconds": 120,
            "started_at_utc": "2026-07-17T120000Z",
            "finished_at_utc": "2026-07-17T120015Z",
            "exit_code": 0,
            "timed_out": False,
            "repo_commit_sha": "c" * 40,
            "plugin_source_id": "researchflow-checkout",
            "plugin_proof_passed": True,
            "plugin_proof_strength": "best_available_source_plus_canary",
            "isolation_profile": "auth-preserving-direct-plugin-dir",
            "environment_contaminated": False,
            "residual_categories": ["auth", "admin-policy"],
            "tool_execution": {
                "detected": False,
                "attempted_tools": [],
                "side_effect_status": "none",
                "audit_complete": True,
            },
            "final_response_path": "final-response.txt",
            "final_response_sha256": "d" * 64,
            "raw_artifact_hashes": {
                "events": "e" * 64,
                "stderr": "f" * 64,
            },
        }
        self.lib.validate_invocation(invocation)

        unknown_top_level = copy.deepcopy(invocation)
        unknown_top_level["unexpected"] = True
        with self.assertRaises(ValueError):
            self.lib.validate_invocation(unknown_top_level)

        bad_sha = copy.deepcopy(invocation)
        bad_sha["final_response_sha256"] = "not-a-sha"
        with self.assertRaises(ValueError):
            self.lib.validate_invocation(bad_sha)


if __name__ == "__main__":
    unittest.main()
