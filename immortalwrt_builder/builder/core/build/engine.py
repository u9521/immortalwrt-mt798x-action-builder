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
    configure_ccache_in_dot_config,
    export_ccache_stats,
    get_ccache_binary,
    print_ccache_banner,
    resolve_effective_ccache_dir,
    setup_ccache_environment,
)
from .toolchain_cache import (
    is_toolchain_cached,
    resolve_toolchain_archive_path,
    restore_toolchain_cache,
    save_toolchain_cache,
    touch_toolchain_stamps,
)


def prepare_config(target: TargetConfig, source_dir: Path) -> Path:
    source_dir = source_dir.resolve()
    work_root = source_dir.parent.parent if source_dir.parent.name == layout.SOURCE_CODE_DIR_NAME else Path.cwd()
    dot_config = source_dir / ".config"

    if target.build.defconfig_path is not None and target.build.defconfig_path.exists():
        print(f"Applying defconfig from {target.build.defconfig_path}...", flush=True)
        shutil.copyfile(target.build.defconfig_path, dot_config)
    elif not dot_config.exists():
        dot_config.touch()

    # Step 1: Initial make defconfig to expand OpenWrt target architecture and toolchain symbols
    print("Generating base configuration (make defconfig)...", flush=True)
    run_command(["make", "defconfig"], cwd=source_dir)

    # Step 2: Calculate canonical architecture ccache directory from expanded .config and inject
    if target.ccache.enabled:
        ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir, warn_if_unset=False)
        configure_ccache_in_dot_config(dot_config, ccache_dir)
        print("Finalizing configuration with ccache settings (make defconfig)...", flush=True)
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

    env = os.environ.copy()
    ccache_dir: Path | None = None
    infos_dir = layout.target_infos_root(work_root, target.name)
    ccache_active = False

    if target.ccache.enabled:
        ccache_active = True
        ccache_dir = resolve_effective_ccache_dir(target, work_root, source_dir, warn_if_unset=False)
        ccache_bin = get_ccache_binary(source_dir)
        ccache_log_file = (infos_dir / "ccache.log").resolve() if target.ccache.log_file else None
        print_ccache_banner(
            ccache_dir,
            target.ccache.max_size,
            ccache_bin=ccache_bin,
            compiler_check=target.ccache.compiler_check,
            sloppiness=target.ccache.sloppiness,
            log_file=ccache_log_file,
        )
        env = setup_ccache_environment(target, ccache_dir, infos_dir, source_dir=source_dir, base_env=env)

    # Toolchain Cache: check and restore
    if target.toolchain_cache.enabled:
        archive_path = resolve_toolchain_archive_path(target, work_root)
        if target.toolchain_cache.auto_restore and not is_toolchain_cached(source_dir) and archive_path.exists():
            restore_toolchain_cache(target, source_dir, archive_path)
        if is_toolchain_cached(source_dir):
            touch_toolchain_stamps(source_dir)

    cmd = ["make", f"-j{resolved_jobs}"]
    if is_verbose:
        cmd.append("V=s")

    print(f"=== Starting firmware compilation (make -j{resolved_jobs}) ===", flush=True)
    try:
        run_command(cmd, cwd=source_dir, env=env, check=True)
        # Toolchain Cache: auto save if configured
        if target.toolchain_cache.enabled and target.toolchain_cache.auto_save and is_toolchain_cached(source_dir):
            archive_path = resolve_toolchain_archive_path(target, work_root)
            if not archive_path.exists():
                save_toolchain_cache(target, source_dir, archive_path)
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
            export_ccache_stats(ccache_dir, infos_dir, source_dir=source_dir)


def clean_build(source_dir: Path, *, dirclean: bool = False) -> None:
    source_dir = source_dir.resolve()
    target_make = "dirclean" if dirclean else "clean"
    print(f"Cleaning build tree (make {target_make})...", flush=True)
    run_command(["make", target_make], cwd=source_dir, check=False)
