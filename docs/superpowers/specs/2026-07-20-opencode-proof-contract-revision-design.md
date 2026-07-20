# ResearchFlow OpenCode Proof Contract Revision Design

Date: 2026-07-20  
Status: Proposed for review  
Topic: Revise the OpenCode preflight proof contract so capability/plugin proof and runtime model proof are evaluated separately without reclassifying existing committed blocked evidence.

## 1. Purpose

This design updates the ResearchFlow harness-acceptance contract for OpenCode after Task 6 real-preflight evidence showed that the current contract conflates two different questions:

1. can OpenCode load the ResearchFlow plugin in the target checkout and execute the preflight canary;
2. can OpenCode emit authoritative runtime model proof from committed redacted artifacts.

The current contract treats selected OpenCode debug surfaces as hard preflight gates. Real evidence and source inspection show those surfaces are not stable proof for the properties we were asking them to prove.

This revision keeps the existing Task 6 and Task 7 top-level lifecycle intact while changing only the OpenCode proof boundary:

- capability/plugin proof becomes a narrower raw gate based on repo proof, workspace proof, and canary execution;
- debug surfaces remain collected as diagnostics but no longer decide raw pass/fail;
- authoritative runtime model proof remains a separate hard gate;
- missing authoritative runtime model proof continues to classify as `blocked` with `reason_code = runtime-proof-unavailable`.

This design is intentionally minimal. It does not redefine Task 5, it does not score any cases, and it does not retroactively reinterpret the committed Task 6 blocked run.

## 2. Confirmed evidence motivating the revision

The revision is based on confirmed code and runtime evidence, not a speculative cleanup.

### 2.1 `debug paths` does not prove plugin source

OpenCode `debug paths` prints global directories such as config/data/cache/state/home. The implementation iterates `Global.Path` and does not expose plugin source paths or checkout identity.

Therefore `debug paths` cannot authoritatively prove that the active plugin came from the target ResearchFlow checkout. Any contract that requires `paths_source_match = true` as a hard preflight gate is stronger than the real OpenCode surface supports.

### 2.2 `debug skill` is not stable proof for runtime-injected skills

ResearchFlow's OpenCode plugin adds `skills.paths` through the plugin `config()` hook. OpenCode skill discovery is initialized earlier than that runtime hook in the observed startup path.

As a result, `debug skill` cannot be treated as authoritative proof that runtime-injected ResearchFlow skills are active for the current run. It remains useful as a diagnostic snapshot, but it is not a reliable hard gate.

### 2.3 `run --format json` does not emit authoritative runtime model proof

OpenCode internally carries model identifiers such as provider/model IDs in runtime events, but the non-interactive `run --format json` surface does not emit an authoritative model event or a stable result payload containing those fields.

As a result, the current OpenCode preflight path cannot derive committed authoritative runtime model proof from that public surface alone. This is exactly the case that `runtime-proof-unavailable` exists to represent.

### 2.4 `OPENCODE_DIRECT_TRACE` is not part of the current non-interactive preflight contract

The direct trace facility is wired to the interactive direct runtime and did not produce usable trace evidence for the current non-interactive preflight-only path. It is therefore not an accepted runtime-proof surface for Task 6 or Task 7 continuation.

## 3. Scope and non-goals

In scope:

- revising the OpenCode capability/plugin proof contract;
- preserving `runtime-proof-unavailable` as the blocked classification for missing authoritative runtime model proof;
- updating specs, plans, handover notes, and harness tests/code so future runs follow the revised contract;
- preserving the currently committed blocked evidence exactly as written.

Out of scope:

- reopening Task 5;
- running scored cases;
- redefining the three Task 6 top-level outcomes;
- changing Claude proof semantics;
- adding a new OpenCode-specific reason code;
- adding a new OpenCode upstream model-proof surface;
- rewriting historical evidence files.

## 4. Revised contract

### 4.1 Capability/plugin proof and runtime model proof are separate gates

Under the revised contract, OpenCode preflight is evaluated in two stages:

1. **Capability/plugin proof gate** — answers whether the target checkout is the active workspace/plugin base and whether the OpenCode runtime can execute the ResearchFlow preflight canary from that setup.
2. **Runtime model proof gate** — answers whether committed redacted runtime artifacts establish authoritative backing model identity.

