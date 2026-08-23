# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from .global_config import GlobalConfig, load_global_config
from .loader import load_mapping, load_target_payload_with_inheritance, parse_target_definition_file
from .provider import TargetConfigProvider
from .resolver import (
    list_selectable_targets,
    load_project_target,
    resolve_target,
    resolve_target_name,
    target_config_path,
)
from .schema import (
    BuildConfig,
    FeedsConfig,
    GitSourceConfig,
    OutputConfig,
    PatchConfig,
    TargetConfig,
)
from .validator import validate_target

__all__ = [
    "BuildConfig",
    "FeedsConfig",
    "GitSourceConfig",
    "GlobalConfig",
    "OutputConfig",
    "PatchConfig",
    "TargetConfig",
    "TargetConfigProvider",
    "list_selectable_targets",
    "load_global_config",
    "load_mapping",
    "load_project_target",
    "load_target_payload_with_inheritance",
    "parse_target_definition_file",
    "resolve_target",
    "resolve_target_name",
    "target_config_path",
    "validate_target",
]
