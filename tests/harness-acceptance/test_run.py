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

        original_run_harness_dir = self.run_module.HARNESS_DIR
        self.run_module.HARNESS_DIR = identity_root
        self.trusted_results_root = identity_root / "results"
        self.addCleanup(setattr, self.run_module, "HARNESS_DIR", original_run_harness_dir)

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
            config["results_root"] = str(self.trusted_results_root)
            run_dir = self.run_module.run_original(config, "2026-07-18T120000Z", "preflight-only")
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(case_calls, [])
            self.assertEqual(len(summary["accounting_rows"]), 14)
            self.assertFalse((run_dir / "preflight" / "baseline.json").exists())

    def test_preflight_only_aligned_writes_baseline_without_final_summary(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
            run_dir = self.run_module.run_original(config, "2026-07-18T121500Z", "preflight-only")
            baseline = json.loads((run_dir / "preflight" / "baseline.json").read_text(encoding="utf-8"))
            self.assertEqual(baseline["repo_commit_sha"], config["repo_commit_sha"])
            self.assertEqual(baseline["cases_sha256"], self.lib.sha256_path(HARNESS_DIR / "cases.json"))
            self.assertEqual(baseline["scored_prompt_sha256"], self.lib.sha256_path(HARNESS_DIR / "scored-prompt.txt"))
            self.assertEqual(baseline["plugin_source_id"], config["plugin_source_id"])
            self.assertEqual(baseline["residual_categories"], config["residual_categories"])
            for harness in ("claude", "opencode"):
                self.assertEqual(
                    baseline["harnesses"][harness]["cli_bin"],
                    config[harness]["cli_bin"],
                )
                self.assertEqual(
                    baseline["harnesses"][harness]["harness_model_value"],
                    config[harness]["harness_model_value"],
                )
                self.assertEqual(
                    baseline["harnesses"][harness]["effort_or_variant"],
                    config[harness]["effort_or_variant"],
                )
                self.assertEqual(
                    baseline["harnesses"][harness]["plugin_source_id"],
                    config["plugin_source_id"],
                )
                self.assertEqual(
                    baseline["harnesses"][harness]["canonical_identity"],
                    "openai/synthetic-model",
                )
                self.assertRegex(baseline["harnesses"][harness]["proof_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(baseline["harnesses"][harness]["endpoint_identity_sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(baseline["harnesses"][harness]["selected_isolation_profile"])
                self.assertTrue(baseline["harnesses"][harness]["plugin_proof_strength"])
            self.assertRegex(baseline["fingerprint_sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse((run_dir / "summary.json").exists())
            self.assertFalse((run_dir / "summary.md").exists())

    def test_run_original_uses_trusted_proof_loader_boundary_across_orchestration(self):
        self.install_fake_adapter()
        loader_calls: list[tuple[Path, str, Path]] = []
        original_loader = self.run_module.lib.load_runtime_model_proof_artifact

        def fake_loader(run_dir: Path, harness: str, results_root: Path):
            loader_calls.append((run_dir, harness, results_root))
            return copy.deepcopy(self.run_module.lib.read_json(run_dir / "preflight" / f"{harness}-model-proof.json"))

        self.run_module.lib.load_runtime_model_proof_artifact = fake_loader
        self.addCleanup(setattr, self.run_module.lib, "load_runtime_model_proof_artifact", original_loader)

        with tempfile.TemporaryDirectory() as temp_dir:
            configured_results_root = Path(temp_dir) / "results"
            config = self.make_config()
            config["results_root"] = str(configured_results_root)
            self.assertNotEqual(configured_results_root.resolve(), self.trusted_results_root.resolve())
            run_dir = self.run_module.run_original(config, "2026-07-18T122000Z", "preflight-only")
            rerun_dir = self.run_module.run_original(config, "2026-07-18T122000Z", "scored")

        self.assertEqual(rerun_dir, run_dir)
        self.assertEqual(
            loader_calls,
            [
                (run_dir, "claude", self.trusted_results_root),
                (run_dir, "opencode", self.trusted_results_root),
                (run_dir, "claude", self.trusted_results_root),
                (run_dir, "opencode", self.trusted_results_root),
                (run_dir, "claude", self.trusted_results_root),
                (run_dir, "opencode", self.trusted_results_root),
            ],
        )

    def test_hydrate_run_config_accepts_minimal_checked_in_config_shape(self):
        minimal = {
            "claude": {"harness_model_value": "fable", "effort_or_variant": "high"},
            "opencode": {"harness_model_value": "openai/proxy-route", "effort_or_variant": "high"},
            "timeout_seconds": 120,
        }
        hydrated = self.run_module.hydrate_run_config(minimal, "2026-07-18T130000Z")
        self.assertEqual(hydrated["repo_root"], str(ROOT))
        self.assertEqual(hydrated["plugin_source_id"], "researchflow-checkout")
        self.assertEqual(hydrated["residual_categories"], ["auth", "admin-policy"])
        self.assertEqual(hydrated["claude"]["cli_bin"], "claude")
        self.assertEqual(hydrated["opencode"]["cli_bin"], "opencode")
        self.assertIn("2026-07-18T130000Z", hydrated["raw_dir"])
        self.assertEqual(hydrated["endpoint_identity"], "https://redacted.invalid/v1")

    def test_build_baseline_record_uses_configured_repo_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            harness_dir = repo_root / "tests" / "harness-acceptance"
            harness_dir.mkdir(parents=True, exist_ok=True)
            cases_path = harness_dir / "cases.json"
            prompt_path = harness_dir / "scored-prompt.txt"
            cases_path.write_text("custom-cases\n", encoding="utf-8")
            prompt_path.write_text("custom-prompt\n", encoding="utf-8")
            config = self.make_config()
            config["repo_root"] = str(repo_root)
            evaluations = {
                "claude": {
                    "plugin_source_id": config["plugin_source_id"],
                    "plugin_proof_strength": "best_available_source_plus_canary",
                    "isolation_profile": "auth-preserving-direct-plugin-dir",
                    "canonical_identity": "openai/synthetic-model",
                },
                "opencode": {
                    "plugin_source_id": config["plugin_source_id"],
                    "plugin_proof_strength": "resolved_runtime_source_inventory_canary",
                    "isolation_profile": "workspace-config-runtime-proof",
                    "canonical_identity": "openai/synthetic-model",
                },
            }
            model_proofs = {
                "claude": {"proof_sha256": "a" * 64, "endpoint_identity_sha256": "b" * 64},
                "opencode": {"proof_sha256": "c" * 64, "endpoint_identity_sha256": "d" * 64},
            }
            baseline = self.run_module.build_baseline_record(repo_root, config, evaluations, model_proofs)
            self.assertEqual(baseline["cases_sha256"], self.lib.sha256_path(cases_path))
            self.assertEqual(baseline["scored_prompt_sha256"], self.lib.sha256_path(prompt_path))

    def test_scored_requires_aligned_baseline_and_runs_cases_in_fixed_order(self):
        case_calls: list[tuple[str, str]] = []
        self.install_fake_adapter(case_calls=case_calls)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
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
            config["results_root"] = str(self.trusted_results_root)
            run_dir = self.run_module.run_original(config, "2026-07-18T124500Z", "preflight-only")
            changed = copy.deepcopy(config)
            changed["timeout_seconds"] = 300
            with self.assertRaisesRegex(ValueError, "baseline"):
                self.run_module.run_original(changed, "2026-07-18T124500Z", "scored")
            changed_bin = copy.deepcopy(config)
            changed_bin["claude"]["cli_bin"] = "/bin/false"
            with self.assertRaisesRegex(ValueError, "baseline"):
                self.run_module.run_original(changed_bin, "2026-07-18T124500Z", "scored")
            blocked = copy.deepcopy(self.base_preflight["claude"])
            blocked["status"] = "blocked"
            write_json(run_dir / "preflight" / "claude.json", blocked)
            with self.assertRaisesRegex(ValueError, "preflight"):
                self.run_module.run_original(config, "2026-07-18T124500Z", "scored")
            write_json(run_dir / "preflight" / "claude.json", copy.deepcopy(self.base_preflight["claude"]))
            case_dir = run_dir / "claude" / self.case_ids[0]
            case_dir.mkdir(parents=True, exist_ok=True)
            with self.assertRaisesRegex(ValueError, "existing case artifact"):
                self.run_module.run_original(config, "2026-07-18T124500Z", "scored")

    def test_preflight_only_rejects_duplicate_run_id(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
            self.run_module.run_original(config, "2026-07-18T125500Z", "preflight-only")
            with self.assertRaises(FileExistsError):
                self.run_module.run_original(config, "2026-07-18T125500Z", "preflight-only")

    def test_scored_rejects_duplicate_completion(self):
        self.install_fake_adapter()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
            self.run_module.run_original(config, "2026-07-18T130500Z", "preflight-only")
            self.run_module.run_original(config, "2026-07-18T130500Z", "scored")
            with self.assertRaisesRegex(ValueError, "scored phase already completed"):
                self.run_module.run_original(config, "2026-07-18T130500Z", "scored")

    def test_scored_fail_closes_runtime_stop_and_still_writes_summary(self):
        case_calls: list[tuple[str, str]] = []
        original = self.run_module._run_adapter

        def fake_run_adapter(harness: str, mode: str, config_path: Path, output_dir: Path, case_id: str | None = None):
            output_dir.mkdir(parents=True, exist_ok=True)
            if mode == "capability":
                write_json(output_dir / f"{harness}.json", copy.deepcopy(self.base_capability[harness]))
                return
            if mode == "preflight":
                preflight = copy.deepcopy(self.base_preflight[harness])
                proof = copy.deepcopy(self.base_model_proof)
                proof["harness"] = harness
                proof["requested_route"] = "fable" if harness == "claude" else "openai/synthetic-model"
                write_json(output_dir / f"{harness}.json", preflight)
                write_json(output_dir / f"{harness}-model-proof.json", proof)
                return
            if mode == "case":
                assert case_id is not None
                case_calls.append((harness, case_id))
                if harness == "claude" and case_id == self.case_ids[1]:
                    (output_dir / "invocation.json").write_text("{}\n", encoding="utf-8")
                    raise RuntimeError("synthetic adapter stop")
                observed_phase = next(case["expected_phase"] for case in self.lib.load_cases(ROOT) if case["case_id"] == case_id)
                self.write_case_artifacts(output_dir, harness, case_id, observed_phase)
                return
            raise AssertionError(f"unexpected mode: {mode}")

        self.run_module._run_adapter = fake_run_adapter
        self.addCleanup(setattr, self.run_module, "_run_adapter", original)

        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.make_config()
            config["results_root"] = str(self.trusted_results_root)
            run_dir = self.run_module.run_original(config, "2026-07-18T131500Z", "preflight-only")
            self.run_module.run_original(config, "2026-07-18T131500Z", "scored")
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            claude_rows = [row for row in summary["accounting_rows"] if row["harness"] == "claude"]
            self.assertEqual(claude_rows[0]["status"], "pass")
            self.assertEqual(claude_rows[1]["status"], "harness_error")
            self.assertTrue(all(row["status"] == "unattempted" for row in claude_rows[2:]))
            self.assertEqual({row["reason_code"] for row in claude_rows[2:]}, {"runtime_harness_stopped"})
            self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["harness_error"], 1)
            self.assertEqual(summary["harnesses"]["claude"]["verdict_counts"]["unattempted"], 5)
            repaired_invocation = json.loads(
                (run_dir / "claude" / self.case_ids[1] / "invocation.json").read_text(encoding="utf-8")
            )
            self.assertEqual(repaired_invocation["harness"], "claude")
            self.assertEqual(repaired_invocation["case_id"], self.case_ids[1])
            self.assertIn(("opencode", self.case_ids[0]), case_calls)

    def test_main_parses_cli_arguments_and_invokes_run_original(self):
        calls = {}
        original = self.run_module.run_original

        def fake_run_original(config, run_id, mode):
            calls["config"] = config
            calls["run_id"] = run_id
            calls["mode"] = mode
            return Path("/tmp/synthetic-run")

        self.run_module.run_original = fake_run_original
        self.addCleanup(setattr, self.run_module, "run_original", original)

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "run-config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "claude": {"harness_model_value": "fable", "effort_or_variant": "high"},
                        "opencode": {"harness_model_value": "openai/proxy-route", "effort_or_variant": "high"},
                        "timeout_seconds": 120,
                    },
                    indent=2,
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
            )
            exit_code = self.run_module.main([
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
        self.assertEqual(calls["config"]["plugin_source_id"], "researchflow-checkout")
        self.assertEqual(calls["config"]["residual_categories"], ["auth", "admin-policy"])
        self.assertEqual(calls["config"]["claude"]["cli_bin"], "claude")
        self.assertEqual(calls["config"]["opencode"]["cli_bin"], "opencode")
