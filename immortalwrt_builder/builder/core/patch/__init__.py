# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .executor import execute_patches, execute_python_patch
from .interface import PatchContext

if TYPE_CHECKING:
    from ..config.schema import TargetConfig


def apply_pre_feeds_patches(target: TargetConfig, source_dir: Path, work_root: Path) -> None:
    if target.patch.pre_feeds_patches:
        print("Executing pre-feeds Python patches...", flush=True)
        context = PatchContext(target=target, source_dir=source_dir, work_root=work_root)
        execute_patches(target.patch.pre_feeds_patches, context)


def apply_post_feeds_patches(target: TargetConfig, source_dir: Path, work_root: Path) -> None:
    if target.patch.post_feeds_patches:
        print("Executing post-feeds Python patches...", flush=True)
        context = PatchContext(target=target, source_dir=source_dir, work_root=work_root)
        execute_patches(target.patch.post_feeds_patches, context)


def apply_post_config_patches(target: TargetConfig, source_dir: Path, work_root: Path) -> None:
    if target.patch.post_config_patches:
        print("Executing post-config Python patches...", flush=True)
        context = PatchContext(target=target, source_dir=source_dir, work_root=work_root)
        execute_patches(target.patch.post_config_patches, context)


__all__ = [
    "PatchContext",
    "apply_post_config_patches",
    "apply_post_feeds_patches",
    "apply_pre_feeds_patches",
    "execute_patches",
    "execute_python_patch",
]
