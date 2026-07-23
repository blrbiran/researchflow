# ResearchFlow Plugin Handover

> Updated: 2026-07-22
> Expected agent cwd: the ResearchFlow repository root (`reference/researchflow/` from the parent; `.` inside this document)
> Remote: `git@github.com:blrbiran/researchflow.git`
> Historical design checkout branch: `docs/live-harness-acceptance-design`
> Repository-root branch: `main`
> Repository-root HEAD: local `main` included `9932dda` when this handover was refreshed. If exact HEAD matters, verify with `git rev-parse --short HEAD` at resume time because later handover edits or local commits will advance it.
> Origin branch state: intentionally omitted here; verify with `git status --short --branch` or `git rev-list --left-right --count origin/main...HEAD` at resume time if exact divergence matters.
> Preserved implementation worktree from this cwd: none
> Preserved implementation branch: none
> Preserved implementation HEAD: none
> Separate active upstream implementation workspace: none
> The earlier `reference/opencode/.worktrees/runtime-proof-surface` checkout remains reference-only and clean at `9747fef07`; do not modify or commit there from this workflow.
> Task 5 synthetic preflight/orchestration was completed, reviewed, merged locally to `main`, and its manual `.worktrees/task5-synthetic-preflight-orchestration` workspace was removed.
> The latest Task 5 code is already in local `main` ancestry under merge commit `673f8a6`.
> Task 6 design is now approved in `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md`.
> Task 6 implementation plan is now approved in `docs/superpowers/plans/2026-07-19-task6-real-preflight.md`.
> Task 6 Task 1/2 synthetic implementation is now merged locally to `main` via `2f243ea`, adding machine-readable preflight outcomes plus a read-only continuation-validation CLI.
> Task 6 later completed as a blocked real-preflight outcome; the committed evidence remains `tests/harness-acceptance/results/2026-07-19T152433Z/` with `reason_code = global_hard_gate_blocked` under the old contract.
> There is still no scored acceptance run and no live acceptance evidence beyond that blocked preflight record.
> The immediate next step is no longer “run Task 6 real preflight-only” — future work should start from the current proof-boundary-hardened `main` state and continue only if the user explicitly wants more Task 6 / Task 7 work.
> Do not reopen Task 5 unless new evidence shows a concrete regression against the merged local `main` behavior or the approved Task 5 design/plan.
> The parent `ccmem_paper` repository currently points to this newer ResearchFlow state; no additional submodule-pointer commit is needed unless later local commits are made here.
> Local planning/design docs now include Task 5 and Task 6 records; preserve them unless the user explicitly asks otherwise.
> Repo-local `.claude/worktrees/agent-a7e704d91a6ea7c24` no longer exists.
> Repo-local `.claude/worktrees/agent-af92299cb5b976a2b` currently remains harness/session residue with local `.omc/`; do not discard it silently.
> Additional `.claude/worktrees/agent-*` entries may remain harness/session residue; do not clean them without explicit per-path review and user approval.
> Safe observed tool versions remain:
> - Claude Code: `2.1.214`
> - OpenCode: `1.18.3`
> - Python: `3.9.13`
> Future agents should treat the latest canonical local implementation state as repo-root `main` including the 2026-07-21 reference-only OpenCode proof-boundary hardening merged during this pass. If an exact SHA matters, verify it at resume time.
> The temporary repo-local implementation workspace `.worktrees/task6-real-preflight-20260719a` was merged back and removed; future agents should start from repo-root `main`, not revive it.
> Root OpenWolf files were only partially refreshed in this pass; future agents should verify `.wolf/anatomy.md`, `.wolf/memory.md`, and `.wolf/buglog.json` against current repo state before relying on them.
> End of current-state header.
> 
> Executive summary for next agent (10 lines max):
> 1. ResearchFlow repo root stays on local `main`; at handover refresh it included commits through `9932dda`, but verify exact SHA at resume time because later handover edits change HEAD.
> 2. Historical Task 6 evidence remains `tests/harness-acceptance/results/2026-07-19T152433Z/` and is still blocked old-contract evidence with `reason_code = global_hard_gate_blocked`.
> 3. Current harness boundary is now explicit: only current-run preflight artifacts under `tests/harness-acceptance/results/<run-id>/preflight/` count as runtime model proof.
> 4. `reference/opencode` is reference-only in this workflow; do not modify it or consume it as authoritative proof input.
> 5. Task 7 is still not started; do not run scored cases unless a new continuation-ready Task 6 run is explicitly produced.
> 6. The 2026-07-21 current-repo design/plan are `docs/superpowers/specs/2026-07-21-reference-opencode-proof-boundary-design.md` and `docs/superpowers/plans/2026-07-21-reference-opencode-proof-boundary.md`.
> 7. Boundary-hardening implementation is merged locally to `main`; the temporary `.worktrees/proof-boundary` branch/worktree were merged and removed.
> 8. Most recent merged verification on repo-root `main`: `./tests/harness-acceptance/run-tests.sh` = **111 passed**, `./tests/run-all.sh` = **pass**.
> 9. OpenCode smoke still emits the pre-existing `[MODULE_TYPELESS_PACKAGE_JSON]` Node warning but exits successfully.
> 10. Preserve repo-local `.claude/worktrees/agent-*` residue and any `.omc/`; do not clean them without explicit approval.
> 
> 
> Historical notes below remain for provenance only.
> 
> > Task 4 synthetic review-closure commits now in `main`: `5ef0c7f`, `4896875`, `1b13451`, `46791dd`, `ab71a30`
> Historical note: the temporary `.worktrees/task4-review-close` and `.worktrees/task5-synthetic-preflight-orchestration` workspaces were both merged back and removed in earlier passes.
> Historical note: earlier handover snapshots referred to repo-local `.claude/worktrees/agent-a7e704d91a6ea7c24`; that path no longer exists in the current checkout.
> Historical note: earlier Task 4 / Task 5 state and parent-repo gitlink references below should be treated as superseded provenance, not current operational guidance.
>
>
## 1. Purpose and settled decisions

