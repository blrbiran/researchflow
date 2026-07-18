#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import judge  # noqa: E402
import lib  # noqa: E402
import preflight  # noqa: E402
import summarize  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HARNESS_DIR = ROOT / "tests" / "harness-acceptance"
HARNESSES = ("claude", "opencode")


def _repo_commit_sha() -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_environment_record(run_id: str) -> dict[str, Any]:
    raw_relative_id = f"local-raw/{run_id}"
    raw_sha256 = hashlib.sha256(raw_relative_id.encode("utf-8")).hexdigest()
    return {
        "run_id": run_id,
        "run_kind": "original",
        "redaction_passed": True,
        "raw_artifacts": {
            "relative_id": raw_relative_id,
            "sha256": raw_sha256,
            "manual_review_status": "pending",
            "reason_not_committed": "raw event streams remain local",
        },
        "manual_notes": [],
        "deviations": [],
    }


def build_baseline_record(
    repo_root: Path,
    config: dict[str, Any],
    evaluations: dict[str, dict[str, Any]],
    model_proofs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    harness_dir = repo_root / "tests" / "harness-acceptance"
    record = {
        "schema_version": 1,
        "repo_commit_sha": config["repo_commit_sha"],
        "cases_sha256": lib.sha256_path(harness_dir / "cases.json"),
        "scored_prompt_sha256": lib.sha256_path(harness_dir / "scored-prompt.txt"),
        "timeout_seconds": int(config["timeout_seconds"]),
        "plugin_source_id": config["plugin_source_id"],
        "residual_categories": list(config["residual_categories"]),
        "harnesses": {
            harness: {
                "harness_model_value": config[harness]["harness_model_value"],
                "effort_or_variant": config[harness]["effort_or_variant"],
                "plugin_source_id": evaluations[harness]["plugin_source_id"],
                "plugin_proof_strength": evaluations[harness]["plugin_proof_strength"],
                "selected_isolation_profile": evaluations[harness]["isolation_profile"],
                "canonical_identity": evaluations[harness]["canonical_identity"],
                "proof_sha256": model_proofs[harness]["proof_sha256"],
                "endpoint_identity_sha256": model_proofs[harness]["endpoint_identity_sha256"],
            }
            for harness in HARNESSES
        },
    }
    fingerprint_input = json.dumps(record, sort_keys=True).encode("utf-8")
    record["fingerprint_sha256"] = hashlib.sha256(fingerprint_input).hexdigest()
    return record


def _run_adapter(
    harness: str,
    mode: str,
    config_path: Path,
    output_dir: Path,
    case_id: str | None = None,
) -> None:
    adapter = HARNESS_DIR / "adapters" / f"{harness}.sh"
    command = [
        "bash",
        str(adapter),
        "--mode",
        mode,
        "--config",
        str(config_path),
        "--output-dir",
        str(output_dir),
    ]
    if case_id is not None:
        command.extend(["--case-id", case_id])
    subprocess.run(command, check=True)


def _write_summary_outputs(run_dir: Path, cases: list[dict[str, Any]]) -> None:
    summary_json_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"
    existing_targets = [path for path in (summary_json_path, summary_md_path) if path.exists()]
    if existing_targets:
        if len(existing_targets) == 1:
            raise FileExistsError(existing_targets[0])
        raise FileExistsError("summary.json and summary.md already exist")
    summary = summarize.build_summary(run_dir, cases)
    lib.write_json(summary_json_path, summary)
    summary_md_path.write_text(summarize.render_summary_markdown(summary), encoding="utf-8")


def _write_verdict(case: dict[str, Any], case_dir: Path) -> None:
    invocation = lib.read_json(case_dir / "invocation.json")
    response = (case_dir / "final-response.txt").read_text(encoding="utf-8")
    verdict = judge.judge(case, invocation, response)
    lib.write_json(case_dir / "verdict.json", verdict)


def run_original(config: dict[str, Any], run_id: str, mode: str) -> Path:
    if mode not in {"preflight-only", "scored"}:
        raise ValueError(f"unsupported mode: {mode}")

    results_root = Path(config.get("results_root", HARNESS_DIR / "results"))
    run_dir = results_root / run_id
    preflight_dir = run_dir / "preflight"
    capabilities_dir = run_dir / "capabilities"
    baseline_path = preflight_dir / "baseline.json"
    cases = lib.load_cases(ROOT)
    identities = preflight.load_identities(HARNESS_DIR)

    if mode == "preflight-only":
        if run_dir.exists():
            raise FileExistsError(run_dir)
        lib.write_json(run_dir / "environment.json", build_environment_record(run_id))
    elif not run_dir.exists():
        raise FileNotFoundError(run_dir)

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "run-config.json"
        config_with_run = dict(config)
        config_with_run.setdefault("repo_root", str(ROOT))
        config_with_run.setdefault("repo_commit_sha", _repo_commit_sha())
        config_with_run.setdefault("endpoint_identity", "https://redacted.invalid/v1")
        config_with_run["run_id"] = run_id
        config_path.write_text(json.dumps(config_with_run, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if mode == "preflight-only":
            evaluations: dict[str, dict[str, Any]] = {}
            model_proofs: dict[str, dict[str, Any]] = {}
            for harness in HARNESSES:
                _run_adapter(harness, "capability", config_path, capabilities_dir)
                _run_adapter(harness, "preflight", config_path, preflight_dir)
                capability = lib.read_json(capabilities_dir / f"{harness}.json")
                preflight_record = lib.read_json(preflight_dir / f"{harness}.json")
                model_proof = lib.read_json(preflight_dir / f"{harness}-model-proof.json")
                evaluations[harness] = preflight.evaluate_preflight(capability, preflight_record, model_proof, identities)
                model_proofs[harness] = model_proof
            alignment = preflight.evaluate_model_alignment(evaluations["claude"], evaluations["opencode"])
            if alignment["aligned"]:
                lib.write_json(
                    baseline_path,
                    build_baseline_record(ROOT, config_with_run, evaluations, model_proofs),
                )
                return run_dir
            _write_summary_outputs(run_dir, cases)
            return run_dir

        baseline = lib.read_json(baseline_path)
        expected_baseline = build_baseline_record(
            ROOT,
            config_with_run,
            {
                harness: preflight.evaluate_preflight(
                    lib.read_json(capabilities_dir / f"{harness}.json"),
                    lib.read_json(preflight_dir / f"{harness}.json"),
                    lib.read_json(preflight_dir / f"{harness}-model-proof.json"),
                    identities,
                )
                for harness in HARNESSES
            },
            {harness: lib.read_json(preflight_dir / f"{harness}-model-proof.json") for harness in HARNESSES},
        )
        if baseline != expected_baseline:
            raise ValueError("baseline fingerprint mismatch")
        if (run_dir / "summary.json").exists():
            raise ValueError("scored phase already completed")
        for harness in HARNESSES:
            harness_dir = run_dir / harness
            if harness_dir.exists() and any(path.is_dir() for path in harness_dir.iterdir()):
                raise ValueError("existing case artifact prevents scored continuation")
            for case in cases:
                case_dir = harness_dir / case["case_id"]
                _run_adapter(harness, "case", config_path, case_dir, case["case_id"])
                _write_verdict(case, case_dir)
        _write_summary_outputs(run_dir, cases)
        return run_dir
