# ResearchFlow Versioning and Release Notes

## Current version source of truth

For now, keep these aligned manually:

- `package.json`
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

At minimum, the plugin version string should move together across package and marketplace metadata.

## Suggested initial release discipline

Until a full release script exists:

1. bump version fields together
2. update any install or release notes that mention the old version
3. run both smoke tests
4. commit the version bump separately when possible

## Compatibility expectations

Version bumps should be driven by behavior surface, not just file churn:

- **patch** — doc improvements, non-breaking packaging changes, small skill clarifications
- **minor** — new skills, new helper scripts, meaningful routing expansions, new support capabilities
- **major** — breaking routing changes, renamed public skills, install-surface breaks, manifest format changes

## Release checklist

- [ ] `package.json` version updated
- [ ] Claude plugin manifest version updated
- [ ] Claude marketplace manifest version updated
- [ ] any agent marketplace metadata updated if needed
- [ ] README install docs still accurate
- [ ] `./tests/opencode/run-tests.sh` passes
- [ ] `./tests/claude-code/run-tests.sh` passes
