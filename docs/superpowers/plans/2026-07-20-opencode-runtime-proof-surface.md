# OpenCode Runtime Proof Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an OpenCode-upstream authoritative runtime-proof surface for non-interactive execution, consisting of a canonical `run --format json` model event and a dedicated `debug proof` surface derived from the same execution-scoped runtime truth.

**Architecture:** Keep this work upstream-only. First define and test an execution-scoped internal proof record keyed by the same session/run identity already used in the CLI runtime, then expose that truth in two ways: a canonical additive `model` event on the non-interactive `run --format json` path, and a read-only `debug proof` command that reads the same stored truth by explicit identifier. Do not change ResearchFlow consumer logic in this plan.

**Tech Stack:** TypeScript, existing OpenCode CLI/runtime event pipeline, Effect, existing CLI command patterns, existing `packages/opencode/test/cli/run/*` and `packages/opencode/test/cli/help/*` suites

## Global Constraints

- Scope is only subproject A: OpenCode upstream authoritative runtime-proof surface.
- do not change ResearchFlow consumer logic in this plan.
- do not reopen Task 5.
- do not run scored cases.
- do not modify historical blocked evidence under `tests/harness-acceptance/results/2026-07-19T152433Z/`.
- keep the design dual-track: canonical run-path model event plus dedicated debug proof surface derived from the same runtime truth.
- `run --format json` remains the only authoritative machine-consumable source for downstream gating.
- `debug proof` / `debug model` is diagnostic only and must never become an independent source of truth.
- authoritative minimum remains `providerID`, `modelID`, `resolved_model_identity`, and `verified`.
- `resolved_model_identity` and `verified` must be derived inside OpenCode upstream from runtime truth plus an upstream-owned canonical mapping source.
- if authoritative runtime truth is unavailable, the run-path surface must fail closed rather than emit guessed proof.
- the debug proof surface must support addressing a specific execution/session identity and must not rely only on “latest”.
- the debug proof surface must read from the same execution-scoped runtime truth instance as the canonical run-path event.

---

## File Structure

- `packages/opencode/src/cli/cmd/run.ts` — add canonical `model` event emission to the non-interactive JSON run path.
- `packages/opencode/src/cli/cmd/run/session-data.ts` — define the minimal execution-scoped internal proof record lifecycle keyed by session/message runtime truth.
- `packages/opencode/src/cli/cmd/run/types.ts` or the nearest existing run-type file — declare any shared proof-record or model-event types used by both run-path and debug command code.
- `packages/opencode/src/cli/cmd/debug/index.ts` — register the new `debug proof` subcommand in the existing debug command tree.
- `packages/opencode/src/cli/cmd/debug/proof.ts` — implement the dedicated diagnostic proof command that reads the same execution-scoped runtime truth by explicit identifier.
- `packages/opencode/src/cli/cmd/run/trace.ts` — only touch if needed to share stored execution-scoped proof state shape; do not repurpose trace as the authoritative surface.
- `packages/opencode/test/cli/run/session-data.test.ts` — add proof-record reducer tests for runtime truth capture and fail-closed behavior.
- `packages/opencode/test/cli/run/runtime.test.ts` — add canonical run-path tests for `run --format json` model-event emission.
- `packages/opencode/test/cli/help/help-snapshots.test.ts` and `packages/opencode/test/cli/help/__snapshots__/help-snapshots.test.ts.snap` — lock in the new `debug proof` command help surface.
- `packages/opencode/test/cli/debug/` — add a focused test file for `debug proof` behavior if no existing debug-command test file fits.
- `docs/superpowers/specs/2026-07-20-opencode-runtime-proof-surface-design.md` — keep the approved spec aligned if implementation reveals one wording bug.

### Task 1: Define the execution-scoped proof record and lock its semantics with tests

**Files:**
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/run/session-data.ts`
- Modify: `reference/opencode/packages/opencode/test/cli/run/session-data.test.ts`
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/run/types.ts` or the nearest existing shared run-type file

