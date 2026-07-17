---
name: using-researchflow
description: Bootstrap and routing layer for the ResearchFlow plugin. Use this as the default entrypoint for research and paper-writing sessions so the agent picks the right phase skill instead of improvising.
version: 0.3.0
metadata:
  tags: [Research, Workflow, Routing, Papers]
  related_skills: [literature-discovery, paper-structuring, paper-drafting, paper-review, artifact-packaging, arxiv, arxiv-pdf-download, figure-support, submission-readiness]
---

# Using ResearchFlow

ResearchFlow is the default workflow layer for research and paper-writing work.

## The rule

Before doing substantive work, identify the user's current phase and route to the matching phase skill. Do not expose a long menu of overlapping specialist skills unless the user explicitly asks for expert mode.

## Thin-router invariants

For ResearchFlow V1, `using-researchflow` is a thin router, not a skill marketplace.

- `docs/workflow-contracts.md` remains the source of truth for the five handoff artifacts, the phase boundaries, and the default earliest-missing-or-unstable routing invariant.
- The only public entrypoint remains `using-researchflow`.
- The only first-class routing targets remain `literature-discovery`, `paper-structuring`, `paper-drafting`, `paper-review`, and `artifact-packaging`.
- External reference libraries may not introduce new top-level phases in V1.
- Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.
- Support behavior stays subordinate and mostly invisible unless the user explicitly asks for expert mode or a named support skill.

## The phase model

ResearchFlow uses five primary phases and four support skills.

Each primary phase should leave behind a named handoff artifact:
- `literature-discovery` -> **Literature Map**
- `paper-structuring` -> **Structure Brief**
- `paper-drafting` -> **Draft Packet**
- `paper-review` -> **Review Packet**
- `artifact-packaging` -> **Submission Packet**

1. **literature-discovery**
   - discover papers
   - build a related-work map
   - identify the closest work and the likely gap
2. **paper-structuring**
   - choose the paper type
   - build the logic chain
   - define the section skeleton and contribution framing
3. **paper-drafting**
   - draft or rewrite prose for one section or the whole paper
4. **paper-review**
   - critique the manuscript
   - check claim-evidence alignment
   - produce a revision order
5. **artifact-packaging**
   - export the paper
   - package supplementary and artifact-facing materials

Support skills:
- **arxiv** — lightweight arXiv discovery and metadata lookup
- **arxiv-pdf-download** — save local PDFs and organize them on disk
- **figure-support** — design or audit figures, captions, and visual storytelling
- **submission-readiness** — final gate for venue-facing submission quality

## Workflow contracts

ResearchFlow uses an artifact-driven contract chain:

```text
Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet
```

See `docs/workflow-contracts.md` for the full contract definition. The routing layer should prefer repairing or producing the missing upstream artifact instead of continuing downstream with an unstable handoff.

## Routing algorithm

### Step 1: Detect the earliest blocked phase

When a request spans multiple phases, route to the earliest phase that is still missing a stable output.

Examples:
- If the user asks for an Introduction but does not yet have a clear literature-backed gap, start with `literature-discovery`.
- If the user asks for a full draft but the contributions and section logic are still fuzzy, start with `paper-structuring`.
- If the user asks to export a PDF from a still-unreviewed manuscript, start with `paper-review` unless they explicitly want a rough internal PDF.

### Step 2: Use one primary phase skill

Pick one primary phase skill per turn. Use support skills only when they are clearly subordinate to the primary phase.

Examples:
- `literature-discovery` may use `arxiv` for quick expansion.
- `artifact-packaging` may package locally downloaded PDFs, but local paper acquisition itself still routes to `arxiv-pdf-download`.
- `artifact-packaging` may use `figure-support` if a packaging pass reveals weak captions or figure quality.
- `paper-review` may escalate to `submission-readiness` when the user wants a final go / no-go gate rather than another broad critique.

### Step 3: Explain the routing briefly

Tell the user in one or two sentences which phase they are in and why you are starting there.

## Fast routing table

### Route to `literature-discovery`

Use when the user asks for:
- related work
- literature review
- survey of a topic
- state of the art
- closest papers
- novelty check grounded in existing papers
- research gap extraction

Escalate to `arxiv` when the user specifically wants:
- arXiv search only
- metadata from arXiv IDs
- abstracts or citation context from arXiv-first discovery

Escalate to `arxiv-pdf-download` when the user wants:
- local PDFs
- a download log
- a paper library organized on disk

### Route to `paper-structuring`

Use when the user asks for:
- paper outline
- contribution framing
- logic chain
- section skeleton
- technical paper vs benchmark paper positioning
- restructuring a draft whose main issue is shape rather than wording

### Route to `paper-drafting`

Use when the user asks for:
- write a section
- draft the paper
- rewrite introduction / methods / discussion
- turn notes into paper prose
- expand a validated outline into text

### Route to `paper-review`

Use when the user asks for:
- review this paper
- critique the draft
- check claims and citations
- prepare for submission
- build a revision plan
- determine whether the issue is structure, evidence, or wording

Escalate to `submission-readiness` when the user explicitly wants:
- a final gate before submission
- a go / no-go judgment
- camera-ready or near-submission final checks

### Route to `artifact-packaging`

Use when the user asks for:
- export PDF
- prepare supplement or appendix
- write artifact README
- package figures, tables, and reproducibility notes
- assemble a submission-facing artifact checklist

Escalate to `figure-support` when the user explicitly wants:
- figure design
- figure audit
- chart-type choice
- caption and visual-storytelling help

## Ambiguity handling

Ask exactly one clarifying question only when the request could plausibly belong to two adjacent phases, the available files or stated intent do not resolve the ambiguity, and the wrong routing choice would waste work.

Good clarifications:
- “Do you already have a stable related-work set, or should I start by finding the closest papers?”
- “Is the main problem the section logic, or do you already like the structure and want prose help only?”
- “Are you asking for a general review, or a final submission gate?”

Do not ask questions whose answers can be inferred from the user's files or stated intent.
Do not expose the whole routing graph unless the user explicitly asks for expert mode.

## Operating rules

- Prefer one main phase skill per turn.
- Ask only the minimum clarifying questions needed to route correctly.
- Treat factual accuracy and evidence discipline as mandatory.
- Never invent citations, results, datasets, or comparisons.
- Start with the earliest blocked phase rather than drafting around missing structure or evidence.
- If the user explicitly asks for expert mode or a named support skill, honor that request.

## Default behavior

If the user simply says they are working on a paper and does not specify the phase:
1. determine whether they are still discovering literature, structuring the paper, drafting text, reviewing a draft, or packaging artifacts;
2. route to the earliest unfinished phase;
3. explain the routing choice briefly;
4. continue inside that skill.

## Acceptance test

A working ResearchFlow integration should make the agent behave as though this routing layer is already loaded at session start. A minimal smoke test is a fresh session with a message like:

> I am writing a paper about agent memory systems and need help figuring out the related work first.

The agent should treat this as a `literature-discovery` phase request rather than jumping straight into prose drafting.
