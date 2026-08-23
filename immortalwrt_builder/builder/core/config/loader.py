# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

from .schema import (
    BuildConfig,
    FeedsConfig,
    GitSourceConfig,
    OutputConfig,
    PatchConfig,
    TargetConfig,
)
from .validator import validate_target

_TARGET_ROOT_KEYS = {"name", "base", "extends", "source", "feeds", "patch", "diy", "build", "output"}
_SOURCE_KEYS = {"url", "branch", "tag", "commit", "depth", "submodules"}
_FEEDS_KEYS = {"update", "install", "custom_feeds", "conf_file"}
_PATCH_KEYS = {
    "pre_feeds_patches",
    "post_feeds_patches",
    "post_config_patches",
    "pre_feeds_scripts",
    "post_feeds_scripts",
    "post_config_scripts",
}
_BUILD_KEYS = {
    "defconfig_path",
    "defconfig",
    "target_profile",
    "jobs",
    "verbose",
    "download",
    "use_ccache",
    "ccache_dir",
    "ccache_max_size",
    "ccache_export_stats",
    "ccache_stats_log",
    "ignore_errors",
}
_OUTPUT_KEYS = {"dist_dir", "target_dir", "packages_dir", "calculate_digest", "firmware_patterns"}


def parse_target_definition_file(
    config_path: str | Path,
    *,
    defconfigs_root: Path | None = None,
    patchs_root: Path | None = None,
) -> TargetConfig:
    path = Path(config_path).resolve()
    payload = _load_target_payload(path)
    _reject_unknown_keys(payload, _TARGET_ROOT_KEYS, "target", path)

    name = payload.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"Missing required 'name' in {path}")

    base = _optional_bool(payload.get("base"), default=False, field="base", config_path=path)
    source = _parse_source_config(payload.get("source"), path)
    feeds = _parse_feeds_config(payload.get("feeds"), path)
    patch = _parse_patch_config(payload.get("patch") or payload.get("diy"), path, patchs_root=patchs_root)
    build = _parse_build_config(payload.get("build"), path, defconfigs_root=defconfigs_root)
    output = _parse_output_config(payload.get("output"), path)

    target = TargetConfig(
        name=name,
        base=base,
        source=source,
        feeds=feeds,
        patch=patch,
        build=build,
        output=output,
        config_path=path,
    )
    validate_target(target, path)
    return target


def _parse_source_config(value: object, config_path: Path) -> GitSourceConfig:
    if value is None:
        return GitSourceConfig()
    if not isinstance(value, dict):
        raise ValueError(f"Invalid 'source' table in {config_path}: expected mapping")
    _reject_unknown_keys(value, _SOURCE_KEYS, "source", config_path)
    return GitSourceConfig(
        url=_optional_string(value.get("url"), field="source.url", config_path=config_path),
        branch=_optional_string(value.get("branch"), field="source.branch", config_path=config_path),
        tag=_optional_string(value.get("tag"), field="source.tag", config_path=config_path),
        commit=_optional_string(value.get("commit"), field="source.commit", config_path=config_path),
        depth=_optional_int(value.get("depth"), default=1, field="source.depth", config_path=config_path),
        submodules=_optional_bool(
            value.get("submodules"), default=False, field="source.submodules", config_path=config_path
        ),
    )


def _parse_feeds_config(value: object, config_path: Path) -> FeedsConfig:
    if value is None:
        return FeedsConfig()
    if not isinstance(value, dict):
        raise ValueError(f"Invalid 'feeds' table in {config_path}: expected mapping")
    _reject_unknown_keys(value, _FEEDS_KEYS, "feeds", config_path)
    conf_file_str = _optional_string(value.get("conf_file"), field="feeds.conf_file", config_path=config_path)
    conf_file_path = (config_path.parent / conf_file_str).resolve() if conf_file_str else None
    return FeedsConfig(
        update=_optional_bool(value.get("update"), default=True, field="feeds.update", config_path=config_path),
        install=_optional_bool(value.get("install"), default=True, field="feeds.install", config_path=config_path),
        custom_feeds=_string_list(value.get("custom_feeds"), [], config_path, "feeds.custom_feeds"),
        conf_file=conf_file_path,
    )


