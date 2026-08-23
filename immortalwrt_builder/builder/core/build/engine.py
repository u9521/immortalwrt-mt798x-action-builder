# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ... import layout
from ...utils import run_command
from ..config.schema import TargetConfig
from .ccache import (
    export_ccache_stats,
    is_openwrt_ccache_enabled,
    print_ccache_banner,
    resolve_effective_ccache_dir,
    setup_ccache_environment,
    show_ccache_stats,
)


def prepare_config(target: TargetConfig, source_dir: Path) -> Path:
    source_dir = source_dir.resolve()
    dot_config = source_dir / ".config"

    if target.build.defconfig_path is not None and target.build.defconfig_path.exists():
        print(f"Applying defconfig from {target.build.defconfig_path}...", flush=True)
        shutil.copyfile(target.build.defconfig_path, dot_config)
    elif not dot_config.exists():
        dot_config.touch()

    print("Generating configuration (make defconfig)...", flush=True)
    run_command(["make", "defconfig"], cwd=source_dir)
    return dot_config


def download_packages(
    target: TargetConfig,
    source_dir: Path,
    *,
    jobs: int | None = None,
    verbose: bool | None = None,
) -> None:
    source_dir = source_dir.resolve()
    resolved_jobs = jobs or target.build.jobs or (os.cpu_count() or 1)
    is_verbose = verbose if verbose is not None else target.build.verbose

    cmd = ["make", "download", f"-j{resolved_jobs}"]
    if is_verbose:
        cmd.append("V=s")

    print(f"Downloading source packages (make download -j{resolved_jobs})...", flush=True)
    run_command(cmd, cwd=source_dir)

    # Clean incomplete or corrupted downloads (< 1024 bytes)
    dl_dir = source_dir / "dl"
    if dl_dir.exists():
        corrupted_count = 0
        for item in dl_dir.iterdir():
            if item.is_file() and item.stat().st_size < 1024:
                print(
                    f"Removing incomplete download: {item.name} ({item.stat().st_size} bytes)",
                    flush=True,
                )
                item.unlink()
                corrupted_count += 1
        if corrupted_count > 0:
            print(f"Cleaned {corrupted_count} incomplete downloads.", flush=True)


def build_firmware(
    target: TargetConfig,
    source_dir: Path,
    *,
    jobs: int | None = None,
    verbose: bool | None = None,
) -> None:
    source_dir = source_dir.resolve()
    work_root = source_dir.parent.parent if source_dir.parent.name == layout.SOURCE_CODE_DIR_NAME else Path.cwd()
    resolved_jobs = jobs or target.build.jobs or (os.cpu_count() or 1)
    is_verbose = verbose if verbose is not None else target.build.verbose

    dot_config = source_dir / ".config"
    ccache_in_config, _ = is_openwrt_ccache_enabled(dot_config)
    ccache_active = ccache_in_config or target.build.use_ccache

    env = os.environ.copy()
    ccache_dir: Path | None = None
    infos_dir = layout.target_infos_root(work_root, target.name)

    if ccache_active:
        ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir)
        print_ccache_banner(ccache_dir, target.build.ccache_max_size)
        env = setup_ccache_environment(target, ccache_dir, infos_dir, base_env=env)

    cmd = ["make", f"-j{resolved_jobs}"]
    if is_verbose:
        cmd.append("V=s")

    print(f"=== Starting firmware compilation (make -j{resolved_jobs}) ===", flush=True)
    try:
        run_command(cmd, cwd=source_dir, env=env, check=True)
    except Exception as exc:
        print(f"\n[BUILD ERROR] Compilation failed: {exc}", flush=True)
        if not is_verbose:
            print(
                "Tip: Rerun with --verbose / V=s to see detailed compiler errors.",
                flush=True,
            )
        if not target.build.ignore_errors:
            raise
    finally:
        if ccache_active and ccache_dir is not None:
            if target.build.ccache_export_stats:
                export_ccache_stats(ccache_dir, infos_dir)
            else:
                show_ccache_stats(ccache_dir)


def clean_build(source_dir: Path, *, dirclean: bool = False) -> None:
    source_dir = source_dir.resolve()
    target_make = "dirclean" if dirclean else "clean"
    print(f"Cleaning build tree (make {target_make})...", flush=True)
    run_command(["make", target_make], cwd=source_dir, check=False)
