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

## Installation

Installation differs by harness. If you use more than one, install ResearchFlow separately for each one.

### Claude Code

ResearchFlow includes Claude plugin metadata in `.claude-plugin/`.

For local development and private use, see [docs/README.claude.md](docs/README.claude.md).

Current local development manifests:
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

### OpenCode

See [.opencode/INSTALL.md](.opencode/INSTALL.md) for installation and verification.

## Local development

See [docs/development.md](docs/development.md) for:
- local repo layout
- harness-specific install loops
- smoke test commands
- helper script expectations

## Versioning and release

See [docs/release/versioning.md](docs/release/versioning.md) and [docs/release/marketplace.md](docs/release/marketplace.md) for:
- version bump expectations
- manifest synchronization
- local development marketplaces
- future publish path notes


## Workflow contracts

ResearchFlow now uses explicit handoff artifacts between its main phases:

```text
Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet
```

See [docs/workflow-contracts.md](docs/workflow-contracts.md) for the contract details and transition gates.

## Repository shape

```text
.claude-plugin/        Claude plugin metadata
.opencode/             OpenCode install docs and plugin bridge
docs/                  Harness-specific docs and release notes
skills/                ResearchFlow skill library
tests/                 Minimal harness smoke tests
```

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

- Run everything: `./tests/run-all.sh`
- OpenCode bridge smoke test: `./tests/opencode/run-tests.sh`
- Claude metadata smoke test: `./tests/claude-code/run-tests.sh`
- Workflow demo contract test: `./tests/demo/test-agent-memory-e2e.sh`


## End-to-end demo

A minimal artifact-chain demo lives under `docs/demos/agent-memory-e2e/`.

Run its check with:

```bash
./tests/demo/test-agent-memory-e2e.sh
```