ResearchFlow is a standalone plugin for research and academic-paper workflows. It exposes one thin public router instead of a marketplace of overlapping research skills.

Settled decisions:

- Plugin and repo name: `researchflow`.
- Bootstrap/router skill: `using-researchflow`.
- First-class harnesses: Claude Code and OpenCode.
- The only primary phases remain:
  - `literature-discovery`
  - `paper-structuring`
  - `paper-drafting`
  - `paper-review`
  - `artifact-packaging`
- Canonical phase contracts live in `docs/workflow-contracts.md`.
- Route to the earliest missing or unstable artifact, not merely to the section or file the user mentions.
- Support skills remain subordinate to one primary phase per turn.
- Router model: thin router; `using-researchflow` remains the sole public entrypoint over the five primary phases.
- The V1 router defaults to direct routing and asks exactly one clarification question only for high-cost adjacent-phase ambiguity that cannot be resolved from available context.
- External reference libraries influence internal route hints, phase policies, and execution heuristics; they do not become peer top-level routes or runtime dependencies.

## 2. Repository topology and current branch state

### 2.1 Cwd contract

Future agents start with this ResearchFlow repository root as their cwd. From that cwd:

- run `git status`, `git log`, and `git worktree list` directly from this cwd; no parent-root path prefix is needed;
- treat paths in this handover as cwd-relative unless explicitly labeled as parent-repo or Git common-dir paths;
- read the approved design at `docs/superpowers/specs/2026-07-17-live-harness-acceptance-design.md`;
- read the execution plan at `docs/superpowers/plans/2026-07-17-live-harness-acceptance.md`;
- use the local links under `reference/` when comparative source material is needed.

### 2.2 Parent integration and Git metadata

ResearchFlow is an intentional submodule of the parent `ccmem_paper` repository:

- parent `.gitmodules` registers `reference/researchflow` with branch `main`;
- the parent gitlink currently points to the current repo-root checkout on `main` as refreshed in this handover pass; verify the exact SHA with `git ls-tree HEAD reference/researchflow` from the parent repo if it matters;
- the parent currently does not need a gitlink update for the merged current state captured here, but it may still contain unrelated local changes outside this submodule;
- do not stage or commit unrelated parent-repo changes while working in ResearchFlow.

The `.git` entry in this cwd is intentionally a submodule pointer:

```text
gitdir: ../../.git/modules/reference/researchflow
```

