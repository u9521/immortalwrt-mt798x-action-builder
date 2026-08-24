# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import prepare_config
from ...core.config import TargetConfigProvider
from ...core.patch import apply_post_config_patches
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("configure", "Configure OpenWrt target using defconfig and post-config patches")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "configure",
        help="Configure OpenWrt target using defconfig and post-config patches",
    )
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--skip-patches", action="store_true", help="Skip executing Python patch scripts")
    parser.set_defaults(handler=handle_configure)


def handle_configure(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    prepare_config(target, source_dir)

    if not getattr(args, "skip_patches", False):
        apply_post_config_patches(target, source_dir, work_root)

    return 0
