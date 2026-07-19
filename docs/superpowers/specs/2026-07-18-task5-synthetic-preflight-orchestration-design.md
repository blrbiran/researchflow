# ResearchFlow Task 5 Synthetic Preflight / Orchestration Design Spec

Date: 2026-07-18  
Status: Approved for implementation planning  
Topic: Minimal-change Task 5 synthetic preflight, same-model hard gate, and run orchestration

## 1. Purpose

This spec narrows Task 5 of the live-harness acceptance plan to the smallest implementation that usefully advances the project after Task 4 synthetic closure.

The immediate goal is not to optimize structure or prepare every later live-run edge in advance. The goal is to make the synthetic gate real: preflight must deterministically decide whether a run may proceed, blocked runs must produce complete machine-accounted artifacts, and the orchestrator must make it impossible to accidentally enter scored execution before the required gates pass.

This spec assumes the current baseline described in `docs/handover/researchwork-plugin-handover.md`:

- Task 4 is synthetically review-closed on `main`.
- Router behavior and workflow contracts are already settled.
- No real Claude Code, OpenCode, LiteLLM, network, or paid-model run is authorized in Task 5.

## 2. Scope and constraints

Task 5 is intentionally narrow.

In scope:

- add `tests/harness-acceptance/preflight.py`;
- add `tests/harness-acceptance/run.py` and `run.sh`;
- add `tests/harness-acceptance/run-config.example.json`;
- add `test_preflight.py`, `test_run.py`, and `tests/harness-acceptance/run-tests.sh`;
- wire Task 5 synthetic tests into `tests/run-all.sh`;
- reuse Task 4 capability and adapter outputs as the upstream proof inputs.

Out of scope:

- changing `skills/using-researchflow/SKILL.md`;
- changing `docs/workflow-contracts.md`;
- reopening Task 4 unless a concrete regression appears;
- introducing real harness runs;
- redesigning the Task 4 adapter boundary;
- adding abstractions aimed mainly at Task 6 or Task 7;
- version bumps, release work, publish, or push.

The implementation preference is explicit: minimum change over elegance. If a choice exists between a cleaner refactor and a direct extension of the current Task 4 shape, Task 5 chooses the direct extension.

## 3. Architecture boundaries

### 3.1 `preflight.py`

`tests/harness-acceptance/preflight.py` owns preflight judgment only.

It consumes already-normalized capability, plugin-proof, and model-proof inputs and produces two kinds of decisions:

1. single-harness preflight status; and
2. cross-harness model-alignment status.

It does not invoke scored cases, manage run directories, or decide retry behavior.

Its core responsibilities are:

- decide whether one harness is preflight-ready;
- fail closed when capability, plugin proof, profile selection, or model proof is incomplete;
- validate that each harness resolves to a verified canonical `openai/<model>` identity before scored execution is allowed;
- produce machine-readable blocked reasons that the runner can expand into 14-row case accounting.

### 3.2 `run.py`

`tests/harness-acceptance/run.py` owns run orchestration and state rules.

It is the only Task 5 component that knows about run modes and phase ordering. It exposes a single run model with two modes:

- `preflight-only`
- `scored`

Its responsibilities are:

- create and guard the run directory;
- enforce no-overwrite behavior;
- enforce the fixed execution order;
- refuse any case execution until preflight and alignment succeed;
- write complete blocked accounting when execution cannot proceed;
- reject illegal state transitions such as duplicate preflight or duplicate scored execution.

It should remain thin. Capability logic stays in Task 4 code; preflight judgment stays in `preflight.py`; verdict logic stays in the existing judge and summary modules.

### 3.3 `run.sh`

`tests/harness-acceptance/run.sh` is only a stable shell entrypoint. It forwards arguments, provides a predictable operator command, and does not contain business logic.

### 3.4 Tests and synthetic entrypoints

`test_preflight.py` and `test_run.py` lock the new Task 5 behavior at the synthetic layer.

`tests/harness-acceptance/run-tests.sh` runs only synthetic unittest discovery.

`tests/run-all.sh` may call that synthetic entrypoint, but it must remain incapable of launching a real paid or network-backed acceptance run.

## 4. Run lifecycle and data flow

### 4.1 Single monotonic run model

Task 5 models one run as a monotonic lifecycle rooted at:

`tests/harness-acceptance/results/<run-id>/`

A run may move forward, but never backward:

1. create the run root;
2. record capability artifacts;
3. record preflight and model-proof artifacts;
4. either stop after preflight or continue to scored execution;
5. record summary artifacts.

A run must never overwrite an existing artifact to “continue.” If a prior attempt produced incompatible state, the operator creates a new run ID.

### 4.2 `preflight-only`

`preflight-only` is the first legal phase for every run.

It is responsible for:

- reading or generating both harness capability results;
- evaluating both harness preflight outcomes;
- evaluating cross-harness alignment;
- writing the redacted preflight/model-proof artifacts needed for later review;
- writing complete blocked accounting when any hard gate prevents scored execution.

When preflight is aligned and eligible to continue later, `preflight-only` writes capability artifacts, preflight/model-proof artifacts, and the stored baseline metadata needed by `scored`, but it does not write a final `summary.json`, a final `summary.md`, or 14 `unattempted` case-accounting rows. Those are written at this stage only for blocked runs.

