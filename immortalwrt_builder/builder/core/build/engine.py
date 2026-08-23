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
    get_target_ccache_dir,
    setup_ccache_environment,
    show_ccache_stats,
)


def prepare_config(target: TargetConfig, source_dir: Path) -> Path:
    source_dir = source_dir.resolve()
    dot_config = source_dir / ".config"

    if target.build.defconfig_path is not None and target.build.defconfig_path.exists():
        print(f"Applying defconfig from {target.build.defconfig_path}...", flush=True)
        shutil.copyfile(target.build.defconfig_path, dot_config)

    configs_to_append: list[str] = list(target.build.extra_configs)

    if configs_to_append:
        print("Configuring extra settings in .config...", flush=True)
        with dot_config.open("a", encoding="utf-8") as f:
            for extra in configs_to_append:
                f.write(f"{extra.strip()}\n")
                print(f"  + {extra.strip()}", flush=True)

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

    env = os.environ.copy()
    if target.build.use_ccache:
        env = setup_ccache_environment(target, work_root, base_env=env)
        ccache_dir = get_target_ccache_dir(work_root, target)
        print(f"Using ccache at: {ccache_dir} (max size: {target.build.ccache_max_size})", flush=True)
        show_ccache_stats(ccache_dir)

    cmd = ["make", f"-j{resolved_jobs}"]
    if is_verbose:
        cmd.append("V=s")

    print(f"\n=== Starting firmware compilation (make -j{resolved_jobs}) ===", flush=True)
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
        if target.build.use_ccache:
            ccache_dir = get_target_ccache_dir(work_root, target)
            print("\n=== Final ccache Statistics ===", flush=True)
            show_ccache_stats(ccache_dir)


def clean_build(source_dir: Path, *, dirclean: bool = False) -> None:
    source_dir = source_dir.resolve()
    target_make = "dirclean" if dirclean else "clean"
    print(f"Cleaning build tree (make {target_make})...", flush=True)
    run_command(["make", target_make], cwd=source_dir, check=False)
