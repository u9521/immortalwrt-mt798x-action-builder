# AGENTS.md

Guidance for coding agents working in `immortalwrt-action-builder`.

## Scope

- Python 3.14+ project with CLI entry point `iwb`.
- Pure Python standard library (no external Python package runtime dependencies).
- Host/CI execution mode: commands run from the project root as the work root.
- Clean core framework: standard OpenWrt lifecycle in core, customizations via Python patches in `patchs/`.
- Prefer small, behavior-preserving edits unless the task clearly needs a larger refactor.

## Project Layout

- Source package: `immortalwrt_builder/builder/`
- Tests: `immortalwrt_builder/tests/`
- Checked-in target inputs: `immortalwrt_builder/configs/targets/`
- Checked-in defconfigs & fragments: `immortalwrt_builder/configs/defconfigs/`
- Checked-in Python patch scripts: `immortalwrt_builder/configs/patchs/`
- Reference docs: `immortalwrt_builder/docs/`
- Agent Notes & ADRs: `.agents/notes/`
- Verification Gates: `scripts/gates/`

## Setup Commands

- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Install editable package with dev deps: `uv sync --dev`

## Common Commands

- CLI help: `uv run iwb --help`
- Show target: `uv run iwb show-target --target official-mt7981-ax3000m`
- Sync source: `uv run iwb sync-source --target official-mt7981-ax3000m`
- Update feeds & pre-patches: `uv run iwb feeds-update --target official-mt7981-ax3000m`
- Install feeds & post-patches: `uv run iwb feeds-install --target official-mt7981-ax3000m`
- Configure (.config + fragments): `uv run iwb configure --target official-mt7981-ax3000m`
- Download packages: `uv run iwb download --target official-mt7981-ax3000m`
- Build firmware: `uv run iwb build --target official-mt7981-ax3000m`
- Calculate digest: `uv run iwb digest --target official-mt7981-ax3000m`
- Print workspace disk usage: `uv run iwb tools usage --target official-mt7981-ax3000m`

## Test, Lint & Verification Commands

- Full test suite: `python3 -m unittest discover -s immortalwrt_builder/tests`
- Verification gates: `python3 scripts/gates/verify_agent_gates.py`
- Ruff format: `uv run ruff format .`
- Ruff lint: `uv run ruff check --fix .`
- Pyright type check: `npx pyright` (or `npx --cache /tmp/npm-cache pyright`)

## Agent-Native Governance & Invariants

1. **Safety & Code Modification Boundary**:
   - Direct changes without confirmation are limited to specification and governance paths: `AGENTS.md`, `.agents/**`, `docs/**`, and `scripts/gates/**`.
   - Modifying existing application/production source code or build configuration files requires explicit user confirmation.
2. **Agent Notes Requirement**:
   - Every non-trivial change (architecture, interfaces, policies, pipeline workflows) must create or update an Agent Note in `.agents/notes/` in the same commit.
   - See [.agents/notes/README.md](.agents/notes/README.md) for note lifecycle rules and headers.
3. **One Home Per Fact**:
   - Link to canonical locations rather than duplicating rules or descriptions across multiple files.
4. **Wordcount Budget**:
   - Root `AGENTS.md` target budget is <= 1,500 words.

## File Creation Rules

- New Python files should start with:
  - `# SPDX-License-Identifier: GPL-3.0-only`
  - `# Copyright (C) 2026 u9521`
- In Python files, put `from __future__ import annotations` immediately after the header.

## Imports & Formatting

- Order imports as:
  1. future import (`from __future__ import annotations`)
  2. standard library imports
  3. local package imports
- 4-space indentation.
- Double quotes in Python files.
- Prefer `pathlib.Path` operations over manual string paths.
- Write JSON as `json.dumps(..., indent=2, sort_keys=True) + "\n"`.

## Patch System

- All patch scripts must be Python (`.py`) files located under `immortalwrt_builder/configs/patchs/`.
- Must define `def patch(context: PatchContext) -> None:` (or `def run(context: PatchContext) -> None:`).
- `context.target` exposes the full `TargetConfig`.
- Context provides helpers: `path`, `exists`, `read_text`, `write_text`, `append_text`, `replace_text`, `remove`, `run_command`.
