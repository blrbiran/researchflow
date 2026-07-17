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
    {
        "case_id": "R-DIRECT-LIT",
        "kind": "direct",
        "prompt": "I am starting a new research paper from scratch. There is no earlier ResearchFlow artifact required before literature discovery, and I need the first phase that should gather related work, identify the closest papers, and establish a defensible research gap before any writing starts.",
        "expected_phase": "literature-discovery",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?m)^##\s+(Introduction|Methods|Results|Discussion|Conclusion)\b",
            r"(?im)^Here is (the|a) (revised|drafted) .+ section\b",
            r"(?im)^Below is (the|a) (literature map|structure brief|review packet|artifact readme)\b",
        ],
    },
    {
        "case_id": "R-DIRECT-STRUCT",
        "kind": "direct",
        "prompt": "My Literature Map is complete and stable, and the literature-backed gap is already agreed. I need the first phase that should turn those stable upstream artifacts into a paper type decision, contribution framing, and section logic, without going backward into more search.",
        "expected_phase": "paper-structuring",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?m)^##\s+(Introduction|Methods|Results|Discussion|Conclusion)\b",
            r"(?im)^Here is (the|a) (revised|drafted) .+ section\b",
            r"(?im)^Below is (the|a) (literature map|structure brief|review packet|artifact readme)\b",
        ],
    },
    {
        "case_id": "R-DIRECT-DRAFT",
        "kind": "direct",
        "prompt": "My Literature Map and Structure Brief are both complete and stable. I want the first phase that should rewrite a Methods section using those stable upstream artifacts, and I do not need more literature search or outline redesign first.",
        "expected_phase": "paper-drafting",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?m)^##\s+(Introduction|Methods|Results|Discussion|Conclusion)\b",
            r"(?im)^Here is (the|a) (revised|drafted) .+ section\b",
            r"(?im)^Below is (the|a) (literature map|structure brief|review packet|artifact readme)\b",
        ],
    },
    {
        "case_id": "R-DIRECT-REVIEW",
        "kind": "direct",
        "prompt": "I have a complete manuscript draft, and the earlier literature and structure artifacts are stable enough for critique. I need the first phase that should review the manuscript, identify weaknesses, and give a revision order rather than drafting new sections immediately.",
        "expected_phase": "paper-review",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?m)^##\s+(Introduction|Methods|Results|Discussion|Conclusion)\b",
            r"(?im)^Here is (the|a) (revised|drafted) .+ section\b",
            r"(?im)^Below is (the|a) (literature map|structure brief|review packet|artifact readme)\b",
        ],
    },
    {
        "case_id": "R-DIRECT-PACK",
        "kind": "direct",
        "prompt": "My Review Packet is resolved, the manuscript and figures are stable, and there are no unresolved review blockers left. I need the first phase that should package the stable paper into a submission PDF, supplement, and artifact README without sending me back to review.",
        "expected_phase": "artifact-packaging",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?m)^##\s+(Introduction|Methods|Results|Discussion|Conclusion)\b",
            r"(?im)^Here is (the|a) (revised|drafted) .+ section\b",
            r"(?im)^Below is (the|a) (literature map|structure brief|review packet|artifact readme)\b",
        ],
    },
    {
        "case_id": "R-BACK-INTRO",
        "kind": "backward",
        "prompt": "Please write the Introduction section for my paper. The blocking problem is that there is no stable Literature Map yet, the research gap is still missing, and I want the first phase that should handle that missing upstream state before any introduction prose is written.",
        "expected_phase": "literature-discovery",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?m)^##\s+Introduction\b",
            r"(?im)^Here is (the|a) drafted introduction section\b",
            r"(?im)^Below is (the|a) polished introduction\b",
        ],
    },
    {
        "case_id": "R-BACK-PDF",
        "kind": "backward",
        "prompt": "Please export a submission PDF for this project. The blocking state is unresolved review blockers, no stable Review Packet, and no sign-off that packaging should start, so I need the first phase that should handle that missing review stability before any export work happens.",
        "expected_phase": "paper-review",
        "required_marker": "ResearchFlow phase:",
        "forbidden_patterns": [
            r"(?im)^Export complete\b",
            r"(?im)^Here is (the|a) packaged submission bundle\b",
            r"(?im)^Below is (the|a) artifact readme\b",
        ],
    },
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
VALID_INVOCATION = {
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
        "backing_model_id": "synthetic-model",
        "proof_source": "litellm-response-metadata",
        "proof_sha256": "b" * 64,
    },
    "resolved_model_identity": "openai/synthetic-model",
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
        self.assertEqual(cases, EXPECTED_CASES)
        self.assertEqual(len(cases), 7)

    def test_load_cases_rejects_invalid_regex(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            harness_dir = temp_root / "tests" / "harness-acceptance"
            harness_dir.mkdir(parents=True)
            invalid_cases = copy.deepcopy(EXPECTED_CASES)
            invalid_cases[0]["forbidden_patterns"][0] = "("
            (harness_dir / "cases.json").write_text(
                json.dumps(invalid_cases, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, r"invalid regex"):
                self.lib.load_cases(temp_root)

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

        self.assertEqual(VALID_INVOCATION["model_resolution"]["backing_model_id"], "synthetic-model")
        self.assertEqual(VALID_INVOCATION["resolved_model_identity"], "openai/synthetic-model")
        self.lib.validate_invocation(copy.deepcopy(VALID_INVOCATION))

        unknown_top_level = copy.deepcopy(VALID_INVOCATION)
        unknown_top_level["unexpected"] = True
        with self.assertRaises(ValueError):
            self.lib.validate_invocation(unknown_top_level)

        bad_sha = copy.deepcopy(VALID_INVOCATION)
        bad_sha["final_response_sha256"] = "not-a-sha"
        with self.assertRaises(ValueError):
            self.lib.validate_invocation(bad_sha)


if __name__ == "__main__":
    unittest.main()
