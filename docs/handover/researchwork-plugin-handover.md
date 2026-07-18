# ResearchFlow Plugin Handover

> Updated: 2026-07-18
> Expected agent cwd: the ResearchFlow repository root (`reference/researchflow/` from the parent; `.` inside this document)
> Remote: `git@github.com:blrbiran/researchflow.git`
> Design checkout branch: `docs/live-harness-acceptance-design`
> Snapshot baseline before this cwd/topology update: `19b199c` (run `git rev-parse --short HEAD` for the live branch tip)
> Active implementation branch: `main`
> Active implementation worktree from this cwd: `.worktrees/live-harness-acceptance/`
> Active implementation HEAD: `007f882`

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
- parent gitlink currently points to `1878a9d`;
- this design checkout is ahead of that gitlink, so the parent reports the submodule as modified until the gitlink is intentionally updated;
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

Registered worktrees currently live in three groups:

1. harness worktrees under the Git common-dir `.git/modules/reference/researchflow/.claude/worktrees/agent-*`;
2. older repo-local harness worktrees under `.claude/worktrees/agent-*`;
3. the intentional feature worktree under `.worktrees/live-harness-acceptance/`.

Do **not** move existing harness-owned `agent-*` directories with filesystem `mv`. Their paths are registered in Git administrative records and may also be owned by current or previous Claude sessions. If a move is ever required, first preserve dirty work, then use `git worktree move <old> <new>` from this cwd, one clean/unlocked worktree at a time, and verify `git worktree list --porcelain` after each move. No move is needed for the current handoff.

For new manually managed feature worktrees, use the ignored cwd-local `.worktrees/<feature>/` directory. This provides a discoverable cwd-relative location without relocating the standard submodule common-dir or harness-managed worktrees.

Snapshot inventory:

- Git common-dir including worktree metadata: about 9 MB;
- common-dir `.claude/worktrees`: 15 worktrees, about 6 MB;
- repo-local `.claude/worktrees`: 13 worktrees, about 3.7 MB;
- cwd-local `.worktrees`: one feature worktree, about 1 MB.

Do not delete, prune, relocate, or clean these worktrees without explicit user approval. Current notable worktree state:

- repo-local `agent-a7e704d91a6ea7c24` still contains a historical uncommitted `tests/claude-code/run-tests.sh` change already represented by commit `b3adc46`; it remains dirty and must not be silently discarded.
- common-dir `agent-a3d082809313796c3` was the original Task 4 source worktree. Its useful commits are now merged to `main`, but the worktree itself still exists locally with untracked `.omc/` and `tests/harness-acceptance/__pycache__/` because automated deletion was blocked by the harness permission policy in this session.
- repo-local `agent-abee9411bb8fc2bd2` is a stopped review-fix worktree created by an accidental reviewer dispatch. It contains only untracked `.omc/`; the user requested deletion, but automated removal was also blocked by the harness permission policy in this session.

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

### 2.5 Design checkout

The repository-root checkout is the design/handover checkout:

- branch: `docs/live-harness-acceptance-design`;
- snapshot before this cwd/topology update: `19b199c docs: clarify handover commit provenance`;
- upstream: `origin/docs/live-harness-acceptance-design`;
- run `git status --short --branch` and `git rev-parse --short HEAD` for live state;
- `.gitignore` covers OpenWolf/session artifacts, Python caches, worktrees, and local `reference/` links.

### 2.6 Active implementation worktree

Current preserved implementation workspace:

```text
.worktrees/live-harness-acceptance/
```

Current state:

- branch: `main`;
- HEAD: `007f882 fix: harden native harness capability probes`;
- `main` in this preserved worktree is ahead of `origin/main` by the merged live-harness acceptance stack and has not been pushed;
- tracked implementation tree is clean;
- remaining untracked local artifacts are `.omc/` session state and `tests/harness-acceptance/__pycache__/`; leave both untouched unless the user explicitly requests cleanup;
- `.superpowers/` is intentionally ignored so SDD briefs, reports, review packages, and the progress ledger remain local.

Do not implement in the design checkout. Future implementation should start from `main` at `007f882`, preferably in a fresh clean worktree/environment rather than reusing stopped agent worktrees.

## 3. Completed thin-router delivery

