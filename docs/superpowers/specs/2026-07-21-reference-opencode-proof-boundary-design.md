# ResearchFlow Reference-Only OpenCode Proof Boundary Design

Date: 2026-07-21  
Status: Draft for review  
Topic: Harden the current ResearchFlow consumer/harness boundary so `reference/opencode` remains reference-only and can never be treated as authoritative runtime model proof.

## 1. Purpose

This design narrows the current ResearchFlow harness contract after a user correction clarified that `reference/opencode` is reference material only and must not be changed, committed, or consumed as proof input.

The current ResearchFlow contract already does the important top-level thing correctly:

- OpenCode capability/plugin proof and runtime model proof are separate gates.
- Missing authoritative OpenCode runtime model proof remains fail-closed.
- Comparable future runs should classify as `blocked` with `reason_code = runtime-proof-unavailable` unless an accepted authoritative proof surface exists.

The remaining risk is not the top-level outcome model. The risk is future drift inside current-repo harness code: someone could later add a convenience fallback that reads diagnostics, checkout state, or artifacts under `reference/opencode` and accidentally upgrades OpenCode proof status inside ResearchFlow.

This design adds a narrow guard so that cannot happen silently.

## 2. Problem statement

Today, the current ResearchFlow harness logic evaluates runtime model proof from model-proof artifacts produced for the current run under `tests/harness-acceptance/results/<run-id>/preflight/`.

That is the correct authority boundary.

However, this boundary is implicit rather than explicitly defended. The code currently reads the expected files directly, and the surrounding docs still contain historical upstream-workstream notes that can make `reference/opencode` look operationally relevant.

That creates a future maintenance hazard:

- a developer sees stronger-looking evidence under `reference/opencode`;
- they add a fallback or alternative proof lookup for convenience;
- ResearchFlow starts treating reference-side material as if it were authoritative runtime proof for the current run;
- Task 6/Task 7 gating becomes dishonest.

The user explicitly wants this prevented at both the documentation layer and the implementation layer.

## 3. Goals

This change must:

1. keep `reference/opencode` reference-only inside the current ResearchFlow repo;
2. make the accepted runtime-proof input boundary explicit in current harness code;
3. keep current fail-closed behavior unchanged when authoritative proof is unavailable;
4. add regression coverage that prevents future fallback to `reference/opencode` or other non-run paths;
5. avoid introducing any new proof source, upstream dependency, or Task 7 continuation path.

## 4. Non-goals

This design does not:

- modify `reference/opencode`;
- assume the upstream OpenCode runtime-proof surface exists or is usable;
- reinterpret historical blocked evidence;
- unblock Task 7;
- add a new proof reason code;
- broaden accepted proof inputs beyond the current run's committed redacted artifacts;
- redesign Task 6 or Task 7 outcome semantics.

## 5. Options considered

### Option 1 — documentation and tests only

Document that `reference/opencode` is reference-only and add regression tests asserting `runtime-proof-unavailable` still holds.

**Pros:** smallest patch surface.  
**Cons:** the implementation layer still has no explicit guard, so future fallback code could be added too easily.

### Option 2 — documentation, tests, and a narrow implementation guard

Add a tiny current-run-only model-proof loader in harness code, route current proof reads through it, and document that no fallback or reference-side scan is allowed.

**Pros:** minimal code change with an actual guardrail; aligns with the user's request; easiest to verify.  
**Cons:** touches one or two harness files instead of documentation only.

### Option 3 — broader provenance framework

Introduce a richer provenance contract for all proof artifacts and enforce source lineage across the harness.

**Pros:** strongest long-term guard.  
**Cons:** over-scoped for the present need and likely to create unnecessary churn.

## 6. Chosen design

Choose **Option 2**.

ResearchFlow should keep the same runtime-proof semantics it already has, but make the source boundary explicit:

- the only accepted OpenCode runtime model proof input is the current run's own preflight artifact under the trusted `tests/harness-acceptance/results/<run-id>/preflight/` tree;
- the harness must not scan, infer from, or fall back to anything under `reference/opencode`;
- when the current run artifact does not carry authoritative proof, the result stays `blocked / runtime-proof-unavailable`.

