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
REQUIRED_PRIMARY_SKILLS = (
    "using-researchflow",
    "literature-discovery",
    "paper-structuring",
    "paper-drafting",
    "paper-review",
    "artifact-packaging",
)


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


def _read_json_object(path: Path) -> Optional[dict[str, Any]]:
    value = _read_json_file(path)
    return value if isinstance(value, dict) else None


def _read_json_list(path: Path) -> Optional[list[Any]]:
    value = _read_json_file(path)
    return value if isinstance(value, list) else None


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
        text = None
        if event.get("event") == "response":
            text = event.get("text")
        elif event.get("type") == "result":
            text = event.get("result")
        elif event.get("type") == "text":
            part = event.get("part")
            if isinstance(part, dict):
                text = part.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def _canary_passed(events: list[dict[str, Any]]) -> bool:
    response = _response_text(events)
    first_line = response.splitlines()[0] if response else ""
    return first_line == CANARY_MARKER


def _normalize_model_usage_key(value: str) -> str:
    normalized = value.split("[", 1)[0].strip()
    if normalized.startswith("openai/"):
        normalized = normalized.split("/", 1)[1]
    return normalized


def _extract_model_event(events: list[dict[str, Any]]) -> dict[str, Any]:
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
    for event in events:
        if event.get("type") != "result":
            continue
        model_usage = event.get("modelUsage")
        if not isinstance(model_usage, dict):
            continue
        for key in model_usage.keys():
            if not isinstance(key, str):
                continue
            backing_model_id = _normalize_model_usage_key(key)
            if not backing_model_id:
                continue
            return {
                "backing_model_id": backing_model_id,
                "resolved_model_identity": f"openai/{backing_model_id}",
                "proof_source": "result-model-usage",
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


def _truthy(value: Any) -> bool:
    return value is True


def _required_skill_inventory(repo_root: Path) -> dict[str, Any]:
    present: list[str] = []
    missing: list[str] = []
    for skill_name in REQUIRED_PRIMARY_SKILLS:
        skill_path = repo_root / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            present.append(skill_name)
        else:
            missing.append(skill_name)
    return {
        "valid": not missing,
        "present": present,
        "missing": missing,
    }


def _validate_claude_repo(repo_root: Path) -> dict[str, Any]:
    plugin_payload = _read_json_object(repo_root / ".claude-plugin" / "plugin.json")
    marketplace_payload = _read_json_object(repo_root / ".claude-plugin" / "marketplace.json")
    plugin_metadata_valid = bool(
        plugin_payload
        and plugin_payload.get("name") == "researchflow"
        and isinstance(plugin_payload.get("description"), str)
        and plugin_payload.get("description")
        and isinstance(plugin_payload.get("version"), str)
        and plugin_payload.get("version")
    )
    marketplace_entry = None
    if marketplace_payload and isinstance(marketplace_payload.get("plugins"), list):
        for item in marketplace_payload["plugins"]:
            if isinstance(item, dict) and item.get("name") == "researchflow":
                marketplace_entry = item
                break
    marketplace_metadata_valid = bool(
        marketplace_payload
        and marketplace_payload.get("name")
        and marketplace_entry
        and marketplace_entry.get("source") == "./"
    )
    skills = _required_skill_inventory(repo_root)
    return {
        "plugin_metadata_valid": plugin_metadata_valid,
        "marketplace_metadata_valid": marketplace_metadata_valid,
        "required_skill_inventory_valid": skills["valid"],
        "required_skill_inventory_missing": skills["missing"],
    }


def _validate_opencode_repo(repo_root: Path) -> dict[str, Any]:
    plugin_source = _read_text(repo_root / ".opencode" / "plugins" / "researchflow.js")
    plugin_source_file_valid = all(
        marker in plugin_source
        for marker in ("ResearchflowPlugin", "using-researchflow", "skillsDir")
    )
    skills = _required_skill_inventory(repo_root)
    return {
        "plugin_source_file_valid": plugin_source_file_valid,
        "required_skill_inventory_valid": skills["valid"],
        "required_skill_inventory_missing": skills["missing"],
    }


def _validate_opencode_workspace_config(path: Path, repo_root: str) -> bool:
    payload = _read_json_object(path)
    if not payload:
        return False
    plugins = payload.get("plugin")
    if not isinstance(plugins, list):
        return False
    return repo_root in plugins


def _runtime_skill_inventory_valid(payload: Any) -> bool:
    skill_names: set[str] = set()
    if isinstance(payload, dict):
        skills = payload.get("skills")
        if isinstance(skills, list):
            skill_names = {item for item in skills if isinstance(item, str)}
    elif isinstance(payload, str):
        for line in payload.splitlines():
            marker = '"name": "'
            if marker not in line:
                continue
            _, _, remainder = line.partition(marker)
            name, _, _ = remainder.partition('"')
            if name:
                skill_names.add(name)
    return all(skill in skill_names for skill in REQUIRED_PRIMARY_SKILLS)


def _plugin_path_matches(payload: Any, repo_root: str) -> bool:
    return isinstance(payload, dict) and payload.get("plugin_path") == repo_root


def _plugin_path_matches_text(payload: str, repo_root: str) -> bool:
    plugin_file = f"{repo_root}/.opencode/plugins/researchflow.js"
    return repo_root in payload or plugin_file in payload or f"file://{plugin_file}" in payload


def _opencode_paths_isolation_supported(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key in ("config_dir", "data_dir", "cache_dir", "state_dir"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return True
        return False
    if isinstance(payload, str):
        prefixes = ("config", "data", "cache", "state")
        return any(line.split(maxsplit=1)[0] in prefixes for line in payload.splitlines() if line.strip())
    return False


def _opencode_paths_source_match(payload: Any, payload_text: str, repo_root: str) -> bool:
    if _plugin_path_matches(payload, repo_root):
        return True
    return _plugin_path_matches_text(payload_text, repo_root)


def _claude_environment_validation(help_text: str) -> dict[str, bool]:
    return {
        "plugin_dir_supported": "--plugin-dir" in help_text,
        "session_persistence_disable_supported": "--no-session-persistence" in help_text,
        "tools_disable_supported": "--tools" in help_text,
        "structured_output_supported": "--output-format" in help_text,
        "full_isolation_supported": "--bare" in help_text,
    }


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


def _claude_repo_validation_ok(probe_results: dict[str, Any]) -> bool:
    repo_validation = probe_results.get("repo_validation")
    return bool(
        isinstance(repo_validation, dict)
        and _truthy(repo_validation.get("plugin_metadata_valid"))
        and _truthy(repo_validation.get("marketplace_metadata_valid"))
        and _truthy(repo_validation.get("required_skill_inventory_valid"))
    )


def _claude_environment_ok(probe_results: dict[str, Any]) -> bool:
    environment = probe_results.get("environment_validation")
    return bool(
        isinstance(environment, dict)
        and _truthy(environment.get("session_persistence_disable_supported"))
        and _truthy(environment.get("tools_disable_supported"))
        and _truthy(environment.get("structured_output_supported"))
    )


def select_claude_load_branch(probe: dict[str, Any]) -> Optional[str]:
    probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
    if not isinstance(probe_results, dict):
        return None
    if not _claude_repo_validation_ok(probe_results):
        return None
    if not _claude_environment_ok(probe_results):
        return None

    direct_plugin_dir = probe_results.get("direct_plugin_dir")
    if isinstance(direct_plugin_dir, dict):
        if (
            _truthy(direct_plugin_dir.get("flag_supported"))
            and _truthy(direct_plugin_dir.get("configured_checkout_match"))
            and direct_plugin_dir.get("canary_passed") is True
        ):
            return CLAUDE_DIRECT_BRANCH

    marketplace = probe_results.get("marketplace")
    if isinstance(marketplace, dict):
        if (
            _truthy(marketplace.get("registration_supported"))
            and _truthy(marketplace.get("install_supported"))
            and _truthy(marketplace.get("resolved_checkout_match"))
            and marketplace.get("canary_passed") is True
        ):
            return CLAUDE_MARKETPLACE_BRANCH
    return None


def _opencode_repo_validation_ok(probe_results: dict[str, Any]) -> bool:
    repo_validation = probe_results.get("repo_validation")
    return bool(
        isinstance(repo_validation, dict)
        and _truthy(repo_validation.get("plugin_source_file_valid"))
        and _truthy(repo_validation.get("required_skill_inventory_valid"))
        and _truthy(repo_validation.get("workspace_config_valid"))
    )


def select_opencode_proof_branch(probe: dict[str, Any]) -> Optional[str]:
    probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
    if not isinstance(probe_results, dict):
        return None
    if not _opencode_repo_validation_ok(probe_results):
        return None

    run = probe_results.get("run")
    if not isinstance(run, dict) or run.get("canary_passed") is not True:
        return None

    debug = probe_results.get("debug")
    if not isinstance(debug, dict):
        return None

    config_available = _truthy(debug.get("config"))
    config_source_match = _truthy(debug.get("config_source_match"))
    repo_validation = probe_results.get("repo_validation") if isinstance(probe_results.get("repo_validation"), dict) else {}
    workspace_config_valid = _truthy(repo_validation.get("workspace_config_valid"))
    paths_available = _truthy(debug.get("paths"))
    paths_source_match = _truthy(debug.get("paths_source_match"))
    paths_isolation_supported = _truthy(debug.get("paths_isolation_supported"))
    skill_available = _truthy(debug.get("skill"))
    skill_inventory_valid = _truthy(debug.get("skill_inventory_valid"))

    if (
        config_available
        and config_source_match
        and paths_available
        and paths_source_match
        and paths_isolation_supported
        and skill_available
        and skill_inventory_valid
    ):
        return OPENCODE_STRONG_BRANCH

    available_debug_evidence_consistent = (
        (not config_available or config_source_match)
        and (not paths_available or (paths_source_match and paths_isolation_supported))
        and (not skill_available or skill_inventory_valid)
    )
    fallback_debug_surface_missing = not (config_available and paths_available and skill_available)
    if (
        available_debug_evidence_consistent
        and fallback_debug_surface_missing
        and workspace_config_valid
        and paths_available
        and paths_source_match
        and paths_isolation_supported
    ):
        return OPENCODE_FALLBACK_BRANCH
    return None


def select_isolation_profile(probe: dict[str, Any]) -> Optional[str]:
    harness = probe.get("harness") if isinstance(probe, dict) else None
    if harness == "claude":
        branch = select_claude_load_branch(probe)
        if branch is None:
            return None
        probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
        environment = probe_results.get("environment_validation") if isinstance(probe_results, dict) else None
        full_isolation = bool(
            isinstance(environment, dict)
            and _truthy(environment.get("full_isolation_supported"))
            and isinstance(probe_results, dict)
            and _truthy(probe_results.get("full_isolation_auth_compatible"))
        )
        auth_preserving = bool(
            isinstance(probe_results, dict) and _truthy(probe_results.get("auth_preserving_supported"))
        )
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
    probe_results = probe.get("probe_results") if isinstance(probe, dict) else None
    environment = probe_results.get("environment_validation") if isinstance(probe_results, dict) else None
    selected_profile = select_isolation_profile(probe)
    record = {
        "schema_version": 1,
        "harness": harness,
        "cli_version": cli_version,
        "noninteractive": True,
        "structured_output": bool(environment.get("structured_output_supported"))
        if harness == "claude" and isinstance(environment, dict)
        else harness != "claude",
        "local_plugin_loading": selected_profile is not None,
        "session_persistence_disable": bool(environment.get("session_persistence_disable_supported"))
        if harness == "claude" and isinstance(environment, dict)
        else harness != "claude",
        "settings_isolation": selected_profile is not None,
        "auth_preserving_full_isolation": selected_profile in {
            CLAUDE_FULL_DIRECT,
            CLAUDE_FULL_MARKETPLACE,
        },
        "selected_isolation_profile": selected_profile,
        "plugin_proof_strength": _plugin_proof_strength_for_probe(probe),
    }
    if harness == "claude":
        selected_load_branch = select_claude_load_branch(probe)
        record["selected_load_branch"] = selected_load_branch
        record["plugin_load_path"] = selected_load_branch
        record["optional_cli_validation"] = bool(
            isinstance(probe.get("probe_results"), dict)
            and isinstance(probe["probe_results"].get("cli_validation"), dict)
            and _truthy(probe["probe_results"]["cli_validation"].get("supported"))
            and _truthy(probe["probe_results"]["cli_validation"].get("passed"))
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


def _resolve_marketplace_checkout_match(payload: Any, repo_root: str) -> bool:
    if not isinstance(payload, list):
        return False
    for item in payload:
        if not isinstance(item, dict):
            continue
        if item.get("name") != "researchflow":
            continue
        if item.get("path") == repo_root or item.get("source") == repo_root:
            return True
    return False


def _probe_from_claude_dir(config: dict[str, Any], probe_dir: Path) -> tuple[str, dict[str, Any]]:
    repo_root = Path(str(config["repo_root"])).resolve()
    repo_validation = _validate_claude_repo(repo_root)
    help_text = _read_text(probe_dir / "help.txt")
    plugin_help_text = _read_text(probe_dir / "plugin-help.txt")
    environment_validation = _claude_environment_validation(help_text)
    direct_events = _read_jsonl(probe_dir / "direct-canary.jsonl")
    marketplace_events = _read_jsonl(probe_dir / "marketplace-canary.jsonl")
    full_events = _read_jsonl(probe_dir / "full-direct-canary.jsonl")
    marketplace_payload = _read_json_list(probe_dir / "marketplace-list.json")
    direct_canary = _read_status(probe_dir / "direct-canary.status") == 0 and _canary_passed(direct_events)
    marketplace_canary = _read_status(probe_dir / "marketplace-canary.status") == 0 and _canary_passed(marketplace_events)
    full_canary = _read_status(probe_dir / "full-direct-canary.status") == 0 and _canary_passed(full_events)
    auth_preserving_supported = bool(
        _claude_environment_ok(
            {
                "repo_validation": repo_validation,
                "environment_validation": environment_validation,
            }
        )
        and (direct_canary or marketplace_canary)
    )
    probe = {
        "harness": "claude",
        "probe_results": {
            "repo_validation": repo_validation,
            "environment_validation": environment_validation,
            "direct_plugin_dir": {
                "flag_supported": environment_validation["plugin_dir_supported"],
                "configured_checkout_match": repo_root.exists(),
                "canary_passed": direct_canary,
            },
            "marketplace": {
                "registration_supported": "list" in plugin_help_text,
                "install_supported": _read_status(probe_dir / "marketplace-list.status") == 0 and marketplace_payload is not None,
                "resolved_checkout_match": _resolve_marketplace_checkout_match(marketplace_payload, str(repo_root)),
                "canary_passed": marketplace_canary,
            },
            "cli_validation": {
                "supported": "validate" in plugin_help_text,
                "passed": _read_status(probe_dir / "validate.status") == 0,
            },
            "full_isolation_auth_compatible": bool(environment_validation["full_isolation_supported"] and full_canary),
            "auth_preserving_supported": auth_preserving_supported,
        },
    }
    return _read_cli_version(probe_dir / "version.txt"), probe


def _probe_from_opencode_dir(config: dict[str, Any], probe_dir: Path) -> tuple[str, dict[str, Any]]:
    repo_root = Path(str(config["repo_root"])).resolve()
    repo_validation = _validate_opencode_repo(repo_root)
    debug_config_payload = _read_json_object(probe_dir / "debug-config.json")
    debug_paths_payload = _read_json_object(probe_dir / "debug-paths.json")
    debug_skill_payload = _read_json_object(probe_dir / "debug-skill.json")
    debug_config_text = _read_text(probe_dir / "debug-config.json")
    debug_paths_text = _read_text(probe_dir / "debug-paths.json")
    debug_skill_text = _read_text(probe_dir / "debug-skill.json")
    debug_config_status = _read_status(probe_dir / "debug-config.status") == 0
    debug_paths_status = _read_status(probe_dir / "debug-paths.status") == 0
    debug_skill_status = _read_status(probe_dir / "debug-skill.status") == 0
    canary_events = _read_jsonl(probe_dir / "canary.jsonl")
    workspace_config_valid = _validate_opencode_workspace_config(
        probe_dir / "workspace" / "opencode.json",
        str(repo_root),
    )
    repo_validation["workspace_config_valid"] = workspace_config_valid
    config_source_match = debug_config_status and (
        _plugin_path_matches(debug_config_payload, str(repo_root))
        or _plugin_path_matches_text(debug_config_text, str(repo_root))
    )
    workspace_plugin_matches_checkout = bool(workspace_config_valid or config_source_match)
    paths_source_match = debug_paths_status and _opencode_paths_source_match(
        debug_paths_payload,
        debug_paths_text,
        str(repo_root),
    )
    skill_inventory_valid = debug_skill_status and _runtime_skill_inventory_valid(debug_skill_payload or debug_skill_text)
    paths_isolation_supported = debug_paths_status and _opencode_paths_isolation_supported(debug_paths_payload or debug_paths_text)
    probe = {
        "harness": "opencode",
        "workspace_plugin_matches_checkout": workspace_plugin_matches_checkout,
        "probe_results": {
            "repo_validation": repo_validation,
            "debug": {
                "config": debug_config_status,
                "config_source_match": config_source_match,
                "paths": debug_paths_status,
                "paths_source_match": paths_source_match,
                "paths_isolation_supported": paths_isolation_supported,
                "skill": debug_skill_status,
                "skill_inventory_valid": skill_inventory_valid,
            },
            "run": {
                "canary_passed": _read_status(probe_dir / "canary.status") == 0 and _canary_passed(canary_events),
            },
        },
    }
    return _read_cli_version(probe_dir / "version.txt"), probe


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
    return 0


def command_normalize_case(args: argparse.Namespace) -> int:
    config = read_config(Path(args.config))
    cli_version, probe = probe_from_dir(args.harness, config, Path(args.probe_dir))
    capability = build_capability_record(args.harness, cli_version, probe)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    events_path = Path(args.events)
    stderr_path = Path(args.stderr)
    exit_code_text = Path(args.status).read_text(encoding="utf-8").strip()
    exit_code = int(exit_code_text) if exit_code_text else 1
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
