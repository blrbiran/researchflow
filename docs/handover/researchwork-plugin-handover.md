# ResearchFlow Plugin Handover

> Updated: 2026-07-20
> Expected agent cwd: the ResearchFlow repository root (`reference/researchflow/` from the parent; `.` inside this document)
> Remote: `git@github.com:blrbiran/researchflow.git`
> Historical design checkout branch: `docs/live-harness-acceptance-design`
> Repository-root branch: `main`
> Repository-root HEAD: `b4cb6b8` at the time this handover was refreshed. This may advance again if the handover itself is later committed or additional local commits are made.
> Origin branch state: intentionally omitted here; verify with `git status --short --branch` or `git rev-list --left-right --count origin/main...HEAD` at resume time if exact divergence matters.
> Preserved implementation worktree from this cwd: none
> Preserved implementation branch: none
> Preserved implementation HEAD: none
> Task 5 synthetic preflight/orchestration was completed, reviewed, merged locally to `main`, and its manual `.worktrees/task5-synthetic-preflight-orchestration` workspace was removed.
> The latest Task 5 code is already in local `main` ancestry under merge commit `673f8a6`.
> Task 6 design is now approved in `docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md`.
> Task 6 implementation plan is now approved in `docs/superpowers/plans/2026-07-19-task6-real-preflight.md`.
> Task 6 Task 1/2 synthetic implementation is now merged locally to `main` via `2f243ea`, adding machine-readable preflight outcomes plus a read-only continuation-validation CLI.
> There is still no real preflight-only run, no scored acceptance run, and no live acceptance evidence.
> The next implementation step is still Task 6 real preflight-only execution.
> Do not reopen Task 5 unless new evidence shows a concrete regression against the merged local `main` behavior or the approved Task 5 design/plan.
> The parent `ccmem_paper` repository still needs a separate submodule-pointer commit if the user wants it to record this newer ResearchFlow state.
> Local planning/design docs now include Task 5 and Task 6 records; preserve them unless the user explicitly asks otherwise.
> Repo-local `.claude/worktrees/agent-a7e704d91a6ea7c24` no longer exists.
> Repo-local `.claude/worktrees/agent-af92299cb5b976a2b` currently remains harness/session residue with local `.omc/`; do not discard it silently.
> Additional `.claude/worktrees/agent-*` entries may remain harness/session residue; do not clean them without explicit per-path review and user approval.
> Safe observed tool versions remain:
> - Claude Code: `2.1.214`
> - OpenCode: `1.18.3`
> - Python: `3.9.13`
> Future agents should treat the latest canonical local implementation state as repo-root `main @ b4cb6b8`, with Task 6 merged, a committed blocked real-preflight evidence set present, and Task 7 still not started.
> The temporary repo-local implementation workspace `.worktrees/task6-real-preflight-20260719a` was merged back and removed; future agents should start from repo-root `main`, not revive it.
> Root OpenWolf files were only partially refreshed in this pass; future agents should verify `.wolf/anatomy.md`, `.wolf/memory.md`, and `.wolf/buglog.json` against current repo state before relying on them.
> End of current-state header.
> 
> Executive summary for next agent (10 lines max):
> 1. CWD is this repo root; current local branch is `main` and this handover was refreshed at `main @ b4cb6b8`.
> 2. Task 5 is done in `main`; do not reopen it without new regression evidence.
> 3. Task 6 is now merged to `main`, including updated spec/plan, fail-closed Opencode proof handling, and final real preflight evidence.
> 4. Final committed evidence run: `tests/harness-acceptance/results/2026-07-19T152433Z/`.
> 5. Final Task 6 result: `blocked` with `reason_code = global_hard_gate_blocked`.
> 6. Claude proved `openai/gpt-5.4`; Opencode remained preflight-blocked and did not yield authoritative runtime model proof.
> 7. There is still no continuation-ready Task 7 entrypoint and no scored acceptance run; do not run scored cases from this state.
> 8. If future work continues Task 6/7, start from repo-root `main`, re-read the updated Task 6 spec/plan, and preserve the committed blocked evidence.
> 9. Preserve repo-local `.claude/worktrees/agent-af92299cb5b976a2b` and any `.omc/`; do not clean harness worktrees without explicit approval.
> 10. The parent `ccmem_paper` repo still needs a separate submodule pointer commit if the user wants to record this ResearchFlow state.
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
- the parent gitlink currently points to `b4cb6b8`, matching this repo-root checkout on `main`;
- the parent no longer needs a gitlink update for the merged Task 6 work captured here, but it may still contain unrelated local changes outside this submodule;
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

