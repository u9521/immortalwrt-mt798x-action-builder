# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import download_packages
from ...core.config import TargetConfigProvider
from ..common import add_jobs_argument, add_target_argument, add_verbose_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("download", "Pre-download all package source tarballs (make download)")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("download", help="Pre-download all package source tarballs (make download)")
    add_target_argument(parser)
    add_work_root_argument(parser)
    add_jobs_argument(parser)
    add_verbose_argument(parser)
    parser.set_defaults(handler=handle_download)


def handle_download(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    download_packages(target, source_dir, jobs=args.jobs, verbose=args.verbose)
    return 0
