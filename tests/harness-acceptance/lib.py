#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PHASES: tuple[str, ...] = (
    "literature-discovery",
    "paper-structuring",
    "paper-drafting",
    "paper-review",
    "artifact-packaging",
)
VERDICTS: tuple[str, ...] = ("pass", "fail", "indeterminate", "harness_error")
REASON_CODES: tuple[str, ...] = (
    "claude_preflight_blocked",
    "opencode_preflight_blocked",
    "model_alignment_blocked",
    "global_hard_gate_blocked",
    "runtime_harness_stopped",
)

_CASE_FIELDS = (
    "case_id",
    "kind",
    "prompt",
    "expected_phase",
    "required_marker",
    "forbidden_patterns",
)
_INVOCATION_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "harness",
    "cli_version",
    "model_request",
    "model_resolution",
    "resolved_model_identity",
    "model_identity_verified",
    "effort_or_variant",
    "timeout_seconds",
    "started_at_utc",
    "finished_at_utc",
    "exit_code",
    "timed_out",
    "repo_commit_sha",
    "plugin_source_id",
    "plugin_proof_passed",
    "plugin_proof_strength",
    "isolation_profile",
    "environment_contaminated",
    "residual_categories",
    "tool_execution",
    "final_response_path",
    "final_response_sha256",
    "raw_artifact_hashes",
)
_KINDS = ("direct", "backward")
_HARNESSES = ("claude", "opencode")
_PLUGIN_PROOF_STRENGTHS = (
    "best_available_source_plus_canary",
    "resolved_runtime_source_inventory_canary",
    "workspace_config_static_inventory_canary",
)
_SIDE_EFFECT_STATUSES = ("none", "blocked", "executed", "unknown")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


def _require_enum(value: Any, label: str, allowed: tuple[str, ...]) -> str:
    text = _require_string(value, label)
    if text not in allowed:
        raise ValueError(f"{label} must be one of {allowed}")
    return text


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return value


def _require_exact_keys(value: dict[str, Any], label: str, expected: tuple[str, ...]) -> None:
    actual = set(value)
    allowed = set(expected)
    missing = sorted(allowed - actual)
    unknown = sorted(actual - allowed)
    if missing or unknown:
        problems = []
        if missing:
            problems.append(f"missing {missing}")
        if unknown:
            problems.append(f"unknown {unknown}")
        raise ValueError(f"{label} has invalid keys: {', '.join(problems)}")


