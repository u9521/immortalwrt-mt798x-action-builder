# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import clean_build, clear_ccache, resolve_effective_ccache_dir, show_ccache_stats
from ...core.config import TargetConfigProvider
from ...utils import run_command
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("tools", "Run maintenance and helper tools")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("tools", help="Run maintenance and helper tools")
    tool_subparsers = parser.add_subparsers(dest="tool_command", required=True)

    # Subcommand: add-git-safe
    git_safe = tool_subparsers.add_parser("add-git-safe", help="Add directories to Git safe.directory")
    git_safe.add_argument("path", help="Directory path to add")
    git_safe.add_argument("-r", "--recursive", action="store_true", help="Also add nested Git repositories")
    git_safe.set_defaults(handler=handle_add_git_safe)

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


def handle_add_git_safe(args: argparse.Namespace) -> int:
    input_path = Path(args.path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Path does not exist: {input_path}")
    if not input_path.is_dir():
        raise ValueError(f"Path must be a directory: {input_path}")

    global_safe = _load_git_safe_directories(system=False)
    system_safe = _load_git_safe_directories(system=True)
    candidates = _collect_git_safe_candidates(input_path, args.recursive)

    global_added: list[Path] = []
    system_added: list[Path] = []

    for candidate in candidates:
        candidate_text = str(candidate)
        if candidate_text not in global_safe:
            run_command(["git", "config", "--global", "--add", "safe.directory", candidate_text], capture_output=True)
            global_safe.add(candidate_text)
            global_added.append(candidate)

        if candidate_text not in system_safe:
            run_command(["git", "config", "--system", "--add", "safe.directory", candidate_text], capture_output=True)
            system_safe.add(candidate_text)
            system_added.append(candidate)

    print(f"Global safe.directory: added {len(global_added)} entries", flush=True)
    for p in global_added:
        print(f"  + {p}", flush=True)
    print(f"System safe.directory: added {len(system_added)} entries", flush=True)
    for p in system_added:
        print(f"  + {p}", flush=True)
    return 0


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


def _load_git_safe_directories(*, system: bool) -> set[str]:
    scope = "--system" if system else "--global"
    result = run_command(["git", "config", scope, "--get-all", "safe.directory"], check=False, capture_output=True)
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _collect_git_safe_candidates(root_path: Path, recursive: bool) -> list[Path]:
    candidates: list[Path] = [root_path]
    if recursive:
        for current_root, dirnames, _ in os.walk(root_path):
            current_path = Path(current_root)
            if current_path == root_path:
                continue
            if ".git" in dirnames:
                candidates.append(current_path.resolve())
                dirnames.remove(".git")
    return _dedupe_paths(candidates)


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        text = str(path)
        if text in seen:
            continue
        seen.add(text)
        unique.append(path)
    return unique