Current inventory snapshot:

- Git common-dir `agent-*` worktrees: 7 registered;
- repo-local `.claude/worktrees/agent-*` directories: 21 present;
- cwd-local `.worktrees`: zero remaining manual worktrees.

Current notable worktree state:

- repo-local `agent-a7e704d91a6ea7c24` still contains a historical tracked modification to `tests/claude-code/run-tests.sh` plus local `.omc/`; it must not be silently discarded;
- many remaining harness-owned worktrees are session residue with only untracked `.omc/`;
- some harness-owned worktrees also contain untracked `.superpowers/` or `__pycache__/` artifacts;
- the previously discussed Task 4 source worktree `agent-a3d082809313796c3` and accidental review worktree `agent-abee9411bb8fc2bd2` have already been manually removed.

Treat any additional cleanup as destructive shared-state work: review exact paths and dirty state before removal.

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

Current repo-root state:

- branch: `main`;
- HEAD: `b4cb6b8 Merge branch 'task6-real-preflight-20260719a'`;
- upstream: `origin/main`;
- local `main` is currently aligned with `origin/main` (`0 ahead / 0 behind`).

Use the historical design branch only when you specifically need to inspect the earlier design-only checkout state.

### 2.6 Active implementation workspace

There is no remaining manual `.worktrees/*` implementation checkout under this repo root.

The temporary `.worktrees/task4-review-close/` workspace used for the Task 4 closure pass has already been merged into `main` and removed.

The later `.worktrees/task5-synthetic-preflight-orchestration/` workspace used for Task 5 implementation and local merge-back has also been removed after successful merge to `main`.

The later `.worktrees/task6-real-preflight-20260719a/` workspace used for Task 6 implementation, review loops, and final real preflight evidence has also been merged into `main` and removed.

Future implementation should start from repo-root `main @ b4cb6b8` or a fresh new repo-local worktree created from it. Do not assume any earlier Task 4/Task 5/Task 6 convenience checkout still exists.

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

Task 4 is therefore **synthetically review-closed only**. This does **not** mean live acceptance has been run. There is still no real preflight-only run, no scored acceptance run, and no live acceptance evidence.

### 5.5 Tasks 5–7 — current status

- Task 5: **complete on `main`** — synthetic preflight, model-alignment hard gate, orchestration, synthetic runner wiring, and fail-closed follow-up fixes are merged into `main` ancestry through `673f8a6` plus later follow-up commits reachable from current `main`.
- Task 6: **complete as a blocked real-preflight outcome on `main`** — Task 1/2 synthetic validation, fail-closed native proof-surface fixes, Task 6 spec/plan updates, and a committed real preflight-only evidence set are now merged into `main`. The final committed Task 6 evidence is the blocked run `tests/harness-acceptance/results/2026-07-19T152433Z/` with `reason_code = global_hard_gate_blocked`.
- Task 7: **not started** — at most 14 scored cases and bounded evidence packaging, only after a continuation-ready Task 6 run exists.

Real Claude Code and OpenCode invocations were performed during Task 6 preflight-only execution. No scored acceptance invocation has been performed yet.

## 6. Current test status

Most recent local verification on merged repo-root `main @ b4cb6b8`:

```bash
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
```

Result on 2026-07-20:

- harness acceptance synthetic suite: **101 passed, 0 failed**
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

Resume from repo-root `main @ b4cb6b8`.

The next implementation step is **decision-making, not more Task 6 replay**: decide whether to accept the current blocked Task 6 evidence as the terminal pre-Task-7 state, revise the Task 6/7 proof contract for OpenCode, or pursue a new OpenCode runtime-proof surface. Do not reopen Task 5 unless new evidence shows a concrete regression or a spec mismatch against merged `main`.

Recommended procedure from this cwd:

1. Verify current git state and whether the user wants any push/sync action; repo-root `main` is currently aligned with `origin/main`.
2. Read the updated Task 6 design and plan:

   ```text
   docs/superpowers/specs/2026-07-19-task6-real-preflight-design.md
   docs/superpowers/plans/2026-07-19-task6-real-preflight.md
   ```

