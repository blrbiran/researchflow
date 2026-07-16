---
name: arxiv
description: Search arXiv papers by keyword, author, category, or arXiv ID. Use for discovery, metadata lookup, abstracts, citation context, and related-paper exploration.
version: 0.2.0
metadata:
  tags: [Research, arXiv, Papers, Discovery]
  related_skills: [literature-discovery, arxiv-pdf-download]
---

# arXiv

Use this skill for lightweight arXiv discovery.

## Best uses

- Find recent papers on a topic.
- Check paper metadata from a known arXiv ID.
- Read abstracts quickly.
- Expand a shortlist during literature discovery.
- Pull a fast citation-context check before deciding which papers deserve deeper reading.

## Route elsewhere when

- The user wants a broader literature map beyond arXiv only. Use `literature-discovery`.
- The user wants PDFs saved to disk. Use `arxiv-pdf-download`.

## Search modes

- **Topic scan** — recent or relevant papers for a keyword cluster.
- **Known-ID lookup** — metadata, abstract, and neighboring context for a specific arXiv paper.
- **Shortlist expansion** — start from a few known papers and widen the candidate set.
- **Citation-context pass** — use citation metadata to see whether a paper looks central, peripheral, or dated.

## Workflow

### Step 1: Clarify the search intent

Decide whether the user wants:
- the latest papers
- the closest papers
- author or category filtering
- citation context around one known paper

If the user does not specify, default to a topic scan plus a compact shortlist.

### Step 2: Run an arXiv-first search

Search by:
- all fields
- title
- author
- category
- known arXiv ID

Use the bundled helper when shell execution is available:

```bash
python "skills/arxiv/scripts/search_arxiv.py" "your query"
python "skills/arxiv/scripts/search_arxiv.py" --author "Author Name" --max 5
python "skills/arxiv/scripts/search_arxiv.py" --category cs.AI --sort date
python "skills/arxiv/scripts/search_arxiv.py" --id 2402.03300
```

### Step 3: Enrich only when useful

If the user needs more than raw metadata, enrich with:
- abstract reading
- citation counts or references when available
- quick paper-to-paper comparison for the shortlist

Do not turn this into a full literature review unless the task has clearly crossed that threshold.

### Step 4: Return a usable shortlist

For each returned paper, include:
- title
- authors
- year or date
- arXiv ID
- why it looks relevant
- whether it seems like a strong candidate for deeper reading or local download

### Step 5: Recommend the next move

Typical next moves:
- deepen into `literature-discovery`
- fetch local PDFs with `arxiv-pdf-download`
- read the top two or three abstracts first

## Output

Return compact search results with:
- title
- authors
- year or date
- arXiv ID
- why it looks relevant
- recommended next move
