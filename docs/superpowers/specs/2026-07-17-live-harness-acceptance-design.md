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

After that line, you may give at most two non-empty single-line explanations.
Do not use headings, lists, blockquotes, or code fences.
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

Each adapter normalizes its native event stream into one `invocation.json`. Harness-specific raw event formats must not escape the adapter boundary.

The required invocation schema is:

```json
{
  "schema_version": 1,
  "run_id": "2026-07-17T120000Z",
  "case_id": "R-BACK-PDF",
  "harness": "claude",
  "cli_version": "2.1.212",
  "model_request": {
    "harness_value": "fable",
    "proxy_kind": "litellm",
    "endpoint_identity_sha256": "<sha256>",
    "requested_route": "fable"
  },
  "model_resolution": {
    "upstream_provider": "openai",
    "backing_model_id": "gpt-5.5",
    "proof_source": "litellm-response-metadata",
    "proof_sha256": "<sha256>"
  },
  "resolved_model_identity": "openai/gpt-5.5",
  "model_identity_verified": true,
  "effort_or_variant": "high",
  "timeout_seconds": 120,
  "started_at_utc": "2026-07-17T120000Z",
  "finished_at_utc": "2026-07-17T120015Z",
  "exit_code": 0,
  "timed_out": false,
  "repo_commit_sha": "<full-sha>",
  "plugin_source_id": "researchflow-checkout",
  "plugin_proof_passed": true,
  "plugin_proof_strength": "best_available_source_plus_canary",
  "isolation_profile": "auth-preserving-direct-plugin-dir",
  "environment_contaminated": false,
  "residual_categories": ["auth", "admin-policy"],
  "tool_execution": {
    "detected": false,
    "attempted_tools": [],
    "side_effect_status": "none",
    "audit_complete": true
  },
  "final_response_path": "final-response.txt",
  "final_response_sha256": "<sha256>",
  "raw_artifact_hashes": {
    "events": "<sha256>",
    "stderr": "<sha256>"
  }
}
```

`endpoint_identity_sha256` is computed from a normalized endpoint identity, but the full `base_url` must never enter committed evidence. API keys, proxy credentials, authentication headers, and raw environment values are prohibited.

### 3.4 Shared deterministic judge

Recommended path:

```text
tests/harness-acceptance/judge.py
```

The judge reads only `cases.json`, `invocation.json`, and `final-response.txt`. It uses exact marker parsing, regular expressions, normalized metadata, hashes, and process status. It must not read native Claude/OpenCode event formats or call an LLM.

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
├── model-identities.json
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
        │   ├── claude-model-proof.json
        │   ├── opencode.json
        │   └── opencode-model-proof.json
        ├── environment.json
        ├── summary.json
        ├── summary.md
        ├── claude/
        │   └── <case-id>/
        │       ├── invocation.json
        │       ├── command.json
        │       ├── final-response.txt
        │       └── verdict.json
        └── opencode/
            └── <case-id>/
                ├── invocation.json
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
\AResearchFlow phase: (literature-discovery|paper-structuring|paper-drafting|paper-review|artifact-packaging)(?:\r?\n|\Z)
```

The full response must contain exactly one line beginning with `ResearchFlow phase:`. The marker value is the sole source for `observed_phase`; explanatory references to other phases do not change it.

After removing trailing blank lines, the complete routing-only structure is mechanical:

1. the response contains one to three non-empty lines total;
2. line 1 is the unique valid marker;
3. lines 2 and 3, when present, are plain single-line explanations;
4. explanation lines must not begin with `#`, `- `, `* `, a numeric-list marker such as `1. `, or `>`;
5. explanation lines must not contain a code fence or another phase marker;
6. internal blank lines, more than three non-empty lines, or any prohibited explanation form make the response structurally invalid.

A structurally invalid response is `indeterminate` unless a concrete case `forbidden_patterns` match, in which case it is `fail`.

### 5.2 Pass

A case is `pass` only when all conditions hold:

1. the process exits successfully;
2. plugin-load proof is complete;
3. exactly one valid marker appears at the beginning of the response;
4. `observed_phase` equals `expected_phase`;
5. no case `forbidden_patterns` match the response;
6. the response remains within the routing-only output contract.

