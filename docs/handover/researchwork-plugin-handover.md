# ResearchFlow Plugin Handover

> Updated: 2026-07-18
> Expected agent cwd: the ResearchFlow repository root (`reference/researchflow/` from the parent; `.` inside this document)
> Remote: `git@github.com:blrbiran/researchflow.git`
> Historical design checkout branch: `docs/live-harness-acceptance-design`
> Repository-root branch: `main`
> Repository-root HEAD: `ab71a30`
> Origin branch state: `main` matches `origin/main` at `ab71a30`
> Preserved implementation worktree from this cwd: none
> Preserved implementation branch: none
> Preserved implementation HEAD: none
> Task 4 synthetic review-closure commits now in `main`: `5ef0c7f`, `4896875`, `1b13451`, `46791dd`, `ab71a30`
> Parent repo note: the parent `ccmem_paper` checkout currently sees `reference/researchflow` as modified both because this handover file is still uncommitted in the repo-root working tree and because the parent gitlink still points to `964d14d`; after this handover update is committed here, the parent will still need a separate gitlink update to record `ab71a30`
> Cleanup note: the temporary `.worktrees/task4-review-close` branch/worktree used for Task 4 closure has already been merged into `main` and removed.
> Local planning artifacts from this closure pass remain untracked in this repo:
> - `docs/superpowers/specs/2026-07-18-task4-review-close-design.md`
> - `docs/superpowers/plans/2026-07-18-task4-review-close.md`
> They are context docs only and were not committed as part of the Task 4 code merge.
> Outstanding historical local worktree to preserve:
> - repo-local `.claude/worktrees/agent-a7e704d91a6ea7c24` still contains a tracked modification to `tests/claude-code/run-tests.sh` plus local `.omc/`; do not discard it silently.
> There is no remaining manual `.worktrees/*` checkout under this repo root.
> Safe verified rerun result after the final Task 4 fix on the merged branch:
> - `bash -n tests/harness-acceptance/adapters/claude.sh` — passed
> - `bash -n tests/harness-acceptance/adapters/opencode.sh` — passed
> - `python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v` — **56 passed, 0 failed**
> - `./tests/run-all.sh` — passed (`All ResearchFlow tests passed.`)
> No real Claude Code, OpenCode, LiteLLM, network, or paid-model invocation was performed during the Task 4 review-closure pass.
> Task 4 is now synthetically review-closed only. There is still no real preflight-only run, no scored acceptance run, and no live acceptance evidence.
> Safe observed tool versions remain:
> - Claude Code: `2.1.214`
> - OpenCode: `1.17.15`
> - Python: `3.9.13`
> Future agents should treat the latest canonical implementation state as repo-root `main @ ab71a30`.
> The next implementation step is Task 5 synthetic preflight/orchestration on top of `main`, not another Task 4 closure pass.
> Do not reopen Task 4 unless new evidence shows a concrete synthetic regression or a spec mismatch.
> This handover supersedes earlier notes that Task 4 still required clean-environment synthetic review closure.
> The latest Task 4 code merge itself is complete, but no push to remote has been performed from this session.
> If another agent resumes this work, they should verify parent/submodule intent before making any parent-repo commits, because the parent still records the old researchflow gitlink.
> Historical branch/worktree references below remain for provenance only where not explicitly updated.
> Current local dirty state while this handover update is still uncommitted: this handover file plus the two untracked local planning docs listed above.
> Once this handover update is committed, the repo-local `main` working tree should return to only those two untracked planning docs.
> Those local docs may be kept, updated, or deleted later by explicit user choice; they are not needed for Task 5 execution.
> The local `reference/` symlinked comparison inputs remain unchanged.
> Nothing in this pass changed router behavior, workflow contracts, versioning, release state, or publish state.
> The final pre-merge whole-branch review found no blocking issues, with only one non-blocking minor note about stale helper parameters in `tests/harness-acceptance/test_adapters.py`.
> That minor note was intentionally left unfixed because it was not required for bounded Task 4 synthetic closure.
> The final merged `main` history relevant to this pass is:
> - `ab71a30` — `fix: fail-close full isolation capability proof`
> - `46791dd` — `fix: remove out-of-scope cerebrum drift`
> - `1b13451` — `fix: close Task 4 synthetic review gaps`
> - `4896875` — `fix: fail-close Task 4 capability normalization`
> - `5ef0c7f` — `fix: lock Task 4 prompt and workspace contract`
> These commits, together with `6a9a451` and `007f882`, represent the final synthetic Task 4 closure state currently in `main`.
> Keep these commit references available for future review-package generation or provenance checks.
> If future work touches Task 5+, do not assume the old preserved `main-preserved` local workspace still exists; it no longer does.
> Recreate any new manual worktree under `.worktrees/<feature>/` only if a new isolated workspace is needed.
> Manual worktree count under `.worktrees/` is currently zero.
> `origin/main` already includes `ab71a30`, so no local-only branch divergence remains inside this repo.
> However, the parent repository still needs an explicit submodule pointer update commit if the user wants `ccmem_paper` to record the new researchflow state.
> That parent-level action was not taken in this session.
> Future agents should mention that distinction explicitly if asked whether everything is fully committed.
> Inside this repo, yes; in the parent repo, no.
> This distinction matters for any later parent-repo PR or handoff.
> End of current-state header.
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
- parent gitlink currently points to `964d14d`, while the repo-root checkout here is now `ab71a30` on `main`;
- the parent currently reports `reference/researchflow` as modified because its recorded gitlink still points to `964d14d`; in the current local checkout it may also appear dirty when this repo-root working tree has uncommitted edits such as this handover update;
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
- HEAD: `ab71a30 fix: fail-close full isolation capability proof`;
- upstream: `origin/main`;
- `main` currently matches `origin/main`.

