#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
ADAPTER_FIXTURE_DIR = HARNESS_DIR / "fixtures" / "adapters"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class AdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = load_module("harness_acceptance_lib", HARNESS_DIR / "lib.py")
        cls.capabilities = load_module("harness_acceptance_capabilities", HARNESS_DIR / "capabilities.py")
        cls.claude_adapter = HARNESS_DIR / "adapters" / "claude.sh"
        cls.opencode_adapter = HARNESS_DIR / "adapters" / "opencode.sh"
        cls.fake_claude = ADAPTER_FIXTURE_DIR / "fake-claude.sh"
        cls.fake_opencode = ADAPTER_FIXTURE_DIR / "fake-opencode.sh"

    def clone_scenario(self, temp_root: Path, scenario_name: str) -> Path:
        source = ADAPTER_FIXTURE_DIR / scenario_name
        target = temp_root / f"{scenario_name}-clone"
        shutil.copytree(source, target)
        return target

    def make_config(
        self,
        temp_root: Path,
        scenario_name: str,
        harness: str,
        *,
        scenario_dir: Optional[Path] = None,
        repo_root: Optional[Path] = None,
    ) -> Path:
        raw_dir = temp_root / "raw"
        output_dir = temp_root / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        effective_repo_root = repo_root or ROOT
        config = {
            "run_id": "2026-07-17T120000Z",
            "repo_root": str(effective_repo_root),
            "repo_commit_sha": "c" * 40,
            "timeout_seconds": 120,
            "endpoint_identity": "https://proxy.example.com/v1?token=secret",
            "plugin_source_id": "researchflow-checkout",
            "residual_categories": ["auth", "admin-policy"],
            "raw_dir": str(raw_dir),
            "claude": {
                "cli_bin": str(self.fake_claude),
                "harness_model_value": "fable",
                "effort_or_variant": "high",
            },
            "opencode": {
                "cli_bin": str(self.fake_opencode),
                "harness_model_value": "openai/synthetic-model",
                "effort_or_variant": "high",
            },
        }
        config_path = temp_root / f"{harness}-config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return config_path

    def run_adapter(
        self,
        script: Path,
        mode: str,
        config_path: Path,
        output_dir: Path,
        case_id: Optional[str] = None,
        scenario_dir: Optional[Path] = None,
    ):
        command = ["bash", str(script), "--mode", mode, "--config", str(config_path), "--output-dir", str(output_dir)]
        if case_id is not None:
            command.extend(["--case-id", case_id])
        env = os.environ.copy()
        env["ECC_GATEGUARD"] = "off"
        if scenario_dir is not None:
            if script == self.claude_adapter:
                env["FAKE_CLAUDE_SCENARIO_DIR"] = str(scenario_dir)
            if script == self.opencode_adapter:
                env["FAKE_OPENCODE_SCENARIO_DIR"] = str(scenario_dir)
        return subprocess.run(command, capture_output=True, text=True, env=env)

    def test_make_config_does_not_embed_test_only_scenario_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            config_path = self.make_config(temp_root, "claude-direct", "claude", scenario_dir=scenario_dir)
            payload = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertNotIn("scenario_dir", payload["claude"])
            self.assertNotIn("scenario_dir", payload["opencode"])

    def test_claude_capability_mode_writes_direct_profile_and_validation_flag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            config_path = self.make_config(temp_root, "claude-direct", "claude")
            output_dir = temp_root / "capabilities"
            result = self.run_adapter(self.claude_adapter, "capability", config_path, output_dir, scenario_dir=scenario_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            capability = read_json(output_dir / "claude.json")
            self.assertEqual(capability["selected_load_branch"], "direct-plugin-dir")
            self.assertEqual(capability["selected_isolation_profile"], "auth-preserving-direct-plugin-dir")
            self.assertEqual(capability["plugin_proof_strength"], "best_available_source_plus_canary")
            self.assertTrue(capability["optional_cli_validation"])
            self.assertNotIn("https://proxy.example.com", json.dumps(capability))

    def test_claude_capability_mode_supports_marketplace_branch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-marketplace")
            config_path = self.make_config(temp_root, "claude-marketplace", "claude")
            output_dir = temp_root / "capabilities"
            result = self.run_adapter(self.claude_adapter, "capability", config_path, output_dir, scenario_dir=scenario_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            capability = read_json(output_dir / "claude.json")
            self.assertEqual(capability["selected_load_branch"], "local-marketplace")
            self.assertEqual(capability["selected_isolation_profile"], "auth-preserving-marketplace")

    def test_opencode_capability_mode_supports_strong_and_fallback_profiles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            strong_scenario_dir = self.clone_scenario(temp_root / "strong", "opencode-strong")
            strong_config = self.make_config(temp_root / "strong", "opencode-strong", "opencode")
            strong_output = temp_root / "strong-capabilities"
            strong_result = self.run_adapter(
                self.opencode_adapter,
                "capability",
                strong_config,
                strong_output,
                scenario_dir=strong_scenario_dir,
            )
            self.assertEqual(strong_result.returncode, 0, strong_result.stderr)
            strong_capability = read_json(strong_output / "opencode.json")
            self.assertEqual(strong_capability["selected_proof_branch"], "strong-runtime-proof")
            self.assertEqual(strong_capability["selected_isolation_profile"], "workspace-config-runtime-proof")
            self.assertEqual(strong_capability["plugin_proof_strength"], "resolved_runtime_source_inventory_canary")

            fallback_scenario_dir = self.clone_scenario(temp_root / "fallback", "opencode-fallback")
            fallback_config = self.make_config(temp_root / "fallback", "opencode-fallback", "opencode")
            fallback_output = temp_root / "fallback-capabilities"
            fallback_result = self.run_adapter(
                self.opencode_adapter,
                "capability",
                fallback_config,
                fallback_output,
                scenario_dir=fallback_scenario_dir,
            )
            self.assertEqual(fallback_result.returncode, 0, fallback_result.stderr)
            fallback_capability = read_json(fallback_output / "opencode.json")
            self.assertEqual(fallback_capability["selected_proof_branch"], "fallback-workspace-proof")
            self.assertEqual(fallback_capability["selected_isolation_profile"], "workspace-config-static-proof")
            self.assertEqual(fallback_capability["plugin_proof_strength"], "workspace_config_static_inventory_canary")

    def test_preflight_mode_writes_redacted_model_proof(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "opencode-strong")
            config_path = self.make_config(temp_root, "opencode-strong", "opencode")
            output_dir = temp_root / "preflight"
            result = self.run_adapter(self.opencode_adapter, "preflight", config_path, output_dir, scenario_dir=scenario_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            preflight = read_json(output_dir / "opencode.json")
            model_proof = read_json(output_dir / "opencode-model-proof.json")
            self.assertEqual(preflight["status"], "pass")
            self.assertEqual(preflight["isolation_profile"], "workspace-config-runtime-proof")
            self.assertTrue(model_proof["verified"])
            self.assertEqual(
                model_proof["endpoint_identity_sha256"],
                self.capabilities.hash_endpoint_identity("https://proxy.example.com/v1?token=secret"),
            )
            self.assertNotIn("https://proxy.example.com", json.dumps(model_proof))

    def test_case_mode_writes_normalized_invocation_and_keeps_raw_artifacts_local(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            config_path = self.make_config(temp_root, "claude-direct", "claude")
            output_dir = temp_root / "claude-case"
            result = self.run_adapter(
                self.claude_adapter,
                "case",
                config_path,
                output_dir,
                case_id="R-DIRECT-LIT",
                scenario_dir=scenario_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            invocation = read_json(output_dir / "invocation.json")
            command = read_json(output_dir / "command.json")
            response_text = (output_dir / "final-response.txt").read_text(encoding="utf-8")
            self.lib.validate_invocation(invocation)
            self.assertEqual(invocation["isolation_profile"], "auth-preserving-direct-plugin-dir")
            self.assertEqual(invocation["plugin_proof_strength"], "best_available_source_plus_canary")
            self.assertEqual(invocation["tool_execution"]["side_effect_status"], "none")
            self.assertEqual(command["raw_artifact_hashes"], invocation["raw_artifact_hashes"])
            self.assertEqual(invocation["final_response_sha256"], hashlib.sha256(response_text.encode("utf-8")).hexdigest())
            raw_dir = temp_root / "raw"
            self.assertTrue(any(path.name == "events.jsonl" for path in raw_dir.rglob("events.jsonl")))
            self.assertFalse(any(path.name == "events.jsonl" for path in output_dir.rglob("events.jsonl")))
            serialized = json.dumps({"invocation": invocation, "command": command})
            self.assertNotIn("https://proxy.example.com", serialized)
            self.assertNotIn("token=secret", serialized)

    def test_case_mode_classifies_blocked_tools_for_opencode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "opencode-fallback")
            config_path = self.make_config(temp_root, "opencode-fallback", "opencode")
            output_dir = temp_root / "opencode-case"
            result = self.run_adapter(
                self.opencode_adapter,
                "case",
                config_path,
                output_dir,
                case_id="R-DIRECT-LIT",
                scenario_dir=scenario_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            invocation = read_json(output_dir / "invocation.json")
            self.assertEqual(invocation["isolation_profile"], "workspace-config-static-proof")
            self.assertEqual(invocation["tool_execution"]["attempted_tools"], ["web_fetch"])
            self.assertEqual(invocation["tool_execution"]["side_effect_status"], "blocked")
            self.assertTrue(invocation["tool_execution"]["audit_complete"])

    def test_case_mode_appends_shared_suffix_for_both_harnesses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            case_prompt = next(
                item["prompt"]
                for item in read_json(HARNESS_DIR / "cases.json")
                if item["case_id"] == "R-DIRECT-LIT"
            )
            scored_prompt = (HARNESS_DIR / "scored-prompt.txt").read_text(encoding="utf-8")
            expected_prompt = f"{case_prompt}\n\n{scored_prompt}"

            cases = [
                ("claude", self.claude_adapter, "claude-direct"),
                ("opencode", self.opencode_adapter, "opencode-strong"),
            ]
            for harness, script, scenario_name in cases:
                scenario_dir = self.clone_scenario(temp_root / harness, scenario_name)
                config_path = self.make_config(temp_root / harness, scenario_name, harness, scenario_dir=scenario_dir)
                output_dir = temp_root / harness / "case"
                result = self.run_adapter(
                    script,
                    "case",
                    config_path,
                    output_dir,
                    case_id="R-DIRECT-LIT",
                    scenario_dir=scenario_dir,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                captured_prompt = (scenario_dir / "last-prompt.txt").read_text(encoding="utf-8")
                self.assertEqual(captured_prompt, expected_prompt)

    def test_claude_case_mode_runs_in_fresh_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            config_path = self.make_config(temp_root, "claude-direct", "claude", scenario_dir=scenario_dir)
            output_dir = temp_root / "claude-case"
            result = self.run_adapter(
                self.claude_adapter,
                "case",
                config_path,
                output_dir,
                case_id="R-DIRECT-LIT",
                scenario_dir=scenario_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            cwd = Path((scenario_dir / "last-cwd.txt").read_text(encoding="utf-8").strip()).resolve()
            raw_workspaces = list((temp_root / "raw").glob("claude-case-R-DIRECT-LIT.*/workspace"))
            self.assertEqual(len(raw_workspaces), 1)
            self.assertEqual(cwd, raw_workspaces[0].resolve())

    def test_case_mode_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            config_path = self.make_config(temp_root, "claude-direct", "claude")
            output_dir = temp_root / "claude-case"
            first = self.run_adapter(
                self.claude_adapter,
                "case",
                config_path,
                output_dir,
                case_id="R-DIRECT-LIT",
                scenario_dir=scenario_dir,
            )
            second = self.run_adapter(
                self.claude_adapter,
                "case",
                config_path,
                output_dir,
                case_id="R-DIRECT-LIT",
                scenario_dir=scenario_dir,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("final-response.txt", second.stderr)

    def test_capability_mode_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            config_path = self.make_config(temp_root, "claude-direct", "claude")
            output_dir = temp_root / "capabilities"
            first = self.run_adapter(self.claude_adapter, "capability", config_path, output_dir, scenario_dir=scenario_dir)
            second = self.run_adapter(self.claude_adapter, "capability", config_path, output_dir, scenario_dir=scenario_dir)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("claude.json", second.stderr)

    def test_preflight_mode_refuses_overwrite_before_partial_bundle_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "opencode-strong")
            config_path = self.make_config(temp_root, "opencode-strong", "opencode")
            output_dir = temp_root / "preflight"
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "opencode-model-proof.json").write_text("{}\n", encoding="utf-8")
            result = self.run_adapter(self.opencode_adapter, "preflight", config_path, output_dir, scenario_dir=scenario_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("opencode-model-proof.json", result.stderr)
            self.assertFalse((output_dir / "opencode.json").exists())

    def test_capability_mode_fail_closes_on_empty_and_malformed_probe_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            scenario_dir = self.clone_scenario(temp_root, "claude-direct")
            (scenario_dir / "version.txt").write_text("", encoding="utf-8")
            (scenario_dir / "help.txt").write_text("", encoding="utf-8")
            (scenario_dir / "marketplace-list-template.json").write_text("{", encoding="utf-8")
            config_path = self.make_config(temp_root, "claude-direct", "claude", scenario_dir=scenario_dir)
            output_dir = temp_root / "capabilities"
            result = self.run_adapter(self.claude_adapter, "capability", config_path, output_dir, scenario_dir=scenario_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            capability = read_json(output_dir / "claude.json")
            self.assertEqual(capability["cli_version"], "unknown")
            self.assertIsNone(capability["selected_load_branch"])
            self.assertIsNone(capability["selected_isolation_profile"])

    def test_capability_mode_blocks_invalid_repo_validation_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            invalid_repo = temp_root / "invalid-repo"
            invalid_repo.mkdir(parents=True, exist_ok=True)

            claude_scenario_dir = self.clone_scenario(temp_root / "claude", "claude-direct")
            claude_config = self.make_config(temp_root / "claude", "claude-direct", "claude", repo_root=invalid_repo)
            claude_output = temp_root / "claude-capabilities"
            claude_result = self.run_adapter(
                self.claude_adapter,
                "capability",
                claude_config,
                claude_output,
                scenario_dir=claude_scenario_dir,
            )
            self.assertEqual(claude_result.returncode, 0, claude_result.stderr)
            claude_capability = read_json(claude_output / "claude.json")
            self.assertIsNone(claude_capability["selected_load_branch"])
            self.assertIsNone(claude_capability["selected_isolation_profile"])

            opencode_scenario_dir = self.clone_scenario(temp_root / "opencode", "opencode-strong")
            opencode_config = self.make_config(temp_root / "opencode", "opencode-strong", "opencode", repo_root=invalid_repo)
            opencode_output = temp_root / "opencode-capabilities"
            opencode_result = self.run_adapter(
                self.opencode_adapter,
                "capability",
                opencode_config,
                opencode_output,
                scenario_dir=opencode_scenario_dir,
            )
            self.assertEqual(opencode_result.returncode, 0, opencode_result.stderr)
            opencode_capability = read_json(opencode_output / "opencode.json")
            self.assertIsNone(opencode_capability["selected_proof_branch"])
            self.assertIsNone(opencode_capability["selected_isolation_profile"])


if __name__ == "__main__":
    unittest.main()