Mentioning another phase in the explanation is allowed because route selection is determined only by the canonical marker. If the output contract cannot be parsed deterministically, the judge returns `indeterminate` rather than guessing.

Contamination does not alter this diagnostic verdict. A contaminated invocation may still have verdict `pass`, `fail`, or `indeterminate`, but it is excluded from `acceptance_passed` by the separate contamination overlay.

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

## 6. LiteLLM/OpenAI model identity and execution configuration

### 6.1 Environment model topology

In this environment, Claude Code is a harness, LiteLLM is the proxy layer, and the actual inference model is an OpenAI backing model reached through a configured `base_url`. A Claude Code alias such as `fable` and an OpenCode `provider/model` request do not by themselves prove the upstream model.

Adapters must not silently use a default model. Each invocation records both the harness request and verified resolution chain in `invocation.json`:

- `model_request.harness_value` — the value passed to the harness;
- `model_request.proxy_kind` — `litellm`;
- `model_request.endpoint_identity_sha256` — hash of normalized endpoint identity, never the raw `base_url`;
- `model_request.requested_route` — LiteLLM alias or deployment route;
- `model_resolution.upstream_provider` — must be `openai` for this run;
- `model_resolution.backing_model_id` — actual OpenAI model ID;
- `model_resolution.proof_source` and `proof_sha256` — source and local raw-proof hash;
- `resolved_model_identity` — canonical value such as `openai/gpt-5.5`;
- `model_identity_verified` — whether resolution proof passed.

Allowed backing-model proof, strongest first:

1. LiteLLM response metadata explicitly naming the actual model;
2. redacted LiteLLM proxy log or callback metadata;
3. a verifiable deployment-to-model configuration snapshot whose raw form stays local while committed evidence records only allowlisted fields and SHA-256.

If the backing model cannot be verified, `resolved_model_identity` is `null`, `model_identity_verified` is false, and the harness preflight is blocked.

### 6.2 Committed model identity allowlist

Recommended path:

```text
tests/harness-acceptance/model-identities.json
```

The file defines only canonical identities and non-proving aliases:

```json
{
  "allowed_provider": "openai",
  "canonical_models": {
    "gpt-5.5": "openai/gpt-5.5"
  },
  "harness_aliases": {
    "fable": {
      "may_route_via": "litellm",
      "does_not_prove_backing_model": true
    }
  }
}
```

The allowlist must not infer the backing model from a harness alias. Only verified response/proxy/config proof may populate `resolved_model_identity`.

### 6.3 Hard model-alignment gate

The first cross-harness acceptance run requires the same actual OpenAI backing model in both harnesses. Before any scored case starts, both preflights must produce:

- non-null `resolved_model_identity`;
- `model_identity_verified = true`;
- `model_resolution.upstream_provider = "openai"`;
- and exact equality of `resolved_model_identity`.

If any condition fails, no scored case runs. The complete run record sets `model_alignment.blocked = true` and `acceptance_passed = false`.

Only an aligned run may set `cross_harness_model_confound = false`. Because equality is mechanically reconstructed from verified canonical identities, it is not an analyst judgment.

### 6.4 Committed model-proof artifacts

Each harness preflight writes and commits `preflight/<harness>-model-proof.json`:

```json
{
  "schema_version": 1,
  "harness": "claude",
  "proxy_kind": "litellm",
  "endpoint_identity_sha256": "<sha256>",
  "requested_route": "fable",
  "upstream_provider": "openai",
  "backing_model_id": "gpt-5.5",
  "resolved_model_identity": "openai/gpt-5.5",
  "proof_method": "litellm-response-metadata",
  "proof_sha256": "<sha256>",
  "verified": true,
  "redaction_passed": true
}
```

This committed artifact must contain enough allowlisted fields to reconstruct model alignment without the local raw-artifact store. If raw proof cannot be transformed into a redacted committed proof with `verified = true`, model alignment is blocked and no scored case runs.

### 6.5 Tool boundary and mechanical classification

