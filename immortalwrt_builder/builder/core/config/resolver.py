# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
from pathlib import Path

from ... import layout
from .loader import load_mapping, parse_target_definition_file
from .schema import TargetConfig


def resolve_target(project_root: Path, target_name: str | None = None) -> TargetConfig:
    return load_project_target(project_root, resolve_target_name(project_root, target_name))


def load_project_target(project_root: Path, target_name: str) -> TargetConfig:
    config_path = target_config_path(project_root, target_name)
    return parse_target_definition_file(
        config_path,
        defconfigs_root=layout.defconfigs_root(project_root),
        patchs_root=layout.patchs_root(project_root),
    )


def target_config_path(project_root: Path, target_name: str) -> Path:
    path = layout.target_config_file(project_root, target_name)
    if not path.exists():
        raise FileNotFoundError(f"Target config not found: {path}")

    _ensure_selectable_target_config(path, target_name)
    return path


def resolve_target_name(project_root: Path, target_name: str | None) -> str:
    if target_name:
        return target_name
    env_target = os.environ.get("IWB_TARGET")
    if env_target:
        return env_target
    selectable_targets = list_selectable_targets(project_root)
    if len(selectable_targets) == 1:
        return selectable_targets[0]
    if not selectable_targets:
        raise FileNotFoundError(f"No target configs found in {layout.target_configs_root(project_root)}")
    raise ValueError("Missing --target or IWB_TARGET; multiple target configs are available")


def list_selectable_targets(project_root: Path) -> list[str]:
    configs_root = layout.target_configs_root(project_root)
    if not configs_root.exists():
        return []
    names: list[str] = []
    for candidate in sorted(configs_root.glob("*.toml")):
        payload = load_mapping(candidate)
        if payload.get("base", False):
            continue
        declared_name = payload.get("name")
        names.append(declared_name if isinstance(declared_name, str) and declared_name else candidate.stem)
    return names


def _ensure_selectable_target_config(path: Path, requested_target_name: str) -> None:
    payload = load_mapping(path)
    base_value = payload.get("base", False)
    if not isinstance(base_value, bool):
        raise ValueError(f"Invalid 'base' in {path}: expected boolean")
    if not base_value:
        return
    raise ValueError(
        f"Target '{requested_target_name}' resolves to base config '{path.name}' and cannot be used as a build target"
    )
