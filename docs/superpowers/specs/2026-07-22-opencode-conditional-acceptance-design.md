# ResearchFlow OpenCode Conditional Acceptance Design

Date: 2026-07-22  
Status: Draft for review  
Topic: Redefine Task 6 / Task 7 acceptance semantics so OpenCode can proceed without authoritative runtime proof under an explicitly weaker acceptance class.

## 1. Purpose

This design changes the ResearchFlow acceptance contract after repeated real-world evidence showed that the current OpenCode non-interactive path can pass capability and preflight while still failing to emit authoritative runtime model proof.

The latest committed real evidence is:

- `tests/harness-acceptance/results/2026-07-19T152433Z/` — historical blocked old-contract evidence
- `tests/harness-acceptance/results/2026-07-22T143702Z/` — current-contract blocked evidence showing:
  - Claude authoritative runtime proof present
  - OpenCode capability / preflight pass present
  - OpenCode runtime proof still unavailable
  - final outcome `blocked` with `reason_code = runtime-proof-unavailable`

The purpose of this design is not to invent proof that OpenCode does not have. It is to redefine what ResearchFlow is allowed to conclude when OpenCode behaves correctly enough to run and score cases, but still lacks authoritative runtime proof.

The accepted product decision is:

- keep the current strong acceptance path;
- add a weaker explicit acceptance class named **OpenCode conditional acceptance**;
- allow Task 7 scored execution on that weaker path;
- require Claude authoritative runtime proof even on the weaker path;
- continue to disclose that OpenCode runtime model identity is not authoritatively proved.

## 2. Problem statement

Today the contract treats OpenCode runtime-proof absence as a hard blocker for Task 7.

That was reasonable when the goal was one single acceptance claim:

> both harnesses proved the same authoritative runtime model identity and then passed scored routing evaluation.

Current evidence shows that this single-claim contract is too rigid for the actual OpenCode surface:

- OpenCode can prove plugin loading and preflight execution under the current repo contract;
- OpenCode can execute the canary successfully;
- OpenCode still does not emit authoritative runtime proof from the accepted current-run preflight artifacts;
- therefore Task 7 cannot start, even though the remaining uncertainty is narrower than a total harness failure.

If the project keeps the current contract unchanged, future work can remain blocked indefinitely on an upstream proof surface that may never exist in a form this repo can consume.

If the project simply drops the proof requirement entirely, it would overstate what acceptance means and erase the distinction between:

- a harness whose runtime model identity is proved; and
- a harness whose routing behavior passed but whose runtime model identity remains unproved.

The required solution is a contract split, not a proof fiction.

## 3. Goals

This design must:

1. preserve the existing strong acceptance claim as the strongest possible result;
2. introduce a weaker acceptance path for OpenCode that is honest about missing runtime proof;
3. allow Task 7 scored execution on that weaker path;
4. require Claude authoritative runtime proof even on the weaker path;
5. keep OpenCode capability / preflight pass as the minimum OpenCode gate for the weaker path;
6. prevent anyone from confusing the weaker path with full cross-harness same-model acceptance;
7. avoid changing the current trusted proof boundary or inventing a new proof source.

## 4. Non-goals

This design does not:

- modify `reference/opencode`;
- treat static config, route labels, or debug diagnostics as authoritative runtime proof;
- relax Claude proof requirements;
- rewrite historical evidence in place;
- claim OpenCode and Claude are aligned on the same verified runtime model when OpenCode proof is absent;
- remove the existing strong acceptance path.

## 5. Options considered

### Option 1 — keep the current contract unchanged

Task 7 remains blocked until OpenCode authoritative runtime proof exists.

**Pros:** strongest claim integrity; no semantic changes.  
**Cons:** repeated time sink on a surface that current evidence still does not expose; Task 7 may remain blocked indefinitely.

### Option 2 — fully relax OpenCode proof requirements

