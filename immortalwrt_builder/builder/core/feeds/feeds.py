# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

from ...utils import run_command


def update_feeds(source_dir: Path) -> None:
    print("Updating package feeds (./scripts/feeds update -a)...", flush=True)
    feeds_script = source_dir / "scripts" / "feeds"
    if feeds_script.exists():
        run_command(["./scripts/feeds", "update", "-a"], cwd=source_dir)
    else:
        print(f"Warning: feeds script not found at {feeds_script}", flush=True)


def install_feeds(source_dir: Path) -> None:
    print("Installing package feeds (./scripts/feeds install -a)...", flush=True)
    feeds_script = source_dir / "scripts" / "feeds"
    if feeds_script.exists():
        run_command(["./scripts/feeds", "install", "-a"], cwd=source_dir)
    else:
        print(f"Warning: feeds script not found at {feeds_script}", flush=True)
