# Installing ResearchFlow for OpenCode

## Prerequisites

- OpenCode installed

## Local development install

Add this checkout to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["/absolute/path/to/reference/researchflow"]
}
```

Restart OpenCode. The plugin registers the bundled skills and injects the `using-researchflow` bootstrap into each session.

## Git-backed install

If you publish this repository, you can install it through OpenCode's git-backed plugin mechanism:

```json
{
  "plugin": ["researchflow@git+<your-git-url>"]
}
```

## Verify

Ask OpenCode:

```text
Tell me about your researchflow skills
```

You should see the research workflow bootstrap active and the bundled skills available through OpenCode's native `skill` tool.

## Tool mapping

ResearchFlow skills speak in actions. On OpenCode these resolve to:

- Create or update todos → `todowrite`
- Invoke a skill → OpenCode's native `skill` tool
- Read files → `read`
- Create or edit files → `apply_patch`
- Run shell commands → `bash`
- Search files → `grep`, `glob`
- Fetch a URL → `webfetch`
- Dispatch a subagent → `task`


## Local smoke test

Run:

```bash
./tests/opencode/run-tests.sh
```

This validates that the plugin registers the `skills/` path and injects the `using-researchflow` bootstrap into the first user message.