Passing the capability/plugin proof gate does not imply runtime model proof exists. It only means the run is eligible to be judged for runtime model proof.

### 4.2 OpenCode capability hard gate

The minimum accepted OpenCode capability hard gate is:

- repo static proof passes;
- workspace config points at the target checkout;
- preflight canary executes successfully for that checkout.

For this design, those terms mean:

- **repo static proof**: the ResearchFlow checkout contains the OpenCode plugin source file and the expected repo-local skills directory/file layout required by the repository contract;
- **workspace proof**: the workspace OpenCode config resolves to the target checkout as the configured local plugin source;
- **canary success**: the actual preflight canary returns the expected bootstrap marker from the target checkout path.

If any of those three fail, the run remains blocked at the raw capability/plugin layer and may still classify as `global_hard_gate_blocked`.

### 4.3 Debug surfaces become advisory diagnostics

The following OpenCode debug surfaces remain collected and committed in redacted form when available:

- `debug config`
- `debug paths`
- `debug skill`

Under the revised contract they are diagnostic evidence, not hard-gate proof.

They may still be used to:

- explain why a run classified as blocked;
- support handover and operator review;
- document what the installed OpenCode build exposed;
- help future work on an upstream proof surface.

They must not be used as sole proof for checkout/source match or for runtime skill activation in final gating logic.

### 4.4 Runtime model proof semantics remain strict

Authoritative runtime model proof remains unchanged in principle:

- canonical model identity comes only from committed redacted runtime proof;
- static config, route labels, and resolved config dumps are not proof;
- if authoritative runtime proof is missing, the run must remain blocked.

The required classification for a future run that passes capability/plugin proof but cannot establish authoritative runtime model proof is:

- `outcome = blocked`
- `reason_code = runtime-proof-unavailable`

This is not a new outcome. It is the already accepted blocked subtype and should be the stable cross-task meaning for this condition in both Task 6 and Task 7 gating.

## 5. Outcome behavior after the revision

### 5.1 Raw capability failure

If repo proof, workspace proof, or canary execution fails, the run remains blocked at the capability/plugin layer. `global_hard_gate_blocked` remains acceptable here.

### 5.2 Capability passes but runtime proof is unavailable

If capability/plugin proof passes but OpenCode still cannot emit authoritative runtime model proof, the run must no longer stop at the earlier generic raw gate. It must proceed to final preflight classification and land on `runtime-proof-unavailable`.

This is the main behavioral change introduced by this revision.

### 5.3 Capability passes and runtime proof exists

If OpenCode can both pass capability/plugin proof and produce authoritative runtime model proof, the existing allowlist and alignment flow continues unchanged:

- exact aligned verified model identity may become `continuation-ready`;
- a same-model allowlist gap becomes `allowlist-update-needed`;
- mismatched or invalid proof remains blocked.

## 6. Historical evidence handling

The committed real-preflight evidence at:

`tests/harness-acceptance/results/2026-07-19T152433Z/`

remains valid historical evidence under the old contract and must not be rewritten, regenerated, or reclassified in place.

This design does not reinterpret those committed files as if they had been produced under the revised contract. Instead, it records that:

- the run was correctly blocked under the contract active at the time;
- future runs in materially similar environments should be expected to land on `runtime-proof-unavailable` once the revised OpenCode capability gate is implemented.

That preserves auditability and avoids mixing historical and revised semantics in one artifact set.

## 7. File-level design impact

### 7.1 `tests/harness-acceptance/capabilities.py`

This is the primary implementation site.

Required design changes:

- revise OpenCode capability selection so `paths_source_match` is no longer a hard prerequisite;
- revise OpenCode capability selection so `skill_inventory_valid` is no longer a hard prerequisite;
- keep computing and recording those values under `probe_results.debug` for diagnostics;
- do not leave the selected OpenCode proof/capability branch semantically ambiguous.

Implementation must choose one explicit path and encode it consistently across code, fixtures, and tests:

1. keep the existing field name but redefine its allowed values and documentation so it now represents the revised capability-gate result rather than the old strong/fallback debug-surface proof model; or
2. introduce a replacement field/value set whose names directly describe the revised capability contract.

