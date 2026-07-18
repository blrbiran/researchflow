# ResearchFlow Task 4 Review-Close Design Spec

Date: 2026-07-18  
Status: Draft for review  
Topic: Clean-environment review closure for live-harness acceptance Task 4

## 1. Purpose

This spec defines a bounded follow-up pass to close Task 4 of the live-harness acceptance work.

Task 4 is already merged on `main`, but the current handover explicitly says it is not yet review-closed for real-environment acceptance confidence. The next step is therefore not Task 5 orchestration, new router work, or more skill expansion. The next step is to re-review Task 4 from a fresh clean worktree, make only the minimum required fixes, and rerun the synthetic verification suite.

This pass answers one bounded question:

> Does the merged Task 4 implementation satisfy the approved adapter contract in a fresh clean worktree, with synthetic verification passing and no unresolved contract gaps?

This is a review-closure pass for synthetic confidence only. It does not claim live acceptance, real harness verification, release readiness, or completion of Tasks 5–7.

## 2. Scope and settled decisions

### 2.1 In scope

This pass covers only Task 4 review closure on top of repo-root `main`.

Allowed code changes are limited to the Task 4 surface and the smallest shared files directly required to close one of the five named review concerns:

- `tests/harness-acceptance/capabilities.py`
- `tests/harness-acceptance/adapters/claude.sh`
- `tests/harness-acceptance/adapters/opencode.sh`
- `tests/harness-acceptance/test_capabilities.py`
- `tests/harness-acceptance/test_adapters.py`
- `tests/harness-acceptance/scored-prompt.txt` only when the scored-suffix concern cannot be closed without changing the shared suffix itself
- directly related shared contract tests such as `tests/harness-acceptance/test_contracts.py` only when one of the five Task 4 review concerns cannot be proven or preserved otherwise
- Task 4-specific fixtures under `tests/harness-acceptance/fixtures/**`

If a contract gap can only be locked down with tests, the pass may add the smallest possible test or fixture update needed to prove the behavior.

### 2.2 Out of scope

This pass does not:

- start Task 5 preflight/orchestration work;
- modify router behavior, `skills/using-researchflow/SKILL.md`, or `docs/workflow-contracts.md`;
- perform real `claude`, `opencode`, LiteLLM, network, or paid-model invocation;
- clean up `.claude/worktrees/agent-*` directories;
- touch any `.omc/` directory;
- or claim live acceptance evidence.

### 2.3 Execution base

The work starts from repo-root `main`, not from `main-preserved` and not from an existing stopped harness worktree.

The implementation surface for this pass must be a fresh local worktree under:

```text
.worktrees/<task4-review-close>
```

This matches the current handover guidance that new manual feature worktrees belong under `.worktrees/` and that old harness-owned worktrees must not be reused or silently cleaned.

## 3. Chosen approach and rejected alternatives

### 3.1 Chosen approach: fresh-worktree review-fix-verify

The selected approach is:

1. create a fresh clean worktree from repo-root `main`;
2. re-read the approved live-harness design, implementation plan, and current handover;
3. re-review the merged Task 4 implementation against the explicit adapter contract;
4. make only the minimum required Task 4 fixes;
5. rerun the Task 4 synthetic suite and the repository-wide test runner;
6. declare Task 4 review-closed only if all review items are either already satisfied or are minimally fixed and verified.

This is the most reliable path because it matches the handover's explicit instruction to continue Task 4 from `main` in a fresh clean environment before any Task 5 work starts.

### 3.2 Rejected alternative: in-place review on the current checkout

Reviewing and fixing directly on the current checkout is faster, but it weakens the main point of the pass: confidence that Task 4 still holds in a fresh clean environment.

### 3.3 Rejected alternative: review-only audit without closure

A pure audit pass would produce findings, but it would split review and closure into two separate loops. The current need is a bounded close-out pass, not another open-ended inspection round.

## 4. Review target and working boundaries

Before any code change, the reviewer must read:

- `docs/handover/researchwork-plugin-handover.md`
- `docs/superpowers/specs/2026-07-17-live-harness-acceptance-design.md`
- `docs/superpowers/plans/2026-07-17-live-harness-acceptance.md`
- `tests/harness-acceptance/scored-prompt.txt`
- `tests/harness-acceptance/capabilities.py`
- `tests/harness-acceptance/adapters/claude.sh`
- `tests/harness-acceptance/adapters/opencode.sh`
- `tests/harness-acceptance/test_capabilities.py`
- `tests/harness-acceptance/test_adapters.py`
- the relevant Task 4 capability and adapter fixtures under `tests/harness-acceptance/fixtures/**` that are needed to evaluate native normalization, workspace isolation, capability proof, or production-vs-test wiring separation

