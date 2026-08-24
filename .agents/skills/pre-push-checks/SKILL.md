---
name: pre-push-checks
description: Run focused pre-push validation by identifying the minimal set of affected tests, specification gates, and linters for the current git diff.
---

# Agent Pre-Push Checks

Use this skill before pushing commits to verify quality gates, test coverage, and specification integrity with minimal turnaround time.

## Workflow

### 1. Inspect Outgoing Diff
Check modified, added, and staged files:
```bash
git status --short
git diff --name-only HEAD~1 HEAD
```

### 2. Run Quality Gates & Tests Based on Affected Areas

#### A. Documentation, Notes & Specifications
When touching `.agents/**`, `AGENTS.md`, `docs/**`, or `scripts/gates/**`:
```bash
python3 scripts/gates/verify_agent_gates.py
```

#### B. Core Python Code (`immortalwrt_builder/builder/**`)
1. Run affected unit tests:
   ```bash
   # Single module test
   python3 -m unittest immortalwrt_builder/tests/test_patch.py
   # Or full suite
   python3 -m unittest discover -s immortalwrt_builder/tests
   ```
2. Lint and format checks:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   ```
3. Static type check:
   ```bash
   npx --cache /tmp/npm-cache pyright
   ```

#### C. Target Configurations & Patches (`configs/**`)
- Verify target parsing and patch execution tests:
  ```bash
  python3 -m unittest immortalwrt_builder/tests/test_target_store.py
  python3 -m unittest immortalwrt_builder/tests/test_builtin_patches.py
  ```

### 3. Check Agent Note Synchronization
If architecture, public interfaces, CLI commands, or pipeline workflows were altered:
- Confirm an Agent Note exists or was updated in `.agents/notes/`.
- Ensure `python3 scripts/gates/verify_agent_gates.py` passes with zero errors.

### 4. Report Summary
Summarize the checks executed and report the final status.
