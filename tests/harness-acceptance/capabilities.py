#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit, urlunsplit

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import lib  # noqa: E402

CLAUDE_DIRECT_BRANCH = "direct-plugin-dir"
CLAUDE_MARKETPLACE_BRANCH = "local-marketplace"
OPENCODE_STRONG_BRANCH = "strong-runtime-proof"
OPENCODE_FALLBACK_BRANCH = "fallback-workspace-proof"

CLAUDE_AUTH_PRESERVING_DIRECT = "auth-preserving-direct-plugin-dir"
CLAUDE_FULL_DIRECT = "full-direct-plugin-dir"
CLAUDE_AUTH_PRESERVING_MARKETPLACE = "auth-preserving-marketplace"
CLAUDE_FULL_MARKETPLACE = "full-marketplace"
OPENCODE_RUNTIME_PROFILE = "workspace-config-runtime-proof"
OPENCODE_STATIC_PROFILE = "workspace-config-static-proof"

CLAUDE_PROOF_STRENGTH = "best_available_source_plus_canary"
OPENCODE_RUNTIME_PROOF_STRENGTH = "resolved_runtime_source_inventory_canary"
OPENCODE_STATIC_PROOF_STRENGTH = "workspace_config_static_inventory_canary"

CANARY_MARKER = "RESEARCHFLOW_BOOTSTRAP_ACTIVE"
DEFAULT_PLUGIN_SOURCE_ID = "researchflow-checkout"
DEFAULT_RESIDUAL_CATEGORIES = ["auth", "admin-policy"]


def read_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("config must be an object")
    return value


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def normalize_endpoint_identity(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("endpoint_identity must be a non-empty string")
    parsed = urlsplit(text)
    if parsed.scheme and parsed.netloc:
        normalized = urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                "",
            )
        )
        return normalized.rstrip("/")
    return text.rstrip("/").lower()


