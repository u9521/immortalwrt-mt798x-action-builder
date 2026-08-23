# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import build_firmware, collect_outputs, write_digest_summary
from ...core.config import TargetConfigProvider
from ...usage_report import write_usage_report
from ..common import add_jobs_argument, add_target_argument, add_verbose_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("build", "Build the configured ImmortalWrt target")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("build", help="Build the configured ImmortalWrt target")
    add_target_argument(parser)
    add_work_root_argument(parser)
    add_jobs_argument(parser)
    add_verbose_argument(parser)
    parser.set_defaults(handler=handle_build)


def handle_build(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    cache_root = layout.target_cache_root(work_root, target.name)
    output_root = layout.target_output_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}. Run 'iwb sync-source' first.")

    build_firmware(target, source_dir, jobs=args.jobs, verbose=args.verbose)
    artifacts = collect_outputs(target, source_dir, output_root)
    if target.output.calculate_digest and artifacts:
        write_digest_summary(work_root, artifacts)

    write_usage_report(target, source_dir, cache_root, output_root)
    return 0