It must not invoke a scored case under any circumstance.

### 4.3 `scored`

`scored` may continue an existing run only when all of the following hold:

- the run root already exists;
- required preflight artifacts already exist;
- those preflight artifacts show aligned pass status;
- no case artifact exists yet;
- no prior scored phase has completed;
- the stored preflight baseline still matches the allowlisted run configuration and proof inputs recorded for that run.

When those checks pass, `scored` proceeds in fixed order:

1. Claude cases in manifest order;
2. Claude completeness check;
3. OpenCode cases in manifest order;
4. OpenCode completeness check;
5. summary and redaction steps.

Task 5 does not need to optimize this flow. It only needs to make the flow impossible to enter incorrectly.

### 4.4 Preflight baseline consistency

To keep Task 5 minimal while still preventing unsafe continuation, the run stores an allowlisted baseline fingerprint derived from the inputs that matter to scored eligibility: selected profile IDs, proof hashes, canonical model identities, non-secret run-config fields, the current `repo_commit_sha`, the hash of `tests/harness-acceptance/cases.json`, and the hash of `tests/harness-acceptance/scored-prompt.txt`.

`scored` must compare the current allowlisted fingerprint to the stored one and refuse continuation on mismatch.

This avoids a broader state-machine abstraction while still enforcing the approved rule that scored execution cannot continue from a changed preflight basis.

## 5. Blocked accounting and summary semantics

Task 5 should optimize for clear blocked semantics before it optimizes the happy path.

### 5.1 Reason-coded unattempted accounting

When scored execution is blocked, the run still produces a complete 14-row accounting set.

The required meanings are:

- if only Claude preflight blocks, Claude’s seven rows use `claude_preflight_blocked` and OpenCode’s seven rows use `global_hard_gate_blocked`;
- if only OpenCode preflight blocks, OpenCode’s seven rows use `opencode_preflight_blocked` and Claude’s seven rows use `global_hard_gate_blocked`;
- if both harnesses preflight-block independently, each harness uses its own harness-specific preflight code for its seven rows;
- if both preflights pass but model alignment fails, all 14 rows use `model_alignment_blocked`;
- if scored execution starts and then one harness stops at runtime, completed cases retain real verdicts and remaining cases on the affected harness use `runtime_harness_stopped`.

Task 5 does not need live evidence to make these semantics real. It only needs deterministic synthetic coverage.

### 5.2 Summary meaning

`summary.json` and `summary.md` must already be reconstructable for blocked runs.

A blocked run is still complete when:

- both harness preflight outcomes are recorded;
- every expected case is represented by either a real verdict or a reason-coded `unattempted` row;
- no expected case disappears silently.

An aligned `preflight-only` run is not yet final and therefore is not required to emit the final summary or 14-row accounting set. It exists only to establish the reviewable preflight basis that a later `scored` phase may continue.

`run_complete` therefore means full accounting, not “all scored cases ran.”

This distinction is important because Task 5 exists to make preflight and blocking auditable before any real live run is attempted.

## 6. Testing strategy

### 6.1 `test_preflight.py`

`test_preflight.py` should focus on correctness of preflight decisions rather than CLI mechanics.

Minimum coverage:

- Claude optional validation present or absent still yields the correct branch decision;
- OpenCode strong-proof and fallback-proof paths are each accepted or blocked correctly;
- missing or inconsistent profile IDs fail closed;
- incomplete plugin proof fails closed;
- verified, unverified, mismatched, and aligned model proofs produce the correct outcomes;
- exact aligned canonical identities are required before scored execution becomes legal.

### 6.2 `test_run.py`

`test_run.py` should focus on orchestration state correctness.

Minimum coverage:

- `preflight-only` never invokes a case;
- blocked runs generate complete 14-row accounting;
- scored execution is rejected when alignment has not passed;
- duplicate `preflight-only` is rejected;
- duplicate `scored` is rejected;
- scored execution is rejected when case artifacts already exist;
- scored execution is rejected when the stored preflight baseline fingerprint no longer matches.

### 6.3 Synthetic-only baseline

`tests/harness-acceptance/run-tests.sh` must run only synthetic tests.

`tests/run-all.sh` remains a safe repository-wide synthetic baseline. Adding Task 5 there must not create any path that invokes real Claude, OpenCode, LiteLLM, network services, or paid models.

## 7. Non-goals

Task 5 intentionally does not solve everything that later tasks will need.

It does not:

- package live evidence;
- claim acceptance success;
- prove a real backing model;
- optimize operator UX for reruns;
- centralize every schema into a new shared framework;
- redesign adapters for elegance;
- or anticipate future router expansion.

Those may become legitimate later tasks. They are not required to complete the synthetic gate.

## 8. Success criteria

Task 5 is complete when all of the following are true:

- preflight decisions are made in `preflight.py` rather than spread across shell entrypoints;
- run state transitions are enforced in `run.py`;
- blocked paths generate deterministic 14-row accounting;
- `preflight-only` is guaranteed not to invoke cases;
- `scored` is guaranteed not to run without an aligned unchanged preflight baseline;
- the new tests cover these rules synthetically;
- `tests/harness-acceptance/run-tests.sh` and `tests/run-all.sh` remain safe synthetic-only commands.

That is enough for Task 5. The design deliberately stops there so implementation can stay close to the existing plan and current repository state.