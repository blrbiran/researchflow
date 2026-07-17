# Task 3 Report — redaction, model-proof validation, and summary reconstruction

## Status
Completed in `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance` on branch `feat/live-harness-acceptance`.

## RED evidence
Command:
```bash
python3 tests/harness-acceptance/test_redact.py
python3 tests/harness-acceptance/test_summarize.py
```
Output before fixes:
```text
SyntaxError: EOL while scanning string literal
```
Why RED:
- The first generated Task 3 test/module files had escaped-newline corruption, so both new test files failed to import before implementation stabilized.
- After syntax repair, intermediate RED/GREEN iterations surfaced the intended contract gaps: base-URL detection missed quoted JSON keys, summary alignment blocked attempted-case fixtures until the allowlist contract was modeled explicitly, and the CLI round-trip needed an allowlist override path for synthetic fixtures.

## GREEN evidence
Command:
```bash
python3 -m unittest discover -s tests/harness-acceptance -p "test_*.py" -v
```
Output:
```text
Ran 24 tests in 0.329s
OK
```

Command:
```bash
python3 -m unittest discover -s tests/harness-acceptance -p "test_judge.py" -v
```
Output:
```text
Ran 5 tests in 0.068s
OK
```

## Files changed
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/redact.py`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/summarize.py`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/test_redact.py`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/test_summarize.py`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/redaction/auth-credential.txt`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/redaction/base-url.txt`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/redaction/clean-hashes.txt`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/redaction/home-path.txt`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/summary/base-capability-claude.json`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/summary/base-capability-opencode.json`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/summary/base-environment.json`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/summary/base-model-proof.json`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/summary/base-preflight-claude.json`
- `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/fixtures/summary/base-preflight-opencode.json`

## Commit
- `68554ac` — `test: add acceptance evidence packaging`

## Self-review
- Redaction is fail-closed and scan-only: it reports hits and returns non-zero without mutating evidence trees.
- Model-proof validation requires LiteLLM, provider `openai`, hashed endpoint/proof fields, `verified=true`, `redaction_passed=true`, and an exact canonical allowlist match; aliases alone do not prove backing identity.
- Summary reconstruction reads only committed-style artifacts, emits exactly 14 ordered accounting rows, keeps verdict partitions exclusive, and reports contamination as a separate overlay.
- Blocked states distinguish preflight block, model-alignment block, allowlist-missing global hard gate, and runtime stop.
- The CLI `--write/--check-only` path is covered with a synthetic allowlist override so future preflight-only runs can validate reconstruction deterministically.

## Concerns
- The worktree still has untracked local artifacts outside the commit: `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/.omc/` and `/Users/biran/code/skills/ccmem_paper/reference/researchflow/.worktrees/live-harness-acceptance/tests/harness-acceptance/__pycache__/`.
- The brief-specified `python3 -m unittest tests/harness-acceptance/...` form is not importable in this repo because `tests/harness-acceptance` contains a hyphen; verification used script execution plus `unittest discover`, which passed.

## Review fixes
### RED evidence
Command:
```bash
python3 tests/harness-acceptance/test_redact.py
python3 tests/harness-acceptance/test_summarize.py
```
Output before review fixes:
```text
Redact: FAILED (TypeError on unexpected allowed_absolute_patterns/committed_roots args; absolute-path CLI check returned 0 instead of 1)
Summarize: FAILED (missing harness plugin_source_id, attempted case accepted after harness_error, conflicting plugin sources accepted, --write created summary.json before discovering existing summary.md)
```
Why RED:
- Redaction only covered home/base_url/auth classes and lacked deterministic fail-closed checks for unrelated absolute paths and private-instruction sentinel fragments.
- Summary reconstruction did not enforce post-harness_error stop accounting, atomic dual-target preflight, or plugin_source_id disclosure/consistency.

### GREEN evidence
Command:
```bash
python3 -m unittest discover -s tests/harness-acceptance -p "test_*.py" -v
python3 -m unittest discover -s tests/harness-acceptance -p "test_judge.py" -v
```
Output after review fixes:
```text
Ran 29 tests in 0.444s
OK
Ran 5 tests in 0.069s
OK
```
Fixes landed:
- Added deterministic redaction detection for unrelated absolute paths, repo-root absolute paths, explicit safe absolute allowlists, and private-instruction sentinel fragments.
- Rejected any attempted artifact after the first harness_error, leaving only later runtime_harness_stopped accounting rows valid.
- Made --write preflight both summary targets before writing either file.
- Required consistent plugin_source_id from attempted invocation artifacts or preflight proof, surfaced it in summary JSON/Markdown, and rejected conflicts.
- Commit: `test: harden acceptance packaging review gaps`
