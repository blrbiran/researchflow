# ResearchFlow Live Harness Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, and execute a bounded live-CLI acceptance pack that runs the same seven routing-only cases once in Claude Code and OpenCode, but only after deterministic synthetic, isolation, plugin-proof, redaction, and same-OpenAI-model gates pass.

**Architecture:** Python standard-library modules own shared schemas, judging, redaction, summary reconstruction, and orchestration; thin Bash adapters own harness-native capability probing and CLI invocation. Both adapters normalize into the same `invocation.json`, and the judge reads only the shared manifest, normalized invocation, and final response. Live evidence is generated only after all local fixtures and both preflights pass.

**Tech Stack:** Python 3 standard library, Bash, JSON, Claude Code CLI, OpenCode CLI, LiteLLM proxy metadata, existing ResearchFlow shell test runner

## Global Constraints

- Work only in the nested `reference/researchflow` repository.
- Do not modify `skills/using-researchflow/SKILL.md`, `docs/workflow-contracts.md`, or any router behavior.
- Use exactly seven shared cases: five direct routes and two backward routes.
- Run each case at most once per harness in the original run; do not add automatic retries.
- Every scored response must begin with exactly one `ResearchFlow phase: <phase-id>` marker and contain at most two non-empty plain explanation lines.
- Judge deterministically; never call an LLM from judge, redactor, summarizer, or tests.
- Claude Code and OpenCode must resolve through LiteLLM to the same verified `openai/<model>` identity before any scored case.
- Never infer the backing model from `fable`, another harness alias, or a requested route.
- Never commit `base_url`, API keys, proxy credentials, authorization headers, user-home paths, raw environment variables, or unredacted event streams.
- Capability probe selects Claude direct-plugin-dir or marketplace proof and OpenCode strong-runtime or workspace-fallback proof.
- Any successful tool execution is `harness_error`; a rejected tool call with complete evidence is contamination.
- Verdict counts are exclusive; contamination is a separate overlay.
- Every original run has exactly 14 verdict or reason-coded `unattempted` accounting rows.
- Do not bump versions, push, publish, add clarification cases, or start release work.

---

## File Structure

- `tests/harness-acceptance/cases.json` — single source for seven prompts and expected phases.
- `tests/harness-acceptance/scored-prompt.txt` — shared routing-only output suffix.
- `tests/harness-acceptance/model-identities.json` — canonical OpenAI identities and non-proving aliases.
- `tests/harness-acceptance/lib.py` — shared constants, JSON I/O, hashes, schemas, and accounting helpers.
- `tests/harness-acceptance/judge.py` — deterministic marker/structure/forbidden-pattern verdict.
- `tests/harness-acceptance/redact.py` — committed-evidence leak scanner.
- `tests/harness-acceptance/summarize.py` — reconstruct 14-row summary from committed artifacts.
- `tests/harness-acceptance/capabilities.py` — capability and plugin-proof branch selection.
- `tests/harness-acceptance/preflight.py` — model-proof, plugin-proof, isolation, and global hard gates.
- `tests/harness-acceptance/adapters/claude.sh` — Claude native probe and normalized invocation producer.
- `tests/harness-acceptance/adapters/opencode.sh` — OpenCode native probe and normalized invocation producer.
- `tests/harness-acceptance/run.py` — no-overwrite orchestration and fixed execution order.
- `tests/harness-acceptance/run.sh` — stable shell entrypoint.
- `tests/harness-acceptance/fixtures/**` — synthetic judge/redaction/summary/proof fixtures.
- `tests/harness-acceptance/test_*.py` — standard-library unit and contract tests.
- `tests/harness-acceptance/run-tests.sh` — acceptance-pack synthetic test entrypoint.
- `tests/run-all.sh` — invokes the synthetic acceptance tests, never the paid live run.
- `tests/harness-acceptance/results/<run-id>/**` — redacted committed live evidence.
- `.gitignore` — ignores local run config, raw events, temporary homes, and caches.
- `docs/handover/researchwork-plugin-handover.md` — updated only after live evidence exists.

### Task 1: Freeze shared case, prompt, model, and invocation contracts

