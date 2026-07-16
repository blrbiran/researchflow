---
name: paper-structuring
description: Build the logic chain and section skeleton for a paper before drafting. Use for paper type selection, contribution framing, outline construction, and section-level planning.
version: 0.2.0
metadata:
  tags: [Research, Paper, Outline, Contributions]
---

# Paper Structuring

Use this skill to turn a literature-backed idea into a paper skeleton.

## When to use

- The user needs an outline.
- The user is unsure how to frame contributions.
- The paper type is not yet clear.
- The draft feels structurally incoherent.
- The user has literature and results notes, but no stable paper story.

## When not to use

- The related-work set is still unstable. Use `literature-discovery` first.
- The structure is settled and the user wants prose. Use `paper-drafting`.
- The user wants reviewer-style critique of a full draft. Use `paper-review`.

## Inputs this skill expects

At minimum, try to gather:
- the paper's object or system
- the main gap or limitation in prior work
- the claimed thesis / goal
- the expected evidence or evaluation plan

If these are too vague to support a logic chain, say so explicitly instead of fabricating a clean outline.

## Core tasks

### Step 1: Classify the paper type

Choose the best fit:
- technical / method paper
- benchmark / evaluation paper
- system / artifact paper
- survey / synthesis paper

Explain the choice briefly. The paper type controls what the introduction must emphasize and what evidence the later sections owe.

Type-specific emphasis:
- **technical / method paper** — the key idea and challenge-to-module chain must carry the narrative
- **benchmark / evaluation paper** — the evaluation gap, construction logic, and diagnostic framework are load-bearing rather than a side chapter
- **system / artifact paper** — scope boundary, architecture choices, and evidence of real utility or reproducibility matter more than algorithmic novelty theater
- **survey / synthesis paper** — taxonomy quality, cross-branch comparison, and gap extraction are the core contribution rather than a new mechanism

### Step 2: Build the logic chain

Fill the skeleton in this order:
1. research background
2. limitations or gap in prior work
3. goal / thesis / key idea
4. challenges or hard constraints
5. method / system / benchmark modules
6. evaluation or evidence plan
7. contributions

The purpose is not to make a pretty outline. The purpose is to make every later section answer a real logical obligation.

### Step 3: Map sections

Produce a section skeleton such as:
- Introduction
- Related Work
- Method / System / Benchmark Design
- Experiments / Evaluation
- Discussion / Limitations
- Conclusion

For each section, note its job in one sentence.

### Step 4: Run integrity checks

Before finalizing, check these chains:
- gap → goal
- goal → challenges
- challenges → method modules
- method modules → evidence plan
- contributions → named sections

If a link fails, flag it as structural risk rather than smoothing over it.

### Step 5: Flag missing inputs

Common blockers:
- no real gap
- no evidence for novelty
- no evaluation plan
- no motivating example or deployment case
- contributions that are really tasks, not claims
- sections that exist only because papers usually have them

## Output

Return:
- paper type with rationale
- contribution list
- logic chain
- section skeleton with one-line role per section
- unresolved structural risks
- recommended next step for drafting or more literature work

## Handoff artifact: Structure Brief

When this skill is used inside the full workflow, its output should be capturable as a **Structure Brief** containing:
- paper type
- thesis or goal
- logic chain
- section skeleton
- contribution list
- structural risks

`paper-drafting` should not begin until the section skeleton and contribution-to-evidence mapping are stable enough to support paragraph-level writing.