Claude scored runs use `--tools ""`. OpenCode scored runs use a no-tool or deny-all profile only when capability probe proves one; otherwise the residual capability is recorded.

Every invocation records:

```json
{
  "tool_execution": {
    "detected": false,
    "attempted_tools": [],
    "side_effect_status": "none",
    "audit_complete": true
  }
}
```

`side_effect_status` is one of `none`, `blocked`, `executed`, or `unknown`.

Classification is fixed:

- no tool event: `none`, no contamination from tools;
- rejected tool call with no side effect and complete event stream/final response: `blocked`, invocation contaminated but verdict may be retained diagnostically;
- any successfully executed tool: `executed`, always `harness_error` regardless of apparent side-effect scope;
- incomplete tool event, unknown success, incomplete final response, or lost fresh-session correspondence: `unknown`, always `harness_error`.

No adapter may classify a successful tool execution as merely audited contamination. The two adapters must implement this same mapping.
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

### 7.1 Claude Code capability-proved load branches

Claude adapter must probe and select one verified local-plugin path. No single command surface is assumed across CLI builds.

#### Branch A: direct plugin directory

Use only when capability probe confirms that the installed CLI supports `--plugin-dir` and that a non-interactive probe loads the current checkout through it.

The invocation profile is equivalent to:

```text
claude -p
--plugin-dir <researchflow-root>
--no-session-persistence
--tools ""
--output-format json
--model <harness-model-value>
--effort <level>
```

The adapter must always validate `.claude-plugin/plugin.json`, the marketplace manifest, and required skill files against committed schemas. `claude plugin validate <researchflow-root>` is optional enhancement evidence used only when capability probe confirms that the installed CLI exposes and successfully executes it; absence of that subcommand does not block an otherwise proved load branch.

#### Branch B: local marketplace install

Use only when capability probe confirms a supported local marketplace registration and plugin installation path. The adapter must prove that the resolved installed plugin points to the current checkout or a deterministic artifact built from its recorded commit SHA, then invoke the real non-interactive session through that installed plugin.

#### Branch C: unsupported

If neither load path can be proved, Claude preflight is `blocked`. The adapter must not guess another command or begin scored cases.

### 7.2 Claude Code authentication/isolation variants

Within a proved load branch, select one authentication-compatible isolation variant.

**Full isolation** is allowed only when API-key or supported external-provider authentication succeeds without keychain access. It may use `--bare`, an isolated working directory, `--no-session-persistence`, disabled tools, and an explicitly fixed model.

**Auth-preserving isolation** retains only the authentication-bearing HOME and uses supported settings-isolation flags, disabled tools, an isolated working directory, no session persistence, and an explicitly fixed model.

The adapter must audit residual user skills, plugins, memory, hooks, project instructions, and policy settings. Authentication material and administrator policy may be allowlisted when they do not introduce another research router. Any unresolved router or instruction source sets `environment_contaminated = true` and blocks acceptance credit.

### 7.3 Claude proof-strength disclosure

When Claude lacks a runtime resolved-source or runtime skill-inventory surface equivalent to OpenCode, record:

```json
{
  "plugin_proof_strength": "best_available_source_plus_canary",
  "plugin_load_path": "direct-plugin-dir"
}
```

The minimum evidence is adapter-side schema validation of the plugin/marketplace manifests and required skill files, explicit load-source command metadata, checkout SHA, static inventory of the repo's `using-researchflow` and five primary phase skills, and a canary probe under the scored isolation profile. CLI-native metadata validation, when available, strengthens but does not define the minimum proof.

OpenCode may record the stronger value `resolved_runtime_source_inventory_canary` when its resolved config and skill inventory are available. Summary must disclose this proof-strength asymmetry and must not imply equivalent runtime proof.

### 7.4 OpenCode capability-proved source branch and proof strength

OpenCode capability probe checks `debug config`, `debug paths`, and `debug skill` independently. No specific debug subcommand is assumed across builds.

Under the revised contract, capability pass records `selected_proof_branch = "workspace-repo-canary-proof"` when repo static proof, workspace proof, and canary success hold. `plugin_proof_strength` then discloses how much supporting debug evidence was actually observed.

