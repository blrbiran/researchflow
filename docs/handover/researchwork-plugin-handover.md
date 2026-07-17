# ResearchFlow Plugin Handover

> Updated: 2026-07-17  
> Plugin repository: `reference/researchflow/`  
> Remote: `git@github.com:blrbiran/researchflow.git`  
> Branch: `main`

## 1. Purpose and settled decisions

ResearchFlow is a standalone plugin for research and academic-paper workflows. It deliberately exposes a small phase-oriented surface instead of shipping every overlapping reference skill as a peer entry.

Settled decisions:

- Plugin and repo name: `researchflow`.
- Bootstrap / router skill name: `using-researchflow`.
- Initial first-class harnesses: Claude Code and OpenCode.
- Core workflow is artifact-driven and routes to the earliest missing or unstable handoff.
- The plugin consolidates ideas from the reference skill libraries; it does not depend on those repositories at runtime.
- Support skills remain subordinate to one primary phase per turn.
- Router model: thin router; `using-researchflow` remains the sole public entrypoint, routes onto the existing five-phase contract chain, and asks at most one clarification question for adjacent high-cost ambiguity.

## 2. Current verified repository state

At handover time:

- `reference/researchflow/` is a nested standalone git repository, not a parent-repo submodule.
- Local branch: `main`.
- HEAD: `e593522 Add a survey-oriented ResearchFlow demo.`
- Upstream state: local `main` is **1 commit ahead** of `origin/main` (`0 behind / 1 ahead`).
- Nested working tree is clean.
- The latest commit has **not been pushed** in this session.
- All plugin manifests currently report version `0.1.0`:
  - `package.json`
  - `.claude-plugin/plugin.json`
  - `.claude-plugin/marketplace.json`
  - `.agents/plugins/marketplace.json`

Important parent-repo state:

- Parent repo sees `reference/researchflow/` as an untracked nested repo.
- Parent repo also contains unrelated modified/untracked work. Do not stage or commit it while working on ResearchFlow.
- Use `git -C reference/researchflow ...` for ResearchFlow git operations.

## 3. Plugin organization

### Claude Code surface

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `docs/README.claude.md`

The Claude test currently validates metadata and required files. It does not perform a live Claude Code plugin installation.

### OpenCode surface

- `package.json` points `main` to `.opencode/plugins/researchflow.js`.
- `.opencode/plugins/researchflow.js`:
  - registers the repo's `skills/` directory;
  - reads and injects `using-researchflow` into the first user message;
  - supplies OpenCode tool mappings;
  - caches bootstrap content for the session.
- `.opencode/INSTALL.md` documents local and git-backed setup.

### Main skills

- `skills/using-researchflow/SKILL.md`
- `skills/literature-discovery/SKILL.md`
- `skills/paper-structuring/SKILL.md`
- `skills/paper-drafting/SKILL.md`
- `skills/paper-review/SKILL.md`
- `skills/artifact-packaging/SKILL.md`

### Support skills

- `skills/arxiv/SKILL.md`
- `skills/arxiv-pdf-download/SKILL.md`
- `skills/figure-support/SKILL.md`
- `skills/submission-readiness/SKILL.md`

Bundled helper scripts:

- `skills/arxiv/scripts/search_arxiv.py`
- `skills/arxiv-pdf-download/scripts/download_arxiv_refs.py`
- `skills/arxiv-pdf-download/scripts/organize_pdf_titles.py`

## 4. Workflow and handoff contracts

Canonical definition: `docs/workflow-contracts.md`.

```text
Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet
```

### Literature Map

Produced by `literature-discovery`; consumed by `paper-structuring`.

Required fields:

- `frozen_question`
- `retrieval_axes`
- `closest_works`
- `taxonomy_or_clusters`
- `likely_gap`
- `confidence_and_uncertainty`

### Structure Brief

Produced by `paper-structuring`; consumed by `paper-drafting`.

Required fields:

- `paper_type`
- `thesis_or_goal`
- `logic_chain`
- `section_skeleton`
- `contribution_list`
- `structural_risks`

### Draft Packet

Produced by `paper-drafting`; consumed by `paper-review`.

Required fields:

- `target_scope`
- `evidence_basis`
- `draft_text_or_path`
- `unresolved_gaps`
- `real_vs_planned_status`

### Review Packet

Produced by `paper-review`; consumed by `artifact-packaging` or `submission-readiness`.

Required fields:

- `manuscript_summary`
- `critical_issues`
- `major_issues`
- `minor_issues`
- `revision_order`
- `recommended_next_phase`

### Submission Packet

Produced by `artifact-packaging`; consumed by final delivery/submission.

Required fields:

- `artifact_inventory`
- `export_paths`
- `figure_status`
- `supplement_status`
- `go_no_go`
- `remaining_manual_checks`

Routing invariant: `using-researchflow` should repair or produce the earliest missing/unstable artifact instead of jumping to the user's most downstream requested action.

## 5. Demo coverage

