# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import (
    build_firmware,
    collect_outputs,
    download_packages,
    prepare_config,
    write_digest_summary,
)
from ...core.config import TargetConfigProvider
from ...core.feeds import setup_feeds
from ...core.patch import (
    apply_post_config_patches,
    apply_post_feeds_patches,
    apply_pre_feeds_patches,
)
from ...core.sync import sync_source
from ...usage_report import write_usage_report
from ..common import add_jobs_argument, add_target_argument, add_verbose_argument, add_work_root_argument, get_work_root
from ..registry import register_command


@register_command("run", "Run full end-to-end build pipeline (sync -> feeds -> config -> download -> build -> digest)")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "run",
        help="Run full end-to-end build pipeline (sync -> feeds -> config -> download -> build -> digest)",
    )
    add_target_argument(parser)
    add_work_root_argument(parser)
    add_jobs_argument(parser)
    add_verbose_argument(parser)
    parser.add_argument("--skip-patches", "--skip-diy", action="store_true", help="Skip executing Python patch scripts")
    parser.add_argument("--skip-download", action="store_true", help="Skip package download step")
    parser.set_defaults(handler=handle_run_all)


def handle_run_all(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    work_root = get_work_root(args, project_root)
    target = TargetConfigProvider(project_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    cache_root = layout.target_cache_root(work_root, target.name)
    output_root = layout.target_output_root(work_root, target.name)

    skip_patch = getattr(args, "skip_patches", False) or getattr(args, "skip_diy", False)

    print("\n=======================================================", flush=True)
    print(f"  Starting Full ImmortalWrt Build Pipeline: {target.name}", flush=True)
    print(f"  Workspace: {work_root}", flush=True)
    print("=======================================================\n", flush=True)

    # Step 1: Sync Source
    print("\n>>> [1/6] Synchronizing source code...", flush=True)
    sync_source(target, source_dir, cache_root)

    # Step 2: Feeds & Python Patches
    print("\n>>> [2/6] Setting up package feeds & applying pre/post Python patches...", flush=True)
    if not skip_patch:
        apply_pre_feeds_patches(target, source_dir, work_root)
    setup_feeds(target, source_dir)
    if not skip_patch:
        apply_post_feeds_patches(target, source_dir, work_root)

    # Step 3: Configure Target (Defconfig + Post-config patches)
    print("\n>>> [3/6] Configuring target (.config)...", flush=True)
    prepare_config(target, source_dir)
    if not skip_patch:
        apply_post_config_patches(target, source_dir, work_root)

    # Step 4: Download Packages
    if not args.skip_download and target.build.download:
        print("\n>>> [4/6] Pre-downloading packages...", flush=True)
        download_packages(target, source_dir, jobs=args.jobs, verbose=args.verbose)
    else:
        print("\n>>> [4/6] Skipping package pre-download.", flush=True)

    # Step 5: Build Firmware
    print("\n>>> [5/6] Building firmware...", flush=True)
    build_firmware(target, source_dir, jobs=args.jobs, verbose=args.verbose)

    # Step 6: Collect Outputs & Generate Digest
    print("\n>>> [6/6] Collecting outputs and calculating digests...", flush=True)
    artifacts = collect_outputs(target, source_dir, output_root)
    if target.output.calculate_digest and artifacts:
        write_digest_summary(work_root, artifacts)

    write_usage_report(target, source_dir, cache_root, output_root)

    print("\n=======================================================", flush=True)
    print(f"  Build Pipeline Complete! Artifacts in: {output_root}", flush=True)
    print("=======================================================\n", flush=True)
    return 0
