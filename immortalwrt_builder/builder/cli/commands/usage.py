# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.config import TargetConfigProvider
from ...usage_report import analyze_workspace_usage, print_usage_report
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("usage", "Analyze and display workspace disk space usage")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("usage", help="Analyze and display workspace disk space usage")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.set_defaults(handler=handle_usage)


def handle_usage(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    cache_root = layout.target_cache_root(work_root, target.name)
    output_root = layout.target_output_root(work_root, target.name)

    report = analyze_workspace_usage(target, source_dir, cache_root, output_root)
    print_usage_report(report)
    return 0
