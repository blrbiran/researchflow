# Harness acceptance summary

- Run ID: `2026-07-22T143702Z`
- Run kind: `original`
- Packaging/redaction passed: `true`
- Raw artifact record: `local-raw/2026-07-22T143702Z` (sha256 `03e0ac911f7f48faef3886041a81101fbfb601421f12a785c1355b6611c20cb8`, manual review `pending`, reason `raw event streams remain local`)
- This is single-run fresh-session acceptance evidence, not a stability or repeated-run estimate.

## Model alignment
- Required: `true`
- Aligned: `false`
- Blocked: `true`
- Canonical identity: `None`
- Model proofs: `preflight/claude-model-proof.json`, `preflight/opencode-model-proof.json`

## Harness summaries
### claude
- Preflight: `pass`
- Plugin proof strength: `best_available_source_plus_canary` (source `researchflow-checkout`)
- Resolved model identity: `openai/gpt-5.4`
- Isolation profile: `full-direct-plugin-dir`
- Contamination overlay: `0` contaminated invocation(s) (`none`)

### opencode
- Preflight: `pass`
- Plugin proof strength: `workspace_config_static_inventory_canary` (source `researchflow-checkout`)
- Resolved model identity: `None`
- Isolation profile: `workspace-config-runtime-proof`
- Contamination overlay: `0` contaminated invocation(s) (`none`)

## Case accounting
| # | Harness | Case ID | Status | Detail | Contaminated |
|---|---|---|---|---|---|
| 1 | claude | R-DIRECT-LIT | unattempted | runtime-proof-unavailable | no |
| 2 | claude | R-DIRECT-STRUCT | unattempted | runtime-proof-unavailable | no |
| 3 | claude | R-DIRECT-DRAFT | unattempted | runtime-proof-unavailable | no |
| 4 | claude | R-DIRECT-REVIEW | unattempted | runtime-proof-unavailable | no |
| 5 | claude | R-DIRECT-PACK | unattempted | runtime-proof-unavailable | no |
| 6 | claude | R-BACK-INTRO | unattempted | runtime-proof-unavailable | no |
| 7 | claude | R-BACK-PDF | unattempted | runtime-proof-unavailable | no |
| 8 | opencode | R-DIRECT-LIT | unattempted | runtime-proof-unavailable | no |
| 9 | opencode | R-DIRECT-STRUCT | unattempted | runtime-proof-unavailable | no |
| 10 | opencode | R-DIRECT-DRAFT | unattempted | runtime-proof-unavailable | no |
| 11 | opencode | R-DIRECT-REVIEW | unattempted | runtime-proof-unavailable | no |
| 12 | opencode | R-DIRECT-PACK | unattempted | runtime-proof-unavailable | no |
| 13 | opencode | R-BACK-INTRO | unattempted | runtime-proof-unavailable | no |
| 14 | opencode | R-BACK-PDF | unattempted | runtime-proof-unavailable | no |

## Verdict partitions
| Harness | Pass | Fail | Indeterminate | Harness error | Unattempted |
|---|---|---|---|---|---|
| claude | 0 | 0 | 0 | 0 | 7 |
| opencode | 0 | 0 | 0 | 0 | 7 |

## Contamination overlays
| Harness | Contaminated invocations | Case IDs |
|---|---|---|
| claude | 0 | none |
| opencode | 0 | none |

## Evidence links
- Capabilities: `capabilities/claude.json`, `capabilities/opencode.json`
- Preflights: `preflight/claude.json`, `preflight/opencode.json`
- Model proofs: `preflight/claude-model-proof.json`, `preflight/opencode-model-proof.json`

## Deviations
- none

## Manual notes
- none