def _parse_patch_config(value: object, config_path: Path, *, patchs_root: Path | None) -> PatchConfig:
    if value is None:
        return PatchConfig()
    if not isinstance(value, dict):
        raise ValueError(f"Invalid 'patch' table in {config_path}: expected mapping")
    _reject_unknown_keys(value, _PATCH_KEYS, "patch", config_path)

    pre_raw = value.get("pre_feeds_patches") or value.get("pre_feeds_scripts")
    post_raw = value.get("post_feeds_patches") or value.get("post_feeds_scripts")
    post_cfg_raw = value.get("post_config_patches") or value.get("post_config_scripts")

    return PatchConfig(
        pre_feeds_patches=_resolve_path_list(pre_raw, patchs_root, config_path),
        post_feeds_patches=_resolve_path_list(post_raw, patchs_root, config_path),
        post_config_patches=_resolve_path_list(post_cfg_raw, patchs_root, config_path),
    )


def _parse_build_config(value: object, config_path: Path, *, defconfigs_root: Path | None) -> BuildConfig:
    if value is None:
        return BuildConfig()
    if not isinstance(value, dict):
        raise ValueError(f"Invalid 'build' table in {config_path}: expected mapping")
    _reject_unknown_keys(value, _BUILD_KEYS, "build", config_path)

    defconfig_raw = value.get("defconfig_path") or value.get("defconfig")
    defconfig_str = _optional_string(defconfig_raw, field="build.defconfig_path", config_path=config_path)
    defconfig_path = _resolve_relative_path(defconfig_str, defconfigs_root, config_path.parent)

    ccache_dir_str = _optional_string(value.get("ccache_dir"), field="build.ccache_dir", config_path=config_path)
    ccache_dir_path = (config_path.parent / ccache_dir_str).resolve() if ccache_dir_str else None

    return BuildConfig(
        defconfig_path=defconfig_path,
        target_profile=_optional_string(
            value.get("target_profile"), field="build.target_profile", config_path=config_path
        ),
        jobs=_optional_int(value.get("jobs"), default=os.cpu_count() or 1, field="build.jobs", config_path=config_path),
        verbose=_optional_bool(value.get("verbose"), default=False, field="build.verbose", config_path=config_path),
        download=_optional_bool(value.get("download"), default=True, field="build.download", config_path=config_path),
        use_ccache=_optional_bool(
            value.get("use_ccache"), default=True, field="build.use_ccache", config_path=config_path
        ),
        ccache_dir=ccache_dir_path,
        ccache_max_size=_optional_string(
            value.get("ccache_max_size"), field="build.ccache_max_size", config_path=config_path
        )
        or "10G",
        ccache_export_stats=_optional_bool(
            value.get("ccache_export_stats"), default=True, field="build.ccache_export_stats", config_path=config_path
        ),
        ccache_stats_log=_optional_bool(
            value.get("ccache_stats_log"), default=False, field="build.ccache_stats_log", config_path=config_path
        ),
        ignore_errors=_optional_bool(
            value.get("ignore_errors"), default=False, field="build.ignore_errors", config_path=config_path
        ),
    )


