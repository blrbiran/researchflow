---
name: arxiv-pdf-download
description: Download arXiv PDFs into a local staging directory and optionally organize them into canonical filenames. Use when the user wants local PDFs on disk rather than discovery only.
version: 0.1.0
metadata:
  tags: [Research, arXiv, PDF, Download]
  related_skills: [arxiv]
---

# arXiv PDF Download

Use this skill when the user wants PDF files saved locally.

## Use for

- downloading PDFs from explicit arXiv IDs
- batch downloading PDFs from a bibliography or markdown reference section
- organizing downloaded PDFs into stable local filenames

## Ask before

1. choosing a non-default download location
2. applying rename / move / organize operations instead of previewing them

## Default workflow

1. discover papers first if needed
2. download into a staging directory
3. optionally preview organization actions
4. apply organization only after explicit approval

## Output

Return:
- staging directory used
- whether organization was previewed or applied
- files downloaded
- files skipped or needing manual review
