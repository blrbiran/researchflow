---
name: literature-discovery
description: Discover, map, and triage literature for a research question. Use for related work, literature review, survey framing, closest-paper discovery, and gap extraction.
version: 0.1.0
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

## When not to use

- The user already has the literature map and wants an outline. Use `paper-structuring`.
- The user wants prose for a section. Use `paper-drafting`.
- The user wants PDFs saved locally. Use `arxiv-pdf-download`.

## Workflow

1. Freeze the question.
   - Turn the request into one primary research question and 2-4 retrieval axes.
2. Search broadly.
   - Build an initial pool using available literature tools and web sources.
3. Narrow to the closest works.
   - Identify the 5-15 most relevant papers or systems.
4. Compare by dimensions.
   - Problem setting
   - method/mechanism
   - dataset/evaluation setup
   - evidence strength
   - recency / influence
5. Synthesize.
   - What is already known?
   - Where do results agree?
   - Where do they conflict?
   - What gap remains?
6. Recommend next action.
   - move to structuring
   - fetch PDFs
   - search another axis

## Output

Return:
- the frozen question
- a shortlist of closest works
- a compact taxonomy or clustering
- the likely research gap
- the recommended next phase

## Routing notes

- If the user wants quick arXiv-only discovery, use `arxiv`.
- If the user wants a local paper library on disk, use `arxiv-pdf-download` after discovery.
