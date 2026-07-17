#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
FIXTURE_DIR = HARNESS_DIR / "fixtures" / "judge"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_text_preserving_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def deep_merge(base: dict, overrides: dict) -> dict:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = load_module("harness_acceptance_lib", HARNESS_DIR / "lib.py")
        cls.judge_module = load_module("harness_acceptance_judge", HARNESS_DIR / "judge.py")
        cls.cases = {case["case_id"]: case for case in cls.lib.load_cases(ROOT)}
        cls.base_invocation = json.loads((FIXTURE_DIR / "base-invocation.json").read_text(encoding="utf-8"))
        cls.scenarios = json.loads((FIXTURE_DIR / "scenarios.json").read_text(encoding="utf-8"))

    def build_invocation(self, scenario: dict, response: str) -> dict:
        invocation = copy.deepcopy(self.base_invocation)
        invocation["case_id"] = scenario["case_id"]
        if "invocation_overrides" in scenario:
            deep_merge(invocation, scenario["invocation_overrides"])
        invocation["final_response_sha256"] = hashlib.sha256(response.encode("utf-8")).hexdigest()
        return invocation

    def test_synthetic_matrix(self):
        for scenario in self.scenarios:
            with self.subTest(name=scenario["name"]):
                case = self.cases[scenario["case_id"]]
                response_path = FIXTURE_DIR / scenario["response_file"]
                response = read_text_preserving_newlines(response_path)
                invocation = self.build_invocation(scenario, response)

                verdict = self.judge_module.judge(case, invocation, response)
                expected = scenario["expected"]
                response_sha256 = hashlib.sha256(response.encode("utf-8")).hexdigest()
                normalized = response.replace("\r\n", "\n").replace("\r", "\n")
                first_line = normalized.split("\n", 1)[0] if normalized else None
                matched_expected = (
                    expected["marker_count"] == 1
                    and expected["observed_phase"] is not None
                    and first_line == f"ResearchFlow phase: {expected['observed_phase']}"
                    and scenario["name"] not in {"marker-non-first", "illegal-phase-id"}
                )

                self.assertEqual(verdict["case_id"], case["case_id"])
                self.assertEqual(verdict["expected_phase"], case["expected_phase"])
                self.assertEqual(verdict["verdict"], expected["verdict"])
                self.assertEqual(verdict["observed_phase"], expected["observed_phase"])
                self.assertEqual(verdict["marker_count"], expected["marker_count"])
                self.assertEqual(verdict["response_sha256"], response_sha256)
                self.assertEqual(
                    verdict["line_1_evidence"],
                    {
                        "line": 1 if first_line is not None else None,
                        "sha256": response_sha256,
                        "text": first_line,
                    },
                )
                self.assertEqual(len(verdict["forbidden_pattern_matches"]), expected["forbidden_match_count"])
                self.assertEqual(verdict["environment_contaminated"], expected["environment_contaminated"])
                self.assertEqual(verdict["contamination"]["contaminated"], expected["contaminated"])
                self.assertEqual(verdict["contamination"]["reasons"], expected["contamination_reasons"])
                self.assertIsNone(verdict["manual_note"])

                if matched_expected:
                    self.assertEqual(
                        verdict["matched_evidence"],
                        {
                            "line": 1,
                            "sha256": response_sha256,
                            "text": first_line,
                        },
                    )
                else:
                    self.assertIsNone(verdict["matched_evidence"])

    def test_structural_invalidity_precedes_wrong_marker(self):
        case = self.cases["R-DIRECT-LIT"]
        response = "ResearchFlow phase: paper-review\n- Invalid explanation formatting\n"
        invocation = self.build_invocation({"case_id": "R-DIRECT-LIT"}, response)

        verdict = self.judge_module.judge(case, invocation, response)

        self.assertEqual(verdict["observed_phase"], "paper-review")
        self.assertEqual(verdict["verdict"], "indeterminate")

    def test_forbidden_match_overrides_structural_invalidity(self):
        case = self.cases["R-BACK-INTRO"]
        response = "ResearchFlow phase: literature-discovery\n# Invalid heading\nHere is the drafted introduction section\n"
        invocation = self.build_invocation({"case_id": "R-BACK-INTRO"}, response)

        verdict = self.judge_module.judge(case, invocation, response)

        self.assertEqual(verdict["observed_phase"], "literature-discovery")
        self.assertEqual(verdict["verdict"], "fail")
        self.assertEqual(len(verdict["forbidden_pattern_matches"]), 1)

    def test_blocked_tool_without_complete_audit_is_harness_error(self):
        case = self.cases["R-DIRECT-LIT"]
        response = read_text_preserving_newlines(FIXTURE_DIR / "responses" / "correct-marker.txt")
        invocation = self.build_invocation(
            {
                "case_id": "R-DIRECT-LIT",
                "invocation_overrides": {
                    "tool_execution": {
                        "detected": True,
                        "attempted_tools": ["web_fetch"],
                        "side_effect_status": "blocked",
                        "audit_complete": False,
                    }
                },
            },
            response,
        )

        verdict = self.judge_module.judge(case, invocation, response)

        self.assertEqual(verdict["observed_phase"], "literature-discovery")
        self.assertEqual(verdict["verdict"], "harness_error")
        self.assertFalse(verdict["contamination"]["contaminated"])
        self.assertEqual(verdict["contamination"]["reasons"], [])

    def test_cli_writes_verdict_json_and_refuses_overwrite(self):
        scenario = next(item for item in self.scenarios if item["name"] == "correct-marker")
        response = read_text_preserving_newlines(FIXTURE_DIR / scenario["response_file"])
        invocation = self.build_invocation(scenario, response)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invocation_path = temp_path / "invocation.json"
            response_path = temp_path / "response.txt"
            output_path = temp_path / "verdict.json"
            invocation_path.write_text(json.dumps(invocation, indent=2) + "\n", encoding="utf-8")
            with response_path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(response)

            command = [
                sys.executable,
                "judge.py",
                "--case",
                scenario["case_id"],
                "--invocation",
                str(invocation_path),
                "--response",
                str(response_path),
                "--output",
                str(output_path),
            ]
            first = subprocess.run(command, cwd=HARNESS_DIR, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            verdict = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(verdict["verdict"], "pass")
            self.assertEqual(verdict["observed_phase"], "literature-discovery")

            second = subprocess.run(command, cwd=HARNESS_DIR, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn(str(output_path), second.stderr)


if __name__ == "__main__":
    unittest.main()
