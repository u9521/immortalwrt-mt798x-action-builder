# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from ... import layout
from ...utils import ensure_directory, run_command, write_json
from ..config.schema import TargetConfig


def is_ccache_available() -> bool:
    return shutil.which("ccache") is not None


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


def resolve_effective_ccache_dir(
    target: TargetConfig,
    work_root: Path,
    source_dir: Path,
) -> Path:
    if target.build.ccache_dir is not None:
        return target.build.ccache_dir.resolve()

    dot_config = source_dir / ".config"
    _, config_dir = is_openwrt_ccache_enabled(dot_config)
    if config_dir:
        candidate = Path(config_dir)
        return candidate.resolve() if candidate.is_absolute() else (source_dir / candidate).resolve()

    env_ccache_dir = os.environ.get("CCACHE_DIR")
    if env_ccache_dir and env_ccache_dir.strip():
        return Path(env_ccache_dir.strip()).expanduser().resolve()

    return layout.target_ccache_dir(work_root, target.name).resolve()


def print_ccache_banner(ccache_dir: Path, max_size: str | None = None) -> None:
    print("\n" + "=" * 70, flush=True)
    print("  [CCACHE ENABLED] OpenWrt native ccache acceleration is active!", flush=True)
    print(f"  Cache Directory: {ccache_dir}", flush=True)
    if max_size:
        print(f"  Max Cache Size:  {max_size}", flush=True)
    print("=" * 70 + "\n", flush=True)


def setup_ccache_environment(
    target: TargetConfig,
    ccache_dir: Path,
    infos_dir: Path,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    env = (base_env or os.environ).copy()
    ensure_directory(ccache_dir)
    ensure_directory(infos_dir)

    env["CCACHE_DIR"] = str(ccache_dir.resolve())
    env["CCACHE_MAXSIZE"] = target.build.ccache_max_size

    if target.build.ccache_stats_log:
        stats_log_file = (infos_dir / "ccache-stats.log").resolve()
        env["CCACHE_STATS_LOG"] = str(stats_log_file)
        print(f"  + ccache stats log directed to: {stats_log_file}", flush=True)

    if is_ccache_available():
        try:
            run_command(
                ["ccache", "-M", target.build.ccache_max_size],
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
) -> dict[str, Any] | None:
    if not is_ccache_available():
        return None

    ensure_directory(infos_dir)
    env = os.environ.copy()
    env["CCACHE_DIR"] = str(ccache_dir.resolve())

    # 1. Try to get JSON stats (ccache 4.x)
    stats_data: dict[str, Any] | None = None
    try:
        res = run_command(
            ["ccache", "--show-stats", "--format=json"],
            env=env,
            check=False,
            capture_output=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            stats_data = json.loads(res.stdout)
    except Exception:
        pass

    # 2. Get text stats summary
    res_text = run_command(
        ["ccache", "-s"],
        env=env,
        check=False,
        capture_output=True,
    )
    raw_text = res_text.stdout.strip() if res_text.returncode == 0 and isinstance(res_text.stdout, str) else ""

    if stats_data is None:
        stats_data = {"raw_text": raw_text}

    # 3. Save detailed files to infos directory
    stats_json_file = infos_dir / "ccache-stats.json"
    stats_txt_file = infos_dir / "ccache-stats.txt"
    write_json(stats_json_file, stats_data)
    if raw_text:
        stats_txt_file.write_text(raw_text + "\n", encoding="utf-8")

    # 4. Print concise summary to console (no spamming)
    _print_concise_ccache_summary(raw_text, stats_data, ccache_dir, stats_json_file)
    return stats_data


def _print_concise_ccache_summary(
    raw_text: str,
    stats_data: dict[str, Any],
    ccache_dir: Path,
    stats_json_file: Path,
) -> None:
    print("\n--- ccache Build Summary ---", flush=True)
    print(f"  Cache Directory: {ccache_dir}", flush=True)

    hit_rate: str | None = None
    cache_size: str | None = None

    if "direct_hit_rate_pct" in stats_data:
        hit_rate = f"{stats_data.get('direct_hit_rate_pct', 0):.1f}%"
    elif "hit_rate" in stats_data:
        hit_rate = str(stats_data["hit_rate"])

    for line in raw_text.splitlines():
        line_clean = line.strip()
        if "hit rate:" in line_clean.lower():
            hit_rate = line_clean.split(":", 1)[1].strip()
        elif "cache size:" in line_clean.lower():
            cache_size = line_clean.split(":", 1)[1].strip()

    if hit_rate:
        print(f"  Hit rate:        {hit_rate}", flush=True)
    if cache_size:
        print(f"  Cache size:      {cache_size}", flush=True)
    print(f"  Detailed report: {stats_json_file}", flush=True)
    print("----------------------------\n", flush=True)


def show_ccache_stats(ccache_dir: Path) -> str:
    if not is_ccache_available():
        msg = "ccache binary is not installed on host."
        print(msg, flush=True)
        return msg

    env = os.environ.copy()
    env["CCACHE_DIR"] = str(ccache_dir.resolve())
    try:
        res = run_command(["ccache", "-s"], env=env, check=False, capture_output=True)
        output = res.stdout.strip()
        print(output, flush=True)
        return output
    except Exception as exc:
        print(f"Failed to query ccache stats: {exc}", flush=True)
        return ""


def clear_ccache(ccache_dir: Path) -> None:
    if not is_ccache_available():
        print("ccache binary is not installed on host.", flush=True)
        return

    env = os.environ.copy()
    env["CCACHE_DIR"] = str(ccache_dir.resolve())
    print(f"Clearing ccache at {ccache_dir}...", flush=True)
    run_command(["ccache", "-C"], env=env, check=False)
