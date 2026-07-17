# ResearchFlow Live Harness Acceptance Design Spec

Date: 2026-07-17  
Status: Draft for review  
Topic: Single-run fresh-session acceptance of the ResearchFlow thin router in real Claude Code and OpenCode CLIs

## 1. Purpose

This spec defines the first live-harness acceptance run for the ResearchFlow V1 thin router.

The existing repo-local tests verify plugin metadata, bootstrap injection, routing-document consistency, and demo artifact contracts. They do not establish that a fresh real CLI session will load the local plugin and route a user's request onto the correct ResearchFlow phase. This design closes that evidence gap without changing the five-phase workflow contract.

The first run answers one bounded question:

> In one fresh non-interactive CLI session per case, do Claude Code and OpenCode load the local ResearchFlow plugin and select the expected primary phase for the same seven core requests?

The scored task ends at the routing decision. It does not execute literature discovery, structuring, drafting, review, or packaging. Every scored prompt requires one canonical phase marker followed by at most two explanatory sentences.

This is acceptance evidence, not a stability estimate. Each case runs once per harness. Failed or indeterminate cases may be rerun later under a separately identified rerun, but the original evidence must remain intact.

## 2. Scope and settled decisions

### 2.1 Harnesses

The first run covers:

1. Claude Code through its real non-interactive CLI using `claude -p`.
2. OpenCode through its real non-interactive CLI using `opencode run` and a documented local-plugin configuration.

The exact supported isolation profile for each installed CLI must be established by capability probe before a scored invocation starts.

### 2.2 Case count

Each harness runs the same seven cases once in independent fresh sessions:

- five direct-routing cases, one for each primary ResearchFlow phase;
- two backward-routing cases that test artifact-first correction.

The first run therefore contains at most 14 scored invocations after successful harness preflight.

### 2.3 Shared semantics, native execution

The two harnesses consume one shared case manifest, one shared scored-prompt suffix, and one shared deterministic judge. Each harness has its own thin adapter for capability discovery, plugin loading, session isolation, CLI invocation, and evidence capture.

Adapters must not duplicate case prompts, contain case-specific routing logic, or decide verdicts.

### 2.4 Non-goals

This work does not:

- alter `docs/workflow-contracts.md`;
- add a new primary phase or router surface;
- add expert-mode behavior;
- execute the selected phase during a scored case;
- measure repeated-run stability;
- run the three ambiguity/clarification cases in the first round;
- automatically modify routing behavior after a failure;
- automatically bump the release version;
- push to a remote repository;
- or treat a harness or environment failure as a routing failure.

## 3. Architecture

The acceptance pack has five layers.

### 3.1 Shared case manifest

A single machine-readable manifest defines the seven prompts and their executable scoring contract.

Recommended path:

```text
tests/harness-acceptance/cases.json
```

Each case must contain:

```json
{
  "case_id": "R-DIRECT-LIT",
  "kind": "direct",
  "prompt": "I need related work, the closest papers, and a defensible research gap. No Literature Map exists yet.",
  "expected_phase": "literature-discovery",
  "required_marker": "ResearchFlow phase:",
  "forbidden_patterns": [
    "(?m)^##\\s+(Methods|Results|Discussion)\\b",
    "(?im)^Here is (the|a) (revised|drafted) .+ section"
  ]
}
```

Field meanings:

- `case_id` — stable identifier used in directories and summaries;
- `kind` — `direct` or `backward`;
- `prompt` — complete user request including enough state to make one route correct;
- `expected_phase` — one of the five primary ResearchFlow phase IDs;
- `required_marker` — the exact marker prefix required at the beginning of the final response;
- `forbidden_patterns` — concrete regular expressions for observable downstream output that invalidates the routing-only task.

Abstract action labels such as `draft_manuscript_prose` are prohibited because the judge cannot evaluate them deterministically. Both adapters must read the same manifest and append the same scored-prompt suffix.

### 3.2 Shared scored-prompt suffix

Recommended path:

```text
tests/harness-acceptance/scored-prompt.txt
```

Every scored case appends this exact adapter-owned instruction after the manifest prompt:

```text
Before doing any research, writing, review, or packaging work, identify
the single ResearchFlow phase to enter first. Do not execute that phase.

Your response must begin with exactly one line in this format:
ResearchFlow phase: <phase-id>

After that line, give at most two sentences explaining the choice.
```