Use the historical design branch only when you specifically need to inspect the earlier design-only checkout state.

### 2.6 Active implementation workspace

There is no remaining manual `.worktrees/*` implementation checkout under this repo root.

The temporary `.worktrees/task4-review-close/` workspace used for the Task 4 closure pass has already been merged into `main` and removed.

Future implementation should start from repo-root `main @ ab71a30` or a fresh new worktree created from it. Do not assume the previously mentioned `main-preserved` convenience checkout still exists.

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

### 5.5 Tasks 5–7 — not started

- Task 5: preflight, model-alignment hard gate, orchestration, synthetic runner wiring
- Task 6: real capability/preflight-only run
- Task 7: at most 14 scored cases and bounded evidence packaging

No real Claude Code, OpenCode, LiteLLM, network, or paid model invocation has been made by the implementation tasks so far.

## 6. Current test status

Most recent local verification on merged repo-root `main @ ab71a30`:

```bash
bash -n tests/harness-acceptance/adapters/claude.sh
bash -n tests/harness-acceptance/adapters/opencode.sh
python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v
./tests/run-all.sh
```

Result on 2026-07-18:

- Claude adapter syntax check: passed
- OpenCode adapter syntax check: passed
- harness acceptance synthetic suite: **56 passed, 0 failed**
- OpenCode bootstrap smoke test: passed
- Claude metadata/file smoke coverage plus repo-local routing-doc smoke coverage: passed
- all three workflow demo contract tests: passed
- unified result: `All ResearchFlow tests passed.`

Safe tool versions observed without exposing configuration values:

- Claude Code: `2.1.214`
- OpenCode: `1.17.15`
- Python: `3.9.13`

## 7. Exact next step for the next agent

Resume from repo-root `main @ ab71a30`.

The next implementation step is **Task 5 synthetic preflight/orchestration**. Do not reopen Task 4 unless new evidence shows a concrete synthetic regression or a spec mismatch.

Recommended procedure from this cwd:

1. Start from a fresh clean worktree or fresh environment based on `main` rather than reusing stopped harness worktrees.
2. Read the approved design and plan:

   ```text
   docs/superpowers/specs/2026-07-17-live-harness-acceptance-design.md
   docs/superpowers/plans/2026-07-17-live-harness-acceptance.md
   ```

3. Implement Task 5 synthetic preflight/orchestration on top of the now-closed Task 4 synthetic baseline.
4. Rerun at least:

   ```bash
   python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v
   ./tests/run-all.sh
   ```

5. Do not move, delete, prune, or clean any `.claude/worktrees/agent-*` directory without explicit user approval. Do not touch `.omc/` in any worktree.
6. Do not invoke real `claude`, `opencode`, LiteLLM, network services, or models until the plan explicitly reaches the real preflight/run stages.

## 8. Remaining implementation order and stop conditions

Proceed in this order only:

1. Task 5 synthetic preflight/orchestration
2. Task 5 review and full synthetic baseline
3. Task 6 real preflight-only run
4. Task 7 scored run only if all hard gates pass

Hard stops:

- If capability/plugin proof cannot be established, create blocked evidence; do not improvise a load command.
- If both harnesses cannot verify the same OpenAI backing model, generate 14 unattempted rows and stop.
- If the model identity is newly proved but absent from the allowlist, commit the exact mapping and rerun preflight under a new run ID; do not score the old run.
- If redaction finds a leak, do not stage evidence.
- If a successful tool execution occurs during a scored case, classify it as `harness_error`.
- Never retry a scored case in the original run.
- Never exceed 14 scored invocations.
- Do not treat the synthetic Task 4 closure as proof that Tasks 6–7 will pass; it only removes the known synthetic adapter/probe blockers.

## 9. Known limitations and unresolved work

- Claude Code still has no saved real fresh-session routing transcript.
- OpenCode still has no saved external real-session acceptance transcript.
- No backing-model identity has been added to `canonical_models`; it must remain empty until real redacted proof exists.
- No live acceptance result exists; do not claim acceptance, stability, or release readiness.
- Release version remains `0.1.0`.
- No release candidate, version bump, publish, or push is authorized by this work.
- Cross-artifact semantic checks and contract-schema centralization remain separate future work.
- repo-local `agent-a7e704d91a6ea7c24` still carries a historical dirty tracked change and must not be silently discarded.
- Many remaining harness worktrees appear to be session residue with only `.omc/` or other untracked local artifacts; clean them only with explicit per-path review and user approval.
- the parent `ccmem_paper` repository still records the old ResearchFlow submodule pointer (`964d14d`) and needs a separate parent-repo commit if the user wants the parent to capture `ab71a30`.

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
