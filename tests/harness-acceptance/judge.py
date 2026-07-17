#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
_MARKER_PREFIX = "ResearchFlow phase:"
_VALID_MARKER_RE = re.compile(
    r"\AResearchFlow phase: (literature-discovery|paper-structuring|paper-drafting|paper-review|artifact-packaging)(?:\n|\Z)"
)
_EXPLANATION_PREFIX_RE = re.compile(r"^(?:#|- |\* |>|\d+\. )")


def _load_lib() -> Any:
    lib_path = HARNESS_DIR / "lib.py"
    spec = importlib.util.spec_from_file_location("harness_acceptance_lib", lib_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {lib_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lib = _load_lib()
PHASES = lib.PHASES
load_cases = lib.load_cases
validate_invocation = lib.validate_invocation
write_json = lib.write_json


def _normalize_response(response: str) -> tuple[str, list[str]]:
    normalized = response.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines), lines


def _first_line(lines: list[str]) -> str | None:
    if not lines:
        return None
    return lines[0]


def _marker_count(lines: list[str]) -> int:
    return sum(1 for line in lines if line.startswith(_MARKER_PREFIX))


def _matched_evidence(observed_phase: str | None, marker_count: int, response_sha256: str) -> dict[str, Any] | None:
    if observed_phase is None or marker_count != 1:
        return None
    text = f"{_MARKER_PREFIX} {observed_phase}"
    return {"line": 1, "sha256": response_sha256, "text": text}


def _line_1_evidence(lines: list[str], response_sha256: str) -> dict[str, Any]:
    text = _first_line(lines)
    return {
        "line": 1 if text is not None else None,
        "sha256": response_sha256,
        "text": text,
    }


def _forbidden_pattern_matches(case: dict[str, Any], response: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for pattern in case["forbidden_patterns"]:
        for matched in re.finditer(pattern, response):
            matches.append(
                {
                    "pattern": pattern,
                    "match": matched.group(0),
                    "line": response.count("\n", 0, matched.start()) + 1,
                }
            )
    return matches


def _structural_invalid(lines: list[str], marker_count: int) -> bool:
    non_empty_lines = [line for line in lines if line != ""]
    if len(non_empty_lines) < 1 or len(non_empty_lines) > 3:
        return True
    if len(non_empty_lines) != len(lines):
        return True
    if marker_count != 1:
        return True
    if not lines:
        return True
    if _VALID_MARKER_RE.match("\n".join(lines)) is None:
        return True
    for line in lines[1:]:
        if _EXPLANATION_PREFIX_RE.match(line):
            return True
        if "```" in line:
            return True
        if _MARKER_PREFIX in line:
            return True
    return False


def _observed_phase(lines: list[str], marker_count: int) -> str | None:
    if not lines or marker_count != 1:
        return None
    match = _VALID_MARKER_RE.match("\n".join(lines))
    if match is None:
        return None
    return match.group(1)


def _contamination(invocation: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if invocation["environment_contaminated"]:
        reasons.append("environment_contaminated")
    if invocation["tool_execution"]["side_effect_status"] == "blocked":
        reasons.append("tool_call_blocked")
    return {"contaminated": bool(reasons), "reasons": reasons}


def _fatal_harness_error(invocation: dict[str, Any], response_sha256: str) -> bool:
    if invocation["exit_code"] != 0:
        return True
    if invocation["timed_out"]:
        return True
    if not invocation["plugin_proof_passed"]:
        return True
    if invocation["final_response_sha256"] != response_sha256:
        return True
    tool_status = invocation["tool_execution"]["side_effect_status"]
    if tool_status in {"executed", "unknown"}:
        return True
    return False


def judge(case: dict[str, Any], invocation: dict[str, Any], response: str) -> dict[str, Any]:
    validate_invocation(invocation)
    if case["case_id"] != invocation["case_id"]:
        raise ValueError("case_id mismatch between case and invocation")

    normalized_response, lines = _normalize_response(response)
    response_sha256 = hashlib.sha256(response.encode("utf-8")).hexdigest()
    marker_count = _marker_count(lines)
    observed_phase = _observed_phase(lines, marker_count)
    matched_evidence = _matched_evidence(observed_phase, marker_count, response_sha256)
    forbidden_pattern_matches = _forbidden_pattern_matches(case, normalized_response)
    contamination = _contamination(invocation)
    structural_invalid = _structural_invalid(lines, marker_count)
    fatal_harness_error = _fatal_harness_error(invocation, response_sha256)

    if fatal_harness_error:
        verdict = "harness_error"
    elif structural_invalid:
        verdict = "fail" if forbidden_pattern_matches else "indeterminate"
    elif observed_phase != case["expected_phase"]:
        verdict = "fail"
    elif forbidden_pattern_matches:
        verdict = "fail"
    else:
        verdict = "pass"

    return {
        "case_id": case["case_id"],
        "expected_phase": case["expected_phase"],
        "verdict": verdict,
        "observed_phase": observed_phase,
        "marker_count": marker_count,
        "response_sha256": response_sha256,
        "line_1_evidence": _line_1_evidence(lines, response_sha256),
        "matched_evidence": matched_evidence,
        "forbidden_pattern_matches": forbidden_pattern_matches,
        "environment_contaminated": invocation["environment_contaminated"],
        "contamination": contamination,
        "manual_note": None,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cases = {case["case_id"]: case for case in load_cases(ROOT)}
    if args.case not in cases:
        raise KeyError(f"unknown case: {args.case}")

    invocation_path = Path(args.invocation)
    response_path = Path(args.response)
    output_path = Path(args.output)

    invocation = lib.read_json(invocation_path)
    with response_path.open("r", encoding="utf-8", newline="") as handle:
        response = handle.read()

    verdict = judge(cases[args.case], invocation, response)
    write_json(output_path, verdict)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