Adapters may append this suffix but must not alter the case's research-state description.

### 3.3 Harness-native adapters

Recommended paths:

```text
tests/harness-acceptance/adapters/claude.sh
tests/harness-acceptance/adapters/opencode.sh
```

Each adapter is responsible for:

- discovering supported CLI capabilities;
- recording the CLI version and fixed model configuration;
- establishing local-plugin loading from the current checkout;
- selecting one documented isolation profile;
- creating an independent session and case workspace;
- invoking the CLI non-interactively;
- enforcing the fixed timeout;
- capturing structured output, final response, stderr, and exit status;
- and reporting infrastructure status without judging route semantics.

The adapter output contract must be identical across harnesses so the shared judge does not branch on CLI-specific formats.

### 3.4 Shared deterministic judge

Recommended path:

```text
tests/harness-acceptance/judge.py
```

The judge reads one case definition and one normalized invocation artifact. It uses only exact marker parsing, regular expressions, structured metadata, hashes, and process status. It must not call an LLM.

The judge emits exactly one machine verdict:

- `pass`
- `fail`
- `indeterminate`
- `harness_error`

An additional `environment_contaminated` boolean records whether the adapter could not establish the required isolation boundary. A contaminated invocation may retain a diagnostic machine verdict, but it cannot count as acceptance evidence.

### 3.5 Evidence bundle and orchestration

Recommended layout:

```text
tests/harness-acceptance/
├── cases.json
├── scored-prompt.txt
├── judge.py
├── summarize.py
├── redact.py
├── run.sh
├── adapters/
│   ├── claude.sh
│   └── opencode.sh
├── fixtures/
└── results/
    └── <run-id>/
        ├── capabilities/
        │   ├── claude.json
        │   └── opencode.json
        ├── preflight/
        │   ├── claude.json
        │   └── opencode.json
        ├── environment.json
        ├── summary.json
        ├── summary.md
        ├── claude/
        │   └── <case-id>/
        │       ├── command.json
        │       ├── final-response.txt
        │       └── verdict.json
        └── opencode/
            └── <case-id>/
                ├── command.json
                ├── final-response.txt
                └── verdict.json
```

Raw JSON event streams and unredacted stderr remain in a local raw-artifact directory outside the committed result tree. Their hashes are recorded in `command.json` and `summary.md`.

A run ID must be stable and collision-safe. The orchestration command supplies an explicit UTC timestamp such as `2026-07-17T120000Z`; model output never determines run identity. An existing run directory must never be overwritten.

## 4. Core cases

### 4.1 Five direct-routing cases

| Case ID | Request state | Expected primary phase |
|---|---|---|
| `R-DIRECT-LIT` | User needs related work, closest papers, and a research gap; no Literature Map exists | `literature-discovery` |
| `R-DIRECT-STRUCT` | Literature and likely gap are supplied and stable; user needs paper type, contributions, and section logic | `paper-structuring` |
| `R-DIRECT-DRAFT` | Literature Map and Structure Brief are explicitly supplied and stable; user asks which phase should rewrite a Methods section | `paper-drafting` |
| `R-DIRECT-REVIEW` | A complete manuscript is supplied; user asks which phase should critique it and produce a revision order | `paper-review` |
| `R-DIRECT-PACK` | Review blockers are explicitly resolved; user asks which phase should package PDF, supplement, and artifact README | `artifact-packaging` |

Each prompt must state enough upstream readiness that the expected phase is unique. Direct cases must not accidentally omit an upstream artifact and thereby test backward routing instead.

### 4.2 Two backward-routing cases

| Case ID | Surface request | Declared missing state | Expected route |
|---|---|---|---|
| `R-BACK-INTRO` | Write the Introduction | No stable Literature Map or literature-backed gap | `literature-discovery` |
| `R-BACK-PDF` | Export a submission PDF | The manuscript has unresolved review blockers and no stable Review Packet | `paper-review` |

These cases operationalize the existing contract rule:

> Surface intent proposes a phase; artifact stability confirms it or routes earlier.

### 4.3 Routing-only boundary

The case prompt and scored suffix jointly require a routing decision without executing the selected phase. Tool use is disabled where the harness supports it. A response that begins drafting, reviewing, or packaging prose is evaluated against the case's concrete `forbidden_patterns`.

## 5. Deterministic verdict contract

