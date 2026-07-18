#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
HARNESS_DIR = Path(os.environ.get("HARNESS_ACCEPTANCE_DIR", str(DEFAULT_HARNESS_DIR)))
HARNESSES = ("claude", "opencode")
CASES_PER_HARNESS = 7
ATTEMPTED_STATUSES = ("pass", "fail", "indeterminate", "harness_error")
PREFLIGHT_STATUSES = ("pass", "blocked")


def _load_lib() -> Any:
    lib_path = DEFAULT_HARNESS_DIR / "lib.py"
    spec = importlib.util.spec_from_file_location("harness_acceptance_lib", lib_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {lib_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_preflight() -> Any:
    preflight_path = DEFAULT_HARNESS_DIR / "preflight.py"
    spec = importlib.util.spec_from_file_location("harness_acceptance_preflight", preflight_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {preflight_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lib = _load_lib()
preflight_contract = _load_preflight()
load_cases = lib.load_cases
read_json = lib.read_json
validate_invocation = lib.validate_invocation
write_json = lib.write_json
REASON_CODES = set(lib.REASON_CODES)
VERDICTS = set(lib.VERDICTS)
_SHA256_RE = getattr(lib, "_SHA256_RE")


def _read_json(path: Path) -> dict[str, Any]:
    return read_json(path)


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _require_sha256(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if _SHA256_RE.fullmatch(text) is None:
        raise ValueError(f"{label} must be lowercase 64-character hex")
    return text


def _inspect_model_proof(value: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]:
    return lib.inspect_model_proof(value, identities)


def validate_model_proof(value: dict[str, Any], identities: dict[str, Any]) -> Optional[str]:
    inspected = _inspect_model_proof(value, identities)
    canonical_identity = inspected["canonical_identity"]
    if isinstance(canonical_identity, str):
        return canonical_identity
    return None


def _read_environment(run_dir: Path) -> dict[str, Any]:
    value = _read_json(run_dir / "environment.json")
    _require_string(value.get("run_id"), "environment.run_id")
    _require_string(value.get("run_kind"), "environment.run_kind")
    _require_bool(value.get("redaction_passed"), "environment.redaction_passed")
    raw_artifacts = value.get("raw_artifacts")
    if not isinstance(raw_artifacts, dict):
        raise ValueError("environment.raw_artifacts must be an object")
    _require_string(raw_artifacts.get("relative_id"), "environment.raw_artifacts.relative_id")
    _require_sha256(raw_artifacts.get("sha256"), "environment.raw_artifacts.sha256")
    _require_string(raw_artifacts.get("manual_review_status"), "environment.raw_artifacts.manual_review_status")
    _require_string(raw_artifacts.get("reason_not_committed"), "environment.raw_artifacts.reason_not_committed")
    for field in ("manual_notes", "deviations"):
        value_field = value.get(field)
        if not isinstance(value_field, list) or not all(isinstance(item, str) for item in value_field):
            raise ValueError(f"environment.{field} must be a list of strings")
    return value


def _derive_gate_preflight_status(raw_status: str, evaluated_preflight: dict[str, Any]) -> str:
    if raw_status != "pass":
        return "blocked"
    if not evaluated_preflight.get("proof_valid"):
        return "blocked"
    required_fields = (
        evaluated_preflight.get("plugin_source_id"),
        evaluated_preflight.get("plugin_proof_strength"),
        evaluated_preflight.get("isolation_profile"),
    )
    if not all(isinstance(value, str) and value for value in required_fields):
        return "blocked"
    return "pass"


def _read_harness_state(run_dir: Path, harness: str, identities: dict[str, Any]) -> dict[str, Any]:
    capability = _read_json(run_dir / "capabilities" / f"{harness}.json")
    preflight = _read_json(run_dir / "preflight" / f"{harness}.json")
    model_proof = _read_json(run_dir / "preflight" / f"{harness}-model-proof.json")
    raw_preflight_status = _require_string(preflight.get("status"), f"preflight.{harness}.status")
    if raw_preflight_status not in PREFLIGHT_STATUSES:
        raise ValueError(f"preflight.{harness}.status must be one of {PREFLIGHT_STATUSES}")
    evaluated_preflight = preflight_contract.evaluate_preflight(capability, preflight, model_proof, identities)
    plugin_proof_strength = evaluated_preflight.get("plugin_proof_strength")
    isolation_profile = evaluated_preflight.get("isolation_profile")
    preflight_plugin_source_id = evaluated_preflight.get("plugin_source_id")
    if not isinstance(plugin_proof_strength, str) or not plugin_proof_strength:
        raise ValueError(f"{harness} plugin_proof_strength missing")
    if not isinstance(isolation_profile, str) or not isolation_profile:
        raise ValueError(f"{harness} isolation_profile missing")
    if preflight_plugin_source_id is not None:
        preflight_plugin_source_id = _require_string(preflight_plugin_source_id, f"preflight.{harness}.plugin_source_id")
    gate_preflight_status = _derive_gate_preflight_status(raw_preflight_status, evaluated_preflight)
    return {
        "capability": capability,
        "preflight": preflight,
        "evaluated_preflight": evaluated_preflight,
        "preflight_status": gate_preflight_status,
        "plugin_proof_strength": plugin_proof_strength,
        "isolation_profile": isolation_profile,
        "preflight_plugin_source_id": preflight_plugin_source_id,
        "model_proof": model_proof,
        "validated_identity": evaluated_preflight["canonical_identity"],
        "proof_identity": evaluated_preflight["proof_identity"],
        "proof_valid": evaluated_preflight["proof_valid"],
        "backing_model_id": evaluated_preflight["backing_model_id"],
        "allowlist_missing": evaluated_preflight["allowlist_missing"],
    }


def _read_attempted_cases(run_dir: Path, harness: str) -> dict[str, dict[str, Any]]:
    harness_dir = run_dir / harness
    attempted: dict[str, dict[str, Any]] = {}
    if not harness_dir.exists():
        return attempted
    for case_dir in sorted(path for path in harness_dir.iterdir() if path.is_dir()):
        invocation_path = case_dir / "invocation.json"
        verdict_path = case_dir / "verdict.json"
        response_path = case_dir / "final-response.txt"
        if not invocation_path.exists() or not verdict_path.exists() or not response_path.exists():
            raise ValueError(f"incomplete attempted case artifact: {case_dir}")
        invocation = _read_json(invocation_path)
        validate_invocation(invocation)
        verdict = _read_json(verdict_path)
        verdict_case_id = _require_string(verdict.get("case_id"), f"{verdict_path}.case_id")
        verdict_status = _require_string(verdict.get("verdict"), f"{verdict_path}.verdict")
        if verdict_status not in VERDICTS:
            raise ValueError(f"unknown verdict status: {verdict_status}")
        if case_dir.name != verdict_case_id:
            raise ValueError(f"case directory {case_dir.name} does not match verdict case_id {verdict_case_id}")
        if invocation.get("case_id") != verdict_case_id:
            raise ValueError(f"invocation/verdict case_id mismatch in {case_dir}")
        if invocation.get("harness") != harness:
            raise ValueError(f"invocation harness mismatch in {case_dir}")
        response_text = response_path.read_text(encoding="utf-8")
        response_sha256 = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
        if invocation.get("final_response_sha256") != response_sha256:
            raise ValueError(f"final response sha mismatch in {case_dir}")
        if verdict.get("response_sha256") != response_sha256:
            raise ValueError(f"verdict response sha mismatch in {case_dir}")
        if verdict_case_id in attempted:
            raise ValueError(f"duplicate case artifact for {harness}/{verdict_case_id}")
        plugin_source_id = _require_string(invocation.get("plugin_source_id"), f"{invocation_path}.plugin_source_id")
        contamination = verdict.get("contamination")
        contaminated = False
        contamination_reasons: list[str] = []
        if isinstance(contamination, dict):
            contaminated = bool(contamination.get("contaminated"))
            reasons = contamination.get("reasons", [])
            if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
                raise ValueError(f"invalid contamination reasons in {case_dir}")
            contamination_reasons = reasons
        elif verdict.get("environment_contaminated"):
            contaminated = True
            contamination_reasons = ["environment_contaminated"]
        attempted[verdict_case_id] = {
            "harness": harness,
            "case_id": verdict_case_id,
            "status": verdict_status,
            "observed_phase": verdict.get("observed_phase"),
            "response_sha256": response_sha256,
            "plugin_source_id": plugin_source_id,
            "contaminated": contaminated,
            "contamination_reasons": contamination_reasons,
        }
    return attempted


def _alignment_reason(states: dict[str, dict[str, Any]]) -> tuple[bool, Optional[str], str]:
    alignment = preflight_contract.evaluate_model_alignment(
        states["claude"]["evaluated_preflight"],
        states["opencode"]["evaluated_preflight"],
    )
    if alignment["aligned"]:
        return True, alignment["canonical_identity"], "aligned"
    return False, None, alignment["reason_code"]


def _validate_prefix(case_order: list[str], attempted: dict[str, dict[str, Any]], harness: str) -> int:
    prefix_len = 0
    missing_seen = False
    harness_error_seen = False
    for case_id in case_order:
        present = case_id in attempted
        if present and missing_seen:
            raise ValueError(f"{harness} attempted cases must form a manifest prefix")
        if present:
            if harness_error_seen:
                raise ValueError(f"{harness} attempted case artifact appears after harness_error: {case_id}")
            prefix_len += 1
            if attempted[case_id]["status"] == "harness_error":
                harness_error_seen = True
        else:
            missing_seen = True
    extras = set(attempted) - set(case_order)
    if extras:
        raise ValueError(f"unexpected case artifact(s) for {harness}: {sorted(extras)}")
    return prefix_len


def _resolve_plugin_source_id(harness: str, attempted: dict[str, dict[str, Any]], state: dict[str, Any]) -> str:
    preflight_source_id = state.get("preflight_plugin_source_id")
    attempted_source_ids = {row["plugin_source_id"] for row in attempted.values()}
    if len(attempted_source_ids) > 1:
        raise ValueError(f"conflicting plugin_source_id values for {harness}: {sorted(attempted_source_ids)}")
    if attempted_source_ids:
        attempted_source_id = next(iter(attempted_source_ids))
        if preflight_source_id is not None and preflight_source_id != attempted_source_id:
            raise ValueError(
                f"conflicting plugin_source_id between preflight and attempted artifacts for {harness}: "
                f"{preflight_source_id} != {attempted_source_id}"
            )
        return attempted_source_id
    if preflight_source_id is None:
        raise ValueError(f"{harness} plugin_source_id missing from preflight proof")
    return preflight_source_id


def build_summary(run_dir: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    run_dir = Path(run_dir)
    if len(cases) != CASES_PER_HARNESS:
        raise ValueError("cases manifest must contain exactly 7 cases")
    case_order = [case["case_id"] for case in cases]
    identities = _read_json(HARNESS_DIR / "model-identities.json")
    environment = _read_environment(run_dir)
    states = {harness: _read_harness_state(run_dir, harness, identities) for harness in HARNESSES}
    attempted = {harness: _read_attempted_cases(run_dir, harness) for harness in HARNESSES}
    progress_made = any(attempted[harness] for harness in HARNESSES)

    preflight_statuses = {harness: states[harness]["preflight_status"] for harness in HARNESSES}
    if any(status != "pass" for status in preflight_statuses.values()):
        if progress_made:
            raise ValueError("attempted case artifacts are not allowed when any preflight is blocked")
        accounting_rows: list[dict[str, Any]] = []
        for harness in HARNESSES:
            reason_code = f"{harness}_preflight_blocked" if preflight_statuses[harness] == "blocked" else "global_hard_gate_blocked"
            if reason_code not in REASON_CODES:
                raise ValueError(f"unknown reason code: {reason_code}")
            for case_id in case_order:
                accounting_rows.append(
                    {"harness": harness, "case_id": case_id, "status": "unattempted", "reason_code": reason_code}
                )
        aligned = False
        canonical_identity = None
    else:
        aligned, canonical_identity, alignment_reason = _alignment_reason(states)
        if not aligned:
            if progress_made:
                raise ValueError("attempted case artifacts are not allowed when model alignment is blocked")
            if alignment_reason not in REASON_CODES:
                raise ValueError(f"unknown alignment reason: {alignment_reason}")
            accounting_rows = [
                {"harness": harness, "case_id": case_id, "status": "unattempted", "reason_code": alignment_reason}
                for harness in HARNESSES
                for case_id in case_order
            ]
        else:
            if not progress_made:
                raise ValueError("aligned run requires attempted case artifacts")
            accounting_rows = []
            for harness in HARNESSES:
                harness_attempted = attempted[harness]
                prefix_len = _validate_prefix(case_order, harness_attempted, harness)
                stopped = any(harness_attempted[item]["status"] == "harness_error" for item in case_order[:prefix_len])
                for case_id in case_order:
                    if case_id in harness_attempted:
                        accounting_rows.append(dict(harness_attempted[case_id]))
                    elif stopped:
                        accounting_rows.append(
                            {
                                "harness": harness,
                                "case_id": case_id,
                                "status": "unattempted",
                                "reason_code": "runtime_harness_stopped",
                            }
                        )
                    else:
                        raise ValueError(f"missing attempted case artifact without runtime stop for {harness}/{case_id}")

    if len(accounting_rows) != CASES_PER_HARNESS * len(HARNESSES):
        raise ValueError("summary must contain exactly 14 accounting rows")

    harness_summaries: dict[str, dict[str, Any]] = {}
    verdict_counts_valid = True
    for harness in HARNESSES:
        harness_rows = [row for row in accounting_rows if row["harness"] == harness]
        if len(harness_rows) != CASES_PER_HARNESS:
            raise ValueError(f"{harness} must have exactly 7 accounting rows")
        if [row["case_id"] for row in harness_rows] != case_order:
            raise ValueError(f"{harness} accounting rows must follow manifest order")
        verdict_counts = {status: 0 for status in ATTEMPTED_STATUSES}
        verdict_counts["unattempted"] = 0
        contaminated_case_ids: list[str] = []
        for row in harness_rows:
            status = row["status"]
            if status == "unattempted":
                reason_code = row.get("reason_code")
                if reason_code not in REASON_CODES:
                    raise ValueError(f"invalid reason code for {harness}/{row['case_id']}: {reason_code}")
            elif status not in VERDICTS:
                raise ValueError(f"invalid attempted status for {harness}/{row['case_id']}: {status}")
            verdict_counts[status] += 1
            if row.get("contaminated"):
                contaminated_case_ids.append(row["case_id"])
        if sum(verdict_counts.values()) != CASES_PER_HARNESS:
            verdict_counts_valid = False
        plugin_source_id = _resolve_plugin_source_id(harness, attempted[harness], states[harness])
        harness_summaries[harness] = {
            "preflight": states[harness]["preflight_status"],
            "plugin_proof_strength": states[harness]["plugin_proof_strength"],
            "plugin_source_id": plugin_source_id,
            "resolved_model_identity": states[harness]["validated_identity"] or states[harness]["proof_identity"],
            "isolation_profile": states[harness]["isolation_profile"],
            "verdict_counts": verdict_counts,
            "contamination": {
                "contaminated_invocations": len(contaminated_case_ids),
                "case_ids": contaminated_case_ids,
            },
        }

    run_complete = verdict_counts_valid and len(accounting_rows) == 14
    contamination_total = sum(
        harness_summaries[harness]["contamination"]["contaminated_invocations"] for harness in HARNESSES
    )
    acceptance_passed = (
        all(harness_summaries[h]["preflight"] == "pass" for h in HARNESSES)
        and aligned
        and all(row["status"] == "pass" for row in accounting_rows)
        and contamination_total == 0
        and environment["redaction_passed"]
    )
    return {
        "run_id": environment["run_id"],
        "run_kind": environment["run_kind"],
        "case_count_per_harness": CASES_PER_HARNESS,
        "cross_harness_model_confound": not aligned,
        "model_alignment": {
            "required": True,
            "aligned": aligned,
            "canonical_identity": canonical_identity,
            "blocked": not aligned,
        },
        "harnesses": harness_summaries,
        "accounting_rows": accounting_rows,
        "verdict_counts_valid": verdict_counts_valid,
        "run_complete": run_complete,
        "acceptance_passed": acceptance_passed,
        "release_candidate_eligible": run_complete and acceptance_passed and environment["redaction_passed"],
        "packaging_redaction_passed": environment["redaction_passed"],
        "raw_artifacts": environment["raw_artifacts"],
        "deviations": environment["deviations"],
        "manual_notes": environment["manual_notes"],
        "evidence_links": {
            "capabilities": {harness: f"capabilities/{harness}.json" for harness in HARNESSES},
            "preflight": {harness: f"preflight/{harness}.json" for harness in HARNESSES},
            "model_proofs": {harness: f"preflight/{harness}-model-proof.json" for harness in HARNESSES},
        },
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Harness acceptance summary",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Run kind: `{summary['run_kind']}`",
        f"- Packaging/redaction passed: `{str(summary['packaging_redaction_passed']).lower()}`",
        (
            "- Raw artifact record: "
            f"`{summary['raw_artifacts']['relative_id']}` "
            f"(sha256 `{summary['raw_artifacts']['sha256']}`, manual review `{summary['raw_artifacts']['manual_review_status']}`, "
            f"reason `{summary['raw_artifacts']['reason_not_committed']}`)"
        ),
        "- This is single-run fresh-session acceptance evidence, not a stability or repeated-run estimate.",
        "",
        "## Model alignment",
        f"- Required: `{str(summary['model_alignment']['required']).lower()}`",
        f"- Aligned: `{str(summary['model_alignment']['aligned']).lower()}`",
        f"- Blocked: `{str(summary['model_alignment']['blocked']).lower()}`",
        f"- Canonical identity: `{summary['model_alignment']['canonical_identity']}`",
        "- Model proofs: `preflight/claude-model-proof.json`, `preflight/opencode-model-proof.json`",
        "",
        "## Harness summaries",
    ]
    for harness in HARNESSES:
        harness_summary = summary["harnesses"][harness]
        case_ids = ", ".join(harness_summary["contamination"]["case_ids"]) or "none"
        lines.extend(
            [
                f"### {harness}",
                f"- Preflight: `{harness_summary['preflight']}`",
                f"- Plugin proof strength: `{harness_summary['plugin_proof_strength']}` (source `{harness_summary['plugin_source_id']}`)",
                f"- Resolved model identity: `{harness_summary['resolved_model_identity']}`",
                f"- Isolation profile: `{harness_summary['isolation_profile']}`",
                (
                    "- Contamination overlay: "
                    f"`{harness_summary['contamination']['contaminated_invocations']}` contaminated invocation(s) "
                    f"(`{case_ids}`)"
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Case accounting",
            "| # | Harness | Case ID | Status | Detail | Contaminated |",
            "|---|---|---|---|---|---|",
        ]
    )
    for index, row in enumerate(summary["accounting_rows"], start=1):
        detail = row.get("reason_code") or row.get("observed_phase") or ""
        contaminated = "yes" if row.get("contaminated") else "no"
        lines.append(
            f"| {index} | {row['harness']} | {row['case_id']} | {row['status']} | {detail} | {contaminated} |"
        )
    lines.extend(
        [
            "",
            "## Verdict partitions",
            "| Harness | Pass | Fail | Indeterminate | Harness error | Unattempted |",
            "|---|---|---|---|---|---|",
        ]
    )
    for harness in HARNESSES:
        counts = summary["harnesses"][harness]["verdict_counts"]
        lines.append(
            f"| {harness} | {counts['pass']} | {counts['fail']} | {counts['indeterminate']} | {counts['harness_error']} | {counts['unattempted']} |"
        )
    lines.extend(
        [
            "",
            "## Contamination overlays",
            "| Harness | Contaminated invocations | Case IDs |",
            "|---|---|---|",
        ]
    )
    for harness in HARNESSES:
        contamination = summary["harnesses"][harness]["contamination"]
        case_ids = ", ".join(contamination["case_ids"]) or "none"
        lines.append(f"| {harness} | {contamination['contaminated_invocations']} | {case_ids} |")
    lines.extend(
        [
            "",
            "## Evidence links",
            "- Capabilities: `capabilities/claude.json`, `capabilities/opencode.json`",
            "- Preflights: `preflight/claude.json`, `preflight/opencode.json`",
            "- Model proofs: `preflight/claude-model-proof.json`, `preflight/opencode-model-proof.json`",
            "",
            "## Deviations",
        ]
    )
    deviations = summary.get("deviations", [])
    if deviations:
        lines.extend([f"- {item}" for item in deviations])
    else:
        lines.append("- none")
    lines.extend(["", "## Manual notes"])
    manual_notes = summary.get("manual_notes", [])
    if manual_notes:
        lines.extend([f"- {item}" for item in manual_notes])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.write and args.check_only:
        raise ValueError("--write and --check-only are mutually exclusive")
    run_dir = Path(args.run_dir)
    summary = build_summary(run_dir, load_cases(ROOT))
    markdown = render_summary_markdown(summary)
    summary_json_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"
    if args.write:
        existing_targets = [path for path in (summary_json_path, summary_md_path) if path.exists()]
        if existing_targets:
            if len(existing_targets) == 1:
                raise FileExistsError(existing_targets[0])
            raise FileExistsError("summary.json and summary.md already exist")
        write_json(summary_json_path, summary)
        summary_md_path.write_text(markdown, encoding="utf-8")
    elif args.check_only:
        if not summary_json_path.exists() or not summary_md_path.exists():
            raise FileNotFoundError("summary.json and summary.md must already exist for --check-only")
        existing_summary = _read_json(summary_json_path)
        if existing_summary != summary:
            raise ValueError("summary.json does not match reconstructed summary")
        existing_markdown = summary_md_path.read_text(encoding="utf-8")
        if existing_markdown != markdown:
            raise ValueError("summary.md does not match reconstructed summary")
    else:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
