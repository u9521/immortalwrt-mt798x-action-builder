# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ... import layout
from ...utils import ensure_directory, run_command
from ..config.schema import TargetConfig

_COMPILER_NAMES = ("gcc", "g++", "cc", "c++", "clang", "clang++")


def is_ccache_available(path_env: str | None = None) -> bool:
    return shutil.which("ccache", path=path_env) is not None


def get_target_ccache_dir(work_root: Path, target: TargetConfig) -> Path:
    if target.build.ccache_dir is not None:
        return target.build.ccache_dir.resolve()
    return layout.target_ccache_dir(work_root, target.name).resolve()


def create_ccache_compiler_symlinks(
    work_root: Path,
    target: TargetConfig,
    env: dict[str, str],
) -> Path | None:
    ccache_bin = shutil.which("ccache", path=env.get("PATH"))
    if not ccache_bin:
        return None

    resolved_ccache = Path(ccache_bin).resolve()
    tools_dir = ensure_directory(layout.target_ccache_tools_dir(work_root, target.name))

    for compiler_name in _COMPILER_NAMES:
        link_path = tools_dir / compiler_name
        if link_path.is_symlink():
            if link_path.resolve() == resolved_ccache:
                continue
            link_path.unlink()
        elif link_path.exists():
            link_path.unlink()

        os.symlink(resolved_ccache, link_path)

    return tools_dir.resolve()


def setup_ccache_environment(
    target: TargetConfig,
    work_root: Path,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    env = (base_env or os.environ).copy()
    if not target.build.use_ccache:
        return env

    ccache_dir = ensure_directory(get_target_ccache_dir(work_root, target))
    env["CCACHE_DIR"] = str(ccache_dir)
    env["CCACHE_MAXSIZE"] = target.build.ccache_max_size
    env["CCACHE_COMPILERCHECK"] = "none"

    tools_dir = create_ccache_compiler_symlinks(work_root, target, env)
    if tools_dir is not None:
        original_path = env.get("PATH", "")
        env["PATH"] = f"{tools_dir}:{original_path}" if original_path else str(tools_dir)

    if is_ccache_available(env.get("PATH")):
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


def show_ccache_stats(ccache_dir: Path) -> str:
    if not is_ccache_available():
        msg = "ccache binary is not installed on host."
        print(msg, flush=True)
        return msg

    env = os.environ.copy()
    env["CCACHE_DIR"] = str(ccache_dir.resolve())
    print(f"\n--- ccache Statistics ({ccache_dir}) ---", flush=True)
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
