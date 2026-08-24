# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class GitSourceConfig:
    url: str | None = None
    branch: str | None = None
    tag: str | None = None
    commit: str | None = None
    depth: int = 1
    submodules: bool = False


@dataclass(slots=True)
class FeedsConfig:
    update: bool = True
    install: bool = True
    custom_feeds: list[str] = field(default_factory=list)
    conf_file: Path | None = None


@dataclass(slots=True)
class PatchConfig:
    pre_feeds_patches: list[Path] = field(default_factory=list)
    post_feeds_patches: list[Path] = field(default_factory=list)
    post_config_patches: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class BuildConfig:
    defconfig_path: Path | None = None
    jobs: int = os.cpu_count() or 1
    verbose: bool = False
    download: bool = True
    ignore_errors: bool = False


@dataclass(slots=True)
class CcacheConfig:
    enabled: bool = True
    dir: Path | None = None
    max_size: str = "10G"
    stats_log: bool = False


@dataclass(slots=True)
class ToolchainCacheConfig:
    enabled: bool = True
    dir: Path | None = None
    auto_restore: bool = True
    auto_save: bool = True


@dataclass(slots=True)
class OutputConfig:
    dist_dir: str = ""
    target_dir: str | None = None
    packages_dir: str | None = None
    calculate_digest: bool = True
    firmware_patterns: list[str] = field(
        default_factory=lambda: [
            "*immortalwrt*.*",
            "*openwrt*.*",
            "*sysupgrade*.bin",
            "*factory*.bin",
            "*.itb",
            "*.ubi",
            "*.img.gz",
            "*.tar.gz",
            "*.manifest",
        ]
    )


@dataclass(slots=True)
class TargetConfig:
    name: str
    base: bool = False
    source: GitSourceConfig = field(default_factory=GitSourceConfig)
    feeds: FeedsConfig = field(default_factory=FeedsConfig)
    patch: PatchConfig = field(default_factory=PatchConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    ccache: CcacheConfig = field(default_factory=CcacheConfig)
    toolchain_cache: ToolchainCacheConfig = field(default_factory=ToolchainCacheConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    config_path: Path = Path()
