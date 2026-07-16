---
name: literature-discovery
description: Discover, map, and triage literature for a research question. Use for related work, literature review, survey framing, closest-paper discovery, and gap extraction.
version: 0.2.0
metadata:
  tags: [Research, Literature, Survey, RelatedWork]
  related_skills: [arxiv, arxiv-pdf-download]
---

# Literature Discovery

Use this skill to build a literature map before drafting prose.

## When to use

- The user needs related work.
- The user wants a literature review or state-of-the-art summary.
- The user wants to know which papers are closest to their idea.
- The user wants a research gap framed from evidence.
- The user wants novelty checked against existing literature rather than intuition.

## When not to use

- The user already has the literature map and wants an outline. Use `paper-structuring`.
- The user wants prose for a section. Use `paper-drafting`.
- The user wants PDFs saved locally. Use `arxiv-pdf-download`.

## Capability check

Before starting, decide what evidence sources are actually available:

- scholarly search tools
- web search over scholarly indexes
- shell access to public APIs such as arXiv, Semantic Scholar, Crossref, or DBLP
- user-supplied paper lists or notes

If no retrieval path exists, say so clearly and operate only on the user-provided corpus. Do not fake a literature map from model memory.

## Modes

- **Quick scan** — 5-10 closest works, enough to orient the next step.
- **Standard map** — enough coverage to structure a paper or subsection.
- **Deep review** — broader theme map with contradictions, methodological fault lines, and a defendable gap statement.

Default to Standard unless the user asks for something lighter or more exhaustive.

## Workflow

### Step 1: Freeze the brief

Turn the request into:
- one primary research question
- 2-4 retrieval axes
- an intended output such as gap statement, related-work notes, or shortlist

If the user only gives a vague topic, ask the minimum clarifying question needed to make the search answerable.

### Step 2: Search from multiple perspectives

Do not search from only one angle. Use 3-5 perspectives such as:
- mainstream technical line
- closest methodological neighbors
- benchmark or evaluation line
- critics / limitations / negative findings
- application, deployment, or policy edge

A good literature map is built from tension, not just from the dominant school.

### Step 3: Verify candidate works

For every work you plan to keep, verify at least:
- title
- author list or first author
- year
- source identity
- why it is relevant

Do not treat search snippets as evidence for detailed claims. Snippets can justify retrieval, not fine-grained technical assertions.

If a work's identity, recency, or relevance cannot be verified with reasonable confidence, keep it out of the closest-work shortlist rather than quietly guessing.

### Step 4: Narrow to the closest works

Identify the 5-15 most relevant papers or systems for the user's actual question.

Compare them on:
- problem setting
- method or mechanism
- dataset / benchmark / evaluation setup
- evidence strength
- recency / influence
- what axis really differs from the user's idea

Similarity of title or topic alone does not establish duplication.

### Step 5: Synthesize into a map

Synthesize by theme, not paper-by-paper.

Produce:
- a compact taxonomy or clustering
- the main line of agreement in the field
- the main contradictions or open tensions
- what is missing from current evaluations, assumptions, or settings

In-sentence comparison is stronger than serial summaries.

### Step 6: Extract the gap honestly

The gap should be one of:
- a missing evaluation dimension
- a missing deployment setting
- a missing methodological comparison
- a contradictory evidence zone
- a weakness in current benchmarks or attribution

Do not force novelty. If the closest work already covers the same object, mechanism, and setting, say that the space looks crowded.

### Step 7: Recommend the next phase

Recommend exactly one next move:
- move to `paper-structuring`
- fetch PDFs with `arxiv-pdf-download`
- deepen one search axis
- narrow or pivot the research question

## Output

Return:
- the frozen question
- search perspectives used
- a shortlist of closest works
- a compact taxonomy or clustering
- the likely research gap
- confidence level and main uncertainty
- the recommended next phase

## Routing notes

- If the user wants quick arXiv-only discovery, use `arxiv`.
- If the user wants a local paper library on disk, use `arxiv-pdf-download` after discovery.