### 5.1 Marker parsing

The first response line must match exactly:

```regex
\AResearchFlow phase: (literature-discovery|paper-structuring|paper-drafting|paper-review|artifact-packaging)\r?\n
```

The full response must contain exactly one line beginning with `ResearchFlow phase:`. The marker value is the sole source for `observed_phase`; explanatory references to other phases do not change it.

### 5.2 Pass

A case is `pass` only when all conditions hold:

1. the process exits successfully;
2. plugin-load proof is complete;
3. exactly one valid marker appears at the beginning of the response;
4. `observed_phase` equals `expected_phase`;
5. no case `forbidden_patterns` match the response;
6. the response remains within the routing-only output contract;
7. `environment_contaminated` is false.

Mentioning another phase in the explanation is allowed because route selection is determined only by the canonical marker. If the output contract cannot be parsed deterministically, the judge returns `indeterminate` rather than guessing.

### 5.3 Fail

A case is `fail` when the process and plugin proof succeed but:

- one valid marker selects a different primary phase;
- or one or more concrete forbidden patterns match downstream work in the response.

### 5.4 Indeterminate

A case is `indeterminate` when:

- the marker is missing;
- the marker occurs more than once, whether values agree or conflict;
- the marker contains an illegal phase ID;
- the marker does not begin the response;
- or the output cannot be parsed under the deterministic contract.

The judge must not call a model to resolve ambiguity.

### 5.5 Harness error

A case is `harness_error` when routing cannot be evaluated because of:

- CLI or plugin-load proof failure;
- authentication failure;
- timeout;
- non-zero process exit unrelated to a semantic route;
- missing required process artifact;
- or adapter/runtime failure.

Harness errors do not count as routing failures.

### 5.6 Environment contamination

`environment_contaminated` is orthogonal to the machine verdict. A contaminated invocation may be parsed for diagnostics, but it never counts toward `acceptance_passed`.

### 5.7 Manual notes

Human review may append a `manual_note` containing reviewer, UTC review timestamp, observation, and agreement with the machine verdict. A manual note must never overwrite the machine verdict, matched evidence, or artifact hash.

## 6. Fixed model and execution configuration

### 6.1 Explicit model requirement

Adapters must not silently use a default model.

Each run configuration supplies:

- Claude Code full model ID and explicit `--effort`;
- OpenCode `provider/model` and explicit `--variant` when the provider supports variants.

A requested model that is unavailable blocks that harness preflight.

### 6.2 Cross-harness model confound

If both harnesses cannot use the same underlying model, `environment.json` and `summary.json` must set:

```json
{
  "cross_harness_model_confound": true
}
```

The summary must then report each harness under its own fixed model. It must not attribute a difference to the harness alone.

### 6.3 Tool boundary

Claude scored runs use `--tools ""`. OpenCode scored runs must use an adapter-selected no-tool or deny-all configuration if supported and proven by capability probe. If OpenCode cannot disable tools deterministically, the prompt contract and forbidden patterns still apply, and the residual capability must be recorded. Unexpected tool execution causes `harness_error` or contamination according to whether the adapter can still guarantee a fresh and safe result.

## 7. Harness capability probes and isolation profiles

Each adapter writes `capabilities/<harness>.json` before preflight.

Required capability fields include:

```json
{
  "harness": "claude",
  "cli_version": "2.1.212",
  "noninteractive": true,
  "structured_output": true,
  "local_plugin_loading": true,
  "session_persistence_disable": true,
  "settings_isolation": true,
  "auth_preserving_full_isolation": false
}
```

### 7.1 Claude Code full-isolation profile

Use full isolation only when capability probe confirms that authentication is available through an API key or supported external provider without keychain access.

The preferred invocation profile is equivalent to:

```text
claude -p
--bare
--plugin-dir <researchflow-root>
--no-session-persistence
--tools ""
--output-format json
--model <full-model-id>
--effort <level>
```

Each case uses a new process, new UUID session ID if explicitly supplied, and isolated working directory. The adapter records whether `--bare` plus explicit `--plugin-dir` loads the plugin successfully in the installed CLI version.

### 7.2 Claude Code auth-preserving profile

When full isolation cannot authenticate, retain only the authentication-bearing HOME and use an auth-preserving profile equivalent to:

```text
claude -p
--plugin-dir <researchflow-root>
--no-session-persistence
--setting-sources ""
--tools ""
--output-format json
--model <full-model-id>
--effort <level>
```

