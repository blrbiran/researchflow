# Harness acceptance summary

- Run ID: `2026-07-19T152433Z`
- Run kind: `original`
- Packaging/redaction passed: `true`
- Raw artifact record: `local-raw/2026-07-19T152433Z` (sha256 `0bcd6cf7699dd4e00ef6a7527483d41573c7182c8e91b93aa050532219019e50`, manual review `pending`, reason `raw event streams remain local`)
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
- Preflight: `blocked`
- Plugin proof strength: `None` (source `researchflow-checkout`)
- Resolved model identity: `None`
- Isolation profile: `None`
- Contamination overlay: `0` contaminated invocation(s) (`none`)

## Case accounting
| # | Harness | Case ID | Status | Detail | Contaminated |
|---|---|---|---|---|---|
| 1 | claude | R-DIRECT-LIT | unattempted | global_hard_gate_blocked | no |
| 2 | claude | R-DIRECT-STRUCT | unattempted | global_hard_gate_blocked | no |
| 3 | claude | R-DIRECT-DRAFT | unattempted | global_hard_gate_blocked | no |
| 4 | claude | R-DIRECT-REVIEW | unattempted | global_hard_gate_blocked | no |
| 5 | claude | R-DIRECT-PACK | unattempted | global_hard_gate_blocked | no |
| 6 | claude | R-BACK-INTRO | unattempted | global_hard_gate_blocked | no |
| 7 | claude | R-BACK-PDF | unattempted | global_hard_gate_blocked | no |
| 8 | opencode | R-DIRECT-LIT | unattempted | opencode_preflight_blocked | no |
| 9 | opencode | R-DIRECT-STRUCT | unattempted | opencode_preflight_blocked | no |
| 10 | opencode | R-DIRECT-DRAFT | unattempted | opencode_preflight_blocked | no |
| 11 | opencode | R-DIRECT-REVIEW | unattempted | opencode_preflight_blocked | no |
| 12 | opencode | R-DIRECT-PACK | unattempted | opencode_preflight_blocked | no |
| 13 | opencode | R-BACK-INTRO | unattempted | opencode_preflight_blocked | no |
| 14 | opencode | R-BACK-PDF | unattempted | opencode_preflight_blocked | no |

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