The resulting Git common-dir is the parent administrative path `.git/modules/reference/researchflow`. This is the standard Git submodule layout and **must not be manually moved into this repository**. Moving it would require coordinated changes to the parent repository, `core.worktree`, every linked-worktree administrative record, and every worktree `.git` pointer; an ad-hoc move risks corrupting all registered worktrees.

Verify the live topology from this cwd with:

```bash
git rev-parse --path-format=absolute --git-dir
git rev-parse --path-format=absolute --git-common-dir
git rev-parse --show-superproject-working-tree
git worktree list --porcelain
```

### 2.3 Existing worktree topology and placement decision

Registered worktrees currently live in two groups:

1. harness worktrees under the Git common-dir `.git/modules/reference/researchflow/.claude/worktrees/agent-*`;
2. older repo-local harness worktrees under `.claude/worktrees/agent-*`.

There is no remaining manual `.worktrees/*` checkout under this repo root.

Do **not** move existing harness-owned `agent-*` directories with filesystem `mv`. Their paths are registered in Git administrative records and may also be owned by current or previous Claude sessions. If a move is ever required, first preserve dirty work, then use `git worktree move <old> <new>` from this cwd, one clean/unlocked worktree at a time, and verify `git worktree list --porcelain` after each move.

For new manually managed feature worktrees, use the ignored cwd-local `.worktrees/<feature>/` directory. This provides a discoverable cwd-relative location without relocating the standard submodule common-dir or harness-managed worktrees.

Current inventory snapshot intentionally omits fixed counts because these worktree totals and residue paths drift quickly between sessions. Re-check live state with:

```bash
git worktree list --porcelain
find .claude/worktrees -maxdepth 1 -type d -name 'agent-*' 2>/dev/null
```

Current notable worktree state:

- repo-local `.claude/worktrees/agent-*` directories may remain as harness/session residue with local `.omc/`, `.superpowers/`, or `__pycache__/` artifacts;
- repo-local `.claude/worktrees/agent-af92299cb5b976a2b` remains specifically called out elsewhere in this handover and must not be silently discarded;
- the previously discussed Task 4 source worktree `agent-a3d082809313796c3` and accidental review worktree `agent-abee9411bb8fc2bd2` were already manually removed in earlier passes.

Treat any additional cleanup as destructive shared-state work: review exact live paths and dirty state before removal.

### 2.4 Local reference-library symlinks

The ignored `reference/` directory contains relative symlinks for cwd-local access:

```text
reference/ECC -> ../../ECC
reference/academic-research-skills -> ../../academic-research-skills
reference/Supervisor-Skills -> ../../Supervisor-Skills
reference/gstack -> ../../gstack
reference/superpowers -> ../../superpowers
```

All five links currently resolve to the corresponding parent `ccmem_paper/reference/*` directories. They are local research inputs, not runtime dependencies. Do not force-add, rewrite, or delete them without an explicit decision. Because the targets are relative, they remain valid while this repository stays at `ccmem_paper/reference/researchflow`; a standalone clone elsewhere must recreate or replace them.

### 2.5 Historical design checkout

The original live-harness design/handover work happened on `docs/live-harness-acceptance-design`, but the repository-root checkout is no longer on that branch.

Current repo-root state at handover refresh:

- branch: `main`;
- local `main` included `9932dda` when refreshed, but re-check exact HEAD if it matters because this handover file may itself be committed later;
- upstream: `origin/main`;
- local `main` was aligned with `origin/main` (`0 ahead / 0 behind`) when refreshed.

Use the historical design branch only when you specifically need to inspect the earlier design-only checkout state.

### 2.6 Active implementation workspace

There is no remaining manual `.worktrees/*` implementation checkout under this repo root.

The temporary `.worktrees/task4-review-close/` workspace used for the Task 4 closure pass has already been merged into `main` and removed.

The later `.worktrees/task5-synthetic-preflight-orchestration/` workspace used for Task 5 implementation and local merge-back has also been removed after successful merge to `main`.

The later `.worktrees/task6-real-preflight-20260719a/` workspace used for Task 6 implementation, review loops, and final real preflight evidence has also been merged into `main` and removed.

Future implementation should start from repo-root `main` as observed at resume time, or from a fresh new repo-local worktree created from that current `main`. Do not assume any earlier Task 4 / Task 5 / Task 6 / proof-boundary convenience checkout still exists.

## 3. Completed thin-router delivery

The thin-router work is complete and already part of `main` ancestry.

