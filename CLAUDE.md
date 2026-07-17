# ResearchFlow Contributor Notes

ResearchFlow is a standalone plugin for research and paper-writing workflows.

## Current scope

- Prioritize Claude Code and OpenCode first.
- Prefer a small number of strong phase skills over many overlapping skills.
- Route similar asks through `using-researchflow` instead of exposing every specialist skill directly.
- Keep `using-researchflow` as a thin router over the existing five-phase workflow.
- Default to direct routing; ask one clarifying question only for high-cost adjacent-phase ambiguity.
- Do not turn support skills or external references into peer top-level routes.

## Skill design rules

- Keep phase skills focused on one workflow stage.
- Prefer routing and composition over duplicating near-identical skills.
- Do not add domain-specific or venue-specific content into the core workflow unless it generalizes.
- Treat skill text as behavior-shaping content: keep it concise, explicit, and testable.

## First-class bundled skills

- `using-researchflow`
- `literature-discovery`
- `paper-structuring`
- `paper-drafting`
- `paper-review`
- `artifact-packaging`
- `arxiv`
- `arxiv-pdf-download`
- `figure-support`
- `submission-readiness`
