# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-07-18

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

- **Project:** researchflow
- **Description:** ResearchFlow skills and runtime bootstrap for research and paper-writing agents
- Reference-library layouts differ: `academic-research-skills` duplicates skills at root and `skills/`, while `gstack` keeps skill directories at repository root with no `skills/` directory. Follow symlinks with `find -L` when inventorying them.
- For live-harness Task 4, reuse the existing dirty draft and preserve the thin-adapter boundary: shell captures native CLI evidence; Python owns parsing, normalization, validation, and fail-closed capability selection.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
