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
    pre_feeds_scripts: list[Path] = field(default_factory=list)
    post_feeds_scripts: list[Path] = field(default_factory=list)
    post_config_scripts: list[Path] = field(default_factory=list)
    custom_files: Path | None = None
    ip_address: str | None = None
    hostname: str | None = None
    wifi_ssid_2g: str | None = None
    wifi_ssid_5g: str | None = None
    default_theme: str | None = None
    distrib_description: str | None = None
    distrib_revision: str | None = None


@dataclass(slots=True)
class BuildConfig:
    defconfig_path: Path | None = None
    target_profile: str | None = None
    extra_configs: list[str] = field(default_factory=list)
    jobs: int = os.cpu_count() or 1
    verbose: bool = False
    download: bool = True
    use_ccache: bool = True
    ccache_dir: Path | None = None
    ccache_max_size: str = "10G"
    ignore_errors: bool = False


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
    output: OutputConfig = field(default_factory=OutputConfig)
    config_path: Path = Path()