The adapter must audit residual user skills, plugins, memory, hooks, project instructions, and policy settings. Authentication material and administrator policy may be allowlisted as residuals when they do not introduce another research router. Any unresolved extra research router or instruction source sets `environment_contaminated = true` and blocks acceptance credit.

### 7.3 OpenCode isolation profile

OpenCode uses:

```text
opencode run
--format json
--model <provider/model>
--variant <variant>
--dir <isolated-case-workspace>
<prompt>
```

Do not use `--pure`, because it disables the external ResearchFlow plugin under test.

Capability probe must determine whether this installed OpenCode version honors isolated HOME or XDG-style config, data, cache, and state directories. The supported variables and effective paths are recorded from `opencode debug paths`; the spec does not assume names that have not been observed.

Each isolated case workspace contains a minimal `opencode.json` equivalent to:

```json
{
  "plugin": ["/absolute/path/to/reference/researchflow"]
}
```

Before scored execution, the adapter captures redacted `opencode debug config`, `opencode debug paths`, and `opencode debug skill` output. Resolved configuration must satisfy an allowlist:

- plugin source resolves to the current ResearchFlow checkout;
- ResearchFlow skills path is registered;
- no additional plugin or research router is active;
- provider/auth configuration may remain but is never serialized with secret values.

Unknown instruction sources or extra research routers set `environment_contaminated = true` and block scored acceptance.

## 8. Joint plugin-load proof and preflight

A canary response alone cannot prove plugin loading because an ordinary model could follow the canary instruction. Plugin-load proof therefore requires joint evidence.

### 8.1 Required joint evidence

For each harness, preflight must establish all of:

1. the current checkout's plugin or marketplace manifest validates;
2. the adapter's resolved plugin source points to the current checkout;
3. the ResearchFlow inventory contains `using-researchflow` and all five primary phase skills;
4. a real non-interactive probe under the same isolation profile returns `RESEARCHFLOW_BOOTSTRAP_ACTIVE`;
5. the probe uses the same model family, plugin source, settings isolation, and tool boundary as scored cases.

For Claude Code, manifest validation uses `claude plugin validate <researchflow-root>`, while explicit `--plugin-dir` command metadata, checkout SHA, static skill inventory, and the probe establish the remaining proof.

For OpenCode, redacted `debug config`, `debug paths`, and `debug skill` outputs establish the resolved source and inventory before the real `opencode run` probe.

### 8.2 Canary prompt

The preflight probe appends:

```text
If the ResearchFlow bootstrap is active, output exactly
RESEARCHFLOW_BOOTSTRAP_ACTIVE before anything else.
```

Canary success without the other joint evidence does not pass preflight.

### 8.3 Other preflight gates

Preflight must also verify:

- CLI discovery and version capture;
- non-interactive execution;
- structured output parsing;
- independent case workspace creation;
- timeout enforcement;
- output capture;
- model availability;
- no-session-reuse behavior;
- and absence of authentication leakage in captured output.

If any hard gate fails, the harness receives overall status `blocked`. The runner must not generate seven placeholder verdicts that imply cases were attempted.

## 9. Execution order and retry policy

The fixed first-run order is:

1. capability probes for both installed harnesses;
2. synthetic manifest, judge, summary, overwrite, and redaction tests;
3. Claude Code preflight;
4. Claude Code cases in manifest order;
5. Claude Code artifact-completeness check;
6. OpenCode preflight;
7. OpenCode cases in the same manifest order;
8. cross-harness summary generation and packaging gate.

A Claude Code semantic `fail` or `indeterminate` does not block OpenCode. A harness-level infrastructure blocker stops only that harness.

Each case has a fixed timeout recorded in `command.json`. The first run performs no automatic retry.

Later retry rules:

- infrastructure fixes may produce `rerun-1`, `rerun-2`, and so on;
- semantic failures are not automatically retried before analysis;
- reruns must never overwrite the original run directory;
- and summaries must identify which run is original and which is a rerun.

## 10. Evidence retention, auditability, and redaction

### 10.1 Required committed artifacts

Commit:

- `cases.json`;
- `scored-prompt.txt`;
- adapters, judge, summarizer, redactor, orchestration script, and synthetic fixtures;
- redacted capability and preflight records;
- redacted `environment.json`;
- `final-response.txt`, `command.json`, and `verdict.json` for every attempted case;
- `summary.json`;
- and `summary.md`.

