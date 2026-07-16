# ResearchFlow Workflow Contracts

ResearchFlow uses artifact-driven handoffs between its five primary phases. The goal is not to force bureaucracy; it is to make phase transitions explicit so the agent does not draft around missing evidence or package around unresolved review defects.

## The contract chain

```text
Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet
```

Each artifact is the minimum stable output that allows the next phase to start responsibly.

## 1. Literature Map

**Produced by:** `literature-discovery`

**Consumed by:** `paper-structuring`

### Required fields

- `frozen_question` — the primary research question or paper-facing problem statement
- `retrieval_axes` — the main search dimensions used to explore the space
- `closest_works` — the most relevant papers or systems, each with title/year/relevance note
- `taxonomy_or_clusters` — the field map used to organize the works
- `likely_gap` — the most defensible missing dimension, setting, comparison, or contradiction zone
- `confidence_and_uncertainty` — what the map supports strongly and where retrieval is still thin

### Gate to next phase

A Literature Map is good enough for `paper-structuring` when:
- the closest-work set is stable enough to explain what the paper is *not*
- the gap can be stated without hand-waving
- the main uncertainty is explicit rather than hidden

If those conditions fail, stay in literature work.

## 2. Structure Brief

**Produced by:** `paper-structuring`

**Consumed by:** `paper-drafting`

### Required fields

- `paper_type` — technical / benchmark / system / survey, with rationale
- `thesis_or_goal` — what the paper is actually trying to establish
- `logic_chain` — background -> gap -> goal -> challenges -> modules -> evidence -> contributions
- `section_skeleton` — named sections and each section's job
- `contribution_list` — claims the paper will ask the reader to accept
- `structural_risks` — broken links, missing evidence plans, weak contribution mapping, or unresolved scope issues

### Gate to next phase

A Structure Brief is good enough for `paper-drafting` when:
- the logic chain is coherent end to end
- the section skeleton is stable enough to assign paragraph roles
- the contribution list maps to actual sections and evidence

If the structure still depends on unresolved literature or missing evaluation logic, route backward.

## 3. Draft Packet

**Produced by:** `paper-drafting`

**Consumed by:** `paper-review`

### Required fields

- `target_scope` — which section(s) or manuscript surface were drafted
- `evidence_basis` — what literature, notes, or results the draft is grounded in
- `draft_text_or_path` — the actual prose or a path to the manuscript section
- `unresolved_gaps` — places that still need confirmation, stronger evidence, or missing citations
- `real_vs_planned_status` — which claims are backed by observed results versus planned or expected results

### Gate to next phase

A Draft Packet is good enough for `paper-review` when:
- enough prose exists for the reviewer to evaluate the argument, not just isolated sentences
- the draft's evidence basis is known
- unresolved gaps are surfaced rather than disguised as confident prose

If the prose is still too fragmentary to judge or the evidence basis is unknown, keep drafting.

## 4. Review Packet

**Produced by:** `paper-review`

**Consumed by:** `artifact-packaging` or `submission-readiness`

### Required fields

- `manuscript_summary` — what the paper seems to claim and what evidence it relies on
- `critical_issues` — publication-blocking or chain-breaking defects
- `major_issues` — important weaknesses that should be fixed before submission
- `minor_issues` — polish items
- `revision_order` — the recommended order of fixes
- `recommended_next_phase` — draft again, package artifacts, or run a final submission gate

### Gate to next phase

A Review Packet is good enough for `artifact-packaging` or `submission-readiness` when:
- critical issues are either absent or explicitly accepted as out of scope for the current deliverable
- the revision order is clear enough that the workflow does not thrash

If critical blockers remain, the default route is back to drafting or structuring, not forward to packaging.

## 5. Submission Packet

**Produced by:** `artifact-packaging`

**Consumed by:** a final external submission or internal delivery checkpoint

### Required fields

- `artifact_inventory` — paper, figures, supplement, appendix, README, and other deliverables
- `export_paths` — where the final or latest deliverables live
- `figure_status` — whether the figures are ready, need audit, or still have surface defects
- `supplement_status` — whether appendix / supplement / artifact docs are complete
- `go_no_go` — the final packaging recommendation for delivery or submission
- `remaining_manual_checks` — anything still requiring human confirmation

### Gate to final delivery

A Submission Packet is good enough for final delivery when:
- every referenced artifact exists
- the reader can tell what to open first
- remaining checks are explicit and small enough to be deliberate human decisions rather than hidden workflow debt

## Routing rule for `using-researchflow`

Route to the earliest missing or unstable artifact, not merely to the section or file the user mentions.

Examples:
- “Write the introduction” with no Literature Map -> start at `literature-discovery`
- “Draft the paper” with no Structure Brief -> start at `paper-structuring`
- “Export a PDF” with unresolved Review Packet blockers -> start at `paper-review`
- “Are we ready to submit?” with no Submission Packet -> start at `artifact-packaging` or `submission-readiness`, depending on whether the surface is still incomplete or just needs a final gate

## Design principle

These contracts are lightweight by design. A skill can return them as explicit structured notes, or produce a lighter equivalent in prose, but the next phase should only begin if the information exists in substance.
