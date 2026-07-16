---
name: arxiv
description: Search arXiv papers by keyword, author, category, or arXiv ID. Use for discovery, metadata lookup, abstracts, citation context, and related-paper exploration.
version: 0.1.0
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

## Route elsewhere when

- The user wants a broader literature map beyond arXiv only. Use `literature-discovery`.
- The user wants PDFs saved to disk. Use `arxiv-pdf-download`.

## Output

Return compact search results with:
- title
- authors
- year or date
- arXiv ID
- why it looks relevant