**Interfaces:**
- Produces: `type RuntimeModelProof = { sessionID: string; providerID: string; modelID: string; resolvedModelIdentity: string | null; verified: boolean; proofSource: string }`
- Produces: `type RuntimeModelProofState = { latestBySession: Map<string, RuntimeModelProof> }`
- Consumes: `event.type === "message.updated"` with `event.properties.info.providerID` and `event.properties.info.modelID`
- Produces for later tasks: a reducer-visible execution-scoped proof record that can be read by run-path emission and debug proof code

- [ ] **Step 1: Write the failing proof-record tests in `session-data.test.ts`**

Add tests like:

```ts
test("records runtime proof from assistant message.updated events", () => {
  const out = reduce(
    createSessionData(),
    assistant("msg-1", {
      providerID: "openai-compatible",
      modelID: "gpt-5.4",
    }),
  )

  expect(out.data.runtimeModelProof.latestBySession.get("session-1")).toEqual(
    expect.objectContaining({
      sessionID: "session-1",
      providerID: "openai-compatible",
      modelID: "gpt-5.4",
      verified: false,
    }),
  )
})


test("does not invent resolved identity when runtime truth is insufficient", () => {
  const out = reduce(
    createSessionData(),
    assistant("msg-1", {
      providerID: "openai-compatible",
      modelID: "gpt-5.4",
    }),
  )

  expect(out.data.runtimeModelProof.latestBySession.get("session-1")).toEqual(
    expect.objectContaining({
      resolvedModelIdentity: null,
      verified: false,
    }),
  )
})
```

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
bun test packages/opencode/test/cli/run/session-data.test.ts
```

Expected:
- FAIL because `createSessionData()` and the reducer do not yet expose `runtimeModelProof`.

- [ ] **Step 3: Add the minimal shared proof types**

In the chosen shared type file, add:

```ts
export type RuntimeModelProof = {
  sessionID: string
  providerID: string
  modelID: string
  resolvedModelIdentity: string | null
  verified: boolean
  proofSource: string
}

export type RuntimeModelProofState = {
  latestBySession: Map<string, RuntimeModelProof>
}
```

Keep the first version minimal. Do not add audit hashes or lineage arrays yet.

- [ ] **Step 4: Extend `createSessionData()` and the reducer state minimally**

In `session-data.ts`, initialize proof storage:

```ts
runtimeModelProof: {
  latestBySession: new Map(),
},
```

Then, inside the existing `message.updated` assistant branch, add the minimal state write:

```ts
data.runtimeModelProof.latestBySession.set(input.sessionID, {
  sessionID: input.sessionID,
  providerID: info.providerID,
  modelID: info.modelID,
  resolvedModelIdentity: null,
  verified: false,
  proofSource: "message.updated",
})
```

Only write this record when `info.role === "assistant"` and `providerID`/`modelID` are present.

- [ ] **Step 5: Run the focused test to verify GREEN**

Run:

```bash
bun test packages/opencode/test/cli/run/session-data.test.ts
```

Expected:
- PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add packages/opencode/src/cli/cmd/run/session-data.ts \
        packages/opencode/src/cli/cmd/run/types.ts \
        packages/opencode/test/cli/run/session-data.test.ts
git commit -m "test: record runtime model proof state"
```

### Task 2: Emit the canonical `model` event on the non-interactive run path

**Files:**
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/run.ts`
- Modify: `reference/opencode/packages/opencode/test/cli/run/runtime.test.ts`
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/run/types.ts` if Task 1 did not already define the event payload type

**Interfaces:**
- Consumes: `RuntimeModelProofState`
- Produces: `type RunJsonModelEvent = { type: "model"; timestamp: number; sessionID: string; providerID: string; modelID: string; resolved_model_identity: string | null; verified: boolean }`
- Produces for later tasks: additive `model` events on `opencode run --format json`

- [ ] **Step 1: Write the failing runtime-path test**

Add a focused test to `runtime.test.ts` that asserts non-interactive JSON output includes a `model` event before idle completes. Use the existing runtime test harness pattern and expect output lines to include:

