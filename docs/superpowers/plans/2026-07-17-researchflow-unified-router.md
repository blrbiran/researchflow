# ResearchFlow Unified Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved thin-router behavior in the nested ResearchFlow plugin repo so `using-researchflow` routes research and paper requests onto the existing five-phase contract chain more explicitly and more testably.

**Architecture:** Keep `using-researchflow` as the single public router and tighten its behavior rather than adding new top-level phases or a second orchestration layer. Implement the behavior mostly as skill-text and repo-doc updates, then lock the new invariants with a small repo-local Claude-side routing-doc test that becomes part of the existing smoke path.

**Tech Stack:** Markdown skill/docs, Python 3, Bash, existing ResearchFlow smoke-test scripts

## Global Constraints

- Version 1 should land on `reference/researchflow` as an evolution of the existing `using-researchflow` entrypoint rather than as a new cross-repo meta-plugin.
- Version 1 is limited to research and academic-paper workflows.
- It does not try to unify general engineering, QA, deployment, debugging, product, or design work.
- The only public entrypoint should remain `using-researchflow`.
- The only first-class routing targets should remain the five existing ResearchFlow phases: `literature-discovery`, `paper-structuring`, `paper-drafting`, `paper-review`, and `artifact-packaging`.
- The router should default to direct routing.
- It should ask a clarifying question only when two adjacent phases are both plausible, the current files and stated intent do not resolve the ambiguity, and routing to the wrong phase would waste substantial work.
- That clarification should be exactly one question.
- `docs/workflow-contracts.md` remains the source of truth for the five handoff artifacts, the meaning of phase boundaries, and the default "earliest missing or unstable artifact" routing invariant.
- External libraries may not introduce new top-level phases in V1.
- Keep the plan scoped to implementation work only; do not add speculative features or expert-mode UI.

---

## File Structure

- `reference/researchflow/skills/using-researchflow/SKILL.md` — primary implementation surface for the thin-router rules, backward-routing rule, one-question clarification gate, and subordinate-support visibility policy.
- `reference/researchflow/tests/claude-code/test-routing-docs.py` — new repo-local executable check for the router wording and doc alignment.
- `reference/researchflow/tests/claude-code/run-tests.sh` — Claude-side smoke runner; should call both the existing manifest check and the new routing-doc test.
- `reference/researchflow/README.md` — user-facing explanation of the thin-router behavior and backward-routing expectation.
- `reference/researchflow/CLAUDE.md` — contributor-facing router constraints so future edits do not reintroduce marketplace-style routing.
- `reference/researchflow/docs/README.claude.md` — Claude Code installation/verification notes; should mention the backward-routing acceptance behavior in addition to the basic related-work bootstrap check.
- `reference/researchflow/docs/handover/researchwork-plugin-handover.md` — repo handover; should record the settled thin-router decision and keep recommended next work consistent with the new local acceptance coverage.

### Task 1: Tighten `using-researchflow` and add a focused router-doc test

**Files:**
- Modify: `reference/researchflow/skills/using-researchflow/SKILL.md`
- Create: `reference/researchflow/tests/claude-code/test-routing-docs.py`
- Test: `reference/researchflow/tests/claude-code/test-routing-docs.py`

**Interfaces:**
- Consumes: `reference/researchflow/docs/workflow-contracts.md` contract rule: “Route to the earliest missing or unstable artifact, not merely to the section or file the user mentions.”
- Produces: `RouterDocsTest(root: Path) -> exit 0|1`
- Produces: `ThinRouterInvariantPhrases = ["docs/workflow-contracts.md", "Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.", "External reference libraries may not introduce new top-level phases in V1."]`

- [ ] **Step 1: Write the failing router-doc test**

Create `reference/researchflow/tests/claude-code/test-routing-docs.py` with this exact content:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

root = Path(sys.argv[1])
using = (root / 'skills' / 'using-researchflow' / 'SKILL.md').read_text(encoding='utf-8')

assert 'docs/workflow-contracts.md' in using
assert 'Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.' in using
assert 'External reference libraries may not introduce new top-level phases in V1.' in using
assert 'Ask exactly one clarifying question only when the request could plausibly belong to two adjacent phases' in using

print('ok - using-researchflow encodes the thin-router invariants')
```

- [ ] **Step 2: Run the new test to verify it fails against the current skill text**

Run:

```bash
python3 reference/researchflow/tests/claude-code/test-routing-docs.py reference/researchflow
```

Expected:
- exit code non-zero
- output ends with `AssertionError`

- [ ] **Step 3: Add the thin-router invariants to `using-researchflow`**

Insert this block immediately after the existing `## The rule` paragraph in `reference/researchflow/skills/using-researchflow/SKILL.md`:

