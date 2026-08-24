# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

from ...utils import ensure_directory, run_command
from ..config.schema import GitSourceConfig


def clone_or_fetch_repo(source: GitSourceConfig, destination: Path) -> None:
    if not source.url:
        raise ValueError("Source URL cannot be empty")

    destination = destination.resolve()
    ensure_directory(destination)
    git_dir = destination / ".git"

    if not git_dir.exists():
        print(f"Initializing repository at {destination}...", flush=True)
        run_command(["git", "init"], cwd=destination)
        run_command(["git", "remote", "add", "origin", source.url], cwd=destination)
    else:
        print(f"Updating existing repository at {destination}...", flush=True)
        run_command(["git", "remote", "set-url", "origin", source.url], cwd=destination, check=False)

    depth_args = ["--depth", str(source.depth)] if source.depth and source.depth > 0 else []

    if source.commit:
        print(f"Fetching commit {source.commit} from {source.url}...", flush=True)
        run_command(["git", "fetch", *depth_args, "origin", source.commit], cwd=destination)
        run_command(["git", "checkout", "FETCH_HEAD"], cwd=destination)
    elif source.tag:
        print(f"Fetching tag {source.tag} from {source.url}...", flush=True)
        run_command(
            ["git", "fetch", *depth_args, "origin", f"refs/tags/{source.tag}:refs/tags/{source.tag}"],
            cwd=destination,
        )
        run_command(["git", "checkout", f"refs/tags/{source.tag}"], cwd=destination)
    elif source.branch:
        print(f"Fetching branch {source.branch} from {source.url}...", flush=True)
        run_command(["git", "fetch", *depth_args, "origin", source.branch], cwd=destination)
        run_command(["git", "checkout", "-B", source.branch, "FETCH_HEAD"], cwd=destination)
    else:
        print(f"Fetching HEAD from {source.url}...", flush=True)
        run_command(["git", "fetch", *depth_args, "origin", "HEAD"], cwd=destination)
        run_command(["git", "checkout", "FETCH_HEAD"], cwd=destination)

    if source.submodules:
        print("Updating git submodules...", flush=True)
        sub_cmd = ["git", "submodule", "update", "--init", "--recursive"]
        if source.depth and source.depth > 0:
            sub_cmd.extend(["--depth", str(source.depth)])
        run_command(sub_cmd, cwd=destination)


def get_local_head_commit(repo_dir: Path) -> str:
    git_dir = repo_dir / ".git"
    if not git_dir.exists() and not (repo_dir / "HEAD").exists():
        return ""
    try:
        result = run_command(["git", "rev-parse", "HEAD"], cwd=repo_dir, check=False, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def get_remote_head_commit(url: str, branch_or_tag: str) -> str | None:
    try:
        result = run_command(["git", "ls-remote", url, branch_or_tag], capture_output=True)
        output = result.stdout.strip()
        if output:
            return output.split()[0]
    except Exception:
        pass
    return None
