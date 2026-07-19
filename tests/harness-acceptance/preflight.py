#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import lib  # noqa: E402

(
    _CLAUDE_PREFLIGHT_BLOCKED,
    _OPENCODE_PREFLIGHT_BLOCKED,
    MODEL_ALIGNMENT_BLOCKED,
    GLOBAL_HARD_GATE_BLOCKED,
    _RUNTIME_HARNESS_STOPPED,
) = lib.REASON_CODES


def load_identities(harness_dir: Path) -> dict[str, Any]:
    return lib.read_json(harness_dir / "model-identities.json")


def _inspect_model_proof(value: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]:
    return lib.inspect_model_proof(value, identities)


def _resolve_consistent_gate_value(capability_value: Any, preflight_value: Any) -> tuple[str | None, bool]:
    capability_text = capability_value if isinstance(capability_value, str) and capability_value else None
    preflight_text = preflight_value if isinstance(preflight_value, str) and preflight_value else None
    if capability_text is not None and preflight_text is not None and capability_text != preflight_text:
        return None, False
    return preflight_text or capability_text, True


def evaluate_preflight(capability: dict[str, Any], preflight: dict[str, Any], model_proof: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]:
    inspected = _inspect_model_proof(model_proof, identities)
    isolation_profile, isolation_profile_consistent = _resolve_consistent_gate_value(
        capability.get("selected_isolation_profile"),
        preflight.get("isolation_profile"),
    )
    plugin_proof_strength, plugin_proof_strength_consistent = _resolve_consistent_gate_value(
        capability.get("plugin_proof_strength"),
        preflight.get("plugin_proof_strength"),
    )
    plugin_source_id = preflight.get("plugin_source_id") if isinstance(preflight.get("plugin_source_id"), str) and preflight.get("plugin_source_id") else None
    passed = (
        preflight.get("status") == "pass"
        and isolation_profile_consistent
        and plugin_proof_strength_consistent
        and isinstance(isolation_profile, str)
        and bool(isolation_profile)
        and isinstance(plugin_proof_strength, str)
        and bool(plugin_proof_strength)
        and isinstance(plugin_source_id, str)
        and bool(plugin_source_id)
        and inspected["proof_valid"]
    )
    canonical_identity = inspected["canonical_identity"] if passed else None
    return {
        "status": "pass" if passed and isinstance(inspected["canonical_identity"], str) else "blocked",
        "plugin_source_id": plugin_source_id,
        "plugin_proof_strength": plugin_proof_strength,
        "isolation_profile": isolation_profile,
        "canonical_identity": canonical_identity,
        "proof_identity": inspected["proof_identity"],
        "proof_valid": inspected["proof_valid"],
        "allowlist_missing": inspected["allowlist_missing"],
        "backing_model_id": inspected["backing_model_id"],
    }


def evaluate_model_alignment(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]:
    if claude_result.get("status") != "pass" or opencode_result.get("status") != "pass":
        return {"aligned": False, "canonical_identity": None, "reason_code": GLOBAL_HARD_GATE_BLOCKED}
    claude_identity = claude_result.get("canonical_identity")
    opencode_identity = opencode_result.get("canonical_identity")
    if isinstance(claude_identity, str) and claude_identity == opencode_identity:
        return {"aligned": True, "canonical_identity": claude_identity, "reason_code": None}
    proofs_same_openai = (
        claude_result.get("proof_valid")
        and opencode_result.get("proof_valid")
        and isinstance(claude_result.get("proof_identity"), str)
        and claude_result.get("proof_identity") == opencode_result.get("proof_identity")
    )
    if proofs_same_openai and (claude_result.get("allowlist_missing") or opencode_result.get("allowlist_missing")):
        return {"aligned": False, "canonical_identity": None, "reason_code": GLOBAL_HARD_GATE_BLOCKED}
    return {"aligned": False, "canonical_identity": None, "reason_code": MODEL_ALIGNMENT_BLOCKED}
