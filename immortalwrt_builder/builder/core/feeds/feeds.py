# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import shutil
from pathlib import Path

from ...utils import run_command
from ..config.schema import TargetConfig


def setup_feeds(target: TargetConfig, source_dir: Path) -> None:
    source_dir = source_dir.resolve()
    feeds_conf_default = source_dir / "feeds.conf.default"

    if target.feeds.conf_file is not None and target.feeds.conf_file.exists():
        print(f"Copying custom feeds configuration from {target.feeds.conf_file}...", flush=True)
        shutil.copyfile(target.feeds.conf_file, feeds_conf_default)

    if target.feeds.custom_feeds:
        print("Appending custom feeds to feeds.conf.default...", flush=True)
        current_content = feeds_conf_default.read_text(encoding="utf-8") if feeds_conf_default.exists() else ""
        lines_to_add: list[str] = []
        for feed_line in target.feeds.custom_feeds:
            feed_line = feed_line.strip()
            if feed_line and feed_line not in current_content:
                lines_to_add.append(feed_line)

        if lines_to_add:
            with feeds_conf_default.open("a", encoding="utf-8") as f:
                if current_content and not current_content.endswith("\n"):
                    f.write("\n")
                for line in lines_to_add:
                    f.write(f"{line}\n")
                    print(f"  + {line}", flush=True)

    if target.feeds.update:
        update_feeds(source_dir)

    if target.feeds.install:
        install_feeds(source_dir)


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