```ts
expect(lines).toContainEqual(
  expect.objectContaining({
    type: "model",
    sessionID: "ses-1",
    providerID: "openai",
    modelID: "gpt-5",
    resolved_model_identity: null,
    verified: false,
  }),
)
```

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
bun test packages/opencode/test/cli/run/runtime.test.ts
```

Expected:
- FAIL because `run.ts` never emits `type: "model"`.

- [ ] **Step 3: Add a dedicated emitter helper in `run.ts`**

Near the existing `emit(type, data)` helper, add a small helper for model emission:

```ts
function emitModel(proof: {
  providerID: string
  modelID: string
  resolvedModelIdentity: string | null
  verified: boolean
}) {
  return emit("model", {
    providerID: proof.providerID,
    modelID: proof.modelID,
    resolved_model_identity: proof.resolvedModelIdentity,
    verified: proof.verified,
  })
}
```

- [ ] **Step 4: Emit the model event from assistant `message.updated` on the JSON path**

In the event loop in `run.ts`, inside the `event.type === "message.updated"` handling, add JSON-path emission for assistant updates using the existing runtime truth:

```ts
if (
  event.type === "message.updated" &&
  event.properties.sessionID === sessionID &&
  event.properties.info.role === "assistant" &&
  args.format === "json"
) {
  const info = event.properties.info
  if (typeof info.providerID === "string" && typeof info.modelID === "string") {
    emitModel({
      providerID: info.providerID,
      modelID: info.modelID,
      resolvedModelIdentity: null,
      verified: false,
    })
  }
}
```

Keep this first version additive and fail-closed: do not guess `resolved_model_identity`.

- [ ] **Step 5: Run the focused test to verify GREEN**

Run:

```bash
bun test packages/opencode/test/cli/run/runtime.test.ts
```

Expected:
- PASS.

- [ ] **Step 6: Commit Task 2**

```bash
git add packages/opencode/src/cli/cmd/run.ts \
        packages/opencode/test/cli/run/runtime.test.ts \
        packages/opencode/src/cli/cmd/run/types.ts
git commit -m "feat: emit runtime model event"
```

### Task 3: Add the dedicated `debug proof` command with explicit session correlation

**Files:**
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/debug/index.ts`
- Create: `reference/opencode/packages/opencode/src/cli/cmd/debug/proof.ts`
- Test: `reference/opencode/packages/opencode/test/cli/help/help-snapshots.test.ts`
- Test: `reference/opencode/packages/opencode/test/cli/help/__snapshots__/help-snapshots.test.ts.snap`
- Create or Modify: `reference/opencode/packages/opencode/test/cli/debug/proof.test.ts`

**Interfaces:**
- Consumes: `RuntimeModelProofState`
- Produces CLI: `opencode debug proof --session <id>`
- Produces optional convenience mode only if explicitly requested in code: `opencode debug proof --latest`
- Produces JSON payload: `{ providerID, modelID, resolved_model_identity, verified, proof_source, sessionID }`

- [ ] **Step 1: Write the failing command-behavior tests**

Create or extend a debug-command test file with cases like:

```ts
test("debug proof requires explicit session or latest selector", async () => {
  const result = await runDebugProof([])
  expect(result.exitCode).not.toBe(0)
})


test("debug proof returns execution-scoped truth for an explicit session", async () => {
  const result = await runDebugProof(["--session", "ses-1"])
  expect(JSON.parse(result.stdout)).toEqual(
    expect.objectContaining({
      sessionID: "ses-1",
      providerID: "openai",
      modelID: "gpt-5",
      verified: false,
    }),
  )
})
```

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```bash
bun test packages/opencode/test/cli/debug/proof.test.ts
```

Expected:
- FAIL because the command does not exist yet.

- [ ] **Step 3: Implement `debug/proof.ts` minimally**

Create `packages/opencode/src/cli/cmd/debug/proof.ts` with a command following the existing debug command style. Minimum shape:

```ts
import { EOL } from "os"
import { Effect } from "effect"
import { effectCmd } from "../../effect-cmd"
import { RuntimeModelProofStore } from "../run/proof-store"

export const ProofCommand = effectCmd({
  command: "proof",
  describe: "show runtime model proof for a specific session",
  builder: (yargs) =>
    yargs
      .option("session", { type: "string" })
      .option("latest", { type: "boolean", default: false }),
  handler: Effect.fn("Cli.debug.proof")(function* (args) {
    if (!args.session && !args.latest) {
      throw new Error("debug proof requires --session or --latest")
    }
    const store = yield* RuntimeModelProofStore
    const proof = args.session ? yield* store.get(args.session) : yield* store.latest()
    process.stdout.write(JSON.stringify(proof, null, 2) + EOL)
  }),
})
```

If there is no matching execution-scoped proof record, fail closed with a non-zero exit.

- [ ] **Step 4: Register the new command in `debug/index.ts` and lock the help surface**

Add `ProofCommand` to the existing debug builder list, then update the help snapshot coverage to include the new command in `help-snapshots.test.ts` and refresh the snapshot entry so the help includes a line like:

```text
opencode debug proof         show runtime model proof for a specific session
```

- [ ] **Step 5: Run the focused tests to verify GREEN**

Run:

```bash
bun test packages/opencode/test/cli/debug/proof.test.ts
bun test packages/opencode/test/cli/help/help-snapshots.test.ts
```

Expected:
- PASS.

- [ ] **Step 6: Commit Task 3**

```bash
git add packages/opencode/src/cli/cmd/debug/index.ts \
        packages/opencode/src/cli/cmd/debug/proof.ts \
        packages/opencode/test/cli/debug/proof.test.ts \
        packages/opencode/test/cli/help/help-snapshots.test.ts \
        packages/opencode/test/cli/help/__snapshots__/help-snapshots.test.ts.snap
git commit -m "feat: add debug proof command"
```

### Task 4: Enforce same-truth and fail-closed behavior across both surfaces

**Files:**
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/run/session-data.ts`
- Modify: `reference/opencode/packages/opencode/src/cli/cmd/debug/proof.ts`
- Modify: `reference/opencode/packages/opencode/test/cli/run/session-data.test.ts`
- Modify: `reference/opencode/packages/opencode/test/cli/debug/proof.test.ts`
- Modify if needed: `reference/opencode/packages/opencode/test/cli/run/runtime.test.ts`

**Interfaces:**
- Produces: execution-scoped proof lookup by session ID
- Produces: fail-closed debug behavior when no matching proof record exists
- Produces: a shared internal truth source consumed by both run-path and debug proof surfaces

- [ ] **Step 1: Write the failing same-truth tests**

Extend the tests with cases like:

```ts
test("debug proof fails closed when no execution-scoped proof record exists", async () => {
  const result = await runDebugProof(["--session", "missing-session"])
  expect(result.exitCode).not.toBe(0)
})


test("debug proof does not substitute a nearby session when exact session is missing", async () => {
  await seedProof("ses-1")
  const result = await runDebugProof(["--session", "ses-2"])
  expect(result.exitCode).not.toBe(0)
})
```

- [ ] **Step 2: Run the focused tests to verify RED**

Run:

```bash
bun test packages/opencode/test/cli/debug/proof.test.ts
bun test packages/opencode/test/cli/run/session-data.test.ts
```

Expected:
- FAIL until the proof store and command lookup are exact-session and fail-closed.

- [ ] **Step 3: Add exact-session lookup and optional explicit latest lookup only**

Implement a tiny internal proof-store surface used by both run-path and debug command code. Minimum interface:

```ts
export type RuntimeModelProofStore = {
  get(sessionID: string): Effect.Effect<RuntimeModelProof>
  latest(): Effect.Effect<RuntimeModelProof>
  set(proof: RuntimeModelProof): Effect.Effect<void>
}
```

Rules to encode in code:

- `get(sessionID)` must fail if the exact session has no proof record;
- `latest()` may exist only as an explicit convenience path;
- `debug proof --session <id>` must never silently fall back to latest.

- [ ] **Step 4: Run the focused tests to verify GREEN**

Run:

```bash
bun test packages/opencode/test/cli/debug/proof.test.ts
bun test packages/opencode/test/cli/run/session-data.test.ts
bun test packages/opencode/test/cli/run/runtime.test.ts
```

Expected:
- PASS.

- [ ] **Step 5: Commit Task 4**

```bash
git add packages/opencode/src/cli/cmd/run/session-data.ts \
        packages/opencode/src/cli/cmd/debug/proof.ts \
        packages/opencode/test/cli/run/session-data.test.ts \
        packages/opencode/test/cli/debug/proof.test.ts \
        packages/opencode/test/cli/run/runtime.test.ts
