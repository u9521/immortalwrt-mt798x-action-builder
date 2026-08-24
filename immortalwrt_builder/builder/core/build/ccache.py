# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ... import layout
from ...utils import ensure_directory, run_command
from ..config.schema import TargetConfig


def get_ccache_binary(source_dir: Path | None = None) -> str | None:
    if source_dir is not None:
        staging_ccache = source_dir / "staging_dir" / "host" / "bin" / "ccache"
        if staging_ccache.exists():
            return str(staging_ccache.resolve())
    return shutil.which("ccache")


def is_ccache_available(source_dir: Path | None = None) -> bool:
    return get_ccache_binary(source_dir) is not None


def is_openwrt_ccache_enabled(dot_config: Path) -> tuple[bool, str | None]:
    if not dot_config.exists():
        return False, None

    enabled = False
    config_dir: str | None = None

    for line in dot_config.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line == "CONFIG_CCACHE=y":
            enabled = True
        elif line.startswith("CONFIG_CCACHE_DIR="):
            raw_val = line.split("=", 1)[1].strip("\"'")
            if raw_val:
                config_dir = raw_val

    return enabled, config_dir


def check_ccache_config_match(
    dot_config: Path,
    expected_ccache_dir: Path | None = None,
) -> tuple[bool, str]:
    if not dot_config.exists():
        return False, "missing .config file"

    enabled, config_dir = is_openwrt_ccache_enabled(dot_config)
    if not enabled:
        return False, "CONFIG_CCACHE is not enabled in .config"

    if expected_ccache_dir is None:
        return True, "matched"

    if config_dir is None or not config_dir.strip():
        return False, "CONFIG_CCACHE_DIR is empty in .config (defaults to source root .ccache)"

    resolved_config_dir = Path(config_dir).resolve()
    resolved_expected = expected_ccache_dir.resolve()

    if resolved_config_dir != resolved_expected:
        return (
            False,
            f"mismatched: .config has '{resolved_config_dir}', expected '{resolved_expected}'",
        )

    return True, "matched"


def resolve_effective_ccache_dir(
    target: TargetConfig,
    work_root: Path,
    source_dir: Path | None = None,
    *,
    warn_if_unset: bool = False,
) -> Path:
    work_root = work_root.resolve()
    if target.ccache.dir is not None:
        if target.ccache.dir.is_absolute():
            return target.ccache.dir.resolve()
        return (work_root / target.ccache.dir).resolve()

    if source_dir is not None:
        dot_config = source_dir / ".config"
        if dot_config.exists():
            _, config_dir = is_openwrt_ccache_enabled(dot_config)
            if config_dir and config_dir.strip():
                return Path(config_dir).resolve()
        return (source_dir / ".ccache").resolve()

    fallback_dir = layout.target_ccache_dir(work_root, target.name).resolve()
    if warn_if_unset:
        print(
            f"\n[CCACHE WARNING] '[ccache] dir' is not explicitly specified in target config '{target.name}'.\n"
            f"  Falling back to default cache directory: '{fallback_dir}'.\n",
            flush=True,
        )

    return fallback_dir


def configure_ccache_in_dot_config(dot_config: Path, ccache_dir: Path | None = None) -> None:
    ensure_directory(dot_config.parent)
    resolved_ccache_dir: Path | None = None
    if ccache_dir is not None:
        resolved_ccache_dir = ccache_dir.resolve()
        ensure_directory(resolved_ccache_dir)

    content = dot_config.read_text(encoding="utf-8") if dot_config.exists() else ""
    lines: list[str] = []

    # Remove any conflicting lines
    for line in content.splitlines():
        trimmed = line.strip()
        if (
            trimmed.startswith("CONFIG_CCACHE=")
            or trimmed.startswith("# CONFIG_CCACHE is not set")
            or trimmed.startswith("CONFIG_CCACHE_DIR=")
        ):
            continue
        lines.append(line)

    lines.append("CONFIG_DEVEL=y")
    lines.append("CONFIG_CCACHE=y")
    if resolved_ccache_dir is not None:
        lines.append(f'CONFIG_CCACHE_DIR="{resolved_ccache_dir}"')
        print(
            f'Configured ccache in .config: CONFIG_CCACHE=y, CONFIG_CCACHE_DIR="{resolved_ccache_dir}"',
            flush=True,
        )
    else:
        print("Configured ccache in .config: CONFIG_CCACHE=y (default directory)", flush=True)

    dot_config.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_ccache_banner(
    ccache_dir: Path,
    max_size: str | None = None,
    ccache_bin: str | None = None,
) -> None:
    print("\n" + "=" * 70, flush=True)
    print("  [CCACHE ENABLED] OpenWrt native ccache acceleration is active!", flush=True)
    if ccache_bin:
        print(f"  Binary Path:     {ccache_bin}", flush=True)
    print(f"  Cache Directory: {ccache_dir}", flush=True)
    if max_size:
        print(f"  Max Cache Size:  {max_size}", flush=True)
    print("=" * 70 + "\n", flush=True)


