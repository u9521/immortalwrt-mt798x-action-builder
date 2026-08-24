# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

from ... import layout
from ...utils import ensure_directory, run_command
from ..config.schema import TargetConfig
from .arch import extract_arch_signature


def compute_toolchain_key(
    target: TargetConfig,
    source_dir: Path,
    *,
    work_root: Path | None = None,
) -> str:
    """Compute a deterministic, cross-target cache key for the target toolchain."""
    source_dir = source_dir.resolve()
    arch_sig = extract_arch_signature(source_dir, target.build.defconfig_path)

    hasher = hashlib.sha256()
    hasher.update(arch_sig.encode("utf-8"))

    if target.source.url:
        hasher.update(target.source.url.encode("utf-8"))

    git_tree_hash = _get_git_tree_hash(source_dir)
    hasher.update(git_tree_hash.encode("utf-8"))

    tree_digest = hasher.hexdigest()[:12]
    return f"toolchain-{arch_sig}-{tree_digest}"


def _get_git_tree_hash(source_dir: Path) -> str:
    """Get tree hashes for tools, toolchain, and include directories."""
    git_dir = source_dir / ".git"
    if not git_dir.exists():
        return "nogit"

    result = run_command(
        ["git", "rev-parse", "HEAD:tools", "HEAD:toolchain", "HEAD:include"],
        cwd=source_dir,
        check=False,
        capture_output=True,
        echo=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return hashlib.sha256(result.stdout.strip().encode("utf-8")).hexdigest()[:16]

    result_head = run_command(
        ["git", "rev-parse", "HEAD"],
        cwd=source_dir,
        check=False,
        capture_output=True,
        echo=False,
    )
    if result_head.returncode == 0 and result_head.stdout.strip():
        return result_head.stdout.strip()[:16]

    return "nogit"


def resolve_toolchain_archive_path(
    target: TargetConfig,
    work_root: Path,
) -> Path:
    """Resolve the path for the toolchain cache archive file."""
    work_root = work_root.resolve()
    if target.toolchain_cache.dir is not None:
        cache_dir = (
            target.toolchain_cache.dir.resolve()
            if target.toolchain_cache.dir.is_absolute()
            else (work_root / target.toolchain_cache.dir).resolve()
        )
        return cache_dir / f"toolchain-{target.name}.tar.gz"

    return layout.target_toolchain_archive_path(work_root, target.name).resolve()


def touch_toolchain_stamps(source_dir: Path) -> int:
    """Touch stamp files in staging_dir (host, toolchain-*, hostpkg) so OpenWrt considers them fresh.

    Uses current system time (mtime <= now) to avoid triggering GNU Make's Clock Skew warning.
    Explicitly excludes target-* directories so target rootfs/package stamps remain isolated.
    """
    source_dir = source_dir.resolve()
    staging_dir = source_dir / "staging_dir"
    if not staging_dir.exists():
        return 0

    now = time.time()
    count = 0

    # Collect toolchain-related directories only (host, hostpkg, packages, and toolchain-*)
    toolchain_dirs: list[Path] = []
    for item in ("host", "hostpkg", "packages"):
        d = staging_dir / item
        if d.is_dir():
            toolchain_dirs.append(d)

    for tc_dir in staging_dir.glob("toolchain-*"):
        if tc_dir.is_dir():
            toolchain_dirs.append(tc_dir)

    for base_dir in toolchain_dirs:
        # Search for stamp directories
        for stamp_dir in base_dir.glob("**/stamp"):
            if stamp_dir.is_dir():
                for stamp_file in stamp_dir.rglob("*"):
                    if stamp_file.is_file():
                        try:
                            os.utime(stamp_file, (now, now))
                            count += 1
                        except OSError:
                            pass

        # Touch top-level built indicators within toolchain components
        for top_stamp in base_dir.glob(".built*"):
            if top_stamp.is_file():
                try:
                    os.utime(top_stamp, (now, now))
                    count += 1
                except OSError:
                    pass

    return count


def is_toolchain_cached(source_dir: Path) -> bool:
    """Check whether a valid compiled toolchain is currently present in source_dir."""
    source_dir = source_dir.resolve()
    staging_dir = source_dir / "staging_dir"
    if not staging_dir.exists():
        return False

    host_bin = staging_dir / "host" / "bin"
    if not host_bin.is_dir() or not any(host_bin.iterdir()):
        return False

    # Check for at least one toolchain directory with binaries
    toolchain_dirs = list(staging_dir.glob("toolchain-*"))
    if not toolchain_dirs:
        return False

    for tc_dir in toolchain_dirs:
        bin_dir = tc_dir / "bin"
        if bin_dir.is_dir() and any(bin_dir.glob("*-gcc*")):
            return True

    return False


def save_toolchain_cache(
    target: TargetConfig,
    source_dir: Path,
    archive_path: Path,
    *,
    key: str | None = None,
) -> Path:
    """Archive staging_dir/host, toolchain-*, and hostpkg to a compressed tarball using system tar."""
    source_dir = source_dir.resolve()
    archive_path = archive_path.resolve()
    staging_dir = source_dir / "staging_dir"

    if not staging_dir.exists():
        raise FileNotFoundError(f"staging_dir does not exist in {source_dir}")

    ensure_directory(archive_path.parent)

    # Collect existing directories to include
    subdirs_to_pack: list[str] = []
    for item in ("host", "hostpkg", "packages"):
        if (staging_dir / item).exists():
            subdirs_to_pack.append(f"staging_dir/{item}")

    for tc_dir in staging_dir.glob("toolchain-*"):
        if tc_dir.is_dir():
            subdirs_to_pack.append(f"staging_dir/{tc_dir.name}")

    if not subdirs_to_pack:
        raise ValueError(f"No toolchain components found in {staging_dir} to save.")

    # Write metadata file inside staging_dir before packing
    meta_file = staging_dir / "toolchain-meta.json"
    meta_payload = {
        "target": target.name,
        "key": key or compute_toolchain_key(target, source_dir),
        "created_at": datetime.now(UTC).isoformat(),
        "source_dir": str(source_dir),
        "subdirs": subdirs_to_pack,
    }
    meta_file.write_text(json.dumps(meta_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    subdirs_to_pack.append("staging_dir/toolchain-meta.json")

    print(f"Creating toolchain cache archive: {archive_path.name} ...", flush=True)

    temp_archive = archive_path.with_suffix(".tmp.tar.gz")
    if temp_archive.exists():
        temp_archive.unlink()

    run_command(
        ["tar", "-czf", str(temp_archive), "-C", str(source_dir), *subdirs_to_pack],
        check=True,
        capture_output=True,
        echo=False,
    )

    # Atomic move
    if archive_path.exists():
        archive_path.unlink()
    shutil.move(temp_archive, archive_path)

    size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"Toolchain cache saved successfully: {archive_path} ({size_mb:.1f} MB)", flush=True)
    return archive_path


def restore_toolchain_cache(
    target: TargetConfig,
    source_dir: Path,
    archive_path: Path,
) -> bool:
    """Extract toolchain cache archive into source_dir using system tar and refresh stamps."""
    source_dir = source_dir.resolve()
    archive_path = archive_path.resolve()

    if not archive_path.exists():
        print(f"[TOOLCHAIN CACHE] Archive not found: {archive_path}", flush=True)
        return False

    size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"[TOOLCHAIN CACHE] Restoring toolchain cache from {archive_path} ({size_mb:.1f} MB)...", flush=True)

    ensure_directory(source_dir)

    try:
        run_command(
            ["tar", "-xf", str(archive_path), "-C", str(source_dir)],
            check=True,
            capture_output=True,
            echo=False,
        )
    except Exception as exc:
        print(f"[TOOLCHAIN CACHE WARNING] Failed to extract archive {archive_path}: {exc}", flush=True)
        corrupted_staging = source_dir / "staging_dir"
        if corrupted_staging.exists():
            shutil.rmtree(corrupted_staging, ignore_errors=True)
        return False

    # Touch stamps so OpenWrt timestamp.pl recognizes toolchain as up-to-date
    touched = touch_toolchain_stamps(source_dir)
    print(f"[TOOLCHAIN CACHE] Toolchain restored successfully ({touched} stamp files refreshed).", flush=True)
    return True


def clear_toolchain_cache(
    target: TargetConfig,
    work_root: Path,
) -> bool:
    """Clear toolchain cache archive for the target."""
    archive_path = resolve_toolchain_archive_path(target, work_root)
    removed = False
    if archive_path.exists():
        archive_path.unlink()
        print(f"Removed toolchain archive: {archive_path}", flush=True)
        removed = True

    cache_dir = archive_path.parent
    if cache_dir.exists() and not any(cache_dir.iterdir()):
        shutil.rmtree(cache_dir, ignore_errors=True)

    return removed
