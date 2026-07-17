# ResearchFlow Live Harness Acceptance Design Spec

Date: 2026-07-17  
Status: Draft for review  
Topic: Single-run fresh-session acceptance of the ResearchFlow thin router in real Claude Code and OpenCode CLIs

## 1. Purpose

This spec defines the first live-harness acceptance run for the ResearchFlow V1 thin router.

The existing repo-local tests verify plugin metadata, bootstrap injection, routing-document consistency, and demo artifact contracts. They do not establish that a fresh real CLI session will load the local plugin and route a user's request onto the correct ResearchFlow phase. This design closes that evidence gap without changing the five-phase workflow contract.

The first run answers one bounded question:

> In one fresh non-interactive CLI session per case, do Claude Code and OpenCode load the local ResearchFlow plugin and select the expected primary phase for the same seven core requests?

This is acceptance evidence, not a stability estimate. Each case runs once per harness. Failed or indeterminate cases may be rerun later under a separately identified rerun, but the original evidence must remain intact.

## 2. Scope and settled decisions

### 2.1 Harnesses

The first run covers:

1. Claude Code through its real non-interactive CLI, using `claude -p` or the documented equivalent available in the execution environment.
2. OpenCode through its real non-interactive CLI, using the documented local-plugin configuration.

The exact OpenCode command must be discovered and recorded during preflight rather than guessed in the spec.

### 2.2 Case count

Each harness runs the same seven cases once in independent fresh sessions:

- five direct-routing cases, one for each primary ResearchFlow phase;
- two backward-routing cases that test artifact-first correction.

The first run therefore contains 14 scored invocations after successful harness preflight.

### 2.3 Shared semantics, native execution

The two harnesses consume one shared case manifest and one shared deterministic judge. Each harness has its own thin adapter for installation, session isolation, CLI invocation, and evidence capture.

Adapters must not contain case-specific routing logic or decide verdicts.

### 2.4 Non-goals

This work does not:

- alter `docs/workflow-contracts.md`;
- add a new primary phase or router surface;
- add expert-mode behavior;
- measure repeated-run stability;
- run the three ambiguity/clarification cases in the first round;
- automatically modify routing behavior after a failure;
- automatically bump the release version;
- push to a remote repository;
- or treat a harness or environment failure as a routing failure.

## 3. Architecture

The acceptance pack has four layers.

### 3.1 Shared case manifest

A single machine-readable manifest defines the seven prompts and their scoring contract.

Recommended path:

```text
tests/harness-acceptance/cases.json
```

Each case must contain:

```json
{
  "case_id": "R-DIRECT-LIT",
  "kind": "direct",
  "prompt": "...",
  "expected_phase": "literature-discovery",
  "allowed_equivalents": ["literature discovery"],
  "forbidden_primary_phases": [
    "paper-structuring",
    "paper-drafting",
    "paper-review",
    "artifact-packaging"
  ],
  "forbidden_actions": ["draft_manuscript_prose"]
}
```

Field meanings:

- `case_id` — stable identifier used in directories and summaries;
- `kind` — `direct` or `backward`;
- `prompt` — complete user request including enough state to make one route correct;
- `expected_phase` — one of the five primary ResearchFlow phases;
- `allowed_equivalents` — narrowly defined textual equivalents accepted by the deterministic judge;
- `forbidden_primary_phases` — primary phases that must not be chosen as the current entrypoint;
- `forbidden_actions` — observable downstream actions that invalidate the route.

The two adapters must read the same manifest. They must not duplicate the prompts.

### 3.2 Harness-native adapters

Recommended paths:

```text
tests/harness-acceptance/adapters/claude.sh
tests/harness-acceptance/adapters/opencode.sh
```

Each adapter is responsible for:

- verifying that its CLI exists;
- recording the CLI version;
- establishing local-plugin loading from the current checkout;
- creating an independent session and isolation directory for every case;
- invoking the CLI non-interactively;
- enforcing the fixed timeout;
- capturing command metadata, stdout, stderr, and exit status;
- and reporting infrastructure status without judging route semantics.

The adapter output contract should be identical across harnesses so the shared judge does not branch on CLI-specific formats.

### 3.3 Shared deterministic judge

