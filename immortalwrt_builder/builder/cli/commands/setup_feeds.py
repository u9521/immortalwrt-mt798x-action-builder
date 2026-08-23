# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.config import TargetConfigProvider
from ...core.feeds import setup_feeds
from ...core.patch import apply_post_feeds_patches, apply_pre_feeds_patches
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("setup-feeds", "Setup package feeds and execute pre/post Python patches")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("setup-feeds", help="Setup package feeds and execute pre/post Python patches")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--skip-patches", "--skip-diy", action="store_true", help="Skip executing Python patch scripts")
    parser.set_defaults(handler=handle_setup_feeds)


def handle_setup_feeds(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    skip_patch = getattr(args, "skip_patches", False) or getattr(args, "skip_diy", False)
    if not skip_patch:
        apply_pre_feeds_patches(target, source_dir, work_root)

    setup_feeds(target, source_dir)

    if not skip_patch:
        apply_post_feeds_patches(target, source_dir, work_root)

    return 0
