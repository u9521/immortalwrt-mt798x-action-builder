# Agent Notes

Agent Notes are RFCs and Architecture Decision Records (ADRs) maintained for both human developers and AI agents working on `immortalwrt-action-builder`.

Every non-trivial architectural, structural, interface, or policy change must create or update an Agent Note in the same PR or commit.

---

## Directory Structure & Path Schema

All notes follow the path convention:

```
.agents/notes/{lifecycle}/{classification}/YYYY-MM-DD-title.md
```

### 1. Lifecycles (`{lifecycle}`)

| Lifecycle | Description | Header Status |
| :--- | :--- | :--- |
| `proposed/` | Active proposals under consideration before implementation | `Status: proposed` |
| `implemented/` | Shipped reality. Kept strictly up to date with code facts | `Status: implemented` |
| `rejected/` | Considered and declined proposals preserved for historical context | `Status: rejected — <reason>` |
| `archived/` | Mature or superseded decisions retired from the active tree | `Status: implemented`<br>`Archived: YYYY-MM-DD` |

### 2. Classifications (`{classification}`)

- `architecture`: Subsystem boundaries, module layout, execution models, and dependency structures.
- `feature`: User-facing CLI commands, pipeline stages, or target build capabilities.
- `bug-fix`: Structural fixes for subtle, multi-component, or recurring defects.
- `simplification`: Refactoring, removing dead paths, or reducing surface area without altering behavior.
- `process`: Development workflows, CI gates, tooling, and repository governance policies.
- `testing`: Test infrastructure, mock strategies, and quality coverage gates.

---

## Header Specification

Every note must begin with the exact header format:

```markdown
# Agent Note: <Title>

Status: <status>
```

For archived notes, the `Archived:` date marker follows immediately after `Status:`:

```markdown
# Agent Note: <Title>

Status: implemented
Archived: YYYY-MM-DD
```

---

## Required Section Skeletons

### Proposed Note Skeleton (`proposed/`)

```markdown
# Agent Note: <Title>

Status: proposed

## Problem
Background context and problem statement without presupposing the solution.

## Proposal
Detailed design, pipeline changes, CLI interface updates, or module contracts.

## Alternatives considered
Alternative architectures or approaches evaluated, and why they were rejected.

## Acceptance criteria
Observable criteria, test cases, and verification commands defining success.

## Risks
Potential edge cases, host compatibility issues, or build pipeline failure modes.
```

### Implemented Note Skeleton (`implemented/`)

```markdown
# Agent Note: <Title>

Status: implemented

## Problem
The original problem or architectural requirement addressed.

## Decision
The shipped architectural design and concrete mechanisms in present tense.

## Alternatives considered
Alternative approaches considered and why this design was chosen.

## Consequences
Trade-offs, operational benefits, invariants established, and constraints.
```

---

## Lifecycle Transitions

1. **Proposal -> Implementation**:
   - Move from `proposed/{class}/...` to `implemented/{class}/...`.
   - Update `Status: proposed` to `Status: implemented`.
   - Rewrite body in present tense (`## Proposal` -> `## Decision`, `## Risks` / `## Acceptance criteria` -> `## Consequences`).
2. **Proposal -> Rejection**:
   - Move to `rejected/{class}/...`.
   - Update `Status: rejected — <one-line reason>`.
3. **Implemented -> Archival**:
   - Move to `archived/{class}/...`.
   - Append `Archived: YYYY-MM-DD` under `Status: implemented`.
   - Update any cross-references in other active notes.

---

## Verification Gate

Run the zero-dependency verification script before committing:

```bash
python3 scripts/gates/verify_agent_gates.py
```