The implementation does not need to prove that an artifact is committed in git. The boundary this design enforces is path provenance inside the current harness results tree, not git-state inspection.

## 7. Design details

### 7.1 Accepted proof source boundary

For current ResearchFlow harness logic, the accepted runtime-proof source for a harness is only:

- `run_dir / "preflight" / "claude-model-proof.json"`
- `run_dir / "preflight" / "opencode-model-proof.json"`

where `run_dir` is the specific harness-acceptance run being evaluated and must resolve under:

- `tests/harness-acceptance/results/<run-id>/`

This boundary is exact at both levels:

- the trusted root is the current harness results tree;
- the trusted filenames are the two fixed model-proof artifact names under that run's `preflight/` directory.

This boundary is exact:

- no fallback to sibling directories;
- no fallback to repository-root files;
- no fallback to `reference/`;
- no fallback to `reference/opencode` checkouts, worktrees, snapshots, or logs;
- no fallback to debug diagnostics or inferred upstream state.

If the current run's model-proof artifact does not establish valid authoritative proof, the harness must continue to classify the run fail-closed.

### 7.2 Narrow implementation guard in `preflight.py`

`tests/harness-acceptance/preflight.py` should stop reading model-proof files inline by path composition alone and instead call one narrow helper with a name that makes the boundary obvious.

Recommended shape:

```python
def load_runtime_model_proof_artifact(run_dir: Path, harness: str) -> dict[str, Any]:
    ...
```

Behavior:

- accept only `claude` or `opencode`;
- validate that `run_dir` resolves under `tests/harness-acceptance/results/` for the current repo checkout;
- construct exactly `run_dir / "preflight" / f"{harness}-model-proof.json"`;
- read exactly that file;
- do not probe alternate locations;
- do not inspect `reference/opencode`;
- do not attempt a best-effort fallback.

If `run_dir` is outside the trusted results tree, the helper must fail loudly rather than broaden its search.

This is the key hardening point: the guard protects both filename selection and proof-root provenance.

The implementation should not add git-state checks for whether the artifact is committed. Path provenance inside the current run-results tree is the intended boundary.

### 7.3 Shared helper placement in `lib.py`

Because this boundary is part of the general harness contract rather than only one preflight function, the loader should live in `tests/harness-acceptance/lib.py` and be called from both `preflight.py` and `run.py`.

That gives the contract one named entrypoint and one obvious place for the explanatory comment, while avoiding duplicate proof-source logic.

Recommended comment style:

- short;
- explicit;
- about **why** fallback is forbidden.

For example, the helper should explain that `reference/opencode` is reference-only and cannot upgrade runtime-proof status for the current run.

### 7.4 Shared helper reuse in `run.py`

`tests/harness-acceptance/run.py` currently reads the same model-proof artifacts directly during preflight-only and scored orchestration.

This design requires those reads to route through the same shared helper in `lib.py`.

That keeps the source-boundary contract singular: `preflight.py` and `run.py` should not have parallel proof loaders with different future drift risk.

The important constraint is that this remains a source-boundary refactor only, not a behavioral redesign.

## 8. Test design

### 8.1 Required regression in `test_preflight.py`

Add a regression that proves ResearchFlow does **not** absorb reference-side proof.

The preferred test shape is:

1. monkeypatch the shared JSON reader or the new shared proof-loader entrypoint;
2. capture attempted proof paths;
3. assert every attempted proof path stays under the current run's `preflight/` directory;
4. assert no attempted proof path includes `reference/opencode`;
5. keep the current run's OpenCode model-proof artifact non-authoritative;
6. assert final classification remains `blocked` with `reason_code = runtime-proof-unavailable`.

A repository-shape fixture that places stronger-looking reference-side proof elsewhere is optional supporting evidence, not the primary assertion mechanism.

The important thing the regression must lock is attempted path provenance, not just the final blocked outcome.

### 8.2 Existing behavior that must remain green

The current revised-contract regression in `test_preflight.py` already proves that OpenCode capability-pass plus missing authoritative runtime proof lands on `runtime-proof-unavailable`.

That behavior must remain unchanged.

The new test is additive: it protects the source boundary, not the top-level reason code logic.

## 9. Documentation updates required at implementation time

