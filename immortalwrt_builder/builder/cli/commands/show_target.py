# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ...core.config import TargetConfigProvider
from ..common import add_target_argument
from ..registry import register_command


@register_command("show-target", "Show resolved target configuration")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("show-target", help="Show resolved target configuration")
    add_target_argument(parser)
    parser.add_argument("--json", action="store_true", help="Print configuration as JSON")
    parser.set_defaults(handler=handle_show_target)


def handle_show_target(args: argparse.Namespace) -> int:
    work_root = Path.cwd()
    target = TargetConfigProvider(work_root).load(args.target)

    payload = {
        "name": target.name,
        "base": target.base,
        "config_path": str(target.config_path),
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
            "pre_feeds_scripts": [str(p) for p in target.patch.pre_feeds_scripts],
            "post_feeds_scripts": [str(p) for p in target.patch.post_feeds_scripts],
            "post_config_scripts": [str(p) for p in target.patch.post_config_scripts],
            "custom_files": str(target.patch.custom_files) if target.patch.custom_files else None,
            "ip_address": target.patch.ip_address,
            "hostname": target.patch.hostname,
            "wifi_ssid_2g": target.patch.wifi_ssid_2g,
            "wifi_ssid_5g": target.patch.wifi_ssid_5g,
            "default_theme": target.patch.default_theme,
            "distrib_description": target.patch.distrib_description,
            "distrib_revision": target.patch.distrib_revision,
        },
        "build": {
            "defconfig_path": str(target.build.defconfig_path) if target.build.defconfig_path else None,
            "target_profile": target.build.target_profile,
            "extra_configs": target.build.extra_configs,
            "jobs": target.build.jobs,
            "verbose": target.build.verbose,
            "download": target.build.download,
            "use_ccache": target.build.use_ccache,
            "ignore_errors": target.build.ignore_errors,
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
        print(f"  Source URL: {target.source.url} (branch: {target.source.branch or 'HEAD'})")
        print(f"  Defconfig: {target.build.defconfig_path or '(none)'}")
        print(f"  Jobs: {target.build.jobs}, Verbose: {target.build.verbose}")
        if target.patch.pre_feeds_scripts:
            print(f"  Pre-feeds DIY: {', '.join(p.name for p in target.patch.pre_feeds_scripts)}")
        if target.patch.post_feeds_scripts:
            print(f"  Post-feeds DIY: {', '.join(p.name for p in target.patch.post_feeds_scripts)}")
        if target.feeds.custom_feeds:
            print(f"  Custom feeds ({len(target.feeds.custom_feeds)}):")
            for f in target.feeds.custom_feeds:
                print(f"    - {f}")
        print(f"  Output directory: out/{target.output.dist_dir or target.name}\n")
    return 0