**Strong runtime proof** uses all three supported debug surfaces to record resolved plugin source, effective paths, runtime skill inventory, and canary. It records `plugin_proof_strength = "resolved_runtime_source_inventory_canary"`.

**Fallback workspace proof** is used when capability passes but one or more debug surfaces are unavailable or inconclusive. It requires the isolated workspace's minimal `opencode.json`, plugin path to the current checkout, checkout SHA, adapter-side validation of `.opencode/plugins/researchflow.js`, static ResearchFlow skill inventory, all available debug evidence, and a real `opencode run` canary. It records `plugin_proof_strength = "workspace_config_static_inventory_canary"`.

If repo proof, workspace proof, or canary evidence is missing, OpenCode preflight is `blocked`.

### 7.5 OpenCode isolation profile

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

Before scored execution, the adapter captures every debug surface proved available. Strong proof captures redacted `opencode debug config`, `opencode debug paths`, and `opencode debug skill`; fallback proof captures available debug output plus workspace/static evidence. The resulting proof bundle must satisfy an allowlist:

- plugin source resolves to the current ResearchFlow checkout;
- ResearchFlow skills path is registered;
- no additional plugin or research router is active;
- provider/auth configuration may remain but is never serialized with secret values.

Unknown instruction sources or extra research routers set `environment_contaminated = true` and block scored acceptance.

## 8. Joint plugin-load proof and preflight

A canary response alone cannot prove plugin loading because an ordinary model could follow the canary instruction. Plugin-load proof therefore requires joint evidence.

### 8.1 Required joint evidence

For each harness, preflight must establish all of:

1. adapter-side schema validation of the current checkout's plugin/marketplace metadata and required skill files, plus optional CLI-native validation when capability probe proves it available;
2. the selected capability-proved source branch points to the current checkout or its deterministic build artifact;
3. the ResearchFlow inventory contains `using-researchflow` and all five primary phase skills, using runtime inventory where available and recorded static checkout inventory otherwise;
4. a real non-interactive probe under the same isolation profile returns `RESEARCHFLOW_BOOTSTRAP_ACTIVE`;
5. the probe uses the same verified OpenAI backing model, plugin source, settings isolation, and tool boundary as scored cases.

For Claude Code, proof follows the selected direct-plugin-dir or local-marketplace branch. If no runtime resolved-source/inventory surface exists, the recorded proof strength is `best_available_source_plus_canary`, not equivalent to OpenCode runtime proof.

For OpenCode, capability selection uses the revised `workspace-repo-canary-proof` branch, while `plugin_proof_strength` distinguishes strong runtime proof from fallback workspace proof. Missing debug surfaces reduce proof strength but do not block a complete fallback bundle.

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
- verified LiteLLM/OpenAI backing-model identity and cross-harness model alignment;
- no-session-reuse behavior;
- and absence of authentication leakage in captured output.

If any hard gate fails, the harness receives overall status `blocked`. The runner must not generate seven placeholder verdicts that imply cases were attempted.

## 9. Execution order and retry policy

The fixed first-run order is:

1. capability probes for both installed harnesses;
2. synthetic manifest, judge, summary, overwrite, and redaction tests;
3. Claude Code preflight, including verified OpenAI backing-model identity;
4. OpenCode preflight, including verified OpenAI backing-model identity;
5. hard model-alignment comparison;
6. Claude Code cases in manifest order;
7. Claude Code artifact-completeness check;
8. OpenCode cases in the same manifest order;
9. OpenCode artifact-completeness check;
10. cross-harness summary generation and packaging gate.

No scored case starts unless both preflights and the model-alignment hard gate pass. After scored execution begins, a Claude Code semantic `fail` or `indeterminate` does not block OpenCode. A runtime harness failure stops only the affected harness and explicitly accounts for remaining cases as `unattempted`.

Each case has a fixed timeout recorded in both `invocation.json` and the review-facing `command.json`. The first run performs no automatic retry.

Later retry rules:

- infrastructure fixes may produce `rerun-1`, `rerun-2`, and so on;
- semantic failures are not automatically retried before analysis;
- reruns must never overwrite the original run directory;
- and summaries must identify which run is original and which is a rerun.

