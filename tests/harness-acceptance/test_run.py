#!/usr/bin/env python3
from __future__ import annotations

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
        cls.run_module = load_module("harness_acceptance_run", HARNESS_DIR / "run.py")
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
        cls.identities = {
            "allowed_provider": "openai",
            "canonical_models": {"synthetic-model": "openai/synthetic-model"},
            "harness_aliases": {
                "fable": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
                "haiku": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
                "opus": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
                "sonnet": {"does_not_prove_backing_model": True, "may_route_via": "litellm"},
            },
        }

    def setUp(self):
        self.identity_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.identity_dir.cleanup)
        identity_root = Path(self.identity_dir.name)
        write_json(identity_root / "model-identities.json", self.identities)

        original_harness_dir = self.run_module.summarize.HARNESS_DIR
        self.run_module.summarize.HARNESS_DIR = identity_root
        self.addCleanup(setattr, self.run_module.summarize, "HARNESS_DIR", original_harness_dir)

        original_load_identities = self.run_module.preflight.load_identities

        def fake_load_identities(_harness_dir: Path):
            return copy.deepcopy(self.identities)

        self.run_module.preflight.load_identities = fake_load_identities
        self.addCleanup(setattr, self.run_module.preflight, "load_identities", original_load_identities)

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
        invocation["run_id"] = case_dir.parents[1].name
        invocation["model_request"]["requested_route"] = "fable" if harness == "claude" else "openai/synthetic-model"
        response_text = f"ResearchFlow phase: {observed_phase}\n"
        response_sha = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        invocation["final_response_sha256"] = response_sha
        (case_dir / "final-response.txt").write_text(response_text, encoding="utf-8")
        write_json(case_dir / "invocation.json", invocation)
        write_json(
            case_dir / "command.json",
            {
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
            },
        )

    def install_fake_adapter(self, blocked_harness: str | None = None, case_calls: list[tuple[str, str]] | None = None):
        original = self.run_module._run_adapter

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

        self.run_module._run_adapter = fake_run_adapter
        self.addCleanup(setattr, self.run_module, "_run_adapter", original)

    def test_preflight_only_blocked_writes_summary_and_never_runs_cases(self):
        case_calls: list[tuple[str, str]] = []
        self.install_fake_adapter(blocked_harness="claude", case_calls=case_calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run_module.run_original(config, "2026-07-18T120000Z", "preflight-only")
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(case_calls, [])
            self.assertEqual(len(summary["accounting_rows"]), 14)
            self.assertFalse((run_dir / "preflight" / "baseline.json").exists())

    def test_preflight_only_aligned_writes_baseline_without_final_summary(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run_module.run_original(config, "2026-07-18T121500Z", "preflight-only")
            self.assertTrue((run_dir / "preflight" / "baseline.json").exists())
            self.assertFalse((run_dir / "summary.json").exists())
            self.assertFalse((run_dir / "summary.md").exists())

    def test_scored_requires_aligned_baseline_and_runs_cases_in_fixed_order(self):
        case_calls: list[tuple[str, str]] = []
        self.install_fake_adapter(case_calls=case_calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run_module.run_original(config, "2026-07-18T123000Z", "preflight-only")
            rerun_dir = self.run_module.run_original(config, "2026-07-18T123000Z", "scored")
            self.assertEqual(run_dir, rerun_dir)
            expected = [("claude", case_id) for case_id in self.case_ids] + [("opencode", case_id) for case_id in self.case_ids]
            self.assertEqual(case_calls, expected)
            self.assertTrue((run_dir / "summary.json").exists())

    def test_scored_rejects_changed_baseline_or_existing_case_artifacts(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(Path(temp_dir) / "results")
            run_dir = self.run_module.run_original(config, "2026-07-18T124500Z", "preflight-only")
            changed = copy.deepcopy(config)
            changed["timeout_seconds"] = 300
            with self.assertRaisesRegex(ValueError, "baseline"):
                self.run_module.run_original(changed, "2026-07-18T124500Z", "scored")
            case_dir = run_dir / "claude" / self.case_ids[0]
            case_dir.mkdir(parents=True, exist_ok=True)
            with self.assertRaisesRegex(ValueError, "existing case artifact"):
                self.run_module.run_original(config, "2026-07-18T124500Z", "scored")
