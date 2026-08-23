# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

from ... import layout
from ...usage_report import write_usage_report
from ...utils import ensure_directory
from ..config.schema import TargetConfig
from .ccache import (
    clear_ccache,
    get_target_ccache_dir,
    is_ccache_available,
    setup_ccache_environment,
    show_ccache_stats,
)
from .engine import build_firmware, clean_build, download_packages, prepare_config
from .output import collect_outputs, generate_digest_table, write_digest_summary


def execute_build_pipeline(
    target: TargetConfig,
    source_dir: Path,
    cache_root: Path,
    output_root: Path,
    *,
    jobs: int | None = None,
    verbose: bool | None = None,
) -> list[dict[str, object]]:
    source_dir = source_dir.resolve()
    cache_root = ensure_directory(cache_root.resolve())
    output_root = ensure_directory(output_root.resolve())

    # 1. Download
    if target.build.download:
        download_packages(target, source_dir, jobs=jobs, verbose=verbose)

    # 2. Build
    build_firmware(target, source_dir, jobs=jobs, verbose=verbose)

    # 3. Collect outputs
    artifacts = collect_outputs(target, source_dir, output_root)

    # 4. Digest summary
    work_root = source_dir.parent.parent if source_dir.parent.name == layout.SOURCE_CODE_DIR_NAME else Path.cwd()
    if target.output.calculate_digest and artifacts:
        write_digest_summary(work_root, artifacts)

    # 5. Usage report
    write_usage_report(target, source_dir, cache_root, output_root)

    return artifacts


__all__ = [
    "build_firmware",
    "clean_build",
    "clear_ccache",
    "collect_outputs",
    "download_packages",
    "execute_build_pipeline",
    "generate_digest_table",
    "get_target_ccache_dir",
    "is_ccache_available",
    "prepare_config",
    "setup_ccache_environment",
    "show_ccache_stats",
    "write_digest_summary",
]
