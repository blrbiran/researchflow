# Claude Code smoke checks

These checks validate the local plugin skeleton without requiring a live Claude Code plugin install.

## Run

```bash
./tests/claude-code/run-tests.sh
```

## What it checks

- `.claude-plugin/plugin.json` parses and names the plugin `researchflow`
- `.claude-plugin/marketplace.json` exposes a `researchflow` plugin entry
- `skills/using-researchflow/SKILL.md` exists as the bootstrap skill