Three end-to-end demos exercise different paper shapes:

1. `docs/demos/agent-memory-e2e/`
   - technical / system-paper flavored;
   - topic: scoped experience reuse for coding-agent memory.
2. `docs/demos/benchmark-ambiguity-e2e/`
   - benchmark / evaluation-paper flavored;
   - topic: ambiguity handling in text-to-visualization systems.
3. `docs/demos/llm-judge-survey-e2e/`
   - survey / synthesis-paper flavored;
   - topic: reliability and validity in LLM-as-a-judge evaluation.

Each demo contains:

- `01-literature-map.md`
- `02-structure-brief.md`
- `03-draft-packet.md`
- `04-review-packet.md`
- `05-submission-packet.md`
- `README.md`

Demo literature is explicitly illustrative, not a verified publication-ready corpus.

## 6. Tests and current result

Unified entrypoint:

```bash
cd reference/researchflow
./tests/run-all.sh
```

Or from the parent repo:

```bash
reference/researchflow/tests/run-all.sh
```

The unified runner executes:

1. OpenCode bootstrap smoke test;
2. Claude manifest/support-file smoke test;
3. agent-memory demo contract test;
4. benchmark-ambiguity demo contract test;
5. LLM-judge survey demo contract test.

Verified on 2026-07-17: **all tests pass**.

The demo tests validate:

- all five artifact files exist;
- every required workflow-contract heading exists;
- every required section body is non-empty.

## 7. Documentation map

- `README.md` — public overview, install pointers, tests, and demos.
- `CLAUDE.md` — contributor constraints and first-class skill list.
- `docs/README.claude.md` — current Claude Code install/development notes.
- `.opencode/INSTALL.md` — OpenCode install guide.
- `docs/development.md` — edit loop, nested repo warning, and test commands.
- `docs/workflow-contracts.md` — canonical handoff contract definitions.
- `docs/release/versioning.md` — SemVer guidance and version sync checklist.
- `docs/release/marketplace.md` — development-marketplace status and future publish notes.

## 8. Commit history for this implementation

Most recent first:

- `e593522` — survey/synthesis demo.
- `1614a87` — benchmark/evaluation demo.
- `aa75e01` — unified test entrypoint.
- `21559d2` — stricter required-field/non-empty demo checks.
- `85d61f7` — first system-paper demo.
- `e48ab6b` — phase handoff contracts.
- `d8a1297` — installation and release docs.
- `78310d1` — support skills and routing.
- `bccb381` — stronger core phase skills.
- `d5ec976` — initial Claude Code/OpenCode plugin skeleton.

## 9. Known limitations and unresolved work

- Claude Code integration now has local metadata/file smoke coverage plus repo-local routing-doc smoke coverage, but it still lacks a clean-session live install/auto-routing transcript.
- OpenCode bridge has an in-process smoke test, not a full external OpenCode session test.
- Demo tests validate schema presence/non-empty sections, not semantic quality or cross-artifact consistency.
- Required-field definitions are duplicated between the contract doc and demo test scripts; schema drift is possible.
- The three demo test scripts duplicate the same validation logic.
- Release version remains `0.1.0`; there is no automated manifest-version synchronizer or release script.
- Local `main` is ahead of remote by one commit and still needs an explicit push if desired.
- `reference/researchflow/` is not registered in the parent repo's `.gitmodules`; decide later whether it should remain an ignored/reference checkout, become a real submodule, or live entirely independently.
- The target handover filename requested by the user is `researchwork-plugin-handover.md`; the plugin itself is consistently named `researchflow`.

## 10. Recommended next work

Recommended order:

1. **Centralize contract schemas**
   - define the five required-field lists in one machine-readable file;
   - make all demo tests consume it;
   - remove duplicated validators.
2. **Add cross-artifact semantic checks**
   - Submission Packet inventory references existing files;
   - Review Packet next phase is consistent with critical blockers;
   - Draft Packet references the prior Literature Map and Structure Brief;
   - `paper_type` differs meaningfully across the three demos.
3. **Run real harness acceptance tests**
   - Claude Code fresh session should auto-route a related-work prompt to `literature-discovery`;
   - OpenCode should load the plugin from documented install configuration and show the same behavior.
4. **Prepare a release candidate**
   - decide whether accumulated capabilities warrant `0.2.0`;
   - sync all manifest versions;
   - add a release checklist/script;
   - push only with explicit user approval.
5. **Decide parent-repo integration**
   - keep as standalone nested checkout, or add as an intentional submodule.

## 11. Safety and workflow reminders

- Do not commit unrelated parent-repo changes.
- Do not push without explicit user approval.
- Keep demo literature claims marked as illustrative unless independently retrieved and verified.
- When adding a new phase or public skill, update:
  - `using-researchflow` routing;
  - `CLAUDE.md` first-class skill list;
  - README;
  - Claude smoke test;
  - workflow contracts if the handoff shape changes;
  - unified test runner and at least one demo where relevant.
