# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.config import TargetConfigProvider
from ...core.feeds import install_feeds, update_feeds
from ...core.patch import apply_post_feeds_patches, apply_pre_feeds_patches
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("feeds-update", "Update package feeds and apply pre-feeds Python patches")
def build_update_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("feeds-update", help="Update package feeds and apply pre-feeds Python patches")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--skip-patches", action="store_true", help="Skip executing pre-feeds Python patch scripts")
    parser.set_defaults(handler=handle_feeds_update)


@register_command("feeds-install", "Install package feeds and apply post-feeds Python patches")
def build_install_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("feeds-install", help="Install package feeds and apply post-feeds Python patches")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--skip-patches", action="store_true", help="Skip executing post-feeds Python patch scripts")
    parser.set_defaults(handler=handle_feeds_install)


def handle_feeds_update(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    skip_patch = getattr(args, "skip_patches", False)
    if not skip_patch:
        apply_pre_feeds_patches(target, source_dir, work_root)

    update_feeds(source_dir)
    return 0


def handle_feeds_install(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    install_feeds(source_dir)

    skip_patch = getattr(args, "skip_patches", False)
    if not skip_patch:
        apply_post_feeds_patches(target, source_dir, work_root)

    return 0