Key commits:

- `2e0aa64` — tighten `using-researchflow` routing invariants
- `9862424` — align public/contributor/handover docs
- `b3adc46` — add repo-local router acceptance check
- `d41f922` — contract-backed routing coverage, remove expert-mode surface, refresh handover, make OpenCode path check worktree-safe
- `23488db` — preserve unified-router design and implementation-plan records

Current router checks verify:

- `using-researchflow` remains the sole public router;
- the five primary phases remain fixed;
- routing stays anchored to `docs/workflow-contracts.md`;
- no expert-mode peer router is exposed;
- Claude-facing docs remain aligned;
- OpenCode bootstrap injects `using-researchflow`.

Do not reopen or modify router behavior as part of the live-harness acceptance work.

## 4. Live-harness acceptance design and plan

The approved design and implementation plan remain:

- Design: `docs/superpowers/specs/2026-07-17-live-harness-acceptance-design.md`
- Plan: `docs/superpowers/plans/2026-07-17-live-harness-acceptance.md`

Design commits:

- `028409e` — initial live-harness design
- `dcf557a` — executable marker, isolation, model, plugin-proof, and evidence contracts
- `eadd9c2` — normalized invocation, LiteLLM/OpenAI alignment, contamination/tool accounting
- `0fd87d5` — capability proof fallbacks, committed model proofs, exact no-score accounting
- `500dd72` — seven-task implementation plan
- `1878a9d` — ignore project-local implementation worktrees

### 4.1 Fixed first-run scope

The original acceptance run remains bounded to:

- seven shared cases per harness;
- five direct routes and two backward routes;
- one fresh non-interactive invocation per case;
- at most 14 scored invocations total;
- no automatic retries;
- no clarification cases;
- no router edits;
- no version bump, release, publish, or push.

### 4.2 Routing-only output contract

Every scored prompt appends one shared suffix. The final response must:

1. begin with exactly one line:

   ```text
   ResearchFlow phase: <phase-id>
   ```

2. contain at most two additional non-empty plain-text lines;
3. not execute literature discovery, structuring, drafting, review, or packaging;
4. not use headings, lists, blockquotes, code fences, or an extra phase marker.

The deterministic judge reads only:

- `cases.json`
- normalized `invocation.json`
- `final-response.txt`

It never calls an LLM.

### 4.3 Model topology and hard gate

The current environment uses this topology:

```text
Claude Code / OpenCode harness -> LiteLLM base_url proxy -> OpenAI backing model
```

Important constraints:

- Claude model aliases such as `fable` do not prove the backing model.
- OpenCode route names do not prove the backing model.
- Never record or print the full `base_url`, API keys, proxy credentials, auth headers, or raw environment values.
- Each harness must emit a committed, redacted `<harness>-model-proof.json`.
- Both proofs must independently resolve to the same verified canonical `openai/<model>` identity before any scored case starts.
- If an otherwise valid backing model is absent from `model-identities.json`, stop before scoring, review the redacted proof, add the exact mapping in a separate commit, and rerun preflight with a new run ID.
- If identity cannot be verified or aligned, generate a complete 14-row reason-coded unattempted result and stop.

### 4.4 Plugin-proof and isolation rules

Capability probes select proof branches rather than assuming CLI commands:

- Claude:
  - direct `--plugin-dir`, or
  - local marketplace install, or
  - blocked if neither can be proved.
- OpenCode:
  - strong runtime source/inventory proof when debug surfaces exist, or
  - workspace-config/static-inventory/canary fallback, or
  - blocked if neither proof bundle is complete.

Plugin metadata is always adapter-schema validated. CLI-native validation is optional strengthening evidence.

The selected isolation profile ID must match capability, preflight, and invocation artifacts. Any successful tool execution is `harness_error`; a runtime-blocked tool attempt with complete evidence is a contamination overlay.

## 5. Implementation progress

### 5.1 Task 1 — shared contracts — complete

Implementation commits:

- `c02ae13` — define live harness acceptance contracts
- `cbce609` — freeze exact case contract, reject invalid regexes, remove guessed production model identity

Delivered:

- `tests/harness-acceptance/cases.json`
- `scored-prompt.txt`
- `model-identities.json` with empty `canonical_models`
- shared `lib.py`
- contract tests
- local/raw evidence ignore rules