### 9.1 Handover

Update `docs/handover/researchwork-plugin-handover.md` to clarify that:

- `reference/opencode` is reference-only in the current workflow;
- no current ResearchFlow continuation decision may consume proof from that checkout;
- only current-run preflight artifacts under `tests/harness-acceptance/results/.../preflight/` count as runtime-proof input.

### 9.2 Adjacent runtime-proof docs

Update `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md` so the current repo's accepted proof-source boundary is explicit and consistent with this design.

This should stay narrow. The purpose is consistency, not rewriting historical upstream notes.

## 10. File impact

### Primary files

- `tests/harness-acceptance/lib.py`
  - add the shared current-run-only model-proof loader and the explicit reference-only comment.

- `tests/harness-acceptance/preflight.py`
  - route model-proof loading through the shared helper.

- `tests/harness-acceptance/run.py`
  - route model-proof loading through the same shared helper so there is one defended boundary.

- `tests/harness-acceptance/test_preflight.py`
  - add the regression that proves no reference-side proof is absorbed.

### Documentation

- `docs/handover/researchwork-plugin-handover.md`
- `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`
- this design spec

## 11. Success criteria

This design is successfully implemented when all of the following are true:

1. ResearchFlow still classifies capability-pass plus missing authoritative OpenCode runtime proof as `blocked / runtime-proof-unavailable`.
2. Harness code has one explicit current-run-only model-proof loader.
3. That loader rejects any `run_dir` outside `tests/harness-acceptance/results/` and cannot fall back to `reference/opencode` or other non-run locations.
4. Both `preflight.py` and `run.py` use that same loader.
5. Regression coverage proves attempted proof reads stay inside the current run's preflight directory.
6. Documentation explicitly states that `reference/opencode` is reference-only and not a proof source.

## 12. Why this is the right-sized change

The current repo already has the correct high-level semantics. The missing piece is an explicit boundary guard against future misuse of reference-side material.

This design adds exactly that:

- one narrow source guard;
- one regression that locks it in;
- one documentation clarification;
- no new authority source;
- no change to Task 7 readiness.

That keeps the current ResearchFlow harness honest without pretending upstream OpenCode proof support exists when it does not.

## 13. Review adjustments incorporated

This spec intentionally makes the following points explicit so planning can proceed without ambiguity:

- trusted proof provenance is defined by the current harness results tree, not by git commit-state checks;
- the guard must validate both the trusted root path and the fixed artifact filenames;
- `run.py` and `preflight.py` must share the same loader so there is one defended boundary;
- the preferred regression asserts attempted proof-read paths, not only the final blocked outcome;
- the adjacent documentation target is explicitly `docs/superpowers/specs/2026-07-20-opencode-proof-contract-revision-design.md`.

These adjustments close the main review gap without broadening scope.

## 14. Final scope check

This remains a single-subsystem plan:

- one narrow harness boundary guard;
- one regression family in `test_preflight.py`;
- narrow doc updates.

It does not need decomposition into multiple specs or plans.

## 15. Ambiguity resolution for planning

The plan should treat the following choices as already decided:

- the shared helper lives in `tests/harness-acceptance/lib.py`;
- both `tests/harness-acceptance/preflight.py` and `tests/harness-acceptance/run.py` must call it;
- the helper fails loudly when `run_dir` resolves outside `tests/harness-acceptance/results/`;
- no implementation step may add fallback to `reference/`, `reference/opencode`, repository-root files, or inferred diagnostics.

That removes the remaining interpretive branches for implementation planning.

## 16. Spec self-review

Checked before planning:

- No placeholders remain.
- The trusted-path requirement and the file-impact section now agree.
- The test strategy and success criteria both assert path provenance, not just outcome.
- Scope remains narrow and current-repo-only.

This spec is ready for implementation planning.

## 17. Implementation transition note

The next step should be a single implementation plan covering:

- shared loader/guard in `lib.py`;
- helper adoption in `preflight.py` and `run.py`;
- regression coverage in `test_preflight.py`;
- narrow doc updates.

No additional design work is required before writing that plan.

## 18. Planning readiness conclusion

This design now has one clear authority boundary, one clear test strategy, and one clear file set for implementation. It is ready for planning.
