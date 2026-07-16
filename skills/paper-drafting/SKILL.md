---
name: paper-drafting
description: Draft paper prose from the user's materials, literature map, and paper structure. Use for section drafting, manuscript rewriting, and full-paper first drafts.
version: 0.2.0
metadata:
  tags: [Research, Paper, Writing, Drafting]
---

# Paper Drafting

Use this skill when the structure is ready and the user wants prose.

## When to use

- Draft a section.
- Turn notes into paper text.
- Rewrite a section for coherence.
- Produce a first full manuscript draft.

## When not to use

- The literature map is still missing or unstable. Use `literature-discovery` first.
- The contribution framing or section logic is not settled. Use `paper-structuring` first.
- The user wants critique instead of drafting. Use `paper-review`.

## Hard rules

- Do not invent citations.
- Do not invent experimental results.
- Do not invent concrete scenarios, mechanisms, magnitudes, procedures, or identifiers.
- Do not strengthen claims beyond the available evidence.
- Separate observed results from planned or expected results.
- Keep internal planning out of the final prose.

## Capability check

Decide whether retrieval is available for citation support. If not, disclose that limitation and stay conservative: cite only what the user supplied or what you can verify through the available environment.

## Workflow

### Step 1: Scope the writing task

Settle:
- target section or full draft
- section role
- paradigm if relevant
- Draft mode versus Final mode

If the section role is unclear, clarify it before drafting.

Section-specific discipline:
- **Introduction** — motivate the problem, position prior work, and state the paper's actual thesis without smuggling in unearned results
- **Methods / System** — provide enough detail for another researcher to understand or reproduce the approach; avoid sales language
- **Results / Evaluation** — report observations first, with comparisons calibrated to what the evidence really shows
- **Discussion / Limitations** — interpret results, connect to prior work, and admit limits without pretending the paper proved more than it did

### Step 2: Inventory the evidence

Gather the minimum evidence base:
- paper structure
- literature shortlist
- experiment notes or claims
- figures / tables / results if relevant

A sentence with no evidence plan behind it should not be drafted as fact.

### Step 3: Build a compact blueprint

Before prose, decide for each paragraph:
- what the paragraph should make the reader believe
- which evidence supports it
- what the paragraph's role is

For introductions, motivate and position.
For methods, enable reproduction.
For results, state observations without over-interpreting.
For discussion, interpret, compare, and admit limits.

### Step 4: Draft

Write section-appropriate prose while enforcing:
- every factual claim traceable
- no placeholder rhetoric
- no unsupported comparison language
- no hidden logical jump masked by style

### Step 5: Self-review

Check:
- claim-evidence alignment
- section-appropriate tone
- no fabrication of citations or specifics
- no mixing of real and expected results
- no internal scaffolding leaked into the output

### Step 6: Deliver

Return clean prose plus only the shortest necessary note on unresolved gaps, if any.

## Output

Return:
- the drafted prose
- optional short note on gaps that require user confirmation