## 10. Evidence retention, auditability, and redaction

### 10.1 Required committed artifacts

Commit:

- `cases.json`;
- `scored-prompt.txt` and `model-identities.json`;
- adapters, judge, summarizer, redactor, orchestration script, and synthetic fixtures;
- redacted capability and preflight records, including both committed `<harness>-model-proof.json` artifacts;
- redacted `environment.json`;
- `invocation.json`, `final-response.txt`, `command.json`, and `verdict.json` for every attempted case;
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

### 10.3 Normalized invocation and reconstructed command metadata

`invocation.json` follows the shared schema in Section 3.3 and is the only process/model/plugin/isolation record read by the judge. Adapter-specific fields are prohibited.

`command.json` is a review-facing, allowlisted reconstruction of the invocation command rather than a shell/environment dump. It records only:

- harness and CLI version;
- harness model request, verified canonical OpenAI identity, and effort/variant;
- timeout;
- repo commit SHA;
- repo-relative plugin source identifier and proof strength;
- isolation profile and residual categories;
- UTC start and finish timestamps;
- exit code and tool-execution classification;
- and raw-artifact hashes.

Neither file may contain tokens, raw environment variables, credentials, full `base_url`, user-home paths, or unredacted absolute plugin paths.

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

`summary.json` must be deterministically reconstructable solely from committed capability, preflight, per-harness model-proof, environment, invocation, response, verdict/unattempted-accounting artifacts, plus the committed model-identity allowlist. Local raw event streams are optional audit aids and must not be required for reconstruction.

Verdicts form a mutually exclusive partition. Contamination is a separate overlay and must never be included in verdict totals.

```json
{
  "run_id": "2026-07-17T120000Z",
  "run_kind": "original",
  "case_count_per_harness": 7,
  "cross_harness_model_confound": false,
  "model_alignment": {
    "required": true,
    "aligned": true,
    "canonical_identity": "openai/gpt-5.5",
    "blocked": false
  },
  "harnesses": {
    "claude": {
      "preflight": "pass",
      "plugin_proof_strength": "best_available_source_plus_canary",
      "resolved_model_identity": "openai/gpt-5.5",
      "verdict_counts": {
        "pass": 7,
        "fail": 0,
        "indeterminate": 0,
        "harness_error": 0,
        "unattempted": 0
      },
      "contamination": {
        "contaminated_invocations": 0,
        "case_ids": []
      }
    },
    "opencode": {
      "preflight": "pass",
      "plugin_proof_strength": "resolved_runtime_source_inventory_canary",
      "resolved_model_identity": "openai/gpt-5.5",
      "verdict_counts": {
        "pass": 7,
        "fail": 0,
        "indeterminate": 0,
        "harness_error": 0,
        "unattempted": 0
      },
      "contamination": {
        "contaminated_invocations": 0,
        "case_ids": []
      }
    }
  },
  "verdict_counts_valid": true,
  "run_complete": true,
  "acceptance_passed": true,
  "release_candidate_eligible": true
}
```

Mechanical rules:

- for each harness, `pass + fail + indeterminate + harness_error + unattempted = 7`;
- `contaminated_invocations` is an overlay count and may overlap any diagnostic verdict without changing the partition;
- `model_alignment.aligned` is true only when both verified `resolved_model_identity` values are non-null, provider `openai`, and exactly equal;
- any unverified/missing/different identity sets `model_alignment.blocked = true`, `cross_harness_model_confound = true`, and prevents scored execution;
- `verdict_counts_valid` is true only when both harness partitions equal seven and every case ID appears exactly once;
- `run_complete` means both preflights have recorded outcomes, every expected case has a verdict or explicit `unattempted` accounting, and no artifact disappears silently;
- `acceptance_passed` means both preflights pass, model alignment passes, all 14 cases pass, and both contamination overlays are zero;
- `release_candidate_eligible` means `run_complete && acceptance_passed` and all evidence/redaction checks pass.

A blocked harness may still produce a complete run record, but `acceptance_passed` and `release_candidate_eligible` remain false. Reruns must not modify the original run's state fields.