If a harness is blocked at preflight, commit its redacted capability/preflight record and the summary explaining that no scored invocations were generated.

### 10.2 Minimum reviewable response evidence

`final-response.txt` contains only the redacted final assistant response, not the complete event stream. The routing-only prompt and disabled-tool profile keep this artifact small and independently reviewable.

Each `verdict.json` includes at least:

```json
{
  "case_id": "R-BACK-PDF",
  "verdict": "pass",
  "observed_phase": "paper-review",
  "marker_count": 1,
  "matched_evidence": {
    "text": "ResearchFlow phase: paper-review",
    "line": 1,
    "sha256": "<sha256-of-final-response>"
  },
  "forbidden_pattern_matches": [],
  "environment_contaminated": false,
  "manual_note": null
}
```

A reviewer can reproduce the marker and forbidden-pattern decision from the committed final response without access to local session state.

### 10.3 Reconstructed command metadata

`command.json` must be constructed from an allowlisted schema rather than dumping the shell environment. It records only:

- harness and CLI version;
- fixed model, effort, or variant;
- timeout;
- repo commit SHA;
- repo-relative plugin source identifier;
- isolation profile and residual categories;
- UTC start and finish timestamps;
- exit code;
- and raw-artifact hashes.

It must not contain tokens, raw environment variables, credentials, user-home paths, or unredacted absolute plugin paths.

### 10.4 Raw event streams

Complete JSON event streams, raw stderr, and temporary homes/config/data/state remain local. `summary.md` records a relative raw-artifact ID, SHA-256, manual-review status, and reason for non-commitment. Original raw artifacts must not be overwritten by reruns.

### 10.5 Redaction packaging gate

Before staging evidence, a deterministic scanner rejects:

- user-home paths;
- disallowed absolute paths;
- common API key or token shapes;
- `Authorization`, `Bearer`, credential, or secret-bearing fields;
- and unrelated private project instruction fragments.

A scanner hit fails packaging. The system must not silently commit a partially redacted artifact.

## 11. Summary schema and state semantics

`summary.json` must be deterministically reconstructable from capability, preflight, environment, command, response, and verdict artifacts.

It includes three separate state fields:

```json
{
  "run_id": "2026-07-17T120000Z",
  "run_kind": "original",
  "case_count_per_harness": 7,
  "cross_harness_model_confound": false,
  "harnesses": {
    "claude": {
      "preflight": "pass",
      "model": "<full-model-id>",
      "counts": {
        "pass": 7,
        "fail": 0,
        "indeterminate": 0,
        "harness_error": 0,
        "environment_contaminated": 0,
        "unattempted": 0
      }
    },
    "opencode": {
      "preflight": "pass",
      "model": "<provider/model>",
      "counts": {
        "pass": 7,
        "fail": 0,
        "indeterminate": 0,
        "harness_error": 0,
        "environment_contaminated": 0,
        "unattempted": 0
      }
    }
  },
  "run_complete": true,
  "acceptance_passed": true,
  "release_candidate_eligible": true
}
```

Definitions:

- `run_complete` — both harnesses have recorded preflight outcomes, every expected case has a verdict or is explicitly `unattempted` due to a documented harness blocker, and no artifact disappears silently;
- `acceptance_passed` — both preflights pass, all 14 cases pass, and no invocation is contaminated;
- `release_candidate_eligible` — `run_complete && acceptance_passed` and all evidence/redaction checks pass.

A blocked harness may still produce a complete run record, but `acceptance_passed` and `release_candidate_eligible` remain false. Reruns must not modify the original run's state fields.

`summary.md` must contain:

- environment, model, isolation, and plugin-source summary;
- a 14-row accounting table when both preflights pass, or explicit unattempted rows when blocked;
- verdict and contamination counts;
- cross-harness model confound disclosure;
- evidence links and raw-artifact hashes;
- deviations and manual notes;
- packaging/redaction status;
- and the exact statement: “This is single-run fresh-session acceptance evidence, not a stability or repeated-run estimate.”

## 12. Failure handling

### 12.1 Semantic failure or indeterminate result

When a scored case is `fail` or `indeterminate`:

- preserve all evidence;
- finish the remaining cases unless the harness becomes unusable;
- do not mutate the router during the run;
- and produce a separate analysis before proposing a router or judge change.