Allow Task 7 whenever OpenCode capability / preflight passes, without distinguishing strong vs weak acceptance.

**Pros:** maximum forward progress.  
**Cons:** acceptance wording becomes misleading because the same final label would cover both proved and unproved OpenCode runtime identity.

### Option 3 — split acceptance into strong and conditional classes

Keep strong acceptance unchanged, but add a second official path that allows Task 7 with Claude authoritative proof plus OpenCode capability / preflight pass even when OpenCode runtime proof is unavailable.

**Pros:** preserves truthfulness, enables progress, and keeps claim strength explicit.  
**Cons:** introduces new outcome/summary vocabulary and requires consumers to understand two acceptance classes.

## 6. Chosen design

Choose **Option 3**.

ResearchFlow should treat OpenCode missing runtime proof as a disclosed acceptance condition rather than an unconditional Task 7 stop, but only when all of the following hold:

- Claude authoritative runtime proof exists;
- OpenCode capability / preflight passes under the current current-repo contract;
- OpenCode runtime proof is unavailable from the accepted current-run preflight artifacts;
- no other hard gate fails.

This path must produce a separate acceptance class:

> **OpenCode conditional acceptance**

That label is not a note or a prose aside. It is a first-class contract result.

## 7. Acceptance classes

### 7.1 Strong acceptance

Strong acceptance remains the highest-grade result.

It requires:

- Claude authoritative runtime proof;
- OpenCode authoritative runtime proof;
- both harnesses proving identities that satisfy the current alignment rules;
- scored execution succeeding under the existing Task 7 rules.

Only this class supports the strong claim that both harnesses were evaluated under a verified cross-harness runtime-model alignment condition.

### 7.2 OpenCode conditional acceptance

OpenCode conditional acceptance is the new weaker class.

It requires:

- Claude authoritative runtime proof;
- Claude `canonical_identity` already available under the allowlist, not merely `proof_valid = true`;
- OpenCode capability / preflight pass;
- OpenCode runtime proof unavailable from accepted current-run proof artifacts;
- no redaction, contamination, or other hard-gate failure;
- Task 7 scored execution succeeding under the bounded existing scoring rules.

It explicitly means:

- OpenCode behavior was accepted under the current runtime environment;
- OpenCode runtime model identity was **not** authoritatively proved;
- the result must **not** be treated as strong cross-harness same-model acceptance.

A Claude allowlist gap is therefore still disqualifying for the conditional path. If Claude has real proof but has not yet resolved to a canonical allowlisted identity, the run remains in the allowlist-update-needed flow rather than entering conditional acceptance.

### 7.2.1 Acceptance-passed rule

`OpenCode conditional acceptance` counts as an acceptance pass.

Future Task 7 summary/result payloads should therefore treat both strong and conditional acceptance as:

- `acceptance_passed = true`

and distinguish them through a separate machine-readable acceptance class field rather than by setting conditional acceptance to a failed or blocked state.

That field should expose at least:

- `acceptance_class = "strong"`
- `acceptance_class = "conditional-opencode"`

This keeps the boolean “did this run end in an accepted state?” separate from the stronger question “what kind of accepted state was it?”

### 7.3 Blocked

The run remains blocked when any of the following hold:

- Claude authoritative proof is missing or invalid;
- OpenCode capability / preflight fails;
- redaction fails;
- contamination or other current hard gates fail;
- strong acceptance is impossible and conditional acceptance prerequisites are also not met.

## 8. Task 6 contract changes

### 8.1 Task 6 no longer has a single continuation-ready state

Task 6 must distinguish three forward-classification states:

1. `blocked`
2. `continuation-ready-strong`
3. `continuation-ready-conditional`

This is the minimum change needed to let Task 7 continue without pretending conditional and strong paths are equivalent.

### 8.2 Strong continuation-ready

`continuation-ready-strong` means:

- both harnesses pass capability / preflight;
- both harnesses provide authoritative runtime proof;
- current alignment rules pass.

