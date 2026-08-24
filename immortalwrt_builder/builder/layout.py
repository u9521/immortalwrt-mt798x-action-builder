# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import tomllib
from pathlib import Path

PROJECT_PACKAGE_DIR_NAME = "immortalwrt_builder"
CONFIGS_DIR_NAME = "configs"
DOCS_DIR_NAME = "docs"
TARGETS_DIR_NAME = "targets"
DEFCONFIGS_DIR_NAME = "defconfigs"
PATCHS_DIR_NAME = "patchs"
SCRIPTS_DIR_NAME = "scripts"

SOURCE_CODE_DIR_NAME = "source-code"
CACHE_DIR_NAME = "cache"
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


def patchs_root(project_root: Path) -> Path:
    return project_configs_root(project_root) / PATCHS_DIR_NAME


def scripts_root(project_root: Path) -> Path:
    return project_package_root(project_root) / SCRIPTS_DIR_NAME


def resolve_work_root(
    project_root: Path | None = None,
    cli_work_root: str | Path | None = None,
) -> Path:
    if cli_work_root:
        return Path(cli_work_root).expanduser().resolve()

    env_work_root = os.environ.get("IWB_WORK_ROOT")
    if env_work_root and env_work_root.strip():
        return Path(env_work_root.strip()).expanduser().resolve()

    root = (project_root or Path.cwd()).resolve()
    global_cfg_file = global_config_file(root)
    if global_cfg_file.exists():
        try:
            payload = tomllib.loads(global_cfg_file.read_text(encoding="utf-8")) or {}
            workspace = payload.get("workspace", {})
            raw = workspace.get("work_root")
            if raw and isinstance(raw, str) and raw.strip():
                p = Path(raw.strip()).expanduser()
                return p.resolve() if p.is_absolute() else (root / p).resolve()
        except Exception:
            pass

    return root


def source_code_root(work_root: Path) -> Path:
    return work_root / SOURCE_CODE_DIR_NAME


def target_source_root(work_root: Path, target_name: str) -> Path:
    return source_code_root(work_root) / target_name


def cache_root(work_root: Path) -> Path:
    return work_root / CACHE_DIR_NAME


def target_cache_root(work_root: Path, target_name: str) -> Path:
    return cache_root(work_root) / target_name


def arch_ccache_dir(work_root: Path, arch_sig: str) -> Path:
    return cache_root(work_root) / "ccache" / arch_sig


def target_ccache_dir(work_root: Path, target_name: str) -> Path:
    return target_cache_root(work_root, target_name) / "ccache"


def target_toolchain_cache_dir(work_root: Path, target_name: str) -> Path:
    return target_cache_root(work_root, target_name) / "toolchain"


def target_toolchain_archive_path(work_root: Path, target_name: str) -> Path:
    return target_toolchain_cache_dir(work_root, target_name) / f"toolchain-{target_name}.tar.gz"


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
