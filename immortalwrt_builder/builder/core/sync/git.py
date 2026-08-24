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
    git_dir = destination / ".git"

    if git_dir.exists():
        print(f"Updating existing repository at {destination}...", flush=True)
        if source.commit:
            run_command(["git", "fetch", "origin"], cwd=destination)
            run_command(["git", "checkout", source.commit], cwd=destination)
        elif source.tag:
            run_command(["git", "fetch", "origin", f"tags/{source.tag}"], cwd=destination)
            run_command(["git", "checkout", f"tags/{source.tag}"], cwd=destination)
        elif source.branch:
            run_command(["git", "fetch", "origin", source.branch], cwd=destination)
            run_command(["git", "checkout", "-B", source.branch, f"origin/{source.branch}"], cwd=destination)
        else:
            run_command(["git", "fetch", "origin", "HEAD"], cwd=destination)
            run_command(["git", "checkout", "FETCH_HEAD"], cwd=destination)
    else:
        print(f"Cloning repository from {source.url} into {destination}...", flush=True)
        ensure_directory(destination.parent)
        clone_cmd = ["git", "clone"]
        if source.depth and source.depth > 0 and not source.commit:
            clone_cmd.extend(["--depth", str(source.depth)])

        if source.commit:
            # Commit SHA checkout handled after clone
            pass
        elif source.tag:
            clone_cmd.extend(["-b", source.tag])
        elif source.branch:
            clone_cmd.extend(["-b", source.branch])

        clone_cmd.extend([source.url, str(destination)])
        run_command(clone_cmd)

        if source.commit:
            run_command(["git", "checkout", source.commit], cwd=destination)

    if source.submodules:
        print("Updating git submodules...", flush=True)
        run_command(["git", "submodule", "update", "--init", "--recursive"], cwd=destination)


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
