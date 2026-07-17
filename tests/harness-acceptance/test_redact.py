#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
FIXTURE_DIR = HARNESS_DIR / "fixtures" / "redaction"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RedactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.redact = load_module("harness_acceptance_redact", HARNESS_DIR / "redact.py")

    def test_scan_text_detects_sensitive_patterns_private_fragments_and_absolute_paths(self):
        clean_text = (FIXTURE_DIR / "clean-hashes.txt").read_text(encoding="utf-8")
        self.assertEqual(self.redact.scan_text(clean_text, None), [])

        home_text = (FIXTURE_DIR / "home-path.txt").read_text(encoding="utf-8")
        absolute_text = (FIXTURE_DIR / "absolute-path.txt").read_text(encoding="utf-8")
        repo_absolute_text = (FIXTURE_DIR / "repo-absolute-path.txt").read_text(encoding="utf-8")
        private_text = (FIXTURE_DIR / "private-instruction-fragment.txt").read_text(encoding="utf-8")
        base_url_text = (FIXTURE_DIR / "base-url.txt").read_text(encoding="utf-8")
        auth_text = (FIXTURE_DIR / "auth-credential.txt").read_text(encoding="utf-8")

        home_hits = self.redact.scan_text(home_text, None)
        absolute_hits = self.redact.scan_text(absolute_text, None)
        repo_hits = self.redact.scan_text(
            repo_absolute_text,
            None,
            committed_roots=[Path("/tmp/committed-tree")],
        )
        private_hits = self.redact.scan_text(private_text, None)
        base_url_hits = self.redact.scan_text(base_url_text, None)
        auth_hits = self.redact.scan_text(auth_text, None)

        self.assertEqual([item["rule"] for item in home_hits], ["home_path"])
        self.assertEqual([item["rule"] for item in absolute_hits], ["absolute_path"])
        self.assertEqual([item["rule"] for item in repo_hits], ["repo_absolute_path"])
        self.assertEqual(
            [item["rule"] for item in private_hits],
            ["private_instruction_fragment", "private_instruction_fragment"],
        )
        self.assertEqual([item["rule"] for item in base_url_hits], ["base_url"])
        self.assertEqual(
            [item["rule"] for item in auth_hits],
            ["authorization_header", "bearer_token", "api_key_field", "token_literal", "api_key_field"],
        )

    def test_scan_text_matches_explicit_forbidden_home(self):
        text = "workspace root: /private/tmp/live-harness-home/session.txt\n"
        hits = self.redact.scan_text(text, "/private/tmp/live-harness-home")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["rule"], "forbidden_home")
        self.assertEqual(hits[0]["line"], 1)
        self.assertEqual(hits[0]["column"], 17)

    def test_scan_text_allows_explicit_safe_absolute_patterns(self):
        text = "python: /opt/homebrew/bin/python3\n"
        self.assertEqual(
            self.redact.scan_text(
                text,
                None,
                allowed_absolute_patterns=[r"^/opt/homebrew/bin/python3$"],
            ),
            [],
        )

    def test_cli_fails_closed_without_editing_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tree = Path(temp_dir)
            evidence_path = tree / "evidence.json"
            evidence_text = (FIXTURE_DIR / "auth-credential.txt").read_text(encoding="utf-8")
            evidence_path.write_text(evidence_text, encoding="utf-8")
            command = [
                sys.executable,
                str(HARNESS_DIR / "redact.py"),
                "--tree",
                str(tree),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(evidence_path.read_text(encoding="utf-8"), evidence_text)
            hits = json.loads(result.stdout)
            self.assertEqual(hits[0]["path"], "evidence.json")
            self.assertEqual(hits[0]["rule"], "authorization_header")

    def test_cli_allowlist_suppresses_safe_absolute_pattern(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tree = Path(temp_dir)
            evidence_path = tree / "evidence.txt"
            evidence_text = "python: /opt/homebrew/bin/python3\n"
            evidence_path.write_text(evidence_text, encoding="utf-8")
            blocked = subprocess.run(
                [
                    sys.executable,
                    str(HARNESS_DIR / "redact.py"),
                    "--tree",
                    str(tree),
                ],
                capture_output=True,
                text=True,
            )
            allowed = subprocess.run(
                [
                    sys.executable,
                    str(HARNESS_DIR / "redact.py"),
                    "--tree",
                    str(tree),
                    "--allow-absolute-pattern",
                    r"^/opt/homebrew/bin/python3$",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(blocked.returncode, 1)
            self.assertEqual(json.loads(blocked.stdout)[0]["rule"], "absolute_path")
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertEqual(evidence_path.read_text(encoding="utf-8"), evidence_text)


if __name__ == "__main__":
    unittest.main()
