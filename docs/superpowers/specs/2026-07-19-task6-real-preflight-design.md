# ResearchFlow Task 6 Real Preflight-Only Design Spec

Date: 2026-07-19  
Status: Approved for implementation planning  
Topic: Real preflight-only gate and continuation-ready run preparation for live harness acceptance

## 1. Purpose

This spec defines Task 6 as the first real-environment execution stage after Task 5 synthetic preflight/orchestration.

Task 6 does not score routing decisions. It does not prove acceptance success. It does not run the seven shared cases. Its job is narrower and more foundational:

> Determine whether the real Claude Code and OpenCode environments satisfy every hard gate required to enter Task 7 scored execution, and record either a continuation-ready run or a fully auditable blocked run.

This design assumes Task 5 is complete and already provides:

- a synthetic-only monotonic run model;
- preflight and alignment judgment in `tests/harness-acceptance/preflight.py`;
- blocked/final summary reconstruction in `tests/harness-acceptance/summarize.py`;
- run orchestration in `tests/harness-acceptance/run.py`;
- synthetic-only test entrypoints in `tests/harness-acceptance/run-tests.sh` and `tests/run-all.sh`.

## 2. Scope and constraints

In scope:

- real `--mode preflight-only` execution using the existing harness acceptance runner;
- real capability, plugin-proof, and model-proof artifact capture;
- real redaction and summary reconstruction against preflight-only artifacts;
- operator workflow for reviewing redacted proof artifacts;
- strict handling of first-seen backing-model allowlist gaps;
- producing one of three outcomes: `blocked`, `allowlist-update-needed`, or `continuation-ready`;
- machine-readable blocked sub-reasons, including `runtime-proof-unavailable` when a harness can execute preflight successfully but cannot emit authoritative runtime model proof.

Out of scope:

- scored case execution;
- proving routing correctness;
- retrying or reusing a blocked run;
- updating router behavior or workflow contracts;
- release readiness claims;
- version bump, publish, or push.

## 3. Task 6 goal and completion definition

Task 6 answers only one question:

> Is the real environment eligible to begin Task 7 scored execution?

It validates four things in real conditions:

1. real capability and plugin-load proof for both harnesses;
2. redacted real model-proof generation for both harnesses;
3. exact same verified canonical `openai/<model>` identity across both harnesses;
4. successful redaction and deterministic summary reconstruction over the real preflight artifact set.

Task 6 has exactly three terminal outcomes:

### 3.1 `blocked`

Any hard gate fails:

- capability/plugin proof is incomplete;
- redacted model proof cannot be established;
- canonical identities differ;
- a provider or proof validity rule fails;
- redaction fails;
- deterministic summary reconstruction fails.

The run is closed as blocked evidence and never continues to Task 7.

Blocked execution may carry a machine-readable sub-reason. One required blocked sub-reason is `runtime-proof-unavailable`.

### 3.1.1 `runtime-proof-unavailable`

`runtime-proof-unavailable` is a blocked result, not a fourth top-level terminal outcome.

It applies when:

- a harness passes capability and preflight evidence;
- the harness can execute the real preflight canary under the selected isolation/plugin proof path;
- but the harness does not emit authoritative runtime model proof sufficient to establish `backing_model_id`, `resolved_model_identity`, and `verified = true` from committed redacted artifacts.

This blocked sub-reason is required so Task 6 can distinguish between:

- a harness that could not run correctly at all; and
- a harness that ran correctly but whose runtime proof surface was insufficient for model-identity verification.

A `runtime-proof-unavailable` run must remain blocked even if static configuration appears to name a model that would otherwise look aligned.

### 3.2 `allowlist-update-needed`

Both real harnesses prove the same backing model, but that model is not yet present in `model-identities.json`.

This is a special case of blocked execution with a distinct next step:

- the current run is closed and preserved;
- the redacted proofs are manually reviewed;
- the exact canonical mapping is added in a separate commit;
- a brand new preflight-only run is started.

The original run never becomes a scored continuation base.

This outcome must also be machine-distinguishable from ordinary blocked execution. The committed blocked summary must therefore expose an explicit outcome marker such as `allowlist-update-needed`, rather than requiring an operator to infer the distinction only from prose.

The run may still share the same blocked artifact shape as other blocked runs, but the summary/result payload must preserve the semantic difference in a deterministic field or reason marker.