def _parse_output_config(value: object, config_path: Path) -> OutputConfig:
    if value is None:
        return OutputConfig()
    if not isinstance(value, dict):
        raise ValueError(f"Invalid 'output' table in {config_path}: expected mapping")
    _reject_unknown_keys(value, _OUTPUT_KEYS, "output", config_path)

    default_patterns = [
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
    return OutputConfig(
        dist_dir=_optional_string(value.get("dist_dir"), field="output.dist_dir", config_path=config_path) or "",
        target_dir=_optional_string(value.get("target_dir"), field="output.target_dir", config_path=config_path),
        packages_dir=_optional_string(value.get("packages_dir"), field="output.packages_dir", config_path=config_path),
        calculate_digest=_optional_bool(
            value.get("calculate_digest"), default=True, field="output.calculate_digest", config_path=config_path
        ),
        firmware_patterns=_string_list(
            value.get("firmware_patterns"), default_patterns, config_path, "output.firmware_patterns"
        ),
    )


def _reject_unknown_keys(payload: dict[str, object], allowed_keys: set[str], section: str, config_path: Path) -> None:
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        joined = ", ".join(unknown_keys)
        raise ValueError(f"Unsupported {section} field in {config_path}: {joined}")


def load_mapping(path: Path) -> dict[str, object]:
    raw_payload: object
    if path.suffix == ".toml":
        raw_payload = tomllib.loads(path.read_text(encoding="utf-8")) or {}
    elif path.suffix == ".json":
        raw_payload = json.loads(path.read_text(encoding="utf-8")) or {}
    else:
        raise ValueError(f"Unsupported config format: {path}")

    if not isinstance(raw_payload, dict):
        raise ValueError(f"Target config must be a mapping: {path}")
    return raw_payload


def _load_target_payload(path: Path, *, stack: tuple[Path, ...] = ()) -> dict[str, object]:
    payload, _ = _load_target_payload_with_chain(path, stack=stack)
    return payload


def load_target_payload_with_inheritance(config_path: str | Path) -> tuple[dict[str, object], list[Path]]:
    return _load_target_payload_with_chain(Path(config_path).resolve())


def _load_target_payload_with_chain(
    path: Path,
    *,
    stack: tuple[Path, ...] = (),
) -> tuple[dict[str, object], list[Path]]:
    resolved_path = path.resolve()
    if resolved_path in stack:
        cycle_paths = [*stack, resolved_path]
        cycle_text = " -> ".join(str(candidate) for candidate in cycle_paths)
        raise ValueError(f"Circular target inheritance detected: {cycle_text}")

    payload = load_mapping(resolved_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Target config must be a mapping: {resolved_path}")

    extends_value = payload.get("extends")
    if extends_value is None:
        return payload, [resolved_path]

    parent_path = _resolve_extends_path(resolved_path, extends_value)
    if not parent_path.exists():
        raise FileNotFoundError(f"Parent target config not found: {parent_path}")

    parent_payload, parent_chain = _load_target_payload_with_chain(parent_path, stack=(*stack, resolved_path))
    parent_copy = dict(parent_payload)
    parent_copy.pop("base", None)
    child_payload = dict(payload)
    child_payload.pop("extends", None)
    return _merge_payload(parent_copy, child_payload), [*parent_chain, resolved_path]


def _resolve_extends_path(config_path: Path, extends_value: object) -> Path:
    if not isinstance(extends_value, str) or not extends_value.strip():
        raise ValueError(f"Invalid extends in {config_path}: expected non-empty string")

    extends_text = extends_value.strip()
    relative_path = Path(extends_text)
    if (
        relative_path.is_absolute()
        or any(part == ".." for part in relative_path.parts)
        or len(relative_path.parts) != 1
        or extends_text.endswith(".toml")
    ):
        raise ValueError(f"Invalid extends in {config_path}: expected target name like 'immortalwrt-base'")

    return (config_path.parent / f"{extends_text}.toml").resolve()


def _merge_payload(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged: dict[str, object] = dict(base)
    for key, value in override.items():
        base_value = merged.get(key)
        if isinstance(base_value, dict) and isinstance(value, dict):
            merged[key] = _merge_payload(base_value, value)
            continue
        merged[key] = value
    return merged


def _optional_string(value: object, *, field: str, config_path: Path) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise ValueError(f"Invalid {field} in {config_path}: expected string or null")


def _optional_bool(value: object, *, default: bool, field: str, config_path: Path) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ValueError(f"Invalid {field} in {config_path}: expected boolean")


def _optional_int(value: object, *, default: int, field: str, config_path: Path) -> int:
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError(f"Invalid {field} in {config_path}: expected integer")


def _string_list(value: object, default: list[str], config_path: Path, field_name: str) -> list[str]:
    if value is None:
        return list(default)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Invalid {field_name} in {config_path}: expected list of strings")
    return list(value)


def _resolve_relative_path(value: str | None, primary_root: Path | None, fallback_root: Path) -> Path | None:
    if value is None or not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    if primary_root is not None and (primary_root / candidate).exists():
        return (primary_root / candidate).resolve()
    return (fallback_root / candidate).resolve()


def _resolve_path_list(value: object, primary_root: Path | None, config_path: Path) -> list[Path]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        raw_items = value
    else:
        raise ValueError(f"Invalid script path list in {config_path}: expected list of path strings")

    results: list[Path] = []
    for item in raw_items:
        resolved = _resolve_relative_path(item, primary_root, config_path.parent)
        if resolved is not None:
            results.append(resolved)
    return results