### 12.2 Harness error

When a case is `harness_error`:

- preserve the failed command metadata, raw hash, and redacted output;
- continue only if the adapter can safely establish a fresh next session;
- otherwise stop that harness and mark later cases `unattempted` in the summary.

### 12.3 Environment contamination

A contaminated invocation may retain a machine route verdict for diagnostics, but it does not count toward acceptance. Fix isolation and create a new rerun directory.

### 12.4 No silent exclusions

Every expected invocation must appear as one of:

- a verdict artifact;
- an explicit `unattempted` case caused by a documented harness blocker;
- or a later rerun linked to its original case.

The summary generator must fail on missing or duplicate case artifacts.

## 13. Pre-scored hard gate and validation matrix

No scored case may start until all hard gates for that harness pass:

- capability probe completed;
- one supported authentication-preserving isolation profile selected;
- joint plugin-load proof passed;
- model and effort/variant fixed explicitly;
- seven-case manifest validated;
- scored-prompt suffix hash recorded;
- all synthetic judge and summary fixtures passed;
- target run ID does not exist;
- redaction scanner fixtures passed;
- timeout enforcement available;
- evidence directory is writable;
- and raw/committed artifact boundaries are configured.

The synthetic matrix includes at least:

| Fixture | Expected result |
|---|---|
| one correct marker | `pass` |
| one wrong marker | `fail` |
| marker missing | `indeterminate` |
| duplicate matching markers | `indeterminate` |
| duplicate conflicting markers | `indeterminate` |
| illegal phase ID | `indeterminate` |
| correct marker plus forbidden pattern | `fail` |
| correct marker plus explanatory mention of another phase | `pass` |
| non-zero exit | `harness_error` |
| timeout | `harness_error` |
| incomplete plugin-load proof | `harness_error` |
| contaminated environment | excluded from acceptance |
| missing case artifact | summary build fails |
| duplicate case artifact | summary build fails |
| existing original run directory | overwrite refused |
| credential or home-path redaction hit | packaging fails |

Any hard-gate failure stops that harness and produces blocked preflight evidence. The runner must not continue with a best-effort scored command.

## 14. Completion and interpretation

The first run is operationally complete when:

- both capability and preflight outcomes are recorded;
- every attempted case has allowlisted command metadata, final response, process status, raw hashes, and machine verdict;
- every expected case is accounted for as attempted or explicitly unattempted;
- committed evidence passes the redaction gate;
- `summary.json` reconstructs from lower-level artifacts;
- and `summary.md` accurately reports the bounded evidence.

Interpretation rules:

- **14/14 pass with no contamination:** eligible for a separate `0.2.0` release-candidate discussion;
- **any fail or indeterminate:** analyze router and judge behavior before release discussion;
- **only harness errors:** repair adapter or installation infrastructure before changing router semantics;
- **any environment contamination:** the affected invocation is not acceptance evidence and requires a separately identified rerun;
- **cross-harness model confound:** report harness results separately and do not attribute differences to the harness alone.

The acceptance run must not be described as reliability, consistency, or repeated-run stability evidence.

## 15. Post-run boundary and success criteria

After evidence exists, implementation may update only:

- the harness acceptance result summary;
- `docs/handover/researchwork-plugin-handover.md` verified state and remaining limitations;
- and installation instructions proven inaccurate by capability probe or preflight.

Do not automatically:

- change the five-phase contract;
- add router features;
- add the three clarification cases;
- run three-trial stability tests;
- bump versions;
- publish or push;
- or treat release-candidate eligibility as release approval.

The design is implemented correctly when:

- Claude Code and OpenCode use the same seven-case manifest and scored suffix;
- each harness uses a native real-CLI adapter and documented isolation profile;
- model configuration is explicit and model confounds are disclosed;
- plugin loading is supported by joint source, inventory, and canary evidence;
- each scored invocation is a fresh non-interactive routing-only session;
- the deterministic judge makes no LLM calls;
- all expected invocations are accounted for after preflight;
- verdict, contamination, run completion, acceptance, and release eligibility remain distinct;
- committed final responses make verdicts independently reviewable;
- original evidence is never overwritten by reruns;
- packaging fails on redaction leaks;
- the summary is deterministically reconstructable;
- and no release, version bump, or push occurs without a separate user decision.