**Files:**
- Create: `tests/harness-acceptance/cases.json`
- Create: `tests/harness-acceptance/scored-prompt.txt`
- Create: `tests/harness-acceptance/model-identities.json`
- Create: `tests/harness-acceptance/lib.py`
- Create: `tests/harness-acceptance/test_contracts.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `PHASES: tuple[str, ...]`
- Produces: `VERDICTS: tuple[str, ...]`
- Produces: `REASON_CODES: tuple[str, ...]`
- Produces: `load_cases(root: Path) -> list[dict]`
- Produces: `read_json(path: Path) -> dict`
- Produces: `write_json(path: Path, value: dict, overwrite: bool = False) -> None`
- Produces: `sha256_path(path: Path) -> str`
- Produces: `validate_invocation(value: dict) -> None`

- [ ] **Step 1: Write the failing contract test**

Create `test_contracts.py` with tests that import `lib.py` by file path and assert seven unique cases, valid kinds/phases, exact reason codes, a harness-neutral scored suffix, and non-proving aliases.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest tests/harness-acceptance/test_contracts.py -v
```

Expected: import or file-not-found failure because contract files do not exist.

- [ ] **Step 3: Create the seven-case manifest**

Use exact IDs and expectations:

```json
[
  {"case_id":"R-DIRECT-LIT","kind":"direct","expected_phase":"literature-discovery"},
  {"case_id":"R-DIRECT-STRUCT","kind":"direct","expected_phase":"paper-structuring"},
  {"case_id":"R-DIRECT-DRAFT","kind":"direct","expected_phase":"paper-drafting"},
  {"case_id":"R-DIRECT-REVIEW","kind":"direct","expected_phase":"paper-review"},
  {"case_id":"R-DIRECT-PACK","kind":"direct","expected_phase":"artifact-packaging"},
  {"case_id":"R-BACK-INTRO","kind":"backward","expected_phase":"literature-discovery"},
  {"case_id":"R-BACK-PDF","kind":"backward","expected_phase":"paper-review"}
]
```

Expand each with a complete state-bearing `prompt`, `required_marker`, and concrete `forbidden_patterns`. Direct prompts explicitly state upstream artifacts are stable; backward prompts state the blocking artifact is missing.

- [ ] **Step 4: Create shared prompt and model allowlist**

The suffix contains the exact routing-only text from the spec. Start `canonical_models` empty; aliases such as `fable` must say `does_not_prove_backing_model: true`. Add a canonical model only when real metadata proves it.

- [ ] **Step 5: Implement shared library and invocation validation**

Require every approved field, validate enums, reject unknown top-level fields, and verify SHA fields are lowercase 64-character hex. JSON writes use sorted keys, two-space indentation, newline, and no-overwrite by default.

- [ ] **Step 6: Add local-artifact ignore rules**

Append:

```gitignore
.harness-acceptance-local/
tests/harness-acceptance/run-config.local.json
tests/harness-acceptance/results/*/raw/
```

- [ ] **Step 7: Run GREEN and baseline**

```bash
python3 -m unittest tests/harness-acceptance/test_contracts.py -v
./tests/run-all.sh
```

- [ ] **Step 8: Commit**

```bash
git add .gitignore tests/harness-acceptance/{cases.json,scored-prompt.txt,model-identities.json,lib.py,test_contracts.py}
git commit -m "test: define live harness acceptance contracts"
```

### Task 2: Implement deterministic judge and synthetic verdict fixtures

**Files:**
- Create: `tests/harness-acceptance/judge.py`
- Create: `tests/harness-acceptance/test_judge.py`
- Create: `tests/harness-acceptance/fixtures/judge/**`

**Interfaces:**
- Consumes: `load_cases`, `validate_invocation`, `PHASES`
- Produces: `judge(case: dict, invocation: dict, response: str) -> dict`
- Produces CLI: `python3 judge.py --case ID --invocation PATH --response PATH --output PATH`

- [ ] **Step 1: Write failing table-driven tests**

Cover correct/wrong/missing/duplicate/illegal/non-first markers; excess lines; heading/list/blockquote/fence; forbidden output; explanatory phase mention; non-zero exit; timeout; plugin-proof failure; blocked/executed/unknown tools.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest tests/harness-acceptance/test_judge.py -v
```

- [ ] **Step 3: Implement line-level judge**

Use the approved anchored marker regex. Normalize only line endings and trailing blank lines. Enforce one-to-three non-empty lines. Classification order: fatal process/plugin/tool → `harness_error`; structural invalidity → `indeterminate`; wrong marker → `fail`; forbidden match → `fail`; otherwise `pass`. Blocked tool calls overlay contamination.

- [ ] **Step 4: Emit reviewable verdict JSON**

Include phase, marker count, response SHA, line-1 evidence, forbidden matches, contamination, and `manual_note: null`. Refuse overwrite.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests/harness-acceptance/test_judge.py -v
git add tests/harness-acceptance/{judge.py,test_judge.py,fixtures/judge}
git commit -m "test: add deterministic routing verdict judge"
```