The review is intentionally narrow. It is not a broad code-health pass and it is not a redesign of the harness layer. It checks only whether the already-merged Task 4 implementation satisfies the approved contract and handover caveats.

## 5. Review checklist

The review must evaluate exactly five contract areas called out by the handover.

Each item gets one of two outcomes:

- `meets contract`
- `needs fix`

If an item needs a fix, the pass applies the smallest change needed to move it to `meets contract` and adds the smallest contract test needed to keep it there.

### 5.1 Scored suffix composition

The adapter layer must compose the scored prompt suffix exactly as required by the shared routing-only output contract. Task 4 must not truncate it, mutate it, or append it inconsistently across harnesses.

### 5.2 Native JSON event-shape normalization

Claude and OpenCode native event streams must normalize into the expected Task 4 structures without optimistic assumptions. Unknown, malformed, or incomplete event shapes must fail closed rather than silently becoming empty-success output.

### 5.3 Claude fresh-workspace isolation

Claude case execution must operate from a fresh case workspace rather than reusing a contaminated working directory. The implementation must prove workspace isolation through the adapter contract rather than by test-only shortcuts.

### 5.4 Evidence-derived capability booleans

Capability and proof booleans must be derived from actual probe evidence. Missing evidence must not default to support. If a proof branch cannot be established, the result must remain unsupported.

### 5.5 Production vs test-only wiring separation

Fixture conveniences used by synthetic tests must remain test-only. Production adapter paths, config, and proof logic must not depend on fixture-only wiring or fake-CLI assumptions.

## 6. Fix strategy

### 6.1 Fail-closed review standard

This pass uses a fail-closed review rule:

- missing proof does not count as support;
- malformed native output does not count as a valid normalized result;
- unproved isolation does not count as isolated execution;
- and fixture-only behavior does not count as production correctness.

Only behavior that is explicitly grounded in code, fixtures, and tests counts as contract satisfaction.

### 6.2 Minimal change rule

The pass must remain surgical.

It should:

- patch the existing files rather than redesigning the adapter stack;
- avoid new abstraction layers unless they are strictly required by the contract;
- avoid unrelated cleanup or formatting churn;
- and add only the smallest test coverage needed to lock the intended behavior.

### 6.3 Repair order

When fixes are needed, the preferred order is:

1. capability/proof correctness;
2. native-event normalization correctness;
3. workspace-isolation correctness;
4. scored-suffix correctness;
5. targeted fixture/test updates.

This ordering prioritizes correctness boundaries that can invalidate all downstream behavior.

## 7. Verification procedure

After the review and any required minimal fixes, the pass must rerun:

```bash
bash -n tests/harness-acceptance/adapters/claude.sh
bash -n tests/harness-acceptance/adapters/opencode.sh
python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v
./tests/run-all.sh
```

The first two commands prove that both native adapter entrypoints remain syntactically valid. The third command proves the Task 4 synthetic acceptance surface. The fourth proves the repository-wide baseline still passes after the Task 4 closure changes.

No real harness or network invocation is allowed during this pass.

## 8. Completion criteria

Task 4 is review-closed for this pass only when all of the following are true:

1. all five review checklist items have an explicit conclusion;
2. every item is either already compliant or is minimally fixed to compliance;
3. `python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v` passes;
4. `./tests/run-all.sh` passes;
5. the final result can truthfully say:

   > Task 4 is synthetically review-closed in a fresh clean worktree with synthetic verification passing; no live harness acceptance has been performed.

This pass must not say:

- live acceptance is complete;
- real harness verification is complete;
- Tasks 5–7 are unblocked by execution evidence;
- or the plugin is release-ready.

## 9. Success criteria

This design is implemented correctly when:

- the work begins from repo-root `main` in a fresh local worktree under `.worktrees/`;
- the review remains limited to the merged Task 4 implementation and its direct synthetic contract;
- the five handover-named risk areas are all explicitly evaluated;
- any required changes are minimal and remain inside the Task 4 surface;
- synthetic verification passes after the fixes;
- and the resulting conclusion is narrow, precise, and does not overclaim beyond synthetic review closure.
