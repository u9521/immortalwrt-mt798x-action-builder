# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import (
    clean_build,
    clear_ccache,
    resolve_effective_ccache_dir,
    show_ccache_stats,
    zero_ccache_stats,
)
from ...core.config import TargetConfigProvider
from ...core.sync import get_local_head_commit, get_remote_head_commit
from ...usage_report import analyze_workspace_usage, print_usage_report
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("tools", "Run maintenance and helper tools")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("tools", help="Run maintenance and helper tools")
    tool_subparsers = parser.add_subparsers(dest="tool_command", required=True)

    # Subcommand: clean
    clean = tool_subparsers.add_parser("clean", help="Clean build directories and artifacts")
    add_target_argument(clean)
    add_work_root_argument(clean)
    clean.add_argument(
        "--dirclean", action="store_true", help="Run 'make dirclean' (removes staging_dir and toolchain builds)"
    )
    clean.add_argument("--all", action="store_true", help="Remove all build source, cache, and out directories")
    clean.set_defaults(handler=handle_clean)

    # Subcommand: ccache-stats
    ccache_stats = tool_subparsers.add_parser("ccache-stats", help="Display ccache statistics for target")
    add_target_argument(ccache_stats)
    add_work_root_argument(ccache_stats)
    ccache_stats.set_defaults(handler=handle_ccache_stats)

    # Subcommand: ccache-dir
    ccache_dir = tool_subparsers.add_parser("ccache-dir", help="Print resolved ccache directory for target")
    add_target_argument(ccache_dir)
    add_work_root_argument(ccache_dir)
    ccache_dir.set_defaults(handler=handle_ccache_dir)

    # Subcommand: ccache-clean
    ccache_clean = tool_subparsers.add_parser("ccache-clean", help="Clear ccache cache directory for target")
    add_target_argument(ccache_clean)
    add_work_root_argument(ccache_clean)
    ccache_clean.set_defaults(handler=handle_ccache_clean)

    # Subcommand: ccache-zero
    ccache_zero = tool_subparsers.add_parser("ccache-zero", help="Reset ccache statistics counters for target")
    add_target_argument(ccache_zero)
    add_work_root_argument(ccache_zero)
    ccache_zero.set_defaults(handler=handle_ccache_zero)

    # Subcommand: check-update
    check_update = tool_subparsers.add_parser(
        "check-update",
        help="Check if upstream source or local repository has changes compared to last build",
    )
    add_target_argument(check_update)
    add_work_root_argument(check_update)
    check_update.set_defaults(handler=handle_check_update)

    # Subcommand: usage
    usage = tool_subparsers.add_parser("usage", help="Analyze and display workspace disk space usage")
    add_target_argument(usage)
    add_work_root_argument(usage)
    usage.set_defaults(handler=handle_usage)


def handle_clean(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    cache_root = layout.target_cache_root(work_root, target.name)
    output_root = layout.target_output_root(work_root, target.name)

    if args.all:
        print(f"Purging all directories for target {target.name} in {work_root}...", flush=True)
        if source_dir.exists():
            shutil.rmtree(source_dir)
            print(f"  - Removed {source_dir}", flush=True)
        if cache_root.exists():
            shutil.rmtree(cache_root)
            print(f"  - Removed {cache_root}", flush=True)
        if output_root.exists():
            shutil.rmtree(output_root)
            print(f"  - Removed {output_root}", flush=True)
    else:
        if source_dir.exists():
            clean_build(source_dir, dirclean=args.dirclean)
        else:
            print(f"Source directory not found: {source_dir}", flush=True)
    return 0


def handle_ccache_stats(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir)
    show_ccache_stats(ccache_dir, source_dir=source_dir)
    return 0


def handle_ccache_dir(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir)
    print(ccache_dir)
    return 0


def handle_ccache_clean(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir)
    clear_ccache(ccache_dir, source_dir=source_dir)
    return 0


def handle_ccache_zero(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir)
    success = zero_ccache_stats(ccache_dir, source_dir=source_dir)
    return 0 if success else 1


def handle_check_update(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)

    # 1. Get current local commit
    current_local_commit = ""
    try:
        current_local_commit = get_local_head_commit(project_root)
    except Exception:
        pass

    # 2. Get remote upstream commit
    current_remote_commit = ""
    if target.source.url:
        if target.source.commit:
            current_remote_commit = target.source.commit
        elif target.source.tag:
            remote_sha = get_remote_head_commit(target.source.url, target.source.tag)
            if remote_sha:
                current_remote_commit = remote_sha
        elif target.source.branch:
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

    print(f"Target: {target.name}")
    print(f"  Workspace:               {work_root}")
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