git commit -m "fix: keep runtime proof surfaces aligned"
```

### Task 5: Align the spec text and run the final focused upstream baseline

**Files:**
- Modify if needed: `docs/superpowers/specs/2026-07-20-opencode-runtime-proof-surface-design.md`
- Verify: `reference/opencode/packages/opencode/test/cli/run/runtime.test.ts`
- Verify: `reference/opencode/packages/opencode/test/cli/run/session-data.test.ts`
- Verify: `reference/opencode/packages/opencode/test/cli/debug/proof.test.ts`
- Verify: `reference/opencode/packages/opencode/test/cli/help/help-snapshots.test.ts`

**Interfaces:**
- Consumes: all earlier tasks
- Produces: final confirmation that the upstream runtime-proof surface matches the approved spec and remains upstream-only

- [ ] **Step 1: Patch spec wording only if implementation forced one narrow terminology change**

If implementation preserved the approved field names and command shape, do not edit the spec. If one exact wording mismatch had to change, make only that narrow edit.

- [ ] **Step 2: Run the final focused upstream baseline**

Run:

```bash
bun test packages/opencode/test/cli/run/session-data.test.ts
bun test packages/opencode/test/cli/run/runtime.test.ts
bun test packages/opencode/test/cli/debug/proof.test.ts
bun test packages/opencode/test/cli/help/help-snapshots.test.ts
```

Expected:
- PASS.

- [ ] **Step 3: Confirm no ResearchFlow-consumer code was changed as part of this upstream-only plan**

Run:

```bash
git diff --name-only HEAD~4..HEAD
```

Expected:
- changed files are limited to `reference/opencode/packages/opencode/src/**`, `reference/opencode/packages/opencode/test/**`, and the one spec file if it needed a wording sync.

- [ ] **Step 4: Commit any final spec-sync change if one was necessary**

```bash
git add docs/superpowers/specs/2026-07-20-opencode-runtime-proof-surface-design.md
git commit -m "docs: sync runtime proof surface spec"
```

Skip this step if the spec needed no change.

## Self-Review

### Spec coverage

- Task 1 creates the execution-scoped internal proof record and locks fail-closed semantics before any CLI surface change.
- Task 2 adds the canonical additive `model` event to the non-interactive `run --format json` path.
- Task 3 adds the dedicated `debug proof` command and locks the user-visible help surface.
- Task 4 enforces the same-truth and exact-session correlation rules so debug proof cannot drift from canonical run-path truth.
- Task 5 runs the focused upstream baseline and verifies the work stayed upstream-only.

### Placeholder scan

- No `TODO`/`TBD` placeholders remain.
- Every task includes exact file paths, concrete tests, commands, and commit steps.
- The plan does not defer ResearchFlow consumer work into this upstream-only cycle.

### Type consistency

- The plan consistently uses `RuntimeModelProof` as the shared truth shape.
- The canonical run-path event consistently uses `resolved_model_identity` and `verified`.
- The debug proof surface consistently uses explicit session correlation and fail-closed lookup.

Plan complete and saved to `docs/superpowers/plans/2026-07-20-opencode-runtime-proof-surface.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**