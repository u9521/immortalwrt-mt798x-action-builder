# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

from .resolver import list_selectable_targets, resolve_target
from .schema import TargetConfig


class TargetConfigProvider:
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = (project_root or Path.cwd()).resolve()

    def load(self, target_name: str | None = None) -> TargetConfig:
        return resolve_target(self.project_root, target_name)

    def list_targets(self) -> list[str]:
        return list_selectable_targets(self.project_root)