### Task 3: Implement redaction, model-proof validation, and summary reconstruction

**Files:**
- Create: `tests/harness-acceptance/redact.py`
- Create: `tests/harness-acceptance/summarize.py`
- Create: `tests/harness-acceptance/test_redact.py`
- Create: `tests/harness-acceptance/test_summarize.py`
- Create: `tests/harness-acceptance/fixtures/redaction/**`
- Create: `tests/harness-acceptance/fixtures/summary/**`

**Interfaces:**
- Produces: `scan_text(text: str, forbidden_home: str | None) -> list[dict]`
- Produces: `validate_model_proof(value: dict, identities: dict) -> str | None`
- Produces: `build_summary(run_dir: Path, cases: list[dict]) -> dict`
- Produces: `render_summary_markdown(summary: dict) -> str`

- [ ] **Step 1: Write RED tests**

Cover home/base URL/auth/token/credential leaks; clean hashes; aligned/unverified/mismatched model proofs; 14 pass; fail; contamination; preflight block; model block; runtime stop; missing/duplicate/invalid partitions.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest tests/harness-acceptance/test_redact.py tests/harness-acceptance/test_summarize.py -v
```

- [ ] **Step 3: Implement fail-closed redaction and model proof**

Scanner reports and exits non-zero without editing evidence. Model proof requires LiteLLM, provider `openai`, endpoint hash, backing model, canonical identity, proof hash, `verified`, and `redaction_passed`; aliases never prove resolution.

If real preflight later proves an OpenAI backing model absent from `canonical_models`, scored execution remains blocked. After reviewing the redacted proof, add exactly that `backing_model_id -> openai/<id>` mapping to `model-identities.json`, rerun all synthetic tests and preflight validation, and create a separate commit:

```bash
git add tests/harness-acceptance/model-identities.json
git commit -m "test: allow verified harness backing model"
```

The allowlist must never be populated from local config, `fable`, or another route alias.

- [ ] **Step 4: Implement deterministic summary**

Read committed artifacts only. Generate exactly 14 accounting rows, exclusive verdict partitions, separate contamination overlay, exact model alignment, and deterministic Markdown. Refuse raw local event dependencies.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests/harness-acceptance/test_redact.py tests/harness-acceptance/test_summarize.py -v
git add tests/harness-acceptance/{redact.py,summarize.py,test_redact.py,test_summarize.py,fixtures/redaction,fixtures/summary}
git commit -m "test: add acceptance evidence packaging"
```

### Task 4: Implement capability probes and normalized native adapters

**Files:**
- Create: `tests/harness-acceptance/capabilities.py`
- Create: `tests/harness-acceptance/adapters/claude.sh`
- Create: `tests/harness-acceptance/adapters/opencode.sh`
- Create: `tests/harness-acceptance/test_capabilities.py`
- Create: `tests/harness-acceptance/test_adapters.py`
- Create: `tests/harness-acceptance/fixtures/capabilities/**`
- Create: `tests/harness-acceptance/fixtures/adapters/**`

**Interfaces:**
- Produces: `select_claude_load_branch(probe: dict) -> str | None`
- Produces: `select_opencode_proof_branch(probe: dict) -> str | None`
- Produces: `select_isolation_profile(probe: dict) -> str | None`
- Adapter CLI: `adapter --mode capability|preflight|case --config PATH --output-dir PATH [--case-id ID]`

- [ ] **Step 1: Write failing capability/adapter tests**