Recommended path:

```text
tests/harness-acceptance/judge.py
```

The judge reads one case definition and one captured invocation. It uses only deterministic string matching, regular expressions, structured metadata, and process status. It must not call an LLM.

The judge emits exactly one machine verdict:

- `pass`
- `fail`
- `indeterminate`
- `harness_error`

An additional `environment_contaminated` boolean records whether the adapter could not establish the required isolation boundary. A contaminated invocation cannot count as acceptance evidence even if its textual route appears correct.

### 3.4 Evidence bundle

Recommended layout:

```text
tests/harness-acceptance/
├── cases.json
├── judge.py
├── adapters/
│   ├── claude.sh
│   └── opencode.sh
└── results/
    └── <run-id>/
        ├── environment.json
        ├── summary.json
        ├── summary.md
        ├── claude/
        │   └── <case-id>/
        │       ├── command.json
        │       ├── stdout.txt
        │       ├── stderr.txt
        │       └── verdict.json
        └── opencode/
            └── <case-id>/
                ├── command.json
                ├── stdout.txt
                ├── stderr.txt
                └── verdict.json
```

A run ID must be stable and collision-safe. Use an explicit UTC timestamp supplied by the orchestration command, for example `2026-07-17T120000Z`; do not derive identity from model output.

## 4. Core cases

### 4.1 Five direct-routing cases

| Case ID | Request state | Expected primary phase |
|---|---|---|
| `R-DIRECT-LIT` | User needs related work, closest papers, and a research gap; no literature map exists | `literature-discovery` |
| `R-DIRECT-STRUCT` | Literature and likely gap are supplied and stable; user needs paper type, contributions, and section logic | `paper-structuring` |
| `R-DIRECT-DRAFT` | Literature map and structure brief are explicitly supplied and stable; user asks to rewrite a Methods section | `paper-drafting` |
| `R-DIRECT-REVIEW` | A complete manuscript is supplied; user asks for critique and revision order | `paper-review` |
| `R-DIRECT-PACK` | Review blockers are explicitly resolved; user asks to package PDF, supplement, and artifact README | `artifact-packaging` |

Each prompt must state enough upstream readiness that the expected phase is unique. Direct cases must not accidentally omit an upstream artifact and thereby test backward routing instead.

### 4.2 Two backward-routing cases

| Case ID | Surface request | Declared missing state | Expected route |
|---|---|---|---|
| `R-BACK-INTRO` | Write the Introduction | No stable Literature Map or literature-backed gap | `literature-discovery` |
| `R-BACK-PDF` | Export a submission PDF | The manuscript has unresolved review blockers and no stable Review Packet | `paper-review` |

These cases operationalize the existing contract rule:

> Surface intent proposes a phase; artifact stability confirms it or routes earlier.

## 5. Deterministic verdict contract

### 5.1 Pass

A case is `pass` only when all conditions hold:

1. the process exits successfully;
2. the captured response explicitly names `expected_phase` or one allowed equivalent;
3. it does not name a forbidden primary phase as the current route;
4. it does not execute or present the forbidden downstream action as the current task result;
5. it does not elevate a support skill to a new primary phase;
6. `environment_contaminated` is false.

Mentioning another phase as a future step, comparison, or reason for not choosing it must not automatically fail the case. The judge regex must distinguish current-route statements from explanatory references. If that distinction cannot be established deterministically, return `indeterminate` rather than guessing.

### 5.2 Fail

A case is `fail` when the transcript provides deterministic evidence that the agent:

- selects a different primary phase as the current entrypoint;
- proceeds with a forbidden downstream action instead of routing;
- or promotes a support skill or external framework to a competing top-level route.

### 5.3 Indeterminate

A case is `indeterminate` when:

- the response does not provide enough text to identify the current primary phase;
- multiple primary phases are presented without a selected entrypoint;
- or deterministic rules cannot separate a route choice from explanatory mention.

The judge must not call a model to resolve ambiguity.

### 5.4 Harness error

A case is `harness_error` when routing cannot be evaluated because of:

- CLI or plugin load failure;
- authentication failure;
- timeout;
- non-zero process exit unrelated to a semantic route;
- missing required artifact;
- or adapter/runtime failure.