Every original run contains exactly 14 case-accounting rows, even when no scored invocation occurs. An unattempted row has:

```json
{
  "case_id": "R-DIRECT-LIT",
  "status": "unattempted",
  "reason_code": "model_alignment_blocked"
}
```

Allowed `reason_code` values are:

- `claude_preflight_blocked`
- `opencode_preflight_blocked`
- `model_alignment_blocked`
- `global_hard_gate_blocked`
- `runtime_harness_stopped`

If both preflights pass but model alignment fails, all 14 rows use `model_alignment_blocked`. If one preflight blocks before the global same-model gate, that harness's seven rows use its harness-specific preflight code and the other seven use `global_hard_gate_blocked`. A runtime stop uses verdicts for completed cases and `runtime_harness_stopped` for the affected harness's remaining cases.

`summary.md` must contain:

- environment, verified OpenAI backing model, isolation, and plugin-source/proof-strength summary;
- exactly 14 case-accounting rows, using verdict rows for attempted cases and explicit reason-coded unattempted rows for every no-score case;
- verdict partitions and separate contamination overlays;
- model alignment outcome, both committed model-proof links, and any confound/block disclosure;
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
- one supported authentication-compatible isolation profile selected and the same profile ID recorded in capability, preflight, and invocation artifacts;
- joint plugin-load proof passed;
- both harness model requests resolve through LiteLLM to the same verified OpenAI backing model;
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
| more than two explanation lines | `indeterminate` |
| heading, list, blockquote, or code fence in explanation | `indeterminate` |
| non-zero exit | `harness_error` |
| timeout | `harness_error` |
| incomplete plugin-load proof | `harness_error` |
| unverified or misaligned OpenAI backing model | preflight blocked; all cases `unattempted` |
| tool call blocked with complete event/response audit | diagnostic verdict retained; contaminated |
| any tool successfully executed | `harness_error` |
| tool result incomplete or success unknown | `harness_error` |
| contaminated environment | excluded from acceptance |
| missing case artifact | summary build fails |
| duplicate case artifact | summary build fails |
| existing original run directory | overwrite refused |
| credential or home-path redaction hit | packaging fails |

Any hard-gate failure stops that harness and produces blocked preflight evidence. The runner must not continue with a best-effort scored command.

## 14. Completion and interpretation

The first run is operationally complete when:

- both capability and preflight outcomes are recorded;
- every attempted case has normalized `invocation.json`, allowlisted command metadata, final response, process status, raw hashes, and machine verdict;
- every expected case is accounted for as attempted or explicitly unattempted;
- committed evidence passes the redaction gate;
- `summary.json` reconstructs from lower-level artifacts;
- and `summary.md` accurately reports the bounded evidence.

Interpretation rules:

- **14/14 pass with no contamination and verified identical OpenAI backing model:** eligible for a separate `0.2.0` release-candidate discussion;
- **model alignment blocked:** run no scored cases; fix LiteLLM route proof or model availability before continuing;
- **any fail or indeterminate:** analyze router and judge behavior before release discussion;
- **only harness errors:** repair adapter or installation infrastructure before changing router semantics;
- **any environment contamination:** the affected invocation is not acceptance evidence and requires a separately identified rerun.

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
- each harness uses a native real-CLI adapter and capability-proved isolation/load profile;
- both harness requests resolve through LiteLLM to the same verified OpenAI backing model before any scored case;
- plugin loading is supported by source, inventory, and canary evidence with proof-strength asymmetry disclosed;
- both adapters emit the same `invocation.json` schema and native events remain behind the adapter boundary;
- each scored invocation is a fresh non-interactive routing-only session;
- the deterministic judge makes no LLM calls and applies only line-level output rules;
- all expected invocations are accounted for after preflight;
- verdict partitions, contamination overlays, model alignment, run completion, acceptance, and release eligibility remain distinct;
- committed final responses make verdicts independently reviewable;
- original evidence is never overwritten by reruns;
- packaging fails on redaction leaks;
- the summary is deterministically reconstructable from committed schemas and allowlists;
- and no release, version bump, or push occurs without a separate user decision.