Review result: clean after fixes.

### 5.2 Task 2 — deterministic judge — complete

Implementation commits:

- `de71099` — deterministic routing verdict judge and synthetic fixtures
- `2173bd4` — fail closed when a blocked tool audit is incomplete

Delivered:

- line-level marker parser;
- `pass`, `fail`, `indeterminate`, and `harness_error` classification;
- contamination overlay;
- concrete forbidden-pattern handling;
- reviewable verdict JSON;
- no-overwrite CLI;
- Python 3.9 compatibility.

Review result: clean after controller-verified Python 3.9 compile/tests.

### 5.3 Task 3 — redaction and summary packaging — complete

Implementation commits:

- `68554ac` — redaction, model-proof validation, deterministic summary
- `2fcb3b6` — close redaction, runtime-stop, plugin-source, and atomic-write review gaps
- `4dc9ff9` — remove accidentally tracked SDD report and ignore `.superpowers/`

Delivered:

- fail-closed scanner for home paths, base URL fields, credentials/tokens, unrelated absolute paths, and deterministic private-instruction fragments;
- committed model-proof validation against the allowlist;
- exactly 14 ordered accounting rows;
- exclusive verdict partitions plus contamination overlay;
- model-alignment and no-score accounting;
- runtime-stop enforcement;
- plugin-source disclosure/consistency;
- atomic no-overwrite summary writes;
- deterministic `summary.json` and `summary.md`.

Review result: clean after fixes.

### 5.4 Task 4 — capability probes and native adapters — synthetically review-closed on `main`

Task 4 implementation and closure commits now in `main` ancestry:

- `6a9a451` — `test: add native harness capability adapters`
- `007f882` — `fix: harden native harness capability probes`
- `5ef0c7f` — `fix: lock Task 4 prompt and workspace contract`
- `4896875` — `fix: fail-close Task 4 capability normalization`
- `1b13451` — `fix: close Task 4 synthetic review gaps`
- `46791dd` — `fix: remove out-of-scope cerebrum drift`
- `ab71a30` — `fix: fail-close full isolation capability proof`

Delivered files committed through Task 4 and its closure pass include:

- `tests/harness-acceptance/capabilities.py`
- `tests/harness-acceptance/adapters/claude.sh`
- `tests/harness-acceptance/adapters/opencode.sh`
- `tests/harness-acceptance/test_capabilities.py`
- `tests/harness-acceptance/test_adapters.py`
- adapter/capability fixtures under `tests/harness-acceptance/fixtures/adapters/**`
- capability fixtures under `tests/harness-acceptance/fixtures/capabilities/**`

What is now verified on merged `main @ ab71a30`:

- `bash -n tests/harness-acceptance/adapters/claude.sh` passed;
- `bash -n tests/harness-acceptance/adapters/opencode.sh` passed;
- `python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v` passed with **56 passed, 0 failed**;
- `./tests/run-all.sh` passed with `All ResearchFlow tests passed.`;
- task-scoped and whole-branch reviews both passed, with only one final non-blocking minor note about stale helper parameters in `tests/harness-acceptance/test_adapters.py`;
- no real Claude Code, OpenCode, LiteLLM, network, or paid-model invocation was performed during the Task 4 closure pass.

Task 4 is therefore **synthetically review-closed only**. Historical note: at the time of Task 4 closure there was still no real preflight-only run, no scored acceptance run, and no live acceptance evidence. Later Task 6 work changed that state by adding a blocked real-preflight evidence set.

### 5.5 Tasks 5–7 — current status

- Task 5: **complete on `main`** — synthetic preflight, model-alignment hard gate, orchestration, synthetic runner wiring, and fail-closed follow-up fixes are merged into `main` ancestry through `673f8a6` plus later follow-up commits reachable from current `main`.
- Task 6: historical blocked evidence remains committed, but future runs now classify under the dual-track contract as `blocked`, `allowlist-update-needed`, `continuation-ready-strong`, or `continuation-ready-conditional`.

  Contract note: `continuation-ready-conditional` is allowed only when Claude is authoritatively proved and canonicalized, OpenCode capability / preflight passes, OpenCode runtime proof remains unavailable, and no other hard gate fails.

  Historical evidence rule: do not rewrite committed blocked runs in place; treat them as records of the contract state that existed when they were generated.

  Current-proof-boundary note: `reference/opencode` is reference-only in the current workflow and must not be consumed as authoritative runtime proof input for Task 6 / Task 7 continuation decisions. Current ResearchFlow harness evaluation accepts runtime model proof only from the current run's preflight artifacts under `tests/harness-acceptance/results/<run-id>/preflight/`.
