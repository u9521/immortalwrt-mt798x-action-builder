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

## Setup Commands

- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Install editable package with dev deps: `uv sync --dev`

## Common Commands

- CLI help: `uv run iwb --help`
- Show target: `uv run iwb show-target --target official-mt7981-ax3000m`
- Sync source: `uv run iwb sync-source --target official-mt7981-ax3000m`
- Setup feeds & patches: `uv run iwb setup-feeds --target official-mt7981-ax3000m`
- Configure (.config + fragments): `uv run iwb configure --target official-mt7981-ax3000m`
- Download packages: `uv run iwb download --target official-mt7981-ax3000m`
- Build firmware: `uv run iwb build --target official-mt7981-ax3000m`
- Calculate digest: `uv run iwb digest --target official-mt7981-ax3000m`
- Run full pipeline: `uv run iwb run --target official-mt7981-ax3000m`
- Print workspace disk usage: `uv run iwb usage`

## Test & Lint Commands

- Full suite: `uv run python -m unittest discover -s immortalwrt_builder/tests`
- Ruff format: `uv run ruff format .`
- Ruff lint: `uv run ruff check --fix .`
- Pyright type check: `npx pyright`

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