Test Claude direct/marketplace/unsupported and optional CLI validation; OpenCode strong/fallback/unsupported with individually probed debug commands; full/auth-preserving profiles; profile-ID consistency; fake CLI normalized schemas; URL hashing; raw isolation; tool classification; no-overwrite.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest tests/harness-acceptance/test_capabilities.py tests/harness-acceptance/test_adapters.py -v
```

- [ ] **Step 3: Implement capability selection and thin adapters**

Keep logic/validation in Python. Bash uses arrays, never `eval`, and only creates directories, invokes CLI, captures streams/status, and calls normalization. Probe commands; do not assume them.

- [ ] **Step 4: Run GREEN and commit**

```bash
bash -n tests/harness-acceptance/adapters/claude.sh
bash -n tests/harness-acceptance/adapters/opencode.sh
python3 -m unittest tests/harness-acceptance/test_capabilities.py tests/harness-acceptance/test_adapters.py -v
git add tests/harness-acceptance/{capabilities.py,adapters,test_capabilities.py,test_adapters.py,fixtures/capabilities,fixtures/adapters}
git commit -m "test: add native harness capability adapters"
```

### Task 5: Implement preflight, same-model hard gate, and orchestration

**Files:**
- Create: `tests/harness-acceptance/preflight.py`
- Create: `tests/harness-acceptance/run.py`
- Create: `tests/harness-acceptance/run.sh`
- Create: `tests/harness-acceptance/run-config.example.json`
- Create: `tests/harness-acceptance/test_preflight.py`
- Create: `tests/harness-acceptance/test_run.py`
- Create: `tests/harness-acceptance/run-tests.sh`
- Modify: `tests/run-all.sh`

**Interfaces:**
- Produces: `evaluate_preflight(capability, plugin_proof, model_proof) -> dict`
- Produces: `evaluate_model_alignment(claude_proof, opencode_proof) -> dict`
- Produces: `run_original(config: dict, run_id: str) -> Path`

- [ ] **Step 1: Write RED tests**

Cover optional Claude validation, OpenCode fallback, canary without source proof, profile mismatch, unverified/mismatched model proof, exact aligned identities, no-overwrite, 14-row block accounting, fixed order, and zero case calls before alignment.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest tests/harness-acceptance/test_preflight.py tests/harness-acceptance/test_run.py -v
```

- [ ] **Step 3: Implement preflight/alignment/orchestration**

Write redacted capability/plugin/model proof. Compare verified canonical identities exactly. Any gate failure creates 14 reason-coded unattempted rows. Order: both capabilities → synthetic gate → both preflights → alignment → Claude 7 → completeness → OpenCode 7 → completeness → summary/redaction. Never retry or overwrite.

- [ ] **Step 4: Create local-config example and synthetic test runner**

The example contains route names, effort/variant, and timeout, but no endpoint, secret, or guessed canonical identity:

```json
{
  "claude": {"harness_model_value":"fable","effort_or_variant":"high"},
  "opencode": {"harness_model_value":"openai/proxy-route","effort_or_variant":"high"},
  "timeout_seconds": 120
}
```

The local operator replaces only the OpenCode proxy route with the configured route name. Verified model proofs, not this config, determine canonical identity. `run-tests.sh` runs only unittest discovery. Append it to `tests/run-all.sh`; baseline never calls real harnesses.