3. Review the committed blocked evidence set:

   ```text
   tests/harness-acceptance/results/2026-07-19T152433Z/
   ```

4. If the user wants to continue Task 6/7 work, start from a fresh clean repo-local worktree or fresh environment based on current `main`; prefer `./.worktrees/` or `./.claude/worktrees/`, not parent `.git/modules/.../.claude/worktrees/agent-*` paths.
5. Re-run the synthetic baseline before any new real-harness work:

   ```bash
   ./tests/harness-acceptance/run-tests.sh
   ./tests/run-all.sh
   ```

6. Do not run scored cases unless a new continuation-ready Task 6 run is explicitly produced.
7. Do not move, delete, prune, or clean any `.claude/worktrees/agent-*` directory without explicit user approval. Do not touch `.omc/` in any worktree.
8. Do not infer canonical model identity from static config, route labels, or resolved config dumps; only real redacted proof can establish it.

## 8. Remaining implementation order and stop conditions

Proceed in this order only:

1. Accept or revise the current Task 6 blocked evidence contract.
2. Produce a new Task 6 continuation-ready run only if the proof contract or harness behavior changes.
3. Task 7 scored run only if a continuation-ready Task 6 run exists.

Hard stops:

- If capability/plugin proof cannot be established, create blocked evidence; do not improvise a load command.
- If both harnesses cannot verify the same OpenAI backing model from real redacted proof, do not start Task 7.
- If the model identity is newly proved but absent from the allowlist, commit the exact mapping and rerun preflight under a new run ID; do not score the old run.
- If redaction finds a leak, do not stage evidence.
- If a successful tool execution occurs during a scored case, classify it as `harness_error`.
- Never retry a scored case in the original run.
- Never exceed 14 scored invocations.
- Do not treat the committed blocked Task 6 evidence as proof that Task 7 can start; it is proof that current `main` still lacks a continuation-ready entrypoint.

## 9. Known limitations and unresolved work

- Claude Code still has no saved real fresh-session routing transcript beyond the Task 6 preflight proof artifacts.
- OpenCode still has no authoritative runtime model-proof surface on the current `openai-compatible` path, so Task 6 remains blocked on `global_hard_gate_blocked` rather than continuation-ready.
- No backing-model identity has been added to `canonical_models`; it must remain empty until real redacted proof exists from both harnesses.
- No scored acceptance result exists; do not claim acceptance, stability, or release readiness.
- Release version remains `0.1.0`.
- No release candidate, version bump, publish, or push is authorized by this work.
- Cross-artifact semantic checks and contract-schema centralization remain separate future work.
- Repo-local `.claude/worktrees/agent-af92299cb5b976a2b` remains harness/session residue with local `.omc/`; preserve it unless the user explicitly approves cleanup.
- Many remaining harness worktrees may still be session residue with `.omc/` or other untracked local artifacts; clean them only with explicit per-path review and user approval.
- The parent `ccmem_paper` repository still needs a separate submodule-pointer commit if the user wants it to record ResearchFlow `main @ b4cb6b8`.

## 10. Safety and workflow reminders

- Future agents should treat this repository root as cwd; use cwd-relative paths and direct Git commands.
- Do not commit unrelated parent-repo changes.
- The cwd-local `reference/` symlinks are ignored local research inputs; do not force-add, rewrite, or delete them.
- Keep the standard submodule Git common-dir at the parent `.git/modules/reference/researchflow`; do not manually relocate it.
- New manual worktrees belong under `.worktrees/`; existing harness-owned `.claude/worktrees/agent-*` stay registered where Git/Claude created them.
- Do not stage any worktree's `.omc/` directory.
- Do not log or commit `base_url`, API keys, auth headers, proxy credentials, raw environment variables, or user-home paths.
- Keep raw event streams in ignored local storage; committed evidence contains only redacted normalized artifacts and hashes.
- Do not modify the thin router or workflow contracts during acceptance implementation.
- Do not push without explicit user approval.
- Before reporting completion, run task review and then whole-branch review as required by subagent-driven development.
- When resuming after cleanup, prefer a new branch from `main` over reviving stopped harness worktrees whose deletion was interrupted.
