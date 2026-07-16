---
name: artifact-packaging
description: Package the final paper artifacts: exportable drafts, supplementary notes, artifact README, figure/table checklist, and reproducibility-facing companion docs.
version: 0.2.0
metadata:
  tags: [Research, Artifact, Packaging, PDF]
---

# Artifact Packaging

Use this skill after drafting and review are largely complete.

## When to use

- The user wants a PDF export.
- The user wants supplementary material packaged.
- The user wants an artifact README or reproducibility guide.
- The user wants a final submission packet checklist.
- The paper is structurally stable and needs a clean export-and-deliver pass.

## When not to use

- The manuscript still has major structural or evidence issues. Use `paper-review` first.
- The user still needs prose written or rewritten. Use `paper-drafting` first.
- The figure story is still unsettled. Resolve that before packaging rather than freezing weak figures into a final artifact set.

## Packaging targets

Typical deliverables include:
- main paper draft
- PDF export
- figures and tables
- supplementary appendix
- artifact or repo README
- reproducibility notes
- submission checklist or delivery note

Not every project needs all of them, but the skill should make the missing pieces explicit.

## Workflow

### Step 1: Inventory the artifact set

List what exists now:
- paper draft source
- export target format
- figures and tables
- supplementary appendix
- artifact or repo documentation
- any venue- or workflow-specific checklist

If the artifact surface is ambiguous, name the uncertainty instead of assuming a finished packet exists.

### Step 2: Check for packaging gaps

Look for:
- missing figure captions
- no README
- no reproducibility note
- inconsistent filenames or output paths
- missing appendix or supplement the paper text depends on
- artifact references in the paper that do not exist on disk yet

### Step 3: Decide the final-mile tools

Use the lightest tool that closes the packaging gap:
- PDF export path when the manuscript is ready for document rendering
- documentation generation path for README / reproducibility / companion docs
- figure audit or figure-design follow-up if the visual assets are not submission-ready

The point is to finish the delivery surface, not to reopen the research argument unless packaging reveals a real blocker.

### Step 4: Produce or update packaging artifacts

Typical actions:
- export a clean PDF
- assemble or update supplementary notes
- write or tighten artifact-facing documentation
- normalize file naming and output locations
- build a compact checklist of what a reader, reviewer, or artifact evaluator should open first

### Step 5: Final packaging review

Before calling the packet ready, verify:
- every referenced artifact exists
- filenames and output paths are consistent
- figures and tables have self-contained enough labels or captions
- the README or delivery note tells the next reader what to open and in what order

## Output

Return:
- packaged artifact list
- missing items
- main risks or manual confirmations still needed
- recommended final export or delivery step