`run_original()` must model one run as monotonic phases: `preflight-only` may create the run root and preflight artifacts; `scored` may continue that same run only when no case artifact exists and aligned preflight artifacts are unchanged. It must reject a second preflight, reject a second scored phase, and reject any overwrite.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest tests/harness-acceptance/test_preflight.py tests/harness-acceptance/test_run.py -v
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
git add tests/harness-acceptance/{preflight.py,run.py,run.sh,run-config.example.json,test_preflight.py,test_run.py,run-tests.sh} tests/run-all.sh
git commit -m "test: gate live harness acceptance runs"
```

### Task 6: Run real capability/preflight gates without scored cases

**Files:**
- Local only: `tests/harness-acceptance/run-config.local.json`
- Local raw: `.harness-acceptance-local/<run-id>/raw/**`
- Create: `tests/harness-acceptance/results/<run-id>/{capabilities,preflight,environment.json,summary.json,summary.md}`

- [ ] **Step 1: Reverify synthetic gates**

```bash
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
```

- [ ] **Step 2: Create local config without printing secrets**

Copy the example; set only the Claude harness route, OpenCode proxy route, effort/variant, and timeout. Do not set an expected canonical identity: committed redacted model proofs and the allowlist establish it. Keep endpoint and credentials in existing process configuration.

- [ ] **Step 3: Allocate run ID and refuse overwrite**

```bash
RUN_ID=$(date -u +%Y-%m-%dT%H%M%SZ)
test ! -e "tests/harness-acceptance/results/$RUN_ID"
```

- [ ] **Step 4: Run preflight-only**

```bash
./tests/harness-acceptance/run.sh --mode preflight-only \
  --config tests/harness-acceptance/run-config.local.json --run-id "$RUN_ID"
```

Expected: both proof/model gates align, or a complete blocked summary with 14 unattempted rows. Stop on block.

- [ ] **Step 5: Scan and reconstruct**

```bash
python3 tests/harness-acceptance/redact.py --tree "tests/harness-acceptance/results/$RUN_ID"
python3 tests/harness-acceptance/summarize.py --run-dir "tests/harness-acceptance/results/$RUN_ID" --check-only
```

- [ ] **Step 6: Resolve a newly proved model identity before scored execution**

If preflight proves the same OpenAI backing model on both harnesses but the identity is absent from `model-identities.json`, do not classify the run as a failed preflight. Pause the run before scoring, review the redacted model proofs, add the exact canonical mapping, run all synthetic tests again, commit the allowlist update using the Task 3 command, and rerun `--mode preflight-only` with a **new** run ID. The original run remains a complete 14-row `global_hard_gate_blocked` record and is never resumed.

- [ ] **Step 7: Commit blocked preflight evidence or continue an aligned run**

```bash
git add "tests/harness-acceptance/results/$RUN_ID"
git commit -m "test: record blocked harness acceptance preflight"
```

Run this evidence commit when blocked or when an allowlist update requires a new run ID. If aligned and already allowlisted, keep the same run directory and continue Task 7 without an intermediate evidence commit.

### Task 7: Execute at most 14 live cases and package bounded evidence

**Files:**
- Create: `tests/harness-acceptance/results/<run-id>/<harness>/<case-id>/{invocation.json,command.json,final-response.txt,verdict.json}`
- Create/Modify: `tests/harness-acceptance/results/<run-id>/summary.{json,md}`
- Modify: `docs/handover/researchwork-plugin-handover.md`
- Modify only if disproved: `docs/README.claude.md`, `.opencode/INSTALL.md`

- [ ] **Step 1: Confirm aligned hard gate**

```bash
python3 tests/harness-acceptance/preflight.py --run-dir \
  "tests/harness-acceptance/results/$RUN_ID" --require-aligned
```

- [ ] **Step 2: Run scored original once**

```bash
./tests/harness-acceptance/run.sh --mode scored \
  --config tests/harness-acceptance/run-config.local.json --run-id "$RUN_ID"
```

Expected: no more than 14 invocations, no retries, all cases accounted.

- [ ] **Step 3: Reconstruct and redaction-check**

```bash
python3 tests/harness-acceptance/summarize.py --run-dir \
  "tests/harness-acceptance/results/$RUN_ID" --write
python3 tests/harness-acceptance/summarize.py --run-dir \
  "tests/harness-acceptance/results/$RUN_ID" --check-only
python3 tests/harness-acceptance/redact.py --tree \
  "tests/harness-acceptance/results/$RUN_ID"
```

- [ ] **Step 4: Manually review all response/verdict evidence**

Verify marker, SHA, forbidden matches, model proof, proof strength, contamination, and privacy. Append manual notes without changing machine verdicts.

- [ ] **Step 5: Update handover conservatively**

Record actual status/counts/proof asymmetry/model identity/alignment/raw hashes and exact single-run limitation. Do not claim stability or release approval.

- [ ] **Step 6: Run final verification**

```bash
./tests/harness-acceptance/run-tests.sh
./tests/run-all.sh
python3 tests/harness-acceptance/redact.py --tree \
  "tests/harness-acceptance/results/$RUN_ID"
git diff --check
git status --short
```

- [ ] **Step 7: Review and commit bounded evidence**

```bash
git diff -- tests/harness-acceptance docs/handover docs/README.claude.md .opencode/INSTALL.md
git add "tests/harness-acceptance/results/$RUN_ID" docs/handover/researchwork-plugin-handover.md
git add docs/README.claude.md .opencode/INSTALL.md 2>/dev/null || true
git commit -m "test: record live router harness acceptance"
```

## Self-Review

### Spec coverage

- Tasks 1–3 cover shared contracts, judge, model proof, redaction, summary, no-overwrite, and 14-row accounting.
- Tasks 4–5 cover capability-based proof branches, native adapters, isolation, plugin proof, same-model hard gate, and orchestration.
- Task 6 separates real preflight from scored execution and stops on block.
- Task 7 runs at most 14 cases, packages reviewable evidence, and updates only evidence-facing docs.

### Placeholder scan

No unresolved implementation placeholders remain. Angle-bracket values are quoted schema/runtime values supplied deterministically by config or evidence.

### Type and schema consistency

- Both adapters emit the same `invocation.json` consumed by judge and summarizer.
- Backing identity comes only from verified committed model proof.
- Verdict partitions sum to seven per harness; contamination stays an overlay.
- Every original run has exactly 14 verdict/unattempted rows.
- Raw events never become required committed reconstruction inputs.