- Task 7: **not started** — at most 14 scored cases and bounded evidence packaging, only after a new Task 6 run reaches either `continuation-ready-strong` or `continuation-ready-conditional`.

  Result-contract note: accepted Task 7 results now use top-level `outcome = accepted` plus `acceptance_class = strong | conditional-opencode`. Only `acceptance_class = strong` supports a verified cross-harness same-model claim.

### 5.6 Current-repo OpenCode proof-boundary hardening — complete on `main`

The earlier OpenCode-upstream runtime-proof surface workstream is no longer the active operational target for this repo.

The user later clarified that `reference/opencode` is reference-only in this workflow and must not be modified, committed, or consumed as authoritative runtime proof input. The accepted implementation scope moved back into the current ResearchFlow repo.

Approved current-repo design / plan records for this follow-up workstream:

- Spec: `docs/superpowers/specs/2026-07-21-reference-opencode-proof-boundary-design.md`
- Plan: `docs/superpowers/plans/2026-07-21-reference-opencode-proof-boundary.md`

What this merged current-repo work now guarantees:

- runtime model proof input is accepted only from the current run's preflight artifacts under `tests/harness-acceptance/results/<run-id>/preflight/`;
- `reference/opencode` remains diagnostic/reference material only;
- both `tests/harness-acceptance/preflight.py` and `tests/harness-acceptance/run.py` route through the same shared proof-loader boundary in `tests/harness-acceptance/lib.py`;
- untrusted `results_root`, symlinked proof-file escapes, cross-run proof borrowing, and symlinked run-dir aliases now fail closed;
- no new proof source or Task 7 continuation path was introduced.

Merged local `main` now includes the current-repo proof-boundary hardening commit series through `9932dda`, including:

- `1f548a4` — `test: guard trusted runtime proof root`
- `97db10a` — `fix: keep runtime proof artifacts inside the current run`
- `1643d32` — `fix: keep preflight proof reads current-run only`
- `60db5ae` — `refactor: share trusted proof loader`
- `abef2b3` — `docs: clarify reference-only opencode proof boundary`
- `fc4e67d` — `fix: reject untrusted harness results roots`
- `9932dda` — `fix: reject symlinked run alias proof paths`

The temporary repo-local implementation workspace `.worktrees/proof-boundary` was merged back and removed after verification. Future agents should work from repo-root `main`, not recreate the earlier boundary-hardening branch unless the user asks for more changes in this area.

The earlier `reference/opencode/.worktrees/runtime-proof-surface` checkout still exists as reference-only context at `9747fef07`, but it is not part of the accepted implementation surface for this repo.

End of current current-repo follow-up note.

Real Claude Code and OpenCode invocations were performed during Task 6 preflight-only execution. No scored acceptance invocation has been performed yet.

## 6. Current test status

Most recent local verification on merged repo-root `main` at handover refresh:

```bash
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
```

Result on 2026-07-22:

- harness acceptance synthetic suite: **111 passed, 0 failed**
- OpenCode bootstrap smoke test: passed
- Claude metadata/file smoke coverage plus repo-local routing-doc smoke coverage: passed
- all three workflow demo contract tests: passed
- unified result: `All ResearchFlow tests passed.`
- note: the OpenCode smoke test still emits the pre-existing Node warning `[MODULE_TYPELESS_PACKAGE_JSON]` for `.opencode/plugins/researchflow.js`; the suite still exits successfully.

Safe tool versions observed without exposing configuration values:

- Claude Code: `2.1.214`
- OpenCode: `1.18.3`
- Python: `3.9.13`

## 7. Exact next step for the next agent

Resume from repo-root `main` and verify the exact SHA at start if that matters; this handover file may have advanced HEAD again by the time the next agent reads it.

The current-repo proof-boundary hardening is complete. The next step is no longer OpenCode-upstream surface work from this repo. Future work, if any, should proceed from the current ResearchFlow repo state and follow these rules:

