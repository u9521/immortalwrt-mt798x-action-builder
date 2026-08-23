# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import stat
from pathlib import Path

from ...utils import copy_directory_contents, ensure_directory, run_command
from ..config.schema import TargetConfig
from .builtin import apply_builtin_patches


def run_diy_scripts(scripts: list[Path], source_dir: Path) -> None:
    source_dir = source_dir.resolve()
    for script_path in scripts:
        script_path = script_path.resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"DIY script not found: {script_path}")

        print(f"\n--- Running DIY script: {script_path.name} ---", flush=True)
        # Ensure script is executable
        try:
            current_mode = script_path.stat().st_mode
            script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass

        if script_path.suffix == ".py":
            run_command(["python3", str(script_path)], cwd=source_dir)
        else:
            run_command(["bash", str(script_path)], cwd=source_dir)


def apply_custom_files(custom_files_dir: Path | None, source_dir: Path) -> None:
    if custom_files_dir is None:
        return
    custom_files_dir = custom_files_dir.resolve()
    if not custom_files_dir.exists():
        raise FileNotFoundError(f"Custom files directory not found: {custom_files_dir}")

    print(f"Applying custom files overlay from {custom_files_dir}...", flush=True)
    destination = ensure_directory(source_dir.resolve() / "files")
    copy_directory_contents(custom_files_dir, destination)


def apply_pre_feeds_patches(target: TargetConfig, source_dir: Path) -> None:
    if target.patch.pre_feeds_scripts:
        print("Executing pre-feeds DIY scripts...", flush=True)
        run_diy_scripts(target.patch.pre_feeds_scripts, source_dir)


def apply_post_feeds_patches(target: TargetConfig, source_dir: Path) -> None:
    apply_builtin_patches(target, source_dir)

    if target.patch.post_feeds_scripts:
        print("Executing post-feeds DIY scripts...", flush=True)
        run_diy_scripts(target.patch.post_feeds_scripts, source_dir)

    if target.patch.custom_files is not None:
        apply_custom_files(target.patch.custom_files, source_dir)


def apply_post_config_patches(target: TargetConfig, source_dir: Path) -> None:
    if target.patch.post_config_scripts:
        print("Executing post-config DIY scripts...", flush=True)
        run_diy_scripts(target.patch.post_config_scripts, source_dir)
