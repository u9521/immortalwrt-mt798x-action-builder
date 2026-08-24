---
name: code-review
description: Perform structured, read-only code reviews grounded in repository AGENTS.md conventions, active Agent Notes, architectural invariants, and defensive programming patterns.
---

# Agent Code Review SOP

This skill defines the standard procedure for performing an Agent-Native code review in `immortalwrt-action-builder`.

## Core Review Invariants

1. **Pure Python Standard Library**:
   - The runtime package MUST NOT introduce external runtime dependencies.
   - Standard library modules (`pathlib`, `subprocess`, `urllib`, `hashlib`, `shutil`, `json`, `tomllib`) must be used.
2. **Patch System Contract**:
   - Patch scripts must be pure Python files accepting `PatchContext`.
   - Patches should use `context` helper methods (`path`, `exists`, `read_text`, `write_text`, `replace_text`, `run_command`).
3. **Workspace & Cache Isolation**:
   - Host/CI execution runs from the repository root.
   - Operations must isolate build targets under `source-code/`, cache under `cache/`, and artifacts under `out/`.
4. **Header and Formatting Standards**:
   - New Python files must have the SPDX/Copyright header and `from __future__ import annotations`.
   - Clean 4-space indentation, double quotes, type annotations on public signatures.
5. **Agent Note Synchronization**:
   - Non-trivial functional or architectural changes must be paired with an Agent Note in `.agents/notes/`.

---

## Review Output Format

```markdown
# Code Review Summary: <Topic / PR>

## Verdict: [Approved / Changes Requested / Comment]

### 1. Architectural & Invariant Alignment
- [Pass/Finding] Stdlib runtime invariant & ADR alignment.

### 2. Correctness & Defensive Design
- [Finding / Location: file:line] Subprocess error handling, path resolution, or race conditions.

### 3. Documentation & Governance Sync
- [Pass/Finding] AGENTS.md and Agent Note synchronization.

### 4. Test Adequacy
- [Pass/Finding] Unit test coverage for new edge cases or error branches.

### Actionable Next Steps
- List 1-3 concrete action items for the author.
```