Whichever path is chosen, the resulting code and fixtures must not keep old strong/fallback names while assigning them revised semantics.

The raw capability decision should be derivable from repo proof, workspace proof, and canary success.

### 7.2 `tests/harness-acceptance/preflight.py`

This file should change minimally.

The intended effect is that once OpenCode capability can pass under the revised contract, existing preflight outcome logic can classify missing authoritative runtime model proof as `runtime-proof-unavailable` without adding a new outcome family.

Any edits here should clarify that capability pass and model-proof pass are separate questions, not rewrite the entire outcome model.

### 7.3 `tests/harness-acceptance/test_capabilities.py`

Update the OpenCode capability tests so they encode the revised contract:

- cases with `paths_source_match = false` do not fail by default if repo/workspace/canary proof holds;
- cases with `skill_inventory_valid = false` do not fail by default if repo/workspace/canary proof holds;
- capability-failure tests continue to fail when repo proof, workspace proof, or canary proof is absent.

At least one synthetic test must encode the observed real-world OpenCode shape where debug diagnostics are weak but capability proof still succeeds.

### 7.4 `tests/harness-acceptance/test_preflight.py`

Add or adjust coverage so the revised capability gate and existing `runtime-proof-unavailable` semantics are tested together.

Required contract test:

- OpenCode capability passes under the revised gate;
- OpenCode model proof remains unverified and lacks authoritative runtime metadata;
- final classification is `blocked` with `reason_code = runtime-proof-unavailable`.

This test is what preserves the intended Task 6 to Task 7 continuity.

### 7.5 Capability fixtures

OpenCode capability fixtures may keep their current filenames if desired, but their semantic meaning must be updated to match the revised contract.

The important requirement is not fixture renaming; it is that the fixture contents and test expectations no longer encode debug-surface hard-gate assumptions.

## 8. Documentation impact

### 8.1 Task 6 real-preflight spec

Update `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md` to record that, for OpenCode:

- `debug paths` is not source proof;
- `debug skill` is not authoritative runtime skill proof;
- `run --format json` is not an authoritative runtime model-proof surface;
- capability/plugin proof and runtime model proof are separate gates.

### 8.2 Task 6 plan

Update `docs/superpowers/plans/2026-07-19-task6-real-preflight.md` so any future implementation work follows the revised capability gate and does not attempt to force debug-surface evidence into a role the real OpenCode build does not support.

### 8.3 Handover

Update `docs/handover/researchwork-plugin-handover.md` to record:

- the decision to revise the OpenCode proof contract;
- that the committed `2026-07-19T152433Z` run remains valid old-contract evidence;
- that future comparable runs should land on `runtime-proof-unavailable` once the revised gate is implemented.

## 9. Compatibility requirements

This revision must preserve all of the following:

- no change to Claude proof semantics;
- no new top-level Task 6 outcomes;
- no new reason code family;
- no scored-case execution;
- no silent reinterpretation of historical evidence;
- no continuation-ready entrypoint unless authoritative runtime model proof actually exists.

In particular, this change must not allow Task 7 to start merely because OpenCode can load the plugin and run the canary. Capability pass is necessary but still insufficient.

## 10. Verification requirements

The revision is complete only when all of the following are true:

1. the revised contract is reflected in spec, plan, and handover documentation;
2. OpenCode capability tests reflect repo/workspace/canary as the hard gate;
3. debug-surface values remain recorded but no longer determine capability pass/fail;
4. preflight tests prove that a capability-pass + model-proof-missing OpenCode run classifies as `runtime-proof-unavailable`;
5. the committed `2026-07-19T152433Z` evidence set is unchanged;
6. no scored cases are executed as part of this revision.

## 11. Recommended implementation approach

Implement this revision as a minimal contract correction, not a broad harness refactor.

Preferred sequence:

1. update the Task 6 spec/plan/handover text;
2. adjust OpenCode capability-gate logic in `capabilities.py`;
3. update capability fixtures and tests;
4. add or update the cross-layer preflight test that proves the revised gate feeds into `runtime-proof-unavailable`;
5. rerun the synthetic baseline only.

This keeps the revision bounded and preserves the rest of the harness acceptance architecture.
