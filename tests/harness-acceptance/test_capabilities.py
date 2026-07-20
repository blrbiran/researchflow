#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
FIXTURE_DIR = HARNESS_DIR / "fixtures" / "capabilities"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clone_json(value):
    return json.loads(json.dumps(value))


class CapabilitiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capabilities = load_module("harness_acceptance_capabilities", HARNESS_DIR / "capabilities.py")
        cls.fixtures = {
            "claude_direct": read_json(FIXTURE_DIR / "claude-direct.json"),
            "claude_marketplace": read_json(FIXTURE_DIR / "claude-marketplace.json"),
            "claude_unsupported": read_json(FIXTURE_DIR / "claude-unsupported.json"),
            "claude_full": read_json(FIXTURE_DIR / "claude-full-isolation.json"),
            "opencode_strong": read_json(FIXTURE_DIR / "opencode-strong.json"),
            "opencode_fallback": read_json(FIXTURE_DIR / "opencode-fallback.json"),
            "opencode_unsupported": read_json(FIXTURE_DIR / "opencode-unsupported.json"),
        }

    def test_select_claude_load_branch_supports_direct_marketplace_and_unsupported(self):
        self.assertEqual(
            self.capabilities.select_claude_load_branch(self.fixtures["claude_direct"]),
            "direct-plugin-dir",
        )
        self.assertEqual(
            self.capabilities.select_claude_load_branch(self.fixtures["claude_marketplace"]),
            "local-marketplace",
        )
        self.assertIsNone(self.capabilities.select_claude_load_branch(self.fixtures["claude_unsupported"]))

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
            self.capabilities.select_isolation_profile(self.fixtures["claude_direct"]),
            "auth-preserving-direct-plugin-dir",
        )
        self.assertEqual(
            self.capabilities.select_isolation_profile(self.fixtures["claude_marketplace"]),
            "auth-preserving-marketplace",
        )
        self.assertEqual(
            self.capabilities.select_isolation_profile(self.fixtures["claude_full"]),
            "full-direct-plugin-dir",
        )
        self.assertEqual(
            self.capabilities.select_isolation_profile(self.fixtures["opencode_strong"]),
            "workspace-config-runtime-proof",
        )
        self.assertEqual(
            self.capabilities.select_isolation_profile(self.fixtures["opencode_fallback"]),
            "workspace-config-runtime-proof",
        )
        self.assertIsNone(self.capabilities.select_isolation_profile(self.fixtures["opencode_unsupported"]))

    def test_select_opencode_proof_branch_allows_weak_debug_diagnostics_when_repo_workspace_and_canary_hold(self):
        weak_debug = clone_json(self.fixtures["opencode_fallback"])
        weak_debug["probe_results"]["debug"]["paths_source_match"] = False
        weak_debug["probe_results"]["debug"]["skill_inventory_valid"] = False
        self.assertEqual(
            self.capabilities.select_opencode_proof_branch(weak_debug),
            "workspace-repo-canary-proof",
        )

    def test_build_capability_record_discloses_optional_claude_validation(self):
        probe = clone_json(self.fixtures["claude_direct"])
        probe["probe_results"]["cli_validation"] = {"supported": True, "passed": True}
        record = self.capabilities.build_capability_record("claude", "2.1.212", probe)
        self.assertEqual(record["selected_load_branch"], "direct-plugin-dir")
        self.assertEqual(record["plugin_load_path"], "direct-plugin-dir")
        self.assertEqual(record["plugin_proof_strength"], "best_available_source_plus_canary")
        self.assertTrue(record["optional_cli_validation"])
        self.assertEqual(record["selected_isolation_profile"], "auth-preserving-direct-plugin-dir")

    def test_build_capability_record_derives_boolean_fields_from_probe_evidence(self):
        probe = clone_json(self.fixtures["claude_direct"])
        probe["probe_results"]["environment_validation"]["structured_output_supported"] = False
        probe["probe_results"]["environment_validation"]["session_persistence_disable_supported"] = False
        record = self.capabilities.build_capability_record("claude", "2.1.212", probe)
        self.assertFalse(record["structured_output"])
        self.assertFalse(record["session_persistence_disable"])
        self.assertIsNone(record["selected_load_branch"])
        self.assertIsNone(record["selected_isolation_profile"])

    def test_build_capability_record_requires_selected_full_isolation_profile(self):
        probe = clone_json(self.fixtures["claude_full"])
        probe["probe_results"]["environment_validation"]["full_isolation_supported"] = False
        record = self.capabilities.build_capability_record("claude", "2.1.212", probe)
        self.assertEqual(record["selected_isolation_profile"], "auth-preserving-direct-plugin-dir")
        self.assertFalse(record["auth_preserving_full_isolation"])

    def test_hash_endpoint_identity_normalizes_without_serializing_raw_url(self):
        first = self.capabilities.hash_endpoint_identity("HTTPS://Proxy.EXAMPLE.com/v1/")
        second = self.capabilities.hash_endpoint_identity("https://proxy.example.com/v1?api_key=secret")
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertNotIn("proxy.example.com/v1?api_key=secret", first)

    def test_tool_classification_follows_fixed_contract(self):
        self.assertEqual(
            self.capabilities.classify_tool_execution([]),
            {
                "detected": False,
                "attempted_tools": [],
                "side_effect_status": "none",
                "audit_complete": True,
            },
        )
        self.assertEqual(
            self.capabilities.classify_tool_execution(
                [{"event": "tool", "tool": "web_fetch", "status": "blocked"}]
            ),
            {
                "detected": True,
                "attempted_tools": ["web_fetch"],
                "side_effect_status": "blocked",
                "audit_complete": True,
            },
        )
        self.assertEqual(
            self.capabilities.classify_tool_execution(
                [{"event": "tool", "tool": "web_fetch", "status": "executed"}]
            )["side_effect_status"],
            "executed",
        )
        unknown = self.capabilities.classify_tool_execution(
            [{"event": "tool", "tool": "web_fetch", "status": "maybe"}]
        )
        self.assertEqual(unknown["side_effect_status"], "unknown")
        self.assertFalse(unknown["audit_complete"])

    def test_select_claude_load_branch_requires_explicit_canary_metadata_inventory_and_source_evidence(self):
        missing_canary = clone_json(self.fixtures["claude_marketplace"])
        missing_canary["probe_results"]["marketplace"].pop("canary_passed")
        self.assertIsNone(self.capabilities.select_claude_load_branch(missing_canary))

        missing_metadata = clone_json(self.fixtures["claude_direct"])
        missing_metadata["probe_results"]["repo_validation"]["plugin_metadata_valid"] = False
        self.assertIsNone(self.capabilities.select_claude_load_branch(missing_metadata))

        missing_inventory = clone_json(self.fixtures["claude_direct"])
        missing_inventory["probe_results"]["repo_validation"]["required_skill_inventory_valid"] = False
        self.assertIsNone(self.capabilities.select_claude_load_branch(missing_inventory))

        missing_source = clone_json(self.fixtures["claude_direct"])
        missing_source["probe_results"]["direct_plugin_dir"]["configured_checkout_match"] = False
        self.assertIsNone(self.capabilities.select_claude_load_branch(missing_source))

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

    def test_probe_from_dir_opencode_keeps_weak_paths_as_diagnostics(self):
        config = {"repo_root": str(ROOT)}
        with tempfile.TemporaryDirectory() as temp_dir:
            probe_dir = Path(temp_dir) / "opencode"
            (probe_dir / "workspace").mkdir(parents=True, exist_ok=True)
            (probe_dir / "workspace" / "opencode.json").write_text(
                json.dumps({"plugin": [str(ROOT)]}),
                encoding="utf-8",
            )
            (probe_dir / "version.txt").write_text("OpenCode 1.18.3\n", encoding="utf-8")
            (probe_dir / "debug-config.json").write_text(
                json.dumps({"plugin_path": str(ROOT)}),
                encoding="utf-8",
            )
            (probe_dir / "debug-config.status").write_text("0\n", encoding="utf-8")
            (probe_dir / "debug-paths.json").write_text(
                "config /tmp/opencode-config\nstate /tmp/opencode-state\n",
                encoding="utf-8",
            )
            (probe_dir / "debug-paths.status").write_text("0\n", encoding="utf-8")
            (probe_dir / "debug-skill.json").write_text("", encoding="utf-8")
            (probe_dir / "debug-skill.status").write_text("1\n", encoding="utf-8")
            (probe_dir / "canary.jsonl").write_text(
                json.dumps({"type": "result", "result": "RESEARCHFLOW_BOOTSTRAP_ACTIVE"}) + "\n",
                encoding="utf-8",
            )
            (probe_dir / "canary.status").write_text("0\n", encoding="utf-8")

            _, probe = self.capabilities.probe_from_dir("opencode", config, probe_dir)

        self.assertTrue(probe["workspace_plugin_matches_checkout"])
        self.assertFalse(probe["probe_results"]["debug"]["paths_source_match"])
        self.assertFalse(probe["probe_results"]["debug"]["skill_inventory_valid"])
        self.assertEqual(
            self.capabilities.select_opencode_proof_branch(probe),
            "workspace-repo-canary-proof",
        )

    def test_probe_from_dir_fail_closes_on_empty_and_malformed_native_outputs(self):
        config = {"repo_root": str(ROOT)}
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            claude_probe = temp_root / "claude"
            claude_probe.mkdir(parents=True, exist_ok=True)
            (claude_probe / "version.txt").write_text("", encoding="utf-8")
            (claude_probe / "help.txt").write_text("", encoding="utf-8")
            (claude_probe / "plugin-help.txt").write_text("", encoding="utf-8")
            (claude_probe / "marketplace-list.json").write_text("{", encoding="utf-8")
            (claude_probe / "direct-canary.jsonl").write_text("not-json\n", encoding="utf-8")
            (claude_probe / "direct-canary.status").write_text("0\n", encoding="utf-8")
            cli_version, probe = self.capabilities.probe_from_dir("claude", config, claude_probe)
            record = self.capabilities.build_capability_record("claude", cli_version, probe)
            self.assertEqual(cli_version, "unknown")
            self.assertIsNone(record["selected_load_branch"])
            self.assertIsNone(record["selected_isolation_profile"])

            opencode_probe = temp_root / "opencode"
            (opencode_probe / "workspace").mkdir(parents=True, exist_ok=True)
            (opencode_probe / "version.txt").write_text("", encoding="utf-8")
            (opencode_probe / "debug-config.json").write_text("{", encoding="utf-8")
            (opencode_probe / "debug-config.status").write_text("0\n", encoding="utf-8")
            (opencode_probe / "debug-paths.json").write_text("{", encoding="utf-8")
            (opencode_probe / "debug-paths.status").write_text("0\n", encoding="utf-8")
            (opencode_probe / "debug-skill.json").write_text("[", encoding="utf-8")
            (opencode_probe / "debug-skill.status").write_text("0\n", encoding="utf-8")
            (opencode_probe / "canary.jsonl").write_text("not-json\n", encoding="utf-8")
            (opencode_probe / "canary.status").write_text("0\n", encoding="utf-8")
            cli_version, probe = self.capabilities.probe_from_dir("opencode", config, opencode_probe)
            record = self.capabilities.build_capability_record("opencode", cli_version, probe)
            self.assertEqual(cli_version, "unknown")
            self.assertIsNone(record["selected_proof_branch"])
            self.assertIsNone(record["selected_isolation_profile"])

    def test_build_invocation_record_fail_closes_on_unrecognized_event_shapes(self):
        config = {
            "run_id": "2026-07-17T120000Z",
            "repo_commit_sha": "c" * 40,
            "timeout_seconds": 120,
            "endpoint_identity": "https://proxy.example.com/v1?token=secret",
            "claude": {
                "harness_model_value": "fable",
                "effort_or_variant": "high",
            },
        }
        capability = self.capabilities.build_capability_record("claude", "2.1.212", self.fixtures["claude_direct"])
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            events_path = temp_root / "events.jsonl"
            stderr_path = temp_root / "stderr.txt"
            events_path.write_text(json.dumps({"type": "unknown", "payload": "x"}) + "\n", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            invocation, command, final_response = self.capabilities.build_invocation_record(
                "claude",
                config,
                capability,
                "R-DIRECT-LIT",
                "2.1.212",
                events_path,
                stderr_path,
                0,
            )
        self.assertEqual(final_response, "")
        self.assertFalse(invocation["model_identity_verified"])
        self.assertEqual(invocation["tool_execution"]["side_effect_status"], "none")
        self.assertIsNone(command["resolved_model_identity"])

    def test_build_invocation_record_preserves_fixture_backed_native_event_shape(self):
        config = {
            "run_id": "2026-07-17T120000Z",
            "repo_commit_sha": "c" * 40,
            "timeout_seconds": 120,
            "endpoint_identity": "https://proxy.example.com/v1?token=secret",
            "claude": {
                "harness_model_value": "fable",
                "effort_or_variant": "high",
            },
        }
        capability = self.capabilities.build_capability_record("claude", "2.1.212", self.fixtures["claude_direct"])
        events_path = HARNESS_DIR / "fixtures" / "adapters" / "claude-direct" / "cases" / "R-DIRECT-LIT.jsonl"
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr_path = Path(temp_dir) / "stderr.txt"
            stderr_path.write_text("", encoding="utf-8")
            invocation, command, final_response = self.capabilities.build_invocation_record(
                "claude",
                config,
                capability,
                "R-DIRECT-LIT",
                "2.1.212",
                events_path,
                stderr_path,
                0,
            )
        self.assertEqual(final_response, "ResearchFlow phase: literature-discovery\n")
        self.assertEqual(invocation["resolved_model_identity"], "openai/synthetic-model")
        self.assertTrue(invocation["model_identity_verified"])
        self.assertEqual(
            invocation["tool_execution"],
            {
                "detected": False,
                "attempted_tools": [],
                "side_effect_status": "none",
                "audit_complete": True,
            },
        )
        self.assertEqual(invocation["model_resolution"]["backing_model_id"], "synthetic-model")
        self.assertEqual(invocation["model_resolution"]["proof_source"], "litellm-response-metadata")
        self.assertEqual(invocation["final_response_sha256"], self.capabilities._sha256_text(final_response))
        self.assertEqual(invocation["raw_artifact_hashes"]["events"], self.capabilities.lib.sha256_path(events_path))
        self.assertEqual(command["resolved_model_identity"], "openai/synthetic-model")
        self.assertEqual(command["tool_execution"], invocation["tool_execution"])
        self.assertEqual(command["isolation_profile"], capability["selected_isolation_profile"])
        self.assertEqual(command["plugin_proof_strength"], capability["plugin_proof_strength"])
        self.assertEqual(command["raw_artifact_hashes"], invocation["raw_artifact_hashes"])
        self.assertEqual(command["model_request"]["endpoint_identity_sha256"], invocation["model_request"]["endpoint_identity_sha256"])

    def test_build_invocation_record_accepts_result_shaped_claude_events(self):
        config = {
            "run_id": "2026-07-17T120000Z",
            "repo_commit_sha": "c" * 40,
            "timeout_seconds": 120,
            "endpoint_identity": "https://proxy.example.com/v1?token=secret",
            "claude": {
                "harness_model_value": "sonnet",
                "effort_or_variant": "high",
            },
        }
        capability = self.capabilities.build_capability_record("claude", "2.1.214", self.fixtures["claude_direct"])
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            events_path = temp_root / "events.jsonl"
            stderr_path = temp_root / "stderr.txt"
            events_path.write_text(
                json.dumps(
                    {
                        "type": "result",
                        "result": "RESEARCHFLOW_BOOTSTRAP_ACTIVE",
                        "modelUsage": {"gpt-5.4[1M]": {"inputTokens": 1, "outputTokens": 1}},
                    }
                ) + "\n",
                encoding="utf-8",
            )
            stderr_path.write_text("", encoding="utf-8")
            invocation, command, final_response = self.capabilities.build_invocation_record(
                "claude",
                config,
                capability,
                "R-DIRECT-LIT",
                "2.1.214",
                events_path,
                stderr_path,
                0,
            )
        self.assertEqual(final_response, "RESEARCHFLOW_BOOTSTRAP_ACTIVE")
        self.assertEqual(invocation["resolved_model_identity"], "openai/gpt-5.4")
        self.assertTrue(invocation["model_identity_verified"])
        self.assertEqual(invocation["model_resolution"]["backing_model_id"], "gpt-5.4")
        self.assertEqual(invocation["model_resolution"]["proof_source"], "result-model-usage")
        self.assertEqual(command["resolved_model_identity"], "openai/gpt-5.4")

    def test_canary_passed_accepts_result_shaped_events(self):
        events = [{"type": "result", "result": "RESEARCHFLOW_BOOTSTRAP_ACTIVE\nextra"}]
        self.assertTrue(self.capabilities._canary_passed(events))
        self.assertEqual(self.capabilities._response_text(events), "RESEARCHFLOW_BOOTSTRAP_ACTIVE\nextra")

    def test_extract_model_event_accepts_model_usage_keys_with_openai_prefix(self):
        event = self.capabilities._extract_model_event(
            [{"type": "result", "modelUsage": {"openai/gpt-5.4[1M]": {"inputTokens": 1}}}]
        )
        self.assertEqual(event["backing_model_id"], "gpt-5.4")
        self.assertEqual(event["resolved_model_identity"], "openai/gpt-5.4")
        self.assertEqual(event["proof_source"], "result-model-usage")

    def test_normalize_model_usage_key_strips_bracket_suffix(self):
        self.assertEqual(self.capabilities._normalize_model_usage_key("gpt-5.4[1M]"), "gpt-5.4")
        self.assertEqual(self.capabilities._normalize_model_usage_key("openai/gpt-5.4[1M]"), "gpt-5.4")

    def test_response_text_prefers_known_event_shapes_only(self):
        self.assertEqual(self.capabilities._response_text([{"type": "other", "result": "ignored"}]), "")
        self.assertEqual(self.capabilities._response_text([{"event": "response", "text": "ok"}]), "ok")
        self.assertEqual(self.capabilities._response_text([{"type": "result", "result": "ok"}]), "ok")

    def test_extract_model_event_still_fail_closes_without_model_metadata(self):
        event = self.capabilities._extract_model_event([{"type": "result", "result": "RESEARCHFLOW_BOOTSTRAP_ACTIVE"}])
        self.assertEqual(event["backing_model_id"], "unknown")
        self.assertIsNone(event["resolved_model_identity"])
        self.assertEqual(event["proof_source"], "missing-model-metadata")

    def test_canary_passed_rejects_non_marker_first_line(self):
        self.assertFalse(self.capabilities._canary_passed([{"type": "result", "result": "not-marker\nRESEARCHFLOW_BOOTSTRAP_ACTIVE"}]))

    def test_normalize_model_usage_key_preserves_plain_model_names(self):
        self.assertEqual(self.capabilities._normalize_model_usage_key("gpt-5.4"), "gpt-5.4")
        self.assertEqual(self.capabilities._normalize_model_usage_key(" openai/gpt-5.4 "), "gpt-5.4")

    def test_extract_model_event_uses_first_valid_result_model_usage_key(self):
        event = self.capabilities._extract_model_event(
            [{"type": "result", "modelUsage": {"gpt-5.4[1M]": {"inputTokens": 1}, "gpt-5.5[1M]": {"inputTokens": 1}}}]
        )
        self.assertEqual(event["backing_model_id"], "gpt-5.4")
        self.assertEqual(event["resolved_model_identity"], "openai/gpt-5.4")


if __name__ == "__main__":
    unittest.main()