```md
## Thin-router invariants

For ResearchFlow V1, `using-researchflow` is a thin router, not a skill marketplace.

- `docs/workflow-contracts.md` remains the source of truth for the five handoff artifacts, the phase boundaries, and the default earliest-missing-or-unstable routing invariant.
- The only public entrypoint remains `using-researchflow`.
- The only first-class routing targets remain `literature-discovery`, `paper-structuring`, `paper-drafting`, `paper-review`, and `artifact-packaging`.
- External reference libraries may not introduce new top-level phases in V1.
- Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.
- Support behavior stays subordinate and mostly invisible unless the user explicitly asks for expert mode or a named support skill.
```

Then replace the current `## Ambiguity handling` section with this exact text:

```md
## Ambiguity handling

Ask exactly one clarifying question only when the request could plausibly belong to two adjacent phases, the available files or stated intent do not resolve the ambiguity, and the wrong routing choice would waste work.

Good clarifications:
- “Do you already have a stable related-work set, or should I start by finding the closest papers?”
- “Is the main problem the section logic, or do you already like the structure and want prose help only?”
- “Are you asking for a general review, or a final submission gate?”

Do not ask questions whose answers can be inferred from the user's files or stated intent.
Do not expose the whole routing graph unless the user explicitly asks for expert mode.
```

- [ ] **Step 4: Run the router-doc test to verify the skill text now passes**

Run:

```bash
python3 reference/researchflow/tests/claude-code/test-routing-docs.py reference/researchflow
```

Expected:
- exit code `0`
- output contains `ok - using-researchflow encodes the thin-router invariants`

- [ ] **Step 5: Commit the skill-surface change**

Run:

```bash
git -C reference/researchflow add \
  skills/using-researchflow/SKILL.md \
  tests/claude-code/test-routing-docs.py

git -C reference/researchflow commit -m "docs: tighten using-researchflow router"
```

### Task 2: Align repo-facing docs and handover to the thin-router contract

**Files:**
- Modify: `reference/researchflow/README.md`
- Modify: `reference/researchflow/CLAUDE.md`
- Modify: `reference/researchflow/docs/README.claude.md`
- Modify: `reference/researchflow/docs/handover/researchwork-plugin-handover.md`
- Modify: `reference/researchflow/tests/claude-code/test-routing-docs.py`
- Test: `reference/researchflow/tests/claude-code/test-routing-docs.py`

**Interfaces:**
- Consumes: `ThinRouterInvariantPhrases`
- Consumes: `RouterDocsTest(root: Path) -> exit 0|1`
- Produces: `RepoLocalRouterDocsAligned = true`

- [ ] **Step 1: Extend the doc test with README / CLAUDE / Claude-doc / handover assertions**

Append these assertions just before the final `print(...)` line in `reference/researchflow/tests/claude-code/test-routing-docs.py`:

```python
readme = (root / 'README.md').read_text(encoding='utf-8')
claude = (root / 'CLAUDE.md').read_text(encoding='utf-8')
claude_doc = (root / 'docs' / 'README.claude.md').read_text(encoding='utf-8')
handover = (root / 'docs' / 'handover' / 'researchwork-plugin-handover.md').read_text(encoding='utf-8')

assert 'thin router' in readme
assert 'Surface intent proposes a phase; artifact stability confirms it or routes earlier.' in readme
assert 'Keep `using-researchflow` as a thin router over the existing five-phase workflow.' in claude
assert 'Do not turn support skills or external references into peer top-level routes.' in claude
assert 'If the user asks to write an introduction without a stable literature-backed gap, the router should still start at `literature-discovery`.' in claude_doc
assert 'If the user asks to export a PDF from a still-unreviewed manuscript, the router should still start at `paper-review`.' in claude_doc
assert 'Router model: thin router;' in handover
assert 'repo-local routing-doc smoke coverage' in handover
```

- [ ] **Step 2: Run the extended test to verify the repo docs are still missing the new wording**

Run:

```bash
python3 reference/researchflow/tests/claude-code/test-routing-docs.py reference/researchflow
```

Expected:
- exit code non-zero
- output ends with `AssertionError`

- [ ] **Step 3: Update the four repo-facing docs with the approved wording**

In `reference/researchflow/README.md`, insert this paragraph immediately after the current first paragraph:

```md
ResearchFlow V1 keeps that entrypoint intentionally thin: direct routing by default, exactly one clarifying question only for high-cost adjacent-phase ambiguity, and no extra top-level phases beyond the existing five-stage workflow. Surface intent proposes a phase; artifact stability confirms it or routes earlier.
```

In `reference/researchflow/CLAUDE.md`, add these bullets under `## Current scope`:

```md
- Keep `using-researchflow` as a thin router over the existing five-phase workflow.
- Default to direct routing; ask one clarifying question only for high-cost adjacent-phase ambiguity.
- Do not turn support skills or external references into peer top-level routes.
```

In `reference/researchflow/docs/README.claude.md`, add these two bullets under `Expected result:`:

```md
- if the user asks to write an introduction without a stable literature-backed gap, the router should still start at `literature-discovery`
- if the user asks to export a PDF from a still-unreviewed manuscript, the router should still start at `paper-review`
```