The thin-router work is complete and already part of the design branch ancestry.

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

The approved design and implementation plan are committed on the design branch:

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

SDD progress ledger:

```text
.worktrees/live-harness-acceptance/.superpowers/sdd/progress.md
```

Current ledger before the Task 4 merge was:

```text
Task 1: complete (commits 1878a9d..cbce609, review clean)
Task 2: complete (commits cbce609..2173bd4, review clean)
Task 3: complete (commits 2173bd4..4dc9ff9, review clean)
```

Task 4 was then developed on a separate branch/worktree and later merged to `main` without a final clean-environment review closeout.

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

Implementation commits on active branch:

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

### 5.4 Task 4 — capability probes and native adapters — merged to `main`, but still requires a clean-environment review pass

Task 4 implementation commits are now part of `main` at `007f882`:

- `6a9a451` — `test: add native harness capability adapters`
- `007f882` — `fix: harden native harness capability probes`

Delivered files now committed on `main` include:

- `tests/harness-acceptance/capabilities.py`
- `tests/harness-acceptance/adapters/claude.sh`
- `tests/harness-acceptance/adapters/opencode.sh`
- `tests/harness-acceptance/test_capabilities.py`
- `tests/harness-acceptance/test_adapters.py`
- adapter/capability fixtures under `tests/harness-acceptance/fixtures/adapters/**`
- capability fixtures under `tests/harness-acceptance/fixtures/capabilities/**`

What is verified:

- Task 4 synthetic unit coverage is green on the merged `main` worktree: **49 passed, 0 failed** across the full `tests/harness-acceptance/test_*.py` suite.
- `./tests/run-all.sh` also passes on the preserved `.worktrees/live-harness-acceptance/` worktree after merging Task 4 into `main`.
- No real Claude Code, OpenCode, LiteLLM, network, or paid-model invocation was performed during Task 4 implementation.

Important caveat for the next agent:

- During task-scoped review, follow-up review findings were identified around real-environment confidence: scored-suffix composition, native JSON event-shape normalization, Claude fresh-workspace isolation, evidence-derived capability booleans, and separation between production config and test-only fixture wiring.
- Those findings were dispatched into a second fix loop, but that background agent was later stopped by the user before a reviewed follow-up commit landed.
- Therefore, treat Task 4 as **merged but not conclusively review-closed for real-environment acceptance confidence**. Do not revert it blindly; instead, continue from `main` in a fresh clean environment and re-review/fix Task 4 before starting Task 5.

Historical worktree note:

- the original Task 4 source worktree was `branch: task4-live-harness-adapters-a3d082809313796c3`, `worktree: .git/modules/reference/researchflow/.claude/worktrees/agent-a3d082809313796c3`, `base: 4dc9ff9`;
- its useful commits are now merged to `main`;
- local cleanup of that worktree was requested, but automated deletion in this session was blocked by the harness permission policy.

Recommended continuation: start from `main` at `007f882` in a fresh clean worktree, rerun Task 4 review against real adapter contracts, land any remaining Task 4 fixes on a new branch, then proceed to Task 5.

### 5.5 Tasks 5–7 — not started

- Task 5: preflight, model-alignment hard gate, orchestration, synthetic runner wiring
- Task 6: real capability/preflight-only run
- Task 7: at most 14 scored cases and bounded evidence packaging

No real Claude Code, OpenCode, LiteLLM, network, or paid model invocation has been made by the implementation tasks so far.

## 6. Current test status

Verified in the preserved `.worktrees/live-harness-acceptance/` worktree on 2026-07-18 after merging Task 4 into `main` at `007f882`:

```bash
cd .worktrees/live-harness-acceptance
python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v
./tests/run-all.sh
```

Results:

- harness acceptance synthetic tests: **49 passed**
- OpenCode bootstrap smoke test: passed
- Claude metadata/file smoke coverage plus repo-local routing-doc smoke coverage: passed
- all three workflow demo contract tests: passed
- unified result: `All ResearchFlow tests passed.`

Safe tool versions observed without exposing configuration values:

- Claude Code: `2.1.214`
- OpenCode: `1.17.15`
- Python: `3.9.13`

## 7. Exact next step for the next agent

Resume from **Task 4 review closure on top of `main` at `007f882`**; do not start Task 5 yet.

