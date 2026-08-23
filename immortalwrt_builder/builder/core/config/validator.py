# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

from .schema import TargetConfig


def validate_target(target: TargetConfig, config_path: Path) -> None:
    if target.base:
        return

    _validate_source(target, config_path)
    _validate_build(target, config_path)
    _validate_patch(target, config_path)


def _validate_source(target: TargetConfig, config_path: Path) -> None:
    if not target.source.url:
        raise ValueError(f"Target requires non-empty source.url in {config_path}")
    if not target.source.branch and not target.source.tag and not target.source.commit:
        raise ValueError(f"Target requires source.branch, source.tag, or source.commit in {config_path}")
    if target.source.depth < 0:
        raise ValueError(f"Invalid source.depth in {config_path}: depth must be non-negative")


def _validate_build(target: TargetConfig, config_path: Path) -> None:
    if target.build.jobs <= 0:
        raise ValueError(f"Build jobs must be positive in {config_path}: {target.build.jobs}")
    if target.build.defconfig_path is not None and not target.build.defconfig_path.exists():
        raise FileNotFoundError(f"Defconfig file not found: {target.build.defconfig_path}")


def _validate_patch(target: TargetConfig, config_path: Path) -> None:
    all_patches = [
        *target.patch.pre_feeds_patches,
        *target.patch.post_feeds_patches,
        *target.patch.post_config_patches,
    ]
    for patch_path in all_patches:
        if not patch_path.exists():
            raise FileNotFoundError(f"Patch file not found: {patch_path} (in {config_path})")
        if patch_path.suffix != ".py":
            raise ValueError(
                f"Invalid patch file: {patch_path.name} (in {config_path}). Only Python (.py) patches are supported."
            )
