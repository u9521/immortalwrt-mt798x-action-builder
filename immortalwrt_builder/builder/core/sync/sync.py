# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path

from ... import layout
from ...utils import directory_size_bytes, ensure_directory, format_bytes, write_json
from ..config.schema import TargetConfig
from .git import clone_or_fetch_repo, get_local_head_commit


def sync_source(
    target: TargetConfig,
    source_dir: Path,
    cache_root: Path,
) -> dict[str, object]:
    source_dir = ensure_directory(source_dir.resolve())
    cache_root = ensure_directory(cache_root.resolve())

    clone_or_fetch_repo(target.source, source_dir)

    upstream_commit = ""
    try:
        upstream_commit = get_local_head_commit(source_dir)
    except Exception:
        pass

    work_root = source_dir.parent.parent if source_dir.parent.name == layout.SOURCE_CODE_DIR_NAME else Path.cwd()
    project_root = Path.cwd()
    local_commit = ""
    try:
        local_commit = get_local_head_commit(project_root)
    except Exception:
        pass

    _print_source_root_entry_sizes(source_dir)

    metadata: dict[str, object] = {
        "target": target.name,
        "config_path": str(target.config_path),
        "source_dir": str(source_dir),
        "cache_root": str(cache_root),
        "repo_url": target.source.url,
        "repo_branch": target.source.branch,
        "repo_tag": target.source.tag,
        "repo_commit": target.source.commit,
        "last_upstream_commit": upstream_commit,
        "last_local_commit": local_commit,
    }

    metadata_file = layout.target_metadata_file(work_root, target.name)
    write_json(metadata_file, metadata)

    legacy_infos_dir = layout.infos_root(work_root)
    if legacy_infos_dir.exists():
        if upstream_commit:
            (legacy_infos_dir / "lastUpstreamCommit").write_text(f"{upstream_commit}\n", encoding="utf-8")
        if local_commit:
            (legacy_infos_dir / "lastCommit").write_text(f"{local_commit}\n", encoding="utf-8")

    return metadata


def _print_source_root_entry_sizes(source_dir: Path) -> None:
    entries: list[tuple[str, int]] = []
    for child in source_dir.iterdir():
        if child.is_dir():
            entries.append((f"{child.name}/", directory_size_bytes(child)))
            continue
        if child.is_file():
            entries.append((child.name, child.stat().st_size))

    print(f"\nSource tree disk usage ({source_dir}):", flush=True)
    for name, size_bytes in sorted(entries, key=lambda entry: entry[1], reverse=True)[:15]:
        print(f"  {name:<35} {format_bytes(size_bytes)}", flush=True)
    print("", flush=True)
