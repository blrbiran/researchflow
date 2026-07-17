# Installing ResearchFlow for Claude Code

## What exists today

ResearchFlow currently ships Claude plugin metadata and a local development marketplace manifest:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

This is enough for local development, private testing, and future marketplace publication work.

## Local development install

If your Claude Code environment supports local marketplace manifests, point it at this repository's development marketplace and install the `researchflow` plugin from there.

The exact command surface can vary by Claude Code build, so the safe local workflow is:

1. Make sure this checkout is up to date.
2. Register or reference the development marketplace rooted at this repo.
3. Install the `researchflow` plugin entry.
4. Start a fresh session and verify the bootstrap behavior.

## What to verify

A working Claude Code install should make the session behave as if `using-researchflow` is already loaded.

Minimal acceptance check:

> I am writing a paper about agent memory systems and need help figuring out the related work first.

Expected result:
- the agent treats this as a `literature-discovery` request
- it does **not** jump directly into prose drafting
- If the user asks to write an introduction without a stable literature-backed gap, the router should still start at `literature-discovery`.
- If the user asks to export a PDF from a still-unreviewed manuscript, the router should still start at `paper-review`.

## Local smoke check

Run:

```bash
./tests/claude-code/run-tests.sh
```

This does not install the plugin into Claude Code. It verifies the local Claude-facing manifests and required bootstrap files are present and internally consistent.

## Development notes

- Keep `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` in sync on plugin name, description, and version.
- If the plugin name changes, update the manifests and the Claude smoke test together.
- If Claude Code later gains a stable documented local install command for this repo shape, record it here rather than scattering it through the root README.
