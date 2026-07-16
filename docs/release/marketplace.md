# ResearchFlow Marketplace Notes

## Current state

ResearchFlow currently includes local development marketplace manifests for Claude-facing workflows:

- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

These are development-oriented manifests rooted at the current repository (`"source": "./"`).

## Purpose of the current manifests

They support:
- local plugin discovery during development
- future migration into a publishable marketplace flow
- consistency checks in local smoke tests

They do **not** by themselves mean the plugin is already published in a public marketplace.

## When editing marketplace metadata

Keep these aligned on:
- plugin name
- description
- version
- source expectations for the intended environment

## Future publish path

When ResearchFlow is ready for a public marketplace or documented install flow, this file should be updated with:
- canonical plugin source URL
- install command examples
- any required owner / author metadata
- release process specifics for each harness

Until then, prefer describing the current state honestly as local-development marketplace support.