Harness errors do not count as routing failures.

### 5.5 Manual notes

Human review may append a `manual_note` containing:

- reviewer;
- review timestamp;
- observation;
- and whether the reviewer agrees with the machine verdict.

A manual note must never overwrite the machine verdict or raw transcript.

## 6. Fresh-session isolation

Each scored invocation must satisfy all of the following:

- launch a new CLI process;
- not reuse a prior conversation or session identifier;
- not inherit another case's transcript;
- use an independent temporary home, config, cache, or data directory where supported;
- load the local ResearchFlow checkout under test;
- exclude unrelated user-level research routers, skills, memory, and project instructions where the harness supports explicit isolation;
- record any unavoidable residual configuration source;
- and record the effective CLI version and plugin source path.

The adapter must test isolation behavior during preflight. If complete isolation is impossible, set `environment_contaminated = true` and preserve the run as diagnostic evidence only.

Secrets and raw environment-variable values must never be copied into committed evidence. Presence may be recorded as a boolean when needed for diagnostics.

## 7. Harness preflight

Each adapter performs a non-scored preflight before generating case verdicts.

Preflight must verify:

1. CLI discovery and version capture;
2. non-interactive execution availability;
3. local ResearchFlow plugin loading;
4. independent isolation directory creation;
5. a bootstrap probe that can observe `using-researchflow`;
6. timeout support;
7. output capture;
8. and absence of obvious authentication leakage in captured output.

If preflight fails, the harness receives overall status `blocked`. The runner must not generate seven placeholder verdicts that imply the cases were attempted.

The preflight record must explain which gate failed and preserve the available stdout/stderr evidence after redaction.

## 8. Execution order and retry policy

The fixed first-run order is:

1. Claude Code preflight;
2. Claude Code cases in manifest order;
3. Claude Code artifact-completeness check;
4. OpenCode preflight;
5. OpenCode cases in the same manifest order;
6. cross-harness summary generation.

A Claude Code semantic `fail` or `indeterminate` does not block OpenCode. A harness-level infrastructure blocker stops only that harness.

Each case has a fixed timeout recorded in `command.json`. The first run performs no automatic retry.

Later retry rules:

- infrastructure fixes may produce `rerun-1`, `rerun-2`, and so on;
- semantic failures are not automatically retried before analysis;
- reruns must never overwrite the original run directory;
- and summaries must identify which run is original and which is a rerun.

## 9. Evidence retention and redaction

### 9.1 Required committed artifacts

Commit:

- `cases.json`;
- adapters;
- deterministic judge;
- redacted `environment.json`;
- all 14 `verdict.json` files when both harnesses complete;
- `summary.json`;
- and `summary.md`.

If a harness is blocked at preflight, commit its redacted preflight record and the summary explaining that no scored invocations were generated.

### 9.2 Never commit

Do not commit:

- temporary home/config/cache/data directories;
- session caches;
- authentication tokens;
- raw environment-variable values;
- credentials;
- or unredacted logs containing sensitive local context.

### 9.3 Review-dependent artifacts

Review `stdout.txt`, `stderr.txt`, and `command.json` before deciding whether to commit them.

If a raw transcript is retained only locally, `summary.md` must record:

- the local relative artifact identifier rather than a user-specific absolute path;
- SHA-256 of the raw artifact;
- the reason it was not committed;
- and the redaction/manual-review status.

No committed artifact may contain a user home path, authentication value, or unrelated private project instruction.

## 10. Summary schema and reconstruction

`summary.json` must be deterministically reconstructable from `environment.json` and the available preflight/verdict files.

It must include:

```json
{
  "run_id": "2026-07-17T120000Z",
  "run_kind": "original",
  "case_count_per_harness": 7,
  "harnesses": {
    "claude": {
      "preflight": "pass",
      "counts": {
        "pass": 7,
        "fail": 0,
        "indeterminate": 0,
        "harness_error": 0,
        "environment_contaminated": 0
      }
    },
    "opencode": {
      "preflight": "pass",
      "counts": {
        "pass": 7,
        "fail": 0,
        "indeterminate": 0,
        "harness_error": 0,
        "environment_contaminated": 0
      }
    }
  },
  "acceptance_complete": true,
  "release_candidate_eligible": true
}
```

