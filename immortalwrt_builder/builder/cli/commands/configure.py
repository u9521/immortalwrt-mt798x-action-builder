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
from ..common import add_target_argument
from ..registry import register_command


@register_command("configure", "Configure OpenWrt target using defconfig and extra settings")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("configure", help="Configure OpenWrt target using defconfig and extra settings")
    add_target_argument(parser)
    parser.set_defaults(handler=handle_configure)


def handle_configure(args: argparse.Namespace) -> int:
    work_root = Path.cwd()
    target = TargetConfigProvider(work_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    prepare_config(target, source_dir)
    apply_post_config_patches(target, source_dir)
    return 0