### 3.2.1 Outcome marker requirement

Task 6 must make all three terminal outcomes reconstructable from committed artifacts alone:

- `blocked`
- `allowlist-update-needed`
- `continuation-ready`

For blocked-style runs, that means the summary payload must distinguish ordinary blocked results, `runtime-proof-unavailable`, and allowlist-update-needed results via machine-readable fields, not only human-readable notes.

The exact field name may be decided at implementation time, but the distinction itself is required.

Possible acceptable shapes include:

- `summary.json.outcome = "allowlist-update-needed"`
- or an equivalent dedicated reason/outcome marker that survives deterministic reconstruction.

A plain blocked summary with no machine-readable distinction is insufficient.

The design intent is that future operator steps and Task 7 gating logic can classify the run without reinterpreting prose.

### 3.3 `continuation-ready`

All real preflight gates pass, both redacted model proofs verify the same canonical identity, redaction succeeds, and the run directory is valid for Task 7 continuation.

This run directory becomes the only legal starting point for Task 7 scored execution.

Task 6 is complete when it produces either a blocked/allowlist-update-needed evidence set or a continuation-ready run. It is not complete merely because a real command executed.

## 4. Run directory and lifecycle model

Task 6 must reuse the Task 5 monotonic run model rather than introducing a new execution shape.

The root remains:

`tests/harness-acceptance/results/<run-id>/`

### 4.1 Shared run semantics

A Task 6 run may only move forward:

1. create run root;
2. write capability artifacts;
3. write preflight and model-proof artifacts;
4. either stop as blocked evidence or stop as continuation-ready baseline.

Task 6 does not enter scored execution.

### 4.2 Required real artifacts

For every real Task 6 run, the committed artifact tree must be sufficient to support either blocked auditing or Task 7 continuation.

Expected artifacts:

- `capabilities/claude.json`
- `capabilities/opencode.json`
- `preflight/claude.json`
- `preflight/opencode.json`
- `preflight/claude-model-proof.json`
- `preflight/opencode-model-proof.json`
- `environment.json`

If the run is blocked or allowlist-update-needed, it must also write:

- `summary.json`
- `summary.md`

If the run is continuation-ready, it must instead write:

- `preflight/baseline.json`

and must not write final summary artifacts yet.

### 4.3 Run permanence

A blocked or allowlist-update-needed run is final. It is evidence, not a workspace to resume.

A continuation-ready run is resumable only by Task 7 scored execution under the same monotonic runner rules.

No Task 6 run may be retroactively converted from blocked to continuation-ready.

## 5. Model identity and allowlist handling

Task 6 must not infer backing-model identity from route labels, aliases, local config, or other static configuration surfaces.

The only acceptable source of canonical model identity remains real redacted proof.

Static declarations may support diagnosis, but they are not proof. In particular, Task 6 must not treat any of the following as canonical model proof:

- Claude route aliases such as `sonnet`;
- OpenCode route labels such as `openai-compatible/gpt-5.4`;
- `run-config.local.json` values;
- `~/.config/opencode/opencode.jsonc` model/provider settings;
- `debug-config` or equivalent resolved configuration dumps.

### 5.1 Same-model rule

Task 6 passes only if both harnesses prove the same verified canonical `openai/<model>` identity.

If they do not match, the run is `blocked`.

### 5.2 Allowlist gap rule

If both harnesses prove the same backing model but that backing model is absent from `model-identities.json`, the run is `allowlist-update-needed`.

The required flow is strict:

1. real preflight generates redacted proofs;
2. the run is stopped and preserved as blocked evidence;
3. a human reviews the redacted proofs;
4. the exact `backing_model_id -> openai/<model>` mapping is added in a separate commit;
5. a new Task 6 run starts with a new `run-id`.

The original run must never continue into Task 7 after an allowlist update.

### 5.3 Separation of concerns

This separates three auditable events:

- first real proof of backing-model identity;
- explicit allowlist update;
- first continuation-ready preflight run under the updated allowlist.

That separation is more important than avoiding an extra preflight run.

## 6. Operator workflow

Task 6 is a real execution path and therefore includes explicit operator steps.

The fixed operator flow is:

