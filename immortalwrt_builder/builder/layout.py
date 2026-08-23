# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

PROJECT_PACKAGE_DIR_NAME = "immortalwrt_builder"
CONFIGS_DIR_NAME = "configs"
DOCS_DIR_NAME = "docs"
TARGETS_DIR_NAME = "targets"
DEFCONFIGS_DIR_NAME = "defconfigs"
DIY_DIR_NAME = "diy"
SCRIPTS_DIR_NAME = "scripts"

SOURCE_CODE_DIR_NAME = "source-code"
CACHE_DIR_NAME = "cache"
CCACHE_TOOLS_DIR_NAME = ".ccache-tools"
TEMP_DIR_NAME = ".temp"
OUTPUT_DIR_NAME = "out"
INFOS_DIR_NAME = "infos"

WORKSPACE_METADATA_FILE_NAME = "workspace.json"
DISK_USAGE_FILE_NAME = "disk-usage.json"
DIGEST_FILE_NAME = "filedigest.md"


def project_package_root(project_root: Path) -> Path:
    return project_root / PROJECT_PACKAGE_DIR_NAME


def project_configs_root(project_root: Path) -> Path:
    return project_package_root(project_root) / CONFIGS_DIR_NAME


def global_config_file(project_root: Path) -> Path:
    return project_configs_root(project_root) / "global.toml"


def target_configs_root(project_root: Path) -> Path:
    return project_configs_root(project_root) / TARGETS_DIR_NAME


def target_config_file(project_root: Path, target_name: str) -> Path:
    return target_configs_root(project_root) / f"{target_name}.toml"


def defconfigs_root(project_root: Path) -> Path:
    return project_configs_root(project_root) / DEFCONFIGS_DIR_NAME


def diy_root(project_root: Path) -> Path:
    return project_configs_root(project_root) / DIY_DIR_NAME


def scripts_root(project_root: Path) -> Path:
    return project_package_root(project_root) / SCRIPTS_DIR_NAME


def source_code_root(work_root: Path) -> Path:
    return work_root / SOURCE_CODE_DIR_NAME


def target_source_root(work_root: Path, target_name: str) -> Path:
    return source_code_root(work_root) / target_name


def cache_root(work_root: Path) -> Path:
    return work_root / CACHE_DIR_NAME


def target_cache_root(work_root: Path, target_name: str) -> Path:
    return cache_root(work_root) / target_name


def target_ccache_dir(work_root: Path, target_name: str) -> Path:
    return target_cache_root(work_root, target_name) / "ccache"


def target_ccache_tools_dir(work_root: Path, target_name: str) -> Path:
    return target_cache_root(work_root, target_name) / CCACHE_TOOLS_DIR_NAME


def target_dl_dir(work_root: Path, target_name: str) -> Path:
    return target_cache_root(work_root, target_name) / "dl"


def temp_root(work_root: Path) -> Path:
    return work_root / TEMP_DIR_NAME


def output_root(work_root: Path) -> Path:
    return work_root / OUTPUT_DIR_NAME


def target_output_root(work_root: Path, target_name: str) -> Path:
    return output_root(work_root) / target_name


def infos_root(work_root: Path) -> Path:
    return work_root / INFOS_DIR_NAME


def target_infos_root(work_root: Path, target_name: str) -> Path:
    return infos_root(work_root) / target_name


def target_metadata_file(work_root: Path, target_name: str) -> Path:
    return target_infos_root(work_root, target_name) / WORKSPACE_METADATA_FILE_NAME


def target_disk_usage_file(work_root: Path, target_name: str) -> Path:
    return target_infos_root(work_root, target_name) / DISK_USAGE_FILE_NAME


def digest_file(work_root: Path) -> Path:
    return work_root / DIGEST_FILE_NAME
