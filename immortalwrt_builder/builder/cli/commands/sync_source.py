# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.config import TargetConfigProvider
from ...core.sync import sync_source
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("sync-source", "Synchronize source code from Git repository")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("sync-source", help="Synchronize source code from Git repository")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.set_defaults(handler=handle_sync_source)


def handle_sync_source(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    sync_source(
        target,
        layout.target_source_root(work_root, target.name),
        layout.target_cache_root(work_root, target.name),
    )
    return 0
