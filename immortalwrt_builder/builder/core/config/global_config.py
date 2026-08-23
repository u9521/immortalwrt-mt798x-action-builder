# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ... import layout


@dataclass(slots=True)
class GlobalConfig:
    default_jobs: int = field(default_factory=lambda: os.cpu_count() or 1)
    default_depth: int = 1
    default_download: bool = True
    default_use_ccache: bool = True
    work_root: Path | None = None


def load_global_config(project_root: Path | None = None) -> GlobalConfig:
    root = (project_root or Path.cwd()).resolve()
    config_path = layout.global_config_file(root)
    if not config_path.exists():
        return GlobalConfig()

    payload = tomllib.loads(config_path.read_text(encoding="utf-8")) or {}

    general = payload.get("general", {})
    if not isinstance(general, dict):
        raise ValueError(f"Global config section 'general' must be a table: {general!r}")

    workspace = payload.get("workspace", {})
    if not isinstance(workspace, dict):
        raise ValueError(f"Global config section 'workspace' must be a table: {workspace!r}")

    raw_work_root = workspace.get("work_root") or general.get("work_root")
    work_root_path: Path | None = None
    if raw_work_root is not None and isinstance(raw_work_root, str) and raw_work_root.strip():
        expanded = Path(raw_work_root.strip()).expanduser()
        if expanded.is_absolute():
            work_root_path = expanded.resolve()
        else:
            work_root_path = (root / expanded).resolve()

    return GlobalConfig(
        default_jobs=general.get("default_jobs", os.cpu_count() or 1),
        default_depth=general.get("default_depth", 1),
        default_download=general.get("default_download", True),
        default_use_ccache=general.get("default_use_ccache", True),
        work_root=work_root_path,
    )
