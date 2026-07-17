# ResearchFlow Local Development

## Scope

This document covers local development for the ResearchFlow plugin repository.

Initial supported harnesses:
- Claude Code
- OpenCode

## Repository layout

- `.claude-plugin/` — Claude plugin metadata
- `.opencode/` — OpenCode plugin bridge and install doc
- `skills/` — skill library and helper scripts
- `tests/` — local smoke tests
- `docs/` — harness-specific and release documentation

## Typical edit loop

1. Update one or more skills or plugin bridge files.
2. Re-run smoke tests.
3. Check `git diff` in the `reference/researchflow` repo.
4. Commit in the nested repo, not only in the parent workspace.

## Smoke tests

### All tests

```bash
./tests/run-all.sh
```

Runs the OpenCode smoke test, the Claude metadata smoke test, and the workflow demo contract test in one entrypoint.

### OpenCode

```bash
./tests/opencode/run-tests.sh
```

Checks:
- the plugin bridge registers `skills/`
- the OpenCode bootstrap injects `using-researchflow`

### Claude Code

```bash
./tests/claude-code/run-tests.sh
```

Checks:
- Claude plugin manifests parse
- required support skills and helper scripts exist

## Helper scripts currently bundled

- `skills/arxiv/scripts/search_arxiv.py`
- `skills/arxiv-pdf-download/scripts/download_arxiv_refs.py`
- `skills/arxiv-pdf-download/scripts/organize_pdf_titles.py`

When changing these, re-run the Claude smoke test because it checks for their presence.

## Nested repo reminder

`reference/researchflow/` is its own git repository.

Use:

```bash
git -C reference/researchflow status
git -C reference/researchflow diff
git -C reference/researchflow commit ...
```

Do not assume parent-repo commits will capture child-repo history.


## Workflow contracts

The main workflow is artifact-driven:

```text
Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet
```

When editing a phase skill, keep its expected handoff artifact synchronized with `docs/workflow-contracts.md`.


### Workflow demo

```bash
./tests/demo/test-agent-memory-e2e.sh
```

Checks that the sample Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet chain exists and that each artifact includes the required workflow-contract fields with non-empty section bodies.

### Benchmark / evaluation demo

```bash
./tests/demo/test-benchmark-ambiguity-e2e.sh
```

Checks the same contract chain on a benchmark / evaluation-paper flavored example so the workflow is not validated only on the agent-memory topic.