Recommended procedure from this cwd:

1. Start from a fresh clean worktree/environment based on `main` rather than reusing stopped agent worktrees.
2. Read the approved design and plan:

   ```text
   docs/superpowers/specs/2026-07-17-live-harness-acceptance-design.md
   docs/superpowers/plans/2026-07-17-live-harness-acceptance.md
   ```

3. Re-review the merged Task 4 implementation against the real adapter contract, with special attention to:
   - scored-prompt suffix composition;
   - native JSON event-shape normalization for Claude and OpenCode;
   - Claude fresh-workspace isolation during case execution;
   - evidence-derived capability flags instead of optimistic assumptions;
   - separation between production config and test-only fixture wiring.

4. Land any remaining Task 4 fixes on a new branch from `main`, rerun:

   ```bash
   python3 -m unittest discover -s tests/harness-acceptance -p 'test_*.py' -v
   ./tests/run-all.sh
   ```

5. Only after Task 4 is review-closed in the fresh environment should work continue to Task 5 synthetic preflight/orchestration.

6. Do not move, delete, prune, or clean any `.claude/worktrees/agent-*` directory without explicit user approval. Do not touch `.omc/` in any worktree.

7. Do not invoke real `claude`, `opencode`, LiteLLM, network services, or models until the plan explicitly reaches the real preflight/run stages.

8. If local cleanup of the stopped Task 4 source/review worktrees is still desired, it may require a manual user-run `git worktree remove` outside the current harness permission policy.

## 8. Remaining implementation order and stop conditions

Proceed in this order only:

1. Task 4 review closure and any remaining synthetic fixes on top of `main`
2. Task 5 synthetic preflight/orchestration
3. Task 5 review and full synthetic baseline
4. Task 6 real preflight-only run
5. Task 7 scored run only if all hard gates pass

Hard stops:

- If capability/plugin proof cannot be established, create blocked evidence; do not improvise a load command.
- If both harnesses cannot verify the same OpenAI backing model, generate 14 unattempted rows and stop.
- If the model identity is newly proved but absent from the allowlist, commit the exact mapping and rerun preflight under a new run ID; do not score the old run.
- If redaction finds a leak, do not stage evidence.
- If a successful tool execution occurs during a scored case, classify it as `harness_error`.
- Never retry a scored case in the original run.
- Never exceed 14 scored invocations.
- Do not treat the merged Task 4 commits as final proof of real-environment correctness without the fresh-environment review pass above.

## 9. Known limitations and unresolved work

- Claude Code still has no saved real fresh-session routing transcript.
- OpenCode still has no saved external real-session acceptance transcript.
- Task 4 is merged to `main`, but follow-up review findings around real-environment confidence remain unresolved until a clean-environment review/fix pass is completed.
- No backing-model identity has been added to `canonical_models`; it must remain empty until real redacted proof exists.
- No live acceptance result exists; do not claim acceptance, stability, or release readiness.
- Release version remains `0.1.0`.
- No release candidate, version bump, publish, or push is authorized by this work.
- Cross-artifact semantic checks and contract-schema centralization remain separate future work.
- Automated deletion of the stopped worktrees requested by the user was blocked by the harness permission policy in this session; the preserved `.worktrees/live-harness-acceptance/` worktree remains the safe local base.
- repo-local `agent-a7e704d91a6ea7c24` still carries a historical dirty `tests/claude-code/run-tests.sh` change and must not be silently discarded.

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
- When resuming after cleanup, prefer a new branch from `main` over reviving stopped agent worktrees whose deletion was interrupted.


## 9. Known limitations and unresolved work

- Claude Code still has no saved real fresh-session routing transcript.
- OpenCode still has no saved external real-session acceptance transcript.
- Capability probes and native adapters are not committed or reviewed yet; an uncommitted Task 4 draft exists in common-dir worktree `agent-a3d082809313796c3`.
- No backing-model identity has been added to `canonical_models`; it must remain empty until real redacted proof exists.
- No live acceptance result exists; do not claim acceptance, stability, or release readiness.
- Release version remains `0.1.0`.
- No release candidate, version bump, publish, or push is authorized by this work.
- Cross-artifact semantic checks and contract-schema centralization remain separate future work.

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