1. re-run the full synthetic baseline;
2. prepare `run-config.local.json` without secrets in the file itself;
3. allocate a new `run-id`;
4. execute `--mode preflight-only`;
5. run redaction scan, then run summary reconstruction/check-only only for blocked-style outcomes;
6. manually review redacted model proofs and the resulting blocked preflight summary when present;
7. classify outcome as `blocked`, `allowlist-update-needed`, or `continuation-ready`.

If either harness proves runtime viability yet cannot emit authoritative runtime model proof, the operator must classify the run as `blocked` with reason `runtime-proof-unavailable`. The current motivating case is Claude proving a canonical model identity while OpenCode passes capability/preflight but cannot emit authoritative runtime model proof.

For a `continuation-ready` preflight-only run, Task 6 does not require final summary artifacts and therefore does not require `summarize --check-only` to succeed against a non-existent final summary. In that outcome, the validation target is the preflight artifact set plus `preflight/baseline.json`, not `summary.json` / `summary.md`.

### 6.1 Local config rules

`run-config.local.json` may provide only local operational values that the runner expects, such as harness route selection, effort/variant, timeout, and any local paths explicitly required by the accepted Task 5 runner shape.

It must not commit secrets, raw endpoints, or environment dumps.

### 6.2 Manual review gate

The operator review after preflight is mandatory.

The review checks:

- both `*-model-proof.json` files are redacted and self-consistent;
- both harnesses resolve to the same canonical identity or clearly fail to do so;
- plugin/load/isolation evidence is coherent;
- the summary accurately states blocked vs continuation-ready status.

The review is not about scored routing correctness. Task 6 does not answer that question.

### 6.3 No opportunistic scoring

The operator must not “just try one scored case” from Task 6. Doing so crosses into Task 7 and invalidates the boundary this design is trying to preserve.

## 7. Evidence and result semantics

### 7.1 Blocked result

A blocked Task 6 run must produce complete blocked accounting via `summary.json` and `summary.md`.

The blocked summary must make it clear which gate failed and why scoring did not begin.

### 7.2 Allowlist-update-needed result

An allowlist-update-needed run uses the same blocked artifact shape as other blocked runs, but the operator next step differs:

- do not discard the run;
- do not continue it;
- use it as the review basis for the allowlist update;
- rerun preflight under a new `run-id` afterward.

Unlike ordinary blocked results, this outcome must carry an explicit machine-readable outcome marker in the committed summary/result payload so later tooling and operator steps can distinguish it without re-reading prose.

### 7.3 Continuation-ready result

A continuation-ready run must leave behind a complete preflight basis for Task 7:

- capability records;
- preflight records;
- model proofs;
- environment metadata;
- baseline metadata.

It must not create final summary artifacts yet, because that would incorrectly imply the run is complete as acceptance evidence.

## 8. Testing and verification expectations

Task 6 should add only the synthetic coverage necessary to support the real preflight-only flow.

High-value verification targets:

- blocked vs allowlist-update-needed distinction is represented correctly in accounting/review outputs;
- continuation-ready preflight-only runs write baseline without final summary;
- blocked real preflight runs always emit complete blocked summaries;
- redaction and `summarize --check-only` work over real preflight artifact shapes.

Task 6 should not broaden into new scored-routing tests.

## 9. Non-goals and allowed language

### 9.1 Non-goals

Task 6 does not:

- run scored cases;
- prove routing correctness;
- claim acceptance success;
- prove release readiness;
- update router behavior;
- update workflow contracts;
- reuse a blocked run after an allowlist update.

### 9.2 Reporting language

Allowed language:

- `real preflight passed and run is continuation-ready`
- `real preflight blocked on model alignment`
- `real preflight requires allowlist update`

Disallowed language:

- `acceptance passed`
- `routing is correct`
- `release ready`

## 10. Recommended design summary

Task 6 should be implemented as a real preflight-only hard gate that reuses the Task 5 monotonic runner model.

The recommended design is:

- run real `preflight-only` only;
- preserve blocked and allowlist-update-needed runs as final evidence;
- require a new run after any allowlist update;
- treat continuation-ready runs as the sole legal Task 7 entrypoint;
- include explicit operator review and redaction checks;
- keep all result language focused on scored eligibility, not routing correctness.

This is the smallest design that moves the project forward while preserving strong auditability and a clean handoff into Task 7.