#!/usr/bin/env python3
import importlib.util
import json
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

    def test_select_opencode_proof_branch_supports_strong_fallback_and_unsupported(self):
        self.assertEqual(
            self.capabilities.select_opencode_proof_branch(self.fixtures["opencode_strong"]),
            "strong-runtime-proof",
        )
        self.assertEqual(
            self.capabilities.select_opencode_proof_branch(self.fixtures["opencode_fallback"]),
            "fallback-workspace-proof",
        )
        self.assertIsNone(self.capabilities.select_opencode_proof_branch(self.fixtures["opencode_unsupported"]))

    def test_select_isolation_profile_keeps_profile_ids_consistent(self):
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
            "workspace-config-static-proof",
        )
        self.assertIsNone(self.capabilities.select_isolation_profile(self.fixtures["opencode_unsupported"]))

    def test_build_capability_record_discloses_optional_claude_validation(self):
        probe = read_json(FIXTURE_DIR / "claude-direct.json")
        probe["probe_results"]["cli_validation"] = {"supported": True, "passed": True}
        record = self.capabilities.build_capability_record("claude", "2.1.212", probe)
        self.assertEqual(record["selected_load_branch"], "direct-plugin-dir")
        self.assertEqual(record["plugin_load_path"], "direct-plugin-dir")
        self.assertEqual(record["plugin_proof_strength"], "best_available_source_plus_canary")
        self.assertTrue(record["optional_cli_validation"])
        self.assertEqual(record["selected_isolation_profile"], "auth-preserving-direct-plugin-dir")

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


if __name__ == "__main__":
    unittest.main()