1. Treat `reference/opencode` as reference-only. Do not modify it and do not consume it as authoritative runtime proof input.
2. If continuing Task 6 / Task 7 work, first read:

   ```text
   docs/superpowers/specs/2026-07-21-reference-opencode-proof-boundary-design.md
   docs/superpowers/plans/2026-07-21-reference-opencode-proof-boundary.md
   tests/harness-acceptance/lib.py
   tests/harness-acceptance/preflight.py
   tests/harness-acceptance/run.py
   tests/harness-acceptance/test_preflight.py
   tests/harness-acceptance/test_run.py
   ```

3. Review the committed blocked evidence set:

   ```text
   tests/harness-acceptance/results/2026-07-19T152433Z/
   ```

4. Re-run the synthetic baseline before any new real-harness work:

   ```bash
   ./tests/harness-acceptance/run-tests.sh
   ./tests/run-all.sh
   ```

5. Do not run scored cases unless a new Task 6 run reaches either `continuation-ready-strong` or `continuation-ready-conditional` under the current contract.
6. Do not infer canonical model identity from static config, route labels, resolved config dumps, or anything under `reference/opencode`; only current-run redacted proof artifacts can establish runtime proof in this repo.
7. Do not move, delete, prune, or clean any `.claude/worktrees/agent-*` directory without explicit user approval. Do not touch `.omc/` in any worktree.

## 8. Remaining implementation order and stop conditions

Proceed in this order only:

1. Preserve the historical Task 6 blocked evidence and apply the revised OpenCode proof contract only to future runs.
2. Produce a new Task 6 run that classifies under the active contract as `blocked`, `allowlist-update-needed`, `continuation-ready-strong`, or `continuation-ready-conditional`.
3. Task 7 scored run only if a new Task 6 run reaches `continuation-ready-strong` or `continuation-ready-conditional`.

Hard stops:

- If capability/plugin proof cannot be established, create blocked evidence; do not improvise a load command.
- If Claude proof is real but not canonicalized under the allowlist, stop on `allowlist-update-needed`; do not treat that as conditional continuation.
- If both harnesses cannot verify the same OpenAI backing model from real redacted proof and the run does not legally qualify for conditional continuation, do not start Task 7.
- If redaction finds a leak, do not stage evidence.
- If a successful tool execution occurs during a scored case, classify it as `harness_error`.
- Never retry a scored case in the original run.
- Never exceed 14 scored invocations.
- Do not treat previously committed blocked Task 6 evidence as proof that Task 7 can start; only a new run classified under the active contract can serve as a legal Task 7 entrypoint.

## 9. Known limitations and unresolved work

- Claude Code still has no saved real fresh-session routing transcript beyond the Task 6 preflight proof artifacts.
- OpenCode still has no accepted authoritative runtime model-proof input for current ResearchFlow continuation decisions beyond the current run's own trusted preflight artifacts.
- No accepted evidence exists yet under either `acceptance_class = strong` or `acceptance_class = conditional-opencode`.
- No backing-model identity has been added to `canonical_models`; it must remain empty until real redacted proof exists from both harnesses or from Claude alone for an allowlist-update-needed path.
- No scored acceptance result exists; do not claim acceptance, stability, or release readiness.
- Release version remains `0.1.0`.
- No release candidate, version bump, publish, or push is authorized by this work.
- Cross-artifact semantic checks and contract-schema centralization remain separate future work.
- Repo-local `.claude/worktrees/agent-af92299cb5b976a2b` remains harness/session residue with local `.omc/`; preserve it unless the user explicitly approves cleanup.
- Many remaining harness worktrees may still be session residue with `.omc/` or other untracked local artifacts; clean them only with explicit per-path review and user approval.
- The parent `ccmem_paper` repository currently reflects this ResearchFlow state at handover refresh time; only future local commits here would require another parent gitlink update.

## 10. Safety and workflow reminders

- Preserve the current-run-only proof boundary.
- Preserve `reference/opencode` as reference-only.
- Preserve the dual-track acceptance split in future docs and summaries.
- Do not collapse `acceptance_class = strong` and `acceptance_class = conditional-opencode` into one generic acceptance claim.
- Keep `proof_facts` as evidence facts, separate from top-level accepted/blocked outcome.
- Keep Claude canonicalization as the anchor for conditional continuation.
- Never clean worktree residue without explicit approval.

End of updated handover note.