This is the existing meaning of continuation readiness, renamed to make room for the weaker class.

### 8.3 Conditional continuation-ready

`continuation-ready-conditional` means:

- Claude proof is authoritative and valid;
- Claude `canonical_identity` is available under the allowlist;
- OpenCode capability / preflight passes;
- OpenCode runtime proof is unavailable;
- no other hard gate blocks the run.

Under this design, `runtime-proof-unavailable` is no longer an automatic Task 7 blocker when it appears only on the OpenCode side and Claude proof remains authoritative.

A Claude allowlist gap still routes the run to `allowlist-update-needed`, not to `continuation-ready-conditional`.

### 8.3.1 Machine-readable proof fact

Under the new contract, OpenCode runtime-proof absence must be represented as a machine-readable proof fact that is distinct from the final outcome classification.

Recommended minimal shape:

```json
{
  "outcome": "continuation-ready-conditional",
  "reason_code": null,
  "proof_facts": {
    "opencode_runtime_proof": "unavailable"
  }
}
```

This separates:

- the evidence fact: OpenCode runtime proof is unavailable;
- the decision: the run may still continue on the conditional path.

For genuinely blocked outcomes, `reason_code = "runtime-proof-unavailable"` remains valid when the contract still intends that fact to terminate execution.

### 8.4 Required implementation scope correction

`tests/harness-acceptance/run.py` must be part of the first implementation scope.

The current runner writes `preflight/baseline.json` only when preflight alignment is already strong enough to satisfy the old single `continuation-ready` contract, and the scored phase rechecks that same aligned baseline before execution.

That means a decision-layer-only change is insufficient: without a corresponding `run.py` change, `continuation-ready-conditional` would exist in documentation but would still be unable to enter Task 7 through the actual runner.

The first implementation scope must therefore include:

- `tests/harness-acceptance/run.py`

alongside the preflight/summary logic and tests.

### 8.5 Blocked conditions after this change

The following remain blocked:

- missing or invalid Claude authoritative proof;
- Claude proof that is real but still unresolved at the allowlist/canonical-identity layer;
- failed OpenCode capability / preflight;
- OpenCode strong-path misalignment when both proofs exist and disagree;
- redaction failures;
- contamination and other current hard failures.

The only case being relaxed is:

- Claude proof authoritative and canonicalized;
- OpenCode capability / preflight pass;
- OpenCode runtime proof unavailable.

That case now becomes `continuation-ready-conditional` instead of `blocked`.

### 8.6 Allowlist-update-needed interaction

`allowlist-update-needed` remains a stronger precedence rule than conditional continuation.

If Claude and/or OpenCode establish real backing-model proof that is sufficient to identify a same-model allowlist gap, the run must continue to use the existing allowlist-update-needed path rather than skipping directly into conditional continuation.

This design intentionally keeps the allowlist workflow intact so the only relaxed axis is OpenCode runtime-proof absence after Claude already anchors the run with a canonical identity.

Conditional continuation is therefore **not** a shortcut around canonical model registration.

## 9. Task 7 contract changes

### 9.1 Task 7 may begin from either continuation class

Task 7 can now legally start from:

- `continuation-ready-strong`; or
- `continuation-ready-conditional`

Task 7 must not erase which entry class it inherited.

### 9.2 Task 7 final outcomes

Task 7 final results should use `outcome` only for the top-level terminal state, with strong vs conditional meaning carried by `acceptance_class`.

Recommended terminal states:

1. `outcome = "accepted"`
2. `outcome = "failed"`
3. `outcome = "blocked"`

When `outcome = "accepted"`, the acceptance grade must be carried separately:

- `acceptance_class = "strong"`
- `acceptance_class = "conditional-opencode"`

The conditional accepted result is the formal implementation of the product wording:

> OpenCode conditional acceptance

This keeps the top-level question “did the run end accepted?” separate from the stronger question “what kind of accepted state was it?”

