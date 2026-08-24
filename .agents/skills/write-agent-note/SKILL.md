---
name: write-agent-note
description: Use when drafting, proposing, updating, or transitioning an Agent Note (RFC/ADR) in the repository to document architectural decisions, rationale, trade-offs, and state changes.
---

# Write & Maintain Agent Notes

Agent Notes are RFCs and Architecture Decision Records (ADRs) written for both human engineers and AI agents working on `immortalwrt-action-builder`.

## When to Write an Agent Note

Every non-trivial change MUST add or update an Agent Note in the same PR or commit. A change is non-trivial when it alters:
- Software architecture, modular structure, or execution models
- Public CLI commands, arguments, or workflow lifecycles
- Patch execution interfaces or target configuration schemas
- Development policies, verification gates, or testing strategies

---

## Path & Lifecycle Structure

Every note's path encodes its state and topic:
`.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-topic-title.md`

### 1. Lifecycles (`{lifecycle}`)
- **`proposed/`**: A proposal under review before full implementation.
- **`implemented/`**: Shipped reality. Kept strictly up to date with code facts in present tense.
- **`rejected/`**: Considered and declined. Preserved only when the rationale prevents future repeated mistakes.
- **`archived/`**: Mature or superseded notes retired from the active tree.

### 2. Classes (`{class}`)
- `architecture`: Structural design of the source code and subsystems.
- `feature`: A new user-facing CLI command or build capability.
- `bug-fix`: Corrects a subtle defect or systemic gap.
- `simplification`: Removes code, complexity, or surface area without adding capabilities.
- `process`: Development workflows, CI gates, tooling, and policies.
- `testing`: Testing infrastructure and coverage strategies.

---

## File Format & Header Skeletons

### The Exact Header
Lines 1-3 must strictly follow:
```markdown
# Agent Note: <Title>

Status: <status>
```
Where `<status>` is:
- `Status: proposed` (if in `proposed/`)
- `Status: implemented` (if in `implemented/`)
- `Status: rejected — <one-line reason>` (if in `rejected/`)

For `archived/` notes, line 4 must contain:
```markdown
Archived: YYYY-MM-DD
```

---

## Section Skeletons

### Body Skeleton: `proposed/`
```markdown
## Problem
Describe the background and motivation clearly without presupposing the solution.

## Proposal
Detailed design, data flows, and planned changes (may use future tense).

## Alternatives considered
What other approaches were evaluated, and why were they declined? (Mandatory section).

## Acceptance criteria
Observable facts and checks that define completion.

## Risks
Potential edge cases, failure modes, or intentional trade-offs.
```

### Body Skeleton: `implemented/`
```markdown
## Problem
The core problem solved.

## Decision
The shipped architectural decision and concrete mechanisms (written in present tense).

## Alternatives considered
Alternative approaches considered and rejected during the design phase.

## Consequences
Trade-offs, benefits gained, constraints introduced, and long-term implications.
```

---

## Transitioning from Proposal to Implemented

When code implementation finishes:
1. Move the file from `.agents/notes/proposed/{class}/...` to `.agents/notes/implemented/{class}/...`.
2. Update the status line to `Status: implemented`.
3. Rewrite the body in present tense: replace `## Proposal` with `## Decision`, and replace `## Risks` / `## Acceptance criteria` with `## Consequences`.
4. Update any code paths, names, or defaults to match the exact shipped code.
5. Run the local gate script:
   ```bash
   python3 scripts/gates/verify_agent_gates.py
   ```
