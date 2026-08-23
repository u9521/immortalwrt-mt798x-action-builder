# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ... import layout
from ...core.config import TargetConfigProvider
from ...core.sync import get_local_head_commit, get_remote_head_commit
from ..common import add_target_argument
from ..registry import register_command


@register_command("check-update", "Check if upstream source or local repository has changes")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "check-update",
        help="Check if upstream source or local repository has changes compared to last build",
    )
    add_target_argument(parser)
    parser.set_defaults(handler=handle_check_update)


def handle_check_update(args: argparse.Namespace) -> int:
    work_root = Path.cwd()
    target = TargetConfigProvider(work_root).load(args.target)

    # 1. Get current local commit
    current_local_commit = ""
    try:
        current_local_commit = get_local_head_commit(work_root)
    except Exception:
        pass

    # 2. Get remote upstream commit
    current_remote_commit = ""
    if target.source.url and target.source.branch:
        remote_sha = get_remote_head_commit(target.source.url, target.source.branch)
        if remote_sha:
            current_remote_commit = remote_sha

    # 3. Read cached build metadata
    metadata_file = layout.target_metadata_file(work_root, target.name)
    cached_local = ""
    cached_upstream = ""

    if metadata_file.exists():
        try:
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            cached_local = str(data.get("last_local_commit", ""))
            cached_upstream = str(data.get("last_upstream_commit", ""))
        except Exception:
            pass

    # Fallback to infos/ directory
    infos_dir = layout.infos_root(work_root)
    if not cached_local and (infos_dir / "lastCommit").exists():
        cached_local = (infos_dir / "lastCommit").read_text(encoding="utf-8").strip()
    if not cached_upstream and (infos_dir / "lastUpstreamCommit").exists():
        cached_upstream = (infos_dir / "lastUpstreamCommit").read_text(encoding="utf-8").strip()

    print(f"Target: {target.name}")
    print(f"  Current local commit:    {current_local_commit or '(unknown)'}")
    print(f"  Cached local commit:     {cached_local or '(none)'}")
    print(f"  Current upstream commit: {current_remote_commit or '(unknown)'}")
    print(f"  Cached upstream commit:  {cached_upstream or '(none)'}")

    if (
        cached_local
        and cached_upstream
        and current_local_commit == cached_local
        and current_remote_commit == cached_upstream
    ):
        print("\nAll repositories are up to date with the previous build (no changes detected).", flush=True)
        return 1

    print("\nChanges detected or no previous build cache found. Build required.", flush=True)
    return 0
