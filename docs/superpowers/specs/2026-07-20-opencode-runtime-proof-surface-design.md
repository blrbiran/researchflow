# OpenCode Non-Interactive Authoritative Runtime Proof Surface Design

Date: 2026-07-20  
Status: Proposed for review  
Topic: Define an OpenCode upstream runtime-proof surface that exposes authoritative model identity for non-interactive execution, with a canonical run-path surface and a dedicated debug proof surface derived from the same runtime truth.

## 1. Purpose

This spec defines the next workstream after the completed ResearchFlow OpenCode proof-contract revision.

The current state is:

- ResearchFlow now separates OpenCode capability/plugin proof from runtime model proof.
- The historical blocked evidence at `tests/harness-acceptance/results/2026-07-19T152433Z/` remains unchanged.
- Task 7 is still blocked because OpenCode does not currently expose authoritative runtime model proof on the non-interactive path ResearchFlow actually uses.

This spec is not a ResearchFlow consumer change. It is an OpenCode-upstream surface design.

Its goal is to define a new authoritative runtime-proof surface for non-interactive OpenCode execution so downstream systems such as ResearchFlow can determine, from runtime truth rather than static configuration or diagnostic inference:

- which provider actually executed the run;
- which backing model actually executed the run;
- which canonical model identity that backing model resolves to;
- whether that identity is verified by OpenCode runtime truth.

The design uses a dual-surface model:

1. a **canonical run-path surface** on `opencode run --format json`, which is the only authoritative machine-consumable truth source for gating;
2. a **dedicated debug proof surface**, intended for human-readable diagnostics and audit-friendly inspection, derived from the same runtime truth.

## 2. Non-goals

This spec does not:

- reopen Task 5;
- run scored cases;
- modify the historical blocked evidence under `tests/harness-acceptance/results/2026-07-19T152433Z/`;
- directly change ResearchFlow harness code;
- directly unlock Task 7;
- redefine the ResearchFlow `runtime-proof-unavailable` meaning;
- promote `debug config`, `debug paths`, `debug skill`, route labels, or workspace config to authoritative runtime proof;
- require OpenCode to expose full audit bundles in the first version.

This is a narrowly scoped upstream surface spec.

## 3. Runtime truth model

### 3.1 Authoritative minimum

The minimum authoritative runtime proof must expose these fields:

- `providerID`
- `modelID`
- `resolved_model_identity`
- `verified`

These four fields are the minimum because they let a downstream gate answer the real Task 6 / Task 7 question:

- which provider actually served the model;
- which model actually ran;
- which canonical identity that model resolves to;
- whether OpenCode itself considers that mapping runtime-verified.

### 3.2 Semantics

The authoritative meanings are:

- **`providerID`** — the provider that actually served the assistant response in runtime execution.
- **`modelID`** — the backing model identifier OpenCode runtime actually observed for that execution.
- **`resolved_model_identity`** — the canonical downstream-facing identity OpenCode resolves from runtime truth, for example `openai/gpt-5.4`.
- **`verified`** — a boolean meaning OpenCode considers the runtime proof sufficient to assert the resolved identity as authoritative, not guessed.

### 3.3 What does not count as proof

The following do not count as authoritative runtime proof on their own:

- requested route labels such as `openai-compatible/gpt-5.4`;
- resolved config model values;
- workspace plugin/config metadata;
- `debug config` output;
- `debug paths` output;
- `debug skill` output;
- canary success by itself;
- any human-readable assistant text that happens to mention a model name.

Those may support diagnosis, but they are not canonical runtime truth.

## 4. Canonical run-path surface

### 4.1 Source of truth

The canonical source of truth must be the real non-interactive execution path:

```text
opencode run --format json
```

This is the path ResearchFlow actually uses for preflight and scored execution. Therefore, it is the only acceptable authoritative source for downstream gating.

### 4.2 New runtime model event

`opencode run --format json` should emit a stable model-proof event whenever authoritative runtime model truth becomes available.

The recommended shape is:

```json
{
  "type": "model",
  "timestamp": 1720000000000,
  "sessionID": "ses_123",
  "providerID": "openai-compatible",
  "modelID": "gpt-5.4",
  "resolved_model_identity": "openai/gpt-5.4",
  "verified": true
}
```

The exact field order is not important. The field names and semantics are.

### 4.2.1 Resolution authority

This spec assumes OpenCode upstream itself owns the authority required to derive `resolved_model_identity` and `verified` from runtime truth.

That means:

- `providerID` and `modelID` come from runtime execution truth;
- `resolved_model_identity` is resolved inside OpenCode upstream from that runtime truth using an upstream-owned canonical mapping source;
- `verified` is asserted by OpenCode upstream only when that runtime truth and that canonical mapping source are sufficient to make the identity authoritative.

Neither downstream consumers nor external config should be required to complete the authoritative minimum after the event is emitted.

If OpenCode upstream does not yet own a canonical mapping source strong enough to support this, it must fail closed rather than emit guessed `resolved_model_identity` / `verified` values.

That fail-closed outcome is preferable to shifting the authority boundary back into downstream consumers.

### 4.2.2 Mapping-source rule

The canonical mapping source used to derive `resolved_model_identity` must itself be part of OpenCode upstream's trusted runtime-proof design.

It must not be:

- borrowed implicitly from downstream allowlists;
- reconstructed from workspace config;
- inferred from route labels;
- guessed from assistant-visible prompt text.

This keeps the authoritative minimum internally coherent: the event is either fully authoritative or explicitly not authoritative.

### 4.3 Emission timing

The event must be emitted from runtime execution truth, not synthesized afterward from config.

It should appear only when OpenCode has enough runtime truth to fill the authoritative minimum. If runtime truth is not sufficient, OpenCode must not fabricate or guess a verified identity.

This event may be emitted once per run when the authoritative truth becomes known. If OpenCode emits more than one model-related event internally, only one stable authoritative event should be exposed to the canonical non-interactive surface unless multiple authoritative model transitions are explicitly part of the run contract.

### 4.4 Relationship to existing internals

This design assumes OpenCode already carries model truth internally during runtime execution. The required upstream change is primarily a publication change: expose stable authoritative runtime truth on the JSON run surface rather than keeping it internal-only.

The spec does not require a new internal truth model if the existing runtime state already knows `providerID` and `modelID`.

## 5. Dedicated debug proof surface

### 5.1 Purpose

OpenCode should also expose a dedicated diagnostic proof surface, for example:

```text
opencode debug proof
```

or equivalently `opencode debug model`.

This surface exists for:

- human debugging;
- audit-friendly inspection;
- easier harness/operator troubleshooting;
- verification that the canonical run-path event and the visible proof summary agree.

### 5.2 Non-authoritative role

This debug proof surface is not an independent truth source.

Its output must be derived from the same runtime truth as the canonical run-path model event. It is a readable inspection view of authoritative truth, not a separate proof mechanism.

If the canonical run-path cannot produce authoritative runtime truth, the debug proof surface must not invent it.

### 5.3 Minimum debug shape

The minimum debug-proof output may be:

```json
{
  "providerID": "openai-compatible",
  "modelID": "gpt-5.4",
  "resolved_model_identity": "openai/gpt-5.4",
  "verified": true,
  "proof_source": "runtime-model-event",
  "sessionID": "ses_123"
}
```

This spec does not require more than that in the first version.

### 5.4 Correlation rule

The dedicated debug proof surface must support reading the proof for a specific canonical runtime execution, not only an ambiguous "most recent" state.

At minimum, the design must support selecting the proof by a stable execution/session identifier such as `sessionID` or an equivalent run identifier.

That means:

- a caller must be able to ask for the proof corresponding to the same run-path event it is auditing;
- the command must not silently return proof for a different recent session when multiple sessions exist;
- if no matching runtime truth exists for the requested identifier, the command must fail closed instead of returning a nearby but unrelated proof record.

A convenience mode such as "latest" may exist, but it must be explicitly marked as convenience-only and must not be the only addressing mode.

This keeps the debug proof surface aligned with the canonical run-path event rather than merely nearby in time.

### 5.5 Same-truth requirement

The debug proof surface must be derived from the exact same recorded runtime truth instance as the canonical run-path event for the addressed execution.

It must not reconstruct a fresh answer from config, route labels, or ad hoc state after the fact.

If the debug proof view cannot bind itself to the same execution-scoped runtime truth, it is not satisfying this spec.

### 5.6 Internal-proof-record rule

Even when the canonical run-path surface does not emit an authoritative `model` event because proof is unavailable or unverified, OpenCode may still retain an execution-scoped internal proof record for that same run.

If it does, the dedicated debug proof surface must read from that execution-scoped internal proof record rather than reconstructing an answer from nearby session state, config, or other indirect evidence.

That means:

- canonical run-path emission may fail closed;
- dedicated debug proof may still explain why authoritative proof was unavailable or unverified;
- both surfaces remain bound to the same execution-scoped runtime truth instance.

The debug proof surface must therefore never fall back to "most recent plausible session state" when the addressed execution lacks an emitted authoritative model event.

If no execution-scoped runtime truth record exists for the requested run, the debug proof surface must fail closed.

## 6. Source-of-truth rules

The dual-surface model must follow these rules:

1. The authoritative source for downstream gating is the runtime model proof emitted by `opencode run --format json`.
2. The dedicated debug proof surface is a derived inspection view of the same truth.
3. The dedicated debug proof surface must never claim stronger truth than the canonical run-path event.
4. Static or diagnostic surfaces may explain, but never replace, canonical runtime proof.
5. If canonical runtime proof is unavailable, downstream consumers must be able to detect that absence unambiguously.

This prevents a repeat of the prior failure mode where configuration/debug evidence appeared informative, yet the real run-path still lacked authority.

## 6. Source-of-truth rules

The dual-surface model must follow these rules:

1. The authoritative source for downstream gating is the runtime model proof emitted by `opencode run --format json`.
2. The dedicated debug proof surface is a derived inspection view of the same truth.
3. The dedicated debug proof surface must never claim stronger truth than the canonical run-path event.
4. Static or diagnostic surfaces may explain, but never replace, canonical runtime proof.
5. If canonical runtime proof is unavailable, downstream consumers must be able to detect that absence unambiguously.

This prevents a repeat of the prior failure mode where configuration/debug evidence appeared informative, yet the real run-path still lacked authority.

## 7. Failure semantics

### 7.1 Missing runtime truth

If OpenCode cannot determine authoritative runtime model truth for a run, the canonical run-path surface must fail closed.

That means:

- it must not emit a fake verified model event;
- it may omit the model event entirely, or emit an explicit unavailable/unverified state if the format supports it;
- any dedicated debug proof view must also reflect that authoritative proof is unavailable.

### 7.2 Unverified identity

If OpenCode can name a provider or requested model but cannot verify the canonical resolved identity from runtime truth, it must not set `verified = true`.

For example, a shape like this is acceptable for a non-authoritative case:

```json
{
  "type": "model",
  "providerID": "openai-compatible",
  "modelID": "gpt-5.4",
  "resolved_model_identity": null,
  "verified": false
}
```

What is not acceptable is any shape that silently turns guessed or config-derived identity into verified proof.

## 8. Compatibility and migration

### 8.1 Backward compatibility

The canonical runtime proof surface should be added in a backward-compatible way.

For `run --format json`, the recommended approach is additive:

- keep existing emitted event types;
- add a new stable `model` event;
- do not require existing consumers to understand it immediately.

### 8.2 Debug surface compatibility

The dedicated debug proof command may be added as a new subcommand without altering existing `debug config`, `debug paths`, or `debug skill` behavior.

### 8.3 Migration for downstream consumers

Downstream consumers such as ResearchFlow should remain free to treat the absence of the new canonical model event as proof-unavailable until they explicitly opt into the new surface.

This spec therefore creates a clean migration path:

- OpenCode first exposes runtime truth;
- downstream consumers later adopt it as canonical proof;
- old behavior remains fail-closed until that adoption happens.

## 9. Downstream contract for consumers

Although this spec does not change ResearchFlow directly, it does define what downstream consumers should rely on once the surface exists.

Downstream consumers should:

- treat the canonical run-path model event as the only machine-consumable authoritative runtime proof source;
- treat the dedicated debug proof surface as human-facing or audit-facing support only;
- classify missing canonical model proof as proof-unavailable rather than inferring identity from config/debug surfaces.

This preserves the current ResearchFlow direction: capability/plugin proof and runtime model proof remain separate gates.

## 10. Verification strategy

OpenCode-upstream verification for this spec should include:

### 10.1 Canonical run-path tests

- `run --format json` emits the new `model` event when runtime truth is sufficient.
- The emitted event includes the authoritative minimum fields.
- The event does not appear as verified when runtime truth is insufficient.

### 10.2 Debug proof tests

- `debug proof` returns the same model truth as the canonical run-path surface when such truth exists.
- `debug proof` does not overstate proof when the run-path truth is unavailable or unverified.

### 10.3 Negative tests

- Config-only or route-only knowledge does not produce `verified = true`.
- Missing authoritative runtime truth does not silently degrade into a guessed canonical identity.

### 10.4 Downstream-readiness check

A downstream consumer should be able to write a fail-closed contract test that passes only when:

- a canonical runtime model event exists;
- `providerID`, `modelID`, `resolved_model_identity`, and `verified` are all present with authoritative semantics;
- the debug proof surface, if queried, agrees with that truth rather than contradicting it.

## 11. Recommended next step

The smallest correct next implementation/spec cycle after this document is:

1. implement the canonical `run --format json` model-proof event upstream in OpenCode;
2. implement the dedicated `debug proof` / `debug model` inspection surface derived from the same runtime truth;
3. only after those surfaces exist, start a separate ResearchFlow consumer spec for adopting them into Task 6 and Task 7 gating.

This keeps the next workstream scoped to the real missing dependency: OpenCode upstream does not yet publish authoritative runtime model proof on the non-interactive execution path.