def _require_sha256(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{label} must be lowercase 64-character hex")
    return text


def _require_commit_sha(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if not _SHA1_RE.fullmatch(text):
        raise ValueError(f"{label} must be lowercase 40-character hex")
    return text


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return _require_dict(value, str(path))


def write_json(path: Path, value: dict[str, Any], overwrite: bool = False) -> None:
    _require_dict(value, "value")
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(root: Path) -> list[dict[str, Any]]:
    path = root / "tests" / "harness-acceptance" / "cases.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("cases.json must be a list")
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        case = _require_dict(item, f"cases[{index}]")
        _require_exact_keys(case, f"cases[{index}]", _CASE_FIELDS)
        case_id = _require_string(case["case_id"], f"cases[{index}].case_id")
        if case_id in seen:
            raise ValueError(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        _require_enum(case["kind"], f"cases[{index}].kind", _KINDS)
        _require_string(case["prompt"], f"cases[{index}].prompt")
        _require_enum(case["expected_phase"], f"cases[{index}].expected_phase", PHASES)
        if case["required_marker"] != "ResearchFlow phase:":
            raise ValueError(f"cases[{index}].required_marker must equal 'ResearchFlow phase:'")
        forbidden_patterns = _require_string_list(case["forbidden_patterns"], f"cases[{index}].forbidden_patterns")
        for pattern_index, pattern in enumerate(forbidden_patterns):
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(
                    f"cases[{index}].forbidden_patterns[{pattern_index}] invalid regex: {exc}"
                ) from exc
        cases.append(case)
    return cases


def validate_invocation(value: dict[str, Any]) -> None:
    invocation = _require_dict(value, "invocation")
    _require_exact_keys(invocation, "invocation", _INVOCATION_FIELDS)
    if invocation["schema_version"] != 1:
        raise ValueError("invocation.schema_version must equal 1")
    _require_string(invocation["run_id"], "invocation.run_id")
    _require_string(invocation["case_id"], "invocation.case_id")
    _require_enum(invocation["harness"], "invocation.harness", _HARNESSES)
    _require_string(invocation["cli_version"], "invocation.cli_version")

    model_request = _require_dict(invocation["model_request"], "invocation.model_request")
    _require_exact_keys(
        model_request,
        "invocation.model_request",
        ("harness_value", "proxy_kind", "endpoint_identity_sha256", "requested_route"),
    )
    _require_string(model_request["harness_value"], "invocation.model_request.harness_value")
    _require_enum(model_request["proxy_kind"], "invocation.model_request.proxy_kind", ("litellm",))
    _require_sha256(
        model_request["endpoint_identity_sha256"],
        "invocation.model_request.endpoint_identity_sha256",
    )
    _require_string(model_request["requested_route"], "invocation.model_request.requested_route")

    model_resolution = _require_dict(invocation["model_resolution"], "invocation.model_resolution")
    _require_exact_keys(
        model_resolution,
        "invocation.model_resolution",
        ("upstream_provider", "backing_model_id", "proof_source", "proof_sha256"),
    )
    _require_enum(
        model_resolution["upstream_provider"],
        "invocation.model_resolution.upstream_provider",
        ("openai",),
    )
    _require_string(model_resolution["backing_model_id"], "invocation.model_resolution.backing_model_id")
    _require_string(model_resolution["proof_source"], "invocation.model_resolution.proof_source")
    _require_sha256(model_resolution["proof_sha256"], "invocation.model_resolution.proof_sha256")

    resolved_model_identity = invocation["resolved_model_identity"]
    if resolved_model_identity is not None:
        if not isinstance(resolved_model_identity, str) or not resolved_model_identity.startswith("openai/"):
            raise ValueError("invocation.resolved_model_identity must be null or start with 'openai/'")
    _require_bool(invocation["model_identity_verified"], "invocation.model_identity_verified")
    _require_string(invocation["effort_or_variant"], "invocation.effort_or_variant")
    if not isinstance(invocation["timeout_seconds"], int) or invocation["timeout_seconds"] <= 0:
        raise ValueError("invocation.timeout_seconds must be a positive integer")
    _require_string(invocation["started_at_utc"], "invocation.started_at_utc")
    _require_string(invocation["finished_at_utc"], "invocation.finished_at_utc")
    if not isinstance(invocation["exit_code"], int):
        raise ValueError("invocation.exit_code must be an integer")
    _require_bool(invocation["timed_out"], "invocation.timed_out")
    _require_commit_sha(invocation["repo_commit_sha"], "invocation.repo_commit_sha")
    _require_string(invocation["plugin_source_id"], "invocation.plugin_source_id")
    _require_bool(invocation["plugin_proof_passed"], "invocation.plugin_proof_passed")
    _require_enum(
        invocation["plugin_proof_strength"],
        "invocation.plugin_proof_strength",
        _PLUGIN_PROOF_STRENGTHS,
    )
    _require_string(invocation["isolation_profile"], "invocation.isolation_profile")
    _require_bool(invocation["environment_contaminated"], "invocation.environment_contaminated")
    _require_string_list(invocation["residual_categories"], "invocation.residual_categories")

    tool_execution = _require_dict(invocation["tool_execution"], "invocation.tool_execution")
    _require_exact_keys(
        tool_execution,
        "invocation.tool_execution",
        ("detected", "attempted_tools", "side_effect_status", "audit_complete"),
    )
    _require_bool(tool_execution["detected"], "invocation.tool_execution.detected")
    _require_string_list(tool_execution["attempted_tools"], "invocation.tool_execution.attempted_tools") if tool_execution["attempted_tools"] else None
    if not isinstance(tool_execution["attempted_tools"], list):
        raise ValueError("invocation.tool_execution.attempted_tools must be a list")
    if not all(isinstance(item, str) and item for item in tool_execution["attempted_tools"]):
        raise ValueError("invocation.tool_execution.attempted_tools must contain non-empty strings")
    _require_enum(
        tool_execution["side_effect_status"],
        "invocation.tool_execution.side_effect_status",
        _SIDE_EFFECT_STATUSES,
    )
    _require_bool(tool_execution["audit_complete"], "invocation.tool_execution.audit_complete")

    _require_string(invocation["final_response_path"], "invocation.final_response_path")
    _require_sha256(invocation["final_response_sha256"], "invocation.final_response_sha256")

    raw_artifact_hashes = _require_dict(invocation["raw_artifact_hashes"], "invocation.raw_artifact_hashes")
    _require_exact_keys(raw_artifact_hashes, "invocation.raw_artifact_hashes", ("events", "stderr"))
    _require_sha256(raw_artifact_hashes["events"], "invocation.raw_artifact_hashes.events")
    _require_sha256(raw_artifact_hashes["stderr"], "invocation.raw_artifact_hashes.stderr")