def setup_ccache_environment(
    target: TargetConfig,
    ccache_dir: Path,
    infos_dir: Path,
    source_dir: Path | None = None,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    env = (base_env or os.environ).copy()
    ensure_directory(ccache_dir)
    ensure_directory(infos_dir)

    resolved_ccache_dir = ccache_dir.resolve()
    env["CCACHE_DIR"] = str(resolved_ccache_dir)
    env["CCACHE_MAXSIZE"] = target.ccache.max_size

    # Write persistent ccache.conf inside the cache directory
    ccache_conf_file = resolved_ccache_dir / "ccache.conf"
    conf_lines = [f"max_size = {target.ccache.max_size}"]

    if target.ccache.stats_log:
        stats_log_file = (infos_dir / "ccache-stats.log").resolve()
        env["CCACHE_STATS_LOG"] = str(stats_log_file)
        conf_lines.append(f"stats_log = {stats_log_file}")
        print(f"  + ccache stats log directed to: {stats_log_file}", flush=True)

    try:
        ccache_conf_file.write_text("\n".join(conf_lines) + "\n", encoding="utf-8")
    except Exception:
        pass

    ccache_bin = get_ccache_binary(source_dir)
    if ccache_bin:
        try:
            run_command(
                [ccache_bin, "-M", target.ccache.max_size],
                env=env,
                check=False,
                capture_output=True,
            )
        except Exception:
            pass

    return env


def export_ccache_stats(
    ccache_dir: Path,
    infos_dir: Path,
    source_dir: Path | None = None,
) -> Path | None:
    ccache_bin = get_ccache_binary(source_dir)
    if not ccache_bin:
        print("ccache binary is not found on host or staging_dir.", flush=True)
        return None

    resolved_ccache_dir = ccache_dir.resolve()
    if not resolved_ccache_dir.exists() and source_dir is not None:
        source_ccache = (source_dir / ".ccache").resolve()
        if source_ccache.exists():
            resolved_ccache_dir = source_ccache

    ensure_directory(infos_dir)
    env = os.environ.copy()
    env["CCACHE_DIR"] = str(resolved_ccache_dir)

    res_text = run_command(
        [ccache_bin, "-s"],
        env=env,
        check=False,
        capture_output=True,
    )
    raw_text = res_text.stdout.strip() if res_text.returncode == 0 and isinstance(res_text.stdout, str) else ""

    stats_txt_file = infos_dir / "ccache-stats.txt"
    report_content = [
        f"ccache binary:   {ccache_bin}",
        f"cache directory: {resolved_ccache_dir}",
        "",
    ]
    if raw_text:
        report_content.append(raw_text)
    stats_txt_file.write_text("\n".join(report_content) + "\n", encoding="utf-8")

    print("\n--- ccache Statistics ---", flush=True)
    print(f"  Binary Path:     {ccache_bin}", flush=True)
    print(f"  Cache Directory: {resolved_ccache_dir}", flush=True)
    if raw_text:
        for line in raw_text.splitlines():
            print(f"  {line}", flush=True)
    else:
        print("  (No statistics output available)", flush=True)
    print(f"  Saved report to: {stats_txt_file}", flush=True)
    print("-------------------------\n", flush=True)
    return stats_txt_file


def show_ccache_stats(ccache_dir: Path, source_dir: Path | None = None) -> str:
    ccache_bin = get_ccache_binary(source_dir)
    if not ccache_bin:
        msg = "ccache binary is not installed on host or staging_dir."
        print(msg, flush=True)
        return msg

    resolved_ccache_dir = ccache_dir.resolve()
    if not resolved_ccache_dir.exists() and source_dir is not None:
        source_ccache = (source_dir / ".ccache").resolve()
        if source_ccache.exists():
            resolved_ccache_dir = source_ccache

    env = os.environ.copy()
    env["CCACHE_DIR"] = str(resolved_ccache_dir)
    try:
        res = run_command([ccache_bin, "-s"], env=env, check=False, capture_output=True)
        raw_text = res.stdout.strip() if res.returncode == 0 and isinstance(res.stdout, str) else ""
        lines = [
            f"ccache binary:   {ccache_bin}",
            f"cache directory: {resolved_ccache_dir}",
        ]
        if raw_text:
            lines.append("")
            lines.append(raw_text)
        output = "\n".join(lines)
        print(output, flush=True)
        return output
    except Exception as exc:
        print(f"Failed to query ccache stats: {exc}", flush=True)
        return ""


def clear_ccache(ccache_dir: Path, source_dir: Path | None = None) -> None:
    ccache_bin = get_ccache_binary(source_dir)
    if not ccache_bin:
        print("ccache binary is not installed on host or staging_dir.", flush=True)
        return

    resolved_ccache_dir = ccache_dir.resolve()
    if not resolved_ccache_dir.exists() and source_dir is not None:
        source_ccache = (source_dir / ".ccache").resolve()
        if source_ccache.exists():
            resolved_ccache_dir = source_ccache

    env = os.environ.copy()
    env["CCACHE_DIR"] = str(resolved_ccache_dir)
    print(f"Clearing ccache at {resolved_ccache_dir}...", flush=True)
    run_command([ccache_bin, "-C"], env=env, check=False)