`release_candidate_eligible` is true only for a complete original run with 14 `pass` verdicts and no contaminated invocation. It is a release-discussion gate, not a version bump or release action.

`summary.md` must contain:

- environment and plugin-source summary;
- a 14-row case table when both harnesses complete;
- preflight blockers, if any;
- counts by verdict;
- links or hashes for evidence;
- deviations and manual notes;
- and the explicit statement: “This is single-run fresh-session acceptance evidence, not a stability or repeated-run estimate.”

## 11. Failure handling

### 11.1 Semantic failure or indeterminate result

When a scored case is `fail` or `indeterminate`:

- preserve all evidence;
- finish the remaining cases unless the harness becomes unusable;
- do not mutate the router during the run;
- and produce a separate analysis before proposing a router or judge change.

### 11.2 Harness error

When a case is `harness_error`:

- preserve the failed command and redacted output;
- continue only if the adapter can safely establish a fresh next session;
- otherwise stop that harness and mark later cases unattempted in the summary, not as implicit failures.

### 11.3 Environment contamination

A contaminated invocation may retain a machine route verdict for diagnostics, but it does not count toward acceptance. Fix isolation and create a new rerun directory.

### 11.4 No silent exclusions

Every expected invocation must appear as one of:

- a verdict artifact;
- an explicitly unattempted case caused by a documented harness blocker;
- or a later rerun linked to its original case.

The summary generator must fail if expected artifacts disappear silently.

## 12. Completion and interpretation

The first acceptance run is operationally complete when:

- both preflights have a recorded result;
- every attempted case has command metadata, captured output, process status, and a machine verdict;
- all expected cases are accounted for;
- committed evidence is redacted;
- `summary.json` reconstructs from lower-level artifacts;
- and `summary.md` accurately reports the bounded evidence.

Interpretation rules:

- **14/14 pass:** eligible for a separate `0.2.0` release-candidate discussion;
- **any fail or indeterminate:** analyze router/judge behavior before release discussion;
- **only harness errors:** repair adapter or installation infrastructure before changing router semantics;
- **any environment contamination:** the affected invocation is not acceptance evidence and requires a separately identified rerun.

The acceptance run must not be described as reliability, consistency, or repeated-run stability evidence.

## 13. Post-run update boundary

After evidence exists, the implementation may update only:

- the harness acceptance result summary;
- `docs/handover/researchwork-plugin-handover.md` verified state and remaining limitations;
- and installation instructions that were proven inaccurate by preflight.

Do not automatically:

- change the five-phase contract;
- add router features;
- add the three clarification cases;
- run three-trial stability tests;
- bump versions;
- publish or push;
- or treat release-candidate eligibility as release approval.

## 14. Validation strategy

Before any live run, local tests should verify:

1. the manifest contains exactly seven unique case IDs;
2. expected phases belong to the five primary ResearchFlow phases;
3. both adapters consume the shared manifest rather than copied prompts;
4. the judge emits only the four allowed verdicts;
5. a synthetic passing transcript passes;
6. wrong-phase, forbidden-action, ambiguous, timeout, and contamination fixtures receive the expected verdict/status;
7. the summary generator rejects missing or duplicate case artifacts;
8. redaction removes user-home paths and credential-shaped values;
9. reruns cannot overwrite an original run;
10. both adapters expose preflight and per-case artifact contracts consistently.

Live acceptance then verifies real CLI behavior. Repo-local synthetic tests remain necessary because a real acceptance transcript alone cannot prove judge completeness or failure-path handling.

## 15. Success criteria

The design is implemented correctly when:

- Claude Code and OpenCode use the same seven-case manifest;
- each harness uses a native real-CLI adapter;
- each scored invocation is a fresh non-interactive session;
- the deterministic judge makes no LLM calls;
- all 14 expected invocations are accounted for after successful preflight;
- failures, indeterminate results, harness errors, and contamination remain distinct;
- original evidence is never overwritten by reruns;
- committed evidence is redacted and auditable;
- the summary is deterministically reconstructable;
- and no release, version bump, or push occurs without a separate user decision.
