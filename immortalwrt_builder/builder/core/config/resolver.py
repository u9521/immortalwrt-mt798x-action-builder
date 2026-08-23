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
        diy_root=layout.diy_root(project_root),
    )


def target_config_path(project_root: Path, target_name: str) -> Path:
    configs_root = layout.target_configs_root(project_root)
    path = layout.target_config_file(project_root, target_name)
    warned_messages: set[str] = set()

    if path.exists():
        declared_name = _declared_target_name(path)
        filename_stem = path.stem

        if declared_name is not None and declared_name != filename_stem:
            _warn_target_mismatch(
                target_name,
                path,
                f"filename '{filename_stem}' != declared name '{declared_name}'",
                warned_messages,
            )

        if declared_name == target_name:
            _ensure_selectable_target_config(path, target_name)
            return path
        if declared_name is not None:
            _warn_target_mismatch(
                target_name,
                path,
                f"requested target '{target_name}' != declared name '{declared_name}'",
                warned_messages,
            )

        fallback_path, fallback_reason = _find_target_config_fallback(configs_root, target_name, skip_path=path)
        if fallback_path is not None and fallback_reason is not None:
            _warn_target_mismatch(
                target_name,
                fallback_path,
                f"using fallback {fallback_reason} match",
                warned_messages,
            )
            _ensure_selectable_target_config(fallback_path, target_name)
            return fallback_path

        if declared_name is not None:
            raise FileNotFoundError(
                f"Target '{target_name}' not found; {path} declares '{declared_name}' and no fallback match exists"
            )
        _ensure_selectable_target_config(path, target_name)
        return path

    fallback_path, fallback_reason = _find_target_config_fallback(configs_root, target_name)
    if fallback_path is not None and fallback_reason is not None:
        _warn_target_mismatch(
            target_name,
            fallback_path,
            f"using fallback {fallback_reason} match",
            warned_messages,
        )
        _ensure_selectable_target_config(fallback_path, target_name)
        return fallback_path

    raise FileNotFoundError(f"Target config not found: {path}")


def resolve_target_name(project_root: Path, target_name: str | None) -> str:
    if target_name:
        return target_name
    env_target = os.environ.get("IWB_TARGET") or os.environ.get("IMMORTALWRT_TARGET")
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


def _declared_target_name(path: Path) -> str | None:
    payload = load_mapping(path)
    name = payload.get("name")
    if isinstance(name, str) and name:
        return name
    return None


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


def _find_target_config_fallback(
    configs_root: Path,
    target_name: str,
    *,
    skip_path: Path | None = None,
) -> tuple[Path | None, str | None]:
    if not configs_root.exists():
        return None, None

    filename_exact_matches: list[Path] = []
    filename_casefold_matches: list[Path] = []
    declared_exact_matches: list[Path] = []

    for candidate in sorted(configs_root.glob("*.toml")):
        resolved_candidate = candidate.resolve()
        if skip_path is not None and resolved_candidate == skip_path.resolve():
            continue

        candidate_stem = candidate.stem
        if candidate_stem == target_name:
            filename_exact_matches.append(candidate)
        elif candidate_stem.casefold() == target_name.casefold():
            filename_casefold_matches.append(candidate)

        declared_name = _declared_target_name(candidate)
        if declared_name == target_name:
            declared_exact_matches.append(candidate)

    if filename_exact_matches:
        return _resolve_single_target_match(filename_exact_matches, target_name, "filename"), "filename"

    if filename_casefold_matches:
        return (
            _resolve_single_target_match(filename_casefold_matches, target_name, "filename (case-insensitive)"),
            "filename (case-insensitive)",
        )

    if declared_exact_matches:
        return _resolve_single_target_match(declared_exact_matches, target_name, "declared name"), "declared name"

    return None, None


def _resolve_single_target_match(matches: list[Path], target_name: str, match_kind: str) -> Path:
    if len(matches) > 1:
        joined = ", ".join(str(path) for path in matches)
        raise ValueError(f"Multiple target configs matched target '{target_name}' by {match_kind}: {joined}")
    return matches[0]


def _warn_target_mismatch(target_name: str, config_path: Path, detail: str, warned_messages: set[str]) -> None:
    message = (
        f"warning: target config mismatch for '{target_name}' in '{config_path.name}': {detail}. "
        "Recommend normalizing filename and name field."
    )
    _warn_once(message, warned_messages)


def _warn_once(message: str, warned_messages: set[str]) -> None:
    if message in warned_messages:
        return
    warned_messages.add(message)
    print(message, flush=True)
