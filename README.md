# ResearchFlow

ResearchFlow is a plugin-shaped skills library for research and paper-writing agents.

It is designed around a small number of workflow stages instead of a long list of overlapping specialist skills. The default entrypoint is `using-researchflow`, which routes the session into the right phase skill.

## Initial targets

- Claude Code
- OpenCode

## Core workflow

1. **literature-discovery** — build a literature map, shortlist papers, and extract a research gap
2. **paper-structuring** — decide the paper type, logic chain, and section skeleton
3. **paper-drafting** — draft sections or a full manuscript with evidence discipline
4. **paper-review** — review structure, claims, citations, and submission readiness
5. **artifact-packaging** — export PDFs, package supplements, and assemble artifact docs

## Bundled support skills

- **using-researchflow** — bootstrap and routing layer
- **arxiv** — lightweight arXiv discovery, metadata, abstract, and shortlist support
- **arxiv-pdf-download** — local PDF download and organization workflow
- **figure-support** — figure design, caption guidance, and visual audit support
- **submission-readiness** — final submission gate for venue-facing polish

## Repository shape

```text
.claude-plugin/        Claude plugin metadata
.opencode/             OpenCode install docs and plugin bridge
skills/                ResearchFlow skill library
tests/                 Minimal harness smoke tests
```

## Claude Code

This repository includes Claude plugin metadata in `.claude-plugin/plugin.json`.

Current local development manifests:
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

## OpenCode

See `.opencode/INSTALL.md` for plugin installation and verification.

## Minimal acceptance behavior

In a fresh session, a request like:

> I am writing a paper about agent memory systems and need help figuring out the related work first.

should be treated as a literature-discovery request. A working bootstrap should not jump directly into prose drafting.

## Current status

V0 provides:
- plugin skeleton for Claude Code and OpenCode
- bootstrap injection for OpenCode
- a compact five-phase research workflow
- arXiv discovery, PDF-download, figure, and submission support skills
- minimal smoke tests under `tests/`

## Smoke tests

- OpenCode bridge smoke test: `./tests/opencode/run-tests.sh`
- Claude metadata smoke test: `./tests/claude-code/run-tests.sh`
