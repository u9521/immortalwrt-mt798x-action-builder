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
        "feeds": {
            "update": target.feeds.update,
            "install": target.feeds.install,
            "custom_feeds": target.feeds.custom_feeds,
            "conf_file": str(target.feeds.conf_file) if target.feeds.conf_file else None,
        },
        "patch": {
            "pre_feeds_patches": [str(p) for p in target.patch.pre_feeds_patches],
            "post_feeds_patches": [str(p) for p in target.patch.post_feeds_patches],
            "post_config_patches": [str(p) for p in target.patch.post_config_patches],
        },
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
            "export_stats": target.ccache.export_stats,
            "stats_log": target.ccache.stats_log,
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
        print(f"  Source URL: {target.source.url} (branch: {target.source.branch or 'HEAD'})")
        print(f"  Defconfig: {target.build.defconfig_path or '(none)'}")
        print(f"  Jobs: {target.build.jobs}, Verbose: {target.build.verbose}")
        print(f"  ccache: enabled={target.ccache.enabled}, max_size={target.ccache.max_size}")
        if target.patch.pre_feeds_patches:
            print(f"  Pre-feeds Patches: {', '.join(p.name for p in target.patch.pre_feeds_patches)}")
        if target.patch.post_feeds_patches:
            print(f"  Post-feeds Patches: {', '.join(p.name for p in target.patch.post_feeds_patches)}")
        if target.patch.post_config_patches:
            print(f"  Post-config Patches: {', '.join(p.name for p in target.patch.post_config_patches)}")
        if target.feeds.custom_feeds:
            print(f"  Custom feeds ({len(target.feeds.custom_feeds)}):")
            for f in target.feeds.custom_feeds:
                print(f"    - {f}")
        print(f"  Output directory: {work_root / 'out' / (target.output.dist_dir or target.name)}\n")
    return 0