In `reference/researchflow/docs/handover/researchwork-plugin-handover.md`, add this bullet under `Settled decisions:`:

```md
- Router model: thin router; `using-researchflow` remains the sole public entrypoint, routes onto the existing five-phase contract chain, and asks at most one clarification question for adjacent high-cost ambiguity.
```

Then replace the current unresolved-work bullet:

```md
- Claude Code integration has only metadata/file smoke coverage; no clean-session live install/auto-routing transcript exists yet.
```

with:

```md
- Claude Code integration now has local metadata/file smoke coverage plus repo-local routing-doc smoke coverage, but it still lacks a clean-session live install/auto-routing transcript.
```

- [ ] **Step 4: Run the extended test to verify the repo docs now align**

Run:

```bash
python3 reference/researchflow/tests/claude-code/test-routing-docs.py reference/researchflow
```

Expected:
- exit code `0`
- output contains `ok - using-researchflow encodes the thin-router invariants`

- [ ] **Step 5: Commit the doc-alignment change**

Run:

```bash
git -C reference/researchflow add \
  README.md \
  CLAUDE.md \
  docs/README.claude.md \
  docs/handover/researchwork-plugin-handover.md \
  tests/claude-code/test-routing-docs.py

git -C reference/researchflow commit -m "docs: align researchflow thin-router docs"
```

### Task 3: Wire the new acceptance check into the repo-local smoke path and verify the full suite

**Files:**
- Modify: `reference/researchflow/tests/claude-code/run-tests.sh`
- Test: `reference/researchflow/tests/claude-code/run-tests.sh`
- Test: `reference/researchflow/tests/run-all.sh`

**Interfaces:**
- Consumes: `RouterDocsTest(root: Path) -> exit 0|1`
- Produces: `ClaudeSmokeIncludesRouterDocs = true`

- [ ] **Step 1: Make the Claude smoke runner execute the new router-doc test**

Replace the contents of `reference/researchflow/tests/claude-code/run-tests.sh` with this exact script:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
"$ROOT/tests/claude-code/test-manifests.sh"
python3 "$ROOT/tests/claude-code/test-routing-docs.py" "$ROOT"
```

- [ ] **Step 2: Run the Claude smoke path directly**

Run:

```bash
reference/researchflow/tests/claude-code/run-tests.sh
```

Expected:
- exit code `0`
- output contains both:
  - `ok - claude manifests point at researchflow and support skills/scripts exist`
  - `ok - using-researchflow encodes the thin-router invariants`

- [ ] **Step 3: Run the full repo-local test suite**

Run:

```bash
reference/researchflow/tests/run-all.sh
```

Expected:
- exit code `0`
- output ends with `All ResearchFlow tests passed.`

- [ ] **Step 4: Check the nested repo diff before committing**

Run:

```bash
git -C reference/researchflow diff -- \
  skills/using-researchflow/SKILL.md \
  README.md \
  CLAUDE.md \
  docs/README.claude.md \
  docs/handover/researchwork-plugin-handover.md \
  tests/claude-code/test-routing-docs.py \
  tests/claude-code/run-tests.sh
```

Expected:
- diff only touches the seven files listed above
- no new top-level phases appear anywhere in the diff

- [ ] **Step 5: Commit the acceptance wiring**

Run:

```bash
git -C reference/researchflow add \
  tests/claude-code/run-tests.sh

git -C reference/researchflow commit -m "test: add researchflow router acceptance check"
```

## Self-Review

### Spec coverage

- Section 1 purpose and Section 2 scope are implemented by Task 1 and Task 2 because they keep the work inside `reference/researchflow`, preserve `using-researchflow`, and avoid new top-level phases.
- Sections 4-9 router behavior are implemented by Task 1 because that task rewrites the actual router rules in `skills/using-researchflow/SKILL.md`.
- Section 10 repo-local implementation surfaces are implemented by Task 2 because it updates `README.md`, `CLAUDE.md`, `docs/README.claude.md`, and `docs/handover/researchwork-plugin-handover.md`.
- Section 12 validation and Section 13 success criteria are implemented by Task 3 because that task wires the new acceptance check into `tests/claude-code/run-tests.sh` and re-runs `tests/run-all.sh`.
- No spec requirement is left without a corresponding task.

### Placeholder scan

- Searched this plan manually for `TBD`, `TODO`, `implement later`, `fill in details`, and unresolved “similar to Task N” wording.
- No placeholders remain; every task names exact files, code blocks, commands, and expected outputs.

### Type consistency

- `RouterDocsTest(root: Path) -> exit 0|1` is defined in Task 1 and reused consistently in Task 2 and Task 3.
- `ThinRouterInvariantPhrases` is introduced in Task 1 and only referenced as content expectations later; no conflicting names are used.
- All file paths remain under `reference/researchflow/...` so the plan stays repo-local.

## Execution Handoff

Plan complete and saved to `reference/researchflow/docs/superpowers/plans/2026-07-17-researchflow-unified-router.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