def hash_endpoint_identity(value: Any) -> str:
    normalized = normalize_endpoint_identity(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_status(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                return []
            events.append(payload)
        return events
    except json.JSONDecodeError:
        return []


def _read_cli_version(path: Path) -> str:
    parts = _read_text(path).strip().split()
    return parts[-1] if parts else "unknown"


def _response_text(events: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for event in events:
        if event.get("event") == "response":
            text = event.get("text", "")
            if not isinstance(text, str):
                raise ValueError("response event text must be a string")
            parts.append(text)
    return "".join(parts)


def _canary_passed(events: list[dict[str, Any]]) -> bool:
    response = _response_text(events)
    first_line = response.splitlines()[0] if response else ""
    return first_line == CANARY_MARKER


def _extract_model_event(events: list[dict[str, Any]]) -> dict[str, str]:
    for event in events:
        if event.get("event") != "model":
            continue
        backing_model_id = event.get("backing_model_id")
        resolved_model_identity = event.get("resolved_model_identity")
        proof_source = event.get("proof_source", "litellm-response-metadata")
        if not isinstance(backing_model_id, str) or not backing_model_id:
            continue
        if not isinstance(resolved_model_identity, str) or not resolved_model_identity:
            continue
        if not isinstance(proof_source, str) or not proof_source:
            continue
        return {
            "backing_model_id": backing_model_id,
            "resolved_model_identity": resolved_model_identity,
            "proof_source": proof_source,
        }
    return {
        "backing_model_id": "unknown",
        "resolved_model_identity": None,
        "proof_source": "missing-model-metadata",
    }


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def classify_tool_execution(events: list[dict[str, Any]]) -> dict[str, Any]:
    tool_events = [event for event in events if event.get("event") == "tool"]
    if not tool_events:
        return {
            "detected": False,
            "attempted_tools": [],
            "side_effect_status": "none",
            "audit_complete": True,
        }

    attempted_tools: list[str] = []
    saw_unknown = False
    audit_complete = True
    saw_executed = False
    saw_blocked = False
    for event in tool_events:
        tool_name = event.get("tool")
        status = event.get("status")
        if isinstance(tool_name, str) and tool_name:
            attempted_tools.append(tool_name)
        else:
            saw_unknown = True
            audit_complete = False
        if status == "executed":
            saw_executed = True
        elif status == "blocked":
            saw_blocked = True
        else:
            saw_unknown = True
            audit_complete = False

    attempted_tools = _unique_preserve_order(attempted_tools)
    if saw_executed:
        side_effect_status = "executed"
    elif saw_unknown:
        side_effect_status = "unknown"
    elif saw_blocked:
        side_effect_status = "blocked"
    else:
        side_effect_status = "unknown"
        audit_complete = False

    return {
        "detected": True,
        "attempted_tools": attempted_tools,
        "side_effect_status": side_effect_status,
        "audit_complete": audit_complete,
    }


def _claude_branch_from_probe(probe: dict[str, Any]) -> Optional[str]:
    return select_claude_load_branch(probe)


def select_claude_load_branch(probe: dict[str, Any]) -> Optional[str]:
    probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
    if not isinstance(probe_results, dict):
        return None
    direct_plugin_dir = probe_results.get("direct_plugin_dir")
    if isinstance(direct_plugin_dir, dict):
        if direct_plugin_dir.get("flag_supported") and direct_plugin_dir.get("canary_passed"):
            return CLAUDE_DIRECT_BRANCH
    marketplace = probe_results.get("marketplace")
    if isinstance(marketplace, dict):
        if (
            marketplace.get("registration_supported")
            and marketplace.get("install_supported")
            and marketplace.get("resolved_checkout_match")
            and marketplace.get("canary_passed", True)
        ):
            return CLAUDE_MARKETPLACE_BRANCH
    return None


def select_opencode_proof_branch(probe: dict[str, Any]) -> Optional[str]:
    if not isinstance(probe, dict):
        return None
    if not probe.get("workspace_plugin_matches_checkout"):
        return None
    probe_results = probe.get("probe_results")
    if not isinstance(probe_results, dict):
        return None
    run = probe_results.get("run")
    if not isinstance(run, dict) or not run.get("canary_passed"):
        return None
    debug = probe_results.get("debug")
    if not isinstance(debug, dict):
        return OPENCODE_FALLBACK_BRANCH
    if debug.get("config") and debug.get("paths") and debug.get("skill"):
        return OPENCODE_STRONG_BRANCH
    return OPENCODE_FALLBACK_BRANCH


def select_isolation_profile(probe: dict[str, Any]) -> Optional[str]:
    harness = probe.get("harness") if isinstance(probe, dict) else None
    if harness == "claude":
        branch = select_claude_load_branch(probe)
        if branch is None:
            return None
        probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
        full_isolation = False
        if isinstance(probe_results, dict):
            full_isolation = bool(probe_results.get("full_isolation_auth_compatible"))
            auth_preserving = bool(probe_results.get("auth_preserving_supported"))
        else:
            auth_preserving = False
        if full_isolation:
            return CLAUDE_FULL_DIRECT if branch == CLAUDE_DIRECT_BRANCH else CLAUDE_FULL_MARKETPLACE
        if auth_preserving:
            return (
                CLAUDE_AUTH_PRESERVING_DIRECT
                if branch == CLAUDE_DIRECT_BRANCH
                else CLAUDE_AUTH_PRESERVING_MARKETPLACE
            )
        return None
    if harness == "opencode":
        branch = select_opencode_proof_branch(probe)
        if branch == OPENCODE_STRONG_BRANCH:
            return OPENCODE_RUNTIME_PROFILE
        if branch == OPENCODE_FALLBACK_BRANCH:
            return OPENCODE_STATIC_PROFILE
    return None


def _plugin_proof_strength_for_probe(probe: dict[str, Any]) -> Optional[str]:
    harness = probe.get("harness")
    if harness == "claude":
        return CLAUDE_PROOF_STRENGTH if select_claude_load_branch(probe) else None
    if harness == "opencode":
        branch = select_opencode_proof_branch(probe)
        if branch == OPENCODE_STRONG_BRANCH:
            return OPENCODE_RUNTIME_PROOF_STRENGTH
        if branch == OPENCODE_FALLBACK_BRANCH:
            return OPENCODE_STATIC_PROOF_STRENGTH
    return None


def build_capability_record(harness: str, cli_version: str, probe: dict[str, Any]) -> dict[str, Any]:
    if harness not in {"claude", "opencode"}:
        raise ValueError(f"unsupported harness: {harness}")
    record = {
        "schema_version": 1,
        "harness": harness,
        "cli_version": cli_version,
        "noninteractive": True,
        "structured_output": True,
        "local_plugin_loading": select_isolation_profile(probe) is not None,
        "session_persistence_disable": True,
        "settings_isolation": select_isolation_profile(probe) is not None,
        "auth_preserving_full_isolation": bool(
            isinstance(probe.get("probe_results"), dict)
            and probe["probe_results"].get("full_isolation_auth_compatible")
        ),
        "selected_isolation_profile": select_isolation_profile(probe),
        "plugin_proof_strength": _plugin_proof_strength_for_probe(probe),
    }
    if harness == "claude":
        selected_load_branch = select_claude_load_branch(probe)
        record["selected_load_branch"] = selected_load_branch
        record["plugin_load_path"] = selected_load_branch
        record["optional_cli_validation"] = bool(
            isinstance(probe.get("probe_results"), dict)
            and isinstance(probe["probe_results"].get("cli_validation"), dict)
            and probe["probe_results"]["cli_validation"].get("supported")
            and probe["probe_results"]["cli_validation"].get("passed")
        )
        record["probe_results"] = probe.get("probe_results", {})
    else:
        record["selected_proof_branch"] = select_opencode_proof_branch(probe)
        record["workspace_plugin_matches_checkout"] = bool(probe.get("workspace_plugin_matches_checkout"))
        record["probe_results"] = probe.get("probe_results", {})
    return record


def build_preflight_record(capability: dict[str, Any], plugin_source_id: str, canary_passed: bool) -> dict[str, Any]:
    status = "pass" if capability.get("selected_isolation_profile") and canary_passed else "blocked"
    return {
        "schema_version": 1,
        "harness": capability["harness"],
        "status": status,
        "plugin_proof_strength": capability.get("plugin_proof_strength"),
        "plugin_source_id": plugin_source_id,
        "isolation_profile": capability.get("selected_isolation_profile"),
    }


def build_model_proof(
    harness: str,
    endpoint_identity: Any,
    requested_route: str,
    model_event: dict[str, Any],
    proof_sha256: str,
) -> dict[str, Any]:
    resolved_model_identity = model_event.get("resolved_model_identity")
    backing_model_id = model_event.get("backing_model_id", "unknown")
    verified = (
        isinstance(resolved_model_identity, str)
        and resolved_model_identity == f"openai/{backing_model_id}"
    )
    return {
        "schema_version": 1,
        "harness": harness,
        "proxy_kind": "litellm",
        "endpoint_identity_sha256": hash_endpoint_identity(endpoint_identity),
        "requested_route": requested_route,
        "upstream_provider": "openai",
        "backing_model_id": backing_model_id,
        "resolved_model_identity": resolved_model_identity,
        "proof_method": model_event.get("proof_source", "missing-model-metadata"),
        "proof_sha256": proof_sha256,
        "verified": verified,
        "redaction_passed": True,
    }


def _write_text(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _probe_from_claude_dir(config: dict[str, Any], probe_dir: Path) -> tuple[str, dict[str, Any]]:
    help_text = _read_text(probe_dir / "help.txt")
    plugin_help_text = _read_text(probe_dir / "plugin-help.txt")
    direct_events = _read_jsonl(probe_dir / "direct-canary.jsonl")
    marketplace_events = _read_jsonl(probe_dir / "marketplace-canary.jsonl")
    full_events = _read_jsonl(probe_dir / "full-direct-canary.jsonl")
    marketplace_payload = _read_json_file(probe_dir / "marketplace-list.json")
    repo_root = str(config["repo_root"])
    cli_version = _read_cli_version(probe_dir / "version.txt")
    resolved_checkout_match = False
    if isinstance(marketplace_payload, list) and marketplace_payload:
        first = marketplace_payload[0]
        if isinstance(first, dict) and first.get("path") == repo_root:
            resolved_checkout_match = True
    probe = {
        "harness": "claude",
        "probe_results": {
            "direct_plugin_dir": {
                "flag_supported": "--plugin-dir" in help_text,
                "canary_passed": _read_status(probe_dir / "direct-canary.status") == 0 and _canary_passed(direct_events),
            },
            "marketplace": {
                "registration_supported": "list" in plugin_help_text,
                "install_supported": _read_status(probe_dir / "marketplace-list.status") == 0,
                "resolved_checkout_match": resolved_checkout_match,
                "canary_passed": _read_status(probe_dir / "marketplace-canary.status") == 0 and _canary_passed(marketplace_events),
            },
            "cli_validation": {
                "supported": "validate" in plugin_help_text,
                "passed": _read_status(probe_dir / "validate.status") == 0,
            },
            "full_isolation_auth_compatible": _read_status(probe_dir / "full-direct-canary.status") == 0 and _canary_passed(full_events),
            "auth_preserving_supported": (
                (_read_status(probe_dir / "direct-canary.status") == 0 and _canary_passed(direct_events))
                or (_read_status(probe_dir / "marketplace-canary.status") == 0 and _canary_passed(marketplace_events))
            ),
        },
    }
    return cli_version, probe


def _probe_from_opencode_dir(config: dict[str, Any], probe_dir: Path) -> tuple[str, dict[str, Any]]:
    cli_version = _read_cli_version(probe_dir / "version.txt")
    debug_config_status = _read_status(probe_dir / "debug-config.status") == 0
    debug_paths_status = _read_status(probe_dir / "debug-paths.status") == 0
    debug_skill_status = _read_status(probe_dir / "debug-skill.status") == 0
    canary_events = _read_jsonl(probe_dir / "canary.jsonl")
    workspace_plugin_matches_checkout = False
    for payload in (
        _read_json_file(probe_dir / "debug-config.json"),
        _read_json_file(probe_dir / "debug-paths.json"),
    ):
        if isinstance(payload, dict) and payload.get("plugin_path") == str(config["repo_root"]):
            workspace_plugin_matches_checkout = True
            break
    if not workspace_plugin_matches_checkout:
        workspace_plugin_matches_checkout = bool(config.get("workspace_plugin_matches_checkout", False))
    probe = {
        "harness": "opencode",
        "workspace_plugin_matches_checkout": workspace_plugin_matches_checkout,
        "probe_results": {
            "debug": {
                "config": debug_config_status,
                "paths": debug_paths_status,
                "skill": debug_skill_status,
            },
            "run": {
                "canary_passed": _read_status(probe_dir / "canary.status") == 0 and _canary_passed(canary_events),
            },
        },
    }
    return cli_version, probe


def probe_from_dir(harness: str, config: dict[str, Any], probe_dir: Path) -> tuple[str, dict[str, Any]]:
    if harness == "claude":
        return _probe_from_claude_dir(config, probe_dir)
    if harness == "opencode":
        return _probe_from_opencode_dir(config, probe_dir)
    raise ValueError(f"unsupported harness: {harness}")


def _raw_hashes(events_path: Path, stderr_path: Path) -> dict[str, str]:
    return {
        "events": lib.sha256_path(events_path),
        "stderr": lib.sha256_path(stderr_path),
    }


def build_invocation_record(
    harness: str,
    config: dict[str, Any],
    capability: dict[str, Any],
    case_id: str,
    cli_version: str,
    events_path: Path,
    stderr_path: Path,
    exit_code: int,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    events = _read_jsonl(events_path)
    final_response = _response_text(events)
    final_response_sha256 = _sha256_text(final_response)
    model_event = _extract_model_event(events)
    tool_execution = classify_tool_execution(events)
    raw_artifact_hashes = _raw_hashes(events_path, stderr_path)
    harness_config = config[harness]
    started_at = config.get("started_at_utc") or utc_timestamp()
    finished_at = config.get("finished_at_utc") or utc_timestamp()
    model_request = {
        "harness_value": harness_config["harness_model_value"],
        "proxy_kind": "litellm",
        "endpoint_identity_sha256": hash_endpoint_identity(config["endpoint_identity"]),
        "requested_route": harness_config["harness_model_value"],
    }
    model_resolution = {
        "upstream_provider": "openai",
        "backing_model_id": model_event["backing_model_id"],
        "proof_source": model_event["proof_source"],
        "proof_sha256": raw_artifact_hashes["events"],
    }
    invocation = {
        "schema_version": 1,
        "run_id": config["run_id"],
        "case_id": case_id,
        "harness": harness,
        "cli_version": cli_version,
        "model_request": model_request,
        "model_resolution": model_resolution,
        "resolved_model_identity": model_event["resolved_model_identity"],
        "model_identity_verified": model_event["resolved_model_identity"] == f"openai/{model_event['backing_model_id']}",
        "effort_or_variant": harness_config["effort_or_variant"],
        "timeout_seconds": int(config["timeout_seconds"]),
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "exit_code": exit_code,
        "timed_out": exit_code == 124,
        "repo_commit_sha": config["repo_commit_sha"],
        "plugin_source_id": config.get("plugin_source_id", DEFAULT_PLUGIN_SOURCE_ID),
        "plugin_proof_passed": bool(capability.get("selected_isolation_profile")),
        "plugin_proof_strength": capability.get("plugin_proof_strength"),
        "isolation_profile": capability.get("selected_isolation_profile"),
        "environment_contaminated": bool(config.get("environment_contaminated", False)),
        "residual_categories": list(config.get("residual_categories", DEFAULT_RESIDUAL_CATEGORIES)),
        "tool_execution": tool_execution,
        "final_response_path": "final-response.txt",
        "final_response_sha256": final_response_sha256,
        "raw_artifact_hashes": raw_artifact_hashes,
    }
    command = {
        "schema_version": 1,
        "harness": harness,
        "cli_version": cli_version,
        "model_request": model_request,
        "resolved_model_identity": model_event["resolved_model_identity"],
        "effort_or_variant": harness_config["effort_or_variant"],
        "timeout_seconds": int(config["timeout_seconds"]),
        "repo_commit_sha": config["repo_commit_sha"],
        "plugin_source_id": config.get("plugin_source_id", DEFAULT_PLUGIN_SOURCE_ID),
        "plugin_proof_strength": capability.get("plugin_proof_strength"),
        "isolation_profile": capability.get("selected_isolation_profile"),
        "residual_categories": list(config.get("residual_categories", DEFAULT_RESIDUAL_CATEGORIES)),
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "exit_code": exit_code,
        "tool_execution": tool_execution,
        "raw_artifact_hashes": raw_artifact_hashes,
    }
    lib.validate_invocation(invocation)
    return invocation, command, final_response


def command_normalize_capability(args: argparse.Namespace) -> int:
    config = read_config(Path(args.config))
    cli_version, probe = probe_from_dir(args.harness, config, Path(args.probe_dir))
    capability = build_capability_record(args.harness, cli_version, probe)
    lib.write_json(Path(args.output), capability)
    return 0


def command_normalize_preflight(args: argparse.Namespace) -> int:
    config = read_config(Path(args.config))
    cli_version, probe = probe_from_dir(args.harness, config, Path(args.probe_dir))
    capability = build_capability_record(args.harness, cli_version, probe)
    events_path = Path(args.events)
    stderr_path = Path(args.stderr)
    events = _read_jsonl(events_path)
    preflight = build_preflight_record(
        capability,
        config.get("plugin_source_id", DEFAULT_PLUGIN_SOURCE_ID),
        _read_status(Path(args.status)) == 0 and _canary_passed(events),
    )
    requested_route = config[args.harness]["harness_model_value"]
    model_proof = build_model_proof(
        args.harness,
        config["endpoint_identity"],
        requested_route,
        _extract_model_event(events),
        lib.sha256_path(events_path),
    )
    lib.write_json(Path(args.output), preflight)
    lib.write_json(Path(args.model_output), model_proof)
    _ = stderr_path
    return 0


def command_normalize_case(args: argparse.Namespace) -> int:
    config = read_config(Path(args.config))
    cli_version, probe = probe_from_dir(args.harness, config, Path(args.probe_dir))
    capability = build_capability_record(args.harness, cli_version, probe)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = Path(args.events)
    stderr_path = Path(args.stderr)
    exit_code = int(Path(args.status).read_text(encoding="utf-8").strip())
    invocation, command, final_response = build_invocation_record(
        args.harness,
        config,
        capability,
        args.case_id,
        cli_version,
        events_path,
        stderr_path,
        exit_code,
    )
    _write_text(output_dir / "final-response.txt", final_response)
    lib.write_json(output_dir / "invocation.json", invocation)
    lib.write_json(output_dir / "command.json", command)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    capability_parser = subparsers.add_parser("normalize-capability")
    capability_parser.add_argument("--harness", required=True, choices=("claude", "opencode"))
    capability_parser.add_argument("--config", required=True)
    capability_parser.add_argument("--probe-dir", required=True)
    capability_parser.add_argument("--output", required=True)
    capability_parser.set_defaults(func=command_normalize_capability)

    preflight_parser = subparsers.add_parser("normalize-preflight")
    preflight_parser.add_argument("--harness", required=True, choices=("claude", "opencode"))
    preflight_parser.add_argument("--config", required=True)
    preflight_parser.add_argument("--probe-dir", required=True)
    preflight_parser.add_argument("--events", required=True)
    preflight_parser.add_argument("--stderr", required=True)
    preflight_parser.add_argument("--status", required=True)
    preflight_parser.add_argument("--output", required=True)
    preflight_parser.add_argument("--model-output", required=True)
    preflight_parser.set_defaults(func=command_normalize_preflight)

    case_parser = subparsers.add_parser("normalize-case")
    case_parser.add_argument("--harness", required=True, choices=("claude", "opencode"))
    case_parser.add_argument("--config", required=True)
    case_parser.add_argument("--probe-dir", required=True)
    case_parser.add_argument("--events", required=True)
    case_parser.add_argument("--stderr", required=True)
    case_parser.add_argument("--status", required=True)
    case_parser.add_argument("--output-dir", required=True)
    case_parser.add_argument("--case-id", required=True)
    case_parser.set_defaults(func=command_normalize_case)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
