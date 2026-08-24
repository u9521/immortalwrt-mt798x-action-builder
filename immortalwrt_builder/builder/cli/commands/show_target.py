# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ...core.config import TargetConfigProvider
from ..common import add_target_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("show-target", "Show resolved target configuration")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("show-target", help="Show resolved target configuration")
    add_target_argument(parser)
    add_work_root_argument(parser)
    parser.add_argument("--json", action="store_true", help="Print configuration as JSON")
    parser.set_defaults(handler=handle_show_target)


def handle_show_target(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)

    payload = {
        "name": target.name,
        "base": target.base,
        "config_path": str(target.config_path),
        "work_root": str(work_root),
        "source": {
            "url": target.source.url,
            "branch": target.source.branch,
            "tag": target.source.tag,
            "commit": target.source.commit,
            "depth": target.source.depth,
            "submodules": target.source.submodules,
        },
        "patch": {
            "pre_feeds_patches": [str(p) for p in target.patch.pre_feeds_patches],
            "post_feeds_patches": [str(p) for p in target.patch.post_feeds_patches],
            "post_config_patches": [str(p) for p in target.patch.post_config_patches],
        },
        "patch_config": target.patch_config,
        "build": {
            "defconfig_path": str(target.build.defconfig_path) if target.build.defconfig_path else None,
            "jobs": target.build.jobs,
            "verbose": target.build.verbose,
            "download": target.build.download,
            "ignore_errors": target.build.ignore_errors,
        },
        "ccache": {
            "enabled": target.ccache.enabled,
            "dir": str(target.ccache.dir) if target.ccache.dir else None,
            "max_size": target.ccache.max_size,
            "stats_log": target.ccache.stats_log,
            "compiler_check": target.ccache.compiler_check,
            "sloppiness": target.ccache.sloppiness,
            "hash_dir": target.ccache.hash_dir,
            "base_dir": str(target.ccache.base_dir) if target.ccache.base_dir else None,
            "log_file": target.ccache.log_file,
        },
        "toolchain_cache": {
            "enabled": target.toolchain_cache.enabled,
            "dir": str(target.toolchain_cache.dir) if target.toolchain_cache.dir else None,
            "auto_restore": target.toolchain_cache.auto_restore,
            "auto_save": target.toolchain_cache.auto_save,
        },
        "output": {
            "dist_dir": target.output.dist_dir,
            "target_dir": target.output.target_dir,
            "packages_dir": target.output.packages_dir,
            "calculate_digest": target.output.calculate_digest,
            "firmware_patterns": target.output.firmware_patterns,
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"\nTarget: {target.name}")
        print(f"  Config: {target.config_path}")
        print(f"  Workspace: {work_root}")
        if target.source.commit:
            ref_desc = f"commit: {target.source.commit}"
        elif target.source.tag:
            ref_desc = f"tag: {target.source.tag}"
        elif target.source.branch:
            ref_desc = f"branch: {target.source.branch}"
        else:
            ref_desc = "HEAD"
        print(f"  Source URL: {target.source.url} ({ref_desc})")
        print(f"  Defconfig: {target.build.defconfig_path or '(none)'}")
        print(f"  Jobs: {target.build.jobs}, Verbose: {target.build.verbose}")
        print(f"  ccache: enabled={target.ccache.enabled}, max_size={target.ccache.max_size}")
        print(f"  Toolchain Cache: enabled={target.toolchain_cache.enabled}")
        if target.patch.pre_feeds_patches:
            print(f"  Pre-feeds Patches: {', '.join(p.name for p in target.patch.pre_feeds_patches)}")
        if target.patch.post_feeds_patches:
            print(f"  Post-feeds Patches: {', '.join(p.name for p in target.patch.post_feeds_patches)}")
        if target.patch.post_config_patches:
            print(f"  Post-config Patches: {', '.join(p.name for p in target.patch.post_config_patches)}")
        if target.patch_config:
            print(f"  Patch Config ({len(target.patch_config)} items):")
            for k, v in target.patch_config.items():
                print(f"    - {k}: {v}")
        print(f"  Output directory: {work_root / 'out' / (target.output.dist_dir or target.name)}\n")
    return 0
