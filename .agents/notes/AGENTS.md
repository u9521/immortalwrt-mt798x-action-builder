# Agent Instructions: Notes Tree

This directory contains Architecture Decision Records (ADRs) and RFCs for `immortalwrt-action-builder`.

## Governance Rules

1. **Path-Encoded State**: The folder hierarchy (`proposed/`, `implemented/`, `rejected/`, `archived/`) defines the state. Never put a note in an arbitrary directory.
2. **Synchronized Facts**: Notes in `implemented/` represent current ground truth. When code changes, update existing notes in `implemented/` or add a new one.
3. **Mandatory Alternatives Section**: Every note must evaluate at least one alternative to document the rationale.
4. **Zero Broken Links**: Cross-note references must use valid relative Markdown links.
5. **Validation**: Always verify notes using `python3 scripts/gates/verify_agent_gates.py`.
