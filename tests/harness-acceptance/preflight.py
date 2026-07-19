#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

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
    RUNTIME_PROOF_UNAVAILABLE,
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
    raw_gate_passed = (
        preflight.get("status") == "pass"
        and isolation_profile_consistent
        and plugin_proof_strength_consistent
        and isinstance(isolation_profile, str)
        and bool(isolation_profile)
        and isinstance(plugin_proof_strength, str)
        and bool(plugin_proof_strength)
        and isinstance(plugin_source_id, str)
        and bool(plugin_source_id)
    )
    proof_gate_passed = raw_gate_passed and inspected["proof_valid"]
    canonical_identity = inspected["canonical_identity"] if proof_gate_passed else None
    return {
        "status": "pass" if raw_gate_passed else "blocked",
        "raw_gate_passed": raw_gate_passed,
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


def determine_preflight_outcome(claude_result: dict[str, Any], opencode_result: dict[str, Any]) -> dict[str, Any]:
    alignment = evaluate_model_alignment(claude_result, opencode_result)
    if alignment["aligned"]:
        return {
            "outcome": "continuation-ready",
            "reason_code": None,
            "canonical_identity": alignment["canonical_identity"],
        }
    raw_gate_passed = bool(claude_result.get("raw_gate_passed")) and bool(opencode_result.get("raw_gate_passed"))
    if (
        raw_gate_passed
        and alignment["reason_code"] == GLOBAL_HARD_GATE_BLOCKED
        and claude_result.get("proof_valid")
        and opencode_result.get("proof_valid")
        and claude_result.get("proof_identity") == opencode_result.get("proof_identity")
        and (claude_result.get("allowlist_missing") or opencode_result.get("allowlist_missing"))
    ):
        return {
            "outcome": "allowlist-update-needed",
            "reason_code": GLOBAL_HARD_GATE_BLOCKED,
            "canonical_identity": None,
        }
    if raw_gate_passed and (not claude_result.get("proof_valid") or not opencode_result.get("proof_valid")):
        return {
            "outcome": "blocked",
            "reason_code": RUNTIME_PROOF_UNAVAILABLE,
            "canonical_identity": None,
        }
    if claude_result.get("status") != "pass" or opencode_result.get("status") != "pass":
        return {
            "outcome": "blocked",
            "reason_code": alignment["reason_code"] or GLOBAL_HARD_GATE_BLOCKED,
            "canonical_identity": None,
        }
    return {
        "outcome": "blocked",
        "reason_code": alignment["reason_code"] or MODEL_ALIGNMENT_BLOCKED,
        "canonical_identity": None,
    }


def load_run_preflight_state(run_dir: Path, harness_dir: Path) -> dict[str, Any]:
    identities = load_identities(harness_dir)
    evaluations = {}
    for harness in ("claude", "opencode"):
        capability = lib.read_json(run_dir / "capabilities" / f"{harness}.json")
        preflight_record = lib.read_json(run_dir / "preflight" / f"{harness}.json")
        model_proof = lib.read_json(run_dir / "preflight" / f"{harness}-model-proof.json")
        evaluations[harness] = evaluate_preflight(capability, preflight_record, model_proof, identities)
    outcome = determine_preflight_outcome(evaluations["claude"], evaluations["opencode"])
    return {
        "outcome": outcome["outcome"],
        "reason_code": outcome["reason_code"],
        "canonical_identity": outcome["canonical_identity"],
        "harnesses": evaluations,
    }


def require_continuation_ready(state: dict[str, Any]) -> None:
    if state.get("outcome") != "continuation-ready":
        raise ValueError(f"run is not continuation-ready: {state.get('outcome')}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--require-aligned", action="store_true")
    args = parser.parse_args(argv)
    state = load_run_preflight_state(Path(args.run_dir), HERE)
    if args.require_aligned:
        require_continuation_ready(state)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
