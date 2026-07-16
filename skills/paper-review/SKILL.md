---
name: paper-review
description: Review a paper draft for logic, claims, evidence support, citation discipline, and submission readiness. Use for critique, revision planning, and pre-submission checks.
version: 0.2.0
metadata:
  tags: [Research, Review, Revision, Submission]
---

# Paper Review

Use this skill to critique a manuscript and produce a revision path.

## When to use

- The user asks for a paper review.
- The user wants revision priorities.
- The user wants a submission-readiness check.
- The user wants claims or citations sanity-checked.
- The user wants to know whether the main problem is structure, evidence, or wording.

## Severity taxonomy

- **CRITICAL** — publication-blocking defect or broken logic chain
- **MAJOR** — high-value issue that materially weakens the paper
- **MINOR** — polish or local improvement that does not change the main argument

## Review dimensions

1. macro logic
2. claim-evidence alignment
3. literature coverage and positioning
4. writing clarity and section discipline
5. figures / tables / artifact readiness if present

## Workflow

### Step 0: Set the review frame

If known, identify:
- paradigm / paper type
- target venue or audience
- whether this is early internal review or near-submission review

Use that frame to judge severity. A missing benchmark detail in a system paper and in a survey paper are not the same problem.

### Step 1: Read for the main argument

Before line-editing, state what the paper is claiming and what evidence seems intended to support it.

If you cannot explain the paper's main claim in a few sentences, the paper has a macro-logic problem.

### Step 2: Check macro logic

Review:
- introduction chain intact
- contributions map to sections
- experiments or evidence actually test the claims
- related work covers the necessary prior art
- conclusions do not outrun the body

A broken chain here is CRITICAL.

### Step 3: Check claim-evidence alignment

Look for:
- unsupported novelty claims
- over-strong verbs relative to evidence
- missing attribution or ablation where attribution matters
- results interpreted beyond what the evaluation supports
- citations attached to claims they may not actually support

### Step 4: Check literature coverage and positioning

Where retrieval is available, use it only for metadata-level review:
- are the closest works named?
- is a canonical baseline or recent survey obviously missing?
- does the paper's positioning survive a quick nearest-neighbor check?

Do not quote technical details from search snippets as if they were verified from full reading.

### Step 5: Check writing and presentation

Review for:
- paragraph role clarity
- transitions and redundancy
- section-appropriate tone
- figure / table readiness if present
- obvious grammar or formatting concerns only after the substantive issues are sorted

### Step 5.5: Add near-submission checks when relevant

If the draft is close to submission, also check:
- abstract actually states problem, method, and result
- captions are self-contained enough for figures and tables to stand on their own
- obvious AI-tone overclaiming or inflated novelty language
- formatting or citation-surface issues that would create avoidable reviewer irritation

These are usually MAJOR or MINOR unless they hide a deeper logic problem.

### Step 6: Build the revision order

Do not dump an unordered issue list.

Return:
1. the blockers that must be fixed first
2. the issues that strengthen the paper next
3. the polish items that can wait

## Output

Return:
- critical issues
- major issues
- minor issues
- a recommended revision order
- the recommended next phase

## Handoff artifact: Review Packet

When this skill is used inside the full workflow, its output should be capturable as a **Review Packet** containing:
- manuscript summary
- critical / major / minor issues
- revision order
- unresolved blockers
- recommended next phase

`artifact-packaging` or `submission-readiness` should not begin until the workflow knows whether any CRITICAL blockers still remain.