### 9.3 Conditional acceptance disclosure rule

Whenever Task 7 ends in conditional OpenCode acceptance, the result must carry a fixed disclosure equivalent in substance to:

- Claude runtime model identity was authoritatively proved;
- OpenCode capability / preflight and scored routing behavior passed;
- OpenCode runtime model identity was not authoritatively proved;
- therefore this result is not strong cross-harness same-model acceptance.

This disclosure must be stable and machine-reconstructable from the result artifacts, not left to ad hoc prose.

## 10. Evidence semantics and summaries

### 10.1 Runtime-proof-unavailable becomes a fact, not always a final decision

After this design, `runtime-proof-unavailable` should be treated as an evidence fact about OpenCode proof status, not automatically as a final blocked outcome.

That means future code should distinguish:

- the proof fact: OpenCode runtime proof unavailable;
- the contract decision: blocked vs conditional continuation vs conditional acceptance.

### 10.2 Conditional acceptance must be first-class in outputs

`OpenCode conditional acceptance` must appear as a formal outcome class in future result payloads and summaries.

It must not be represented only as:

- a free-text note;
- a handover aside;
- a prose caveat after a generic acceptance label.

### 10.3 Historical evidence remains unchanged

The following committed runs remain historical artifacts produced under older semantics and must not be rewritten in place:

- `tests/harness-acceptance/results/2026-07-19T152433Z/`
- `tests/harness-acceptance/results/2026-07-22T143702Z/`

Future documentation may explain how those runs would map conceptually under the new contract, but the artifact files themselves remain unchanged.

## 11. Minimal implementation surface

This design intentionally changes the decision and reporting layer, not the proof extraction layer.

### 11.1 Do not change proof collection first

The following must remain unchanged unless a later task proves they are insufficient for the new semantics:

- adapter capture behavior;
- trusted current-run proof boundary;
- `reference/opencode` reference-only status;
- underlying OpenCode proof-unavailable detection.

The project should not claim that OpenCode now has proof. It should only change how the repo classifies the absence of that proof.

### 11.2 Primary files

The expected first implementation surface is:

- `tests/harness-acceptance/preflight.py`
- `tests/harness-acceptance/summarize.py`
- `tests/harness-acceptance/run.py`
- `tests/harness-acceptance/test_preflight.py`
- `tests/harness-acceptance/test_summarize.py`
- `tests/harness-acceptance/test_run.py`
- handover/spec/plan docs that define Task 6 / Task 7 semantics

This design does **not** initially require changes to:

- `tests/harness-acceptance/capabilities.py`
- `tests/harness-acceptance/adapters/*.sh`

unless later implementation proves that the proof-fact representation or scored output surface requires narrower support changes.

### 11.3 Recommended machine-readable shape split

The implementation should separate:

- final outcome classification;
- acceptance class;
- proof facts.

Recommended minimum shape for future summary/result payloads:

```json
{
  "outcome": "continuation-ready-conditional",
  "acceptance_class": null,
  "reason_code": null,
  "proof_facts": {
    "opencode_runtime_proof": "unavailable"
  }
}
```

and for final conditional acceptance:

```json
{
  "outcome": "accepted",
  "acceptance_passed": true,
  "acceptance_class": "conditional-opencode",
  "reason_code": null,
  "proof_facts": {
    "opencode_runtime_proof": "unavailable"
  }
}
```

The corresponding strong accepted shape should remain parallel:

```json
{
  "outcome": "accepted",
  "acceptance_passed": true,
  "acceptance_class": "strong",
  "reason_code": null,
  "proof_facts": {}
}
```

This design does not require these exact field names if implementation finds a clearer equivalent, but it does require the same separation of concepts.

Blocked results may continue to use `reason_code = "runtime-proof-unavailable"` when the contract says the fact is still terminal.

## 12. Verification requirements

Implementation of this design is complete only when all of the following are true:

1. Task 6 can distinguish `blocked`, `continuation-ready-strong`, and `continuation-ready-conditional`.
2. A run with authoritative Claude proof plus OpenCode capability / preflight pass plus OpenCode proof unavailable no longer lands on blocked by default.
3. Task 7 can produce `accepted + acceptance_class = strong` and `accepted + acceptance_class = conditional-opencode` as distinct formal results.
4. Conditional acceptance results always carry the fixed disclosure that OpenCode runtime identity was not authoritatively proved.
5. A missing or invalid Claude proof still blocks execution.
6. A failed OpenCode capability / preflight still blocks execution.
7. Historical evidence directories remain unchanged.

## 13. Test strategy

Implementation of this design is complete only when all of the following are true:

1. Task 6 can distinguish `blocked`, `continuation-ready-strong`, and `continuation-ready-conditional`.
2. A run with authoritative Claude proof plus OpenCode capability / preflight pass plus OpenCode proof unavailable no longer lands on blocked by default.
3. Task 7 can produce `strong-acceptance` and `conditional-opencode-acceptance` as distinct formal results.
4. Conditional acceptance results always carry the fixed disclosure that OpenCode runtime identity was not authoritatively proved.
5. A missing or invalid Claude proof still blocks execution.
6. A failed OpenCode capability / preflight still blocks execution.
7. Historical evidence directories remain unchanged.

## 13. Test strategy

### 13.1 Required Task 6 tests

At minimum, add coverage proving:

- Claude authoritative proof + OpenCode capability/preflight pass + OpenCode proof unavailable => `continuation-ready-conditional`
- missing Claude proof => `blocked`
- failed OpenCode capability/preflight => `blocked`
- both proofs present and aligned => `continuation-ready-strong`

### 13.2 Required summary/result tests

At minimum, add coverage proving:

- conditional path renders a distinct formal result class;
- conditional path cannot be rendered as strong acceptance;
- the fixed OpenCode-conditional disclosure is always present on the conditional path;
- strong path does not inherit the conditional disclosure.

### 13.3 Anti-overreach tests

Add explicit guard tests so the contract relaxation does not spread beyond the intended case.

The implementation must prove that it relaxed only this case:

- OpenCode proof unavailable while Claude proof remains authoritative and OpenCode capability/preflight passes.

It must not accidentally relax:

- missing Claude proof;
- failed OpenCode capability/preflight;
- other redaction or contamination failures.

## 14. Documentation impact

The following docs must be updated during implementation:

- `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md`
- the Task 7 planning/design records that currently assume one continuation-ready state
- `docs/handover/researchwork-plugin-handover.md`

Documentation must make the claim boundary explicit:

- conditional acceptance allows scored execution and a weaker acceptance class;
- strong acceptance remains the only path to a verified cross-harness same-model claim.

## 15. Why this is the right-sized change

This design does not try to repair OpenCode proof production. It acknowledges that the current repo has already spent significant effort validating the absence of an acceptable OpenCode proof surface.

The user decision is not “pretend proof exists.” It is:

> continue the acceptance workflow honestly, with a weaker but explicit claim class.

That is a contract change, not a proof-layer hack.

It is therefore smaller, safer, and more truthful than either:

- continuing indefinite proof-surface work before any Task 7 progress; or
- silently downgrading the meaning of acceptance without naming the downgrade.

## 16. Final scope check

This is a single design topic with one coherent objective:

- redefine Task 6 / Task 7 outcome semantics so OpenCode proof absence can lead to conditional acceptance instead of mandatory blockage.

It is narrow enough for one implementation plan.

## 17. Spec self-review

Checked before handoff:

- No placeholders remain.
- The chosen path matches the explicit user decisions: dual acceptance classes, Claude proof still required, OpenCode conditional acceptance wording selected.
- Strong and conditional claims are separated consistently across Task 6, Task 7, summaries, and docs.
- Historical evidence is explicitly preserved.

This spec is ready for review and implementation planning.
