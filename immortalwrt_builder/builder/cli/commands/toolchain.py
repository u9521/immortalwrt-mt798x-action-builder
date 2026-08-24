# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import (
    clear_toolchain_cache,
    compute_toolchain_key,
    resolve_toolchain_archive_path,
    restore_toolchain_cache,
    save_toolchain_cache,
    touch_toolchain_stamps,
)
from ...core.config import TargetConfigProvider
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("toolchain-key", "Print calculated toolchain cache key for target")
def build_key_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("toolchain-key", help="Print calculated toolchain cache key for target")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.set_defaults(handler=handle_toolchain_key)


@register_command("toolchain-save", "Archive and save compiled toolchain for target")
def build_save_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("toolchain-save", help="Archive and save compiled toolchain for target")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--output", type=str, default=None, help="Custom output archive path")
    parser.set_defaults(handler=handle_toolchain_save)


@register_command("toolchain-restore", "Restore toolchain cache and refresh stamps for target")
def build_restore_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("toolchain-restore", help="Restore toolchain cache and refresh stamps for target")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--input", type=str, default=None, help="Custom input archive path")
    parser.set_defaults(handler=handle_toolchain_restore)


@register_command("toolchain-touch", "Touch toolchain stamp files to prevent rebuilds")
def build_touch_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("toolchain-touch", help="Touch toolchain stamp files to prevent rebuilds")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.set_defaults(handler=handle_toolchain_touch)


@register_command("toolchain-clean", "Remove saved toolchain cache archive for target")
def build_clean_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("toolchain-clean", help="Remove saved toolchain cache archive for target")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.set_defaults(handler=handle_toolchain_clean)


def handle_toolchain_key(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    key = compute_toolchain_key(target, source_dir, work_root=work_root)
    print(key)
    return 0


def handle_toolchain_save(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    archive_path = Path(args.output).resolve() if args.output else resolve_toolchain_archive_path(target, work_root)
    save_toolchain_cache(target, source_dir, archive_path)
    return 0


def handle_toolchain_restore(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    archive_path = Path(args.input).resolve() if args.input else resolve_toolchain_archive_path(target, work_root)
    if not archive_path.exists():
        print(f"Toolchain archive not found: {archive_path}", flush=True)
        return 1

    success = restore_toolchain_cache(target, source_dir, archive_path)
    return 0 if success else 1


def handle_toolchain_touch(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    touched = touch_toolchain_stamps(source_dir)
    print(f"Refreshed {touched} toolchain stamp files in {source_dir / 'staging_dir'}")
    return 0


def handle_toolchain_clean(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)

    removed = clear_toolchain_cache(target, work_root)
    if not removed:
        print(f"No toolchain archive found for target '{target.name}'.")
    return 0
