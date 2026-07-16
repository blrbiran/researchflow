---
name: arxiv-pdf-download
description: Download arXiv PDFs into a local staging directory and optionally organize them into canonical filenames. Use when the user wants local PDFs on disk rather than discovery only.
version: 0.2.0
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
- creating a local paper staging area before deeper reading or annotation

## Ask before

1. choosing a non-default download location
2. applying rename / move / organize operations instead of previewing them

## Default workflow

This skill has two phases:

1. **Download into staging**
2. **Optionally organize staged PDFs**

Unless the repo already has a stronger convention, default to:
- staging directory: `paper/pdf/download/`
- canonical directory: `paper/pdf/`
- arXiv alias directory: `paper/pdf/arxiv/`

## Bundled helpers

When shell execution is available, use the bundled scripts:

```bash
python "skills/arxiv-pdf-download/scripts/download_arxiv_refs.py" --ids 2402.03300 2401.12345v2
python "skills/arxiv-pdf-download/scripts/organize_pdf_titles.py"
python "skills/arxiv-pdf-download/scripts/organize_pdf_titles.py" --apply
```

The download helper supports explicit IDs and markdown-reference extraction.
The organizer supports preview and apply modes.

## Operational rules

- Download approval does not automatically imply rename / move approval.
- Use preview-first for organization unless the user explicitly approved apply mode.
- Do not invent filenames by hand when canonical title extraction is available through the organizer logic.
- If collisions or unresolved titles appear, keep them for manual review instead of forcing a rename.

## Workflow

### Step 1: Choose the source set

Start from one of:
- explicit arXiv IDs
- a markdown bibliography or page range
- a staging directory that already contains copied PDFs

### Step 2: Download into staging

Save PDFs into the staging directory and summarize what landed there.

### Step 3: Preview organization

If the user wants the files normalized, preview the move / rename / symlink behavior first unless apply mode was already approved.

### Step 4: Apply organization when approved

When approved:
- move canonical files into the target paper/pdf area
- create arXiv alias symlinks if the workflow uses them
- report duplicates, collisions, and unresolved files separately

## Output

Return:
- staging directory used
- whether organization was previewed or applied
- where canonical PDFs were written
- files downloaded, moved, duplicated, or skipped
- which files still need manual review
