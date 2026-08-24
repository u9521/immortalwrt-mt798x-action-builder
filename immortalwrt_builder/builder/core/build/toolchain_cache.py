# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path

from ... import layout
from ...utils import ensure_directory, run_command
from ..config.schema import TargetConfig


def compute_toolchain_key(
    target: TargetConfig,
    source_dir: Path,
    *,
    work_root: Path | None = None,
) -> str:
    """Compute a deterministic cache key for the target toolchain."""
    source_dir = source_dir.resolve()
    hasher = hashlib.sha256()

    # 1. Target basic identifier
    hasher.update(target.name.encode("utf-8"))

    # 2. Extract toolchain symbols from .config if present, or fallback to defconfig
    dot_config = source_dir / ".config"
    config_content = ""
    if dot_config.exists():
        config_content = dot_config.read_text(encoding="utf-8", errors="replace")
    elif target.build.defconfig_path is not None and target.build.defconfig_path.exists():
        config_content = target.build.defconfig_path.read_text(encoding="utf-8", errors="replace")

    arch = "unknown"
    target_board = "unknown"
    target_subtarget = "unknown"
    gcc_ver = "unknown"
    libc = "unknown"
    binutils_ver = "unknown"

    for line in config_content.splitlines():
        line = line.strip()
        if line.startswith("CONFIG_ARCH="):
            arch = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_TARGET_BOARD="):
            target_board = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_TARGET_SUBTARGET="):
            target_subtarget = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_GCC_VERSION="):
            gcc_ver = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_LIBC="):
            libc = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_BINUTILS_VERSION="):
            binutils_ver = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_TARGET_") and line.endswith("=y"):
            parts = line[len("CONFIG_TARGET_") : -2].split("_")
            if target_board == "unknown" and len(parts) >= 1:
                target_board = parts[0]
            if target_subtarget == "unknown" and len(parts) >= 2 and parts[1] != "DEVICE":
                target_subtarget = parts[1]

    # Include source ref (commit > tag > branch) and repo url in hasher
    if target.source.url:
        hasher.update(target.source.url.encode())
    if target.source.commit:
        hasher.update(f"commit:{target.source.commit}".encode())
    elif target.source.tag:
        hasher.update(f"tag:{target.source.tag}".encode())
    elif target.source.branch:
        hasher.update(f"branch:{target.source.branch}".encode())

    config_signature = f"{arch}|{target_board}|{target_subtarget}|{gcc_ver}|{libc}|{binutils_ver}"
    hasher.update(config_signature.encode("utf-8"))

    # 3. Git tree hashes for tools, toolchain, and include if in a git repo
    git_tree_hash = _get_git_tree_hash(source_dir)
    hasher.update(git_tree_hash.encode("utf-8"))

    # 4. Hash of target patches
    all_patches = [
        *target.patch.pre_feeds_patches,
        *target.patch.post_feeds_patches,
        *target.patch.post_config_patches,
    ]
    for patch_file in sorted(all_patches):
        if patch_file.exists():
            hasher.update(patch_file.read_bytes())

    digest = hasher.hexdigest()[:16]
    return f"toolchain-{target.name}-{arch}-{gcc_ver}-{libc}-{digest}"


def _get_git_tree_hash(source_dir: Path) -> str:
    """Get tree hashes for tools, toolchain, and include directories."""
    git_dir = source_dir / ".git"
    if not git_dir.exists():
        # Fallback: hash the directory names/timestamps if git is missing
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

    # Fallback to HEAD commit
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
    """Archive staging_dir/host, toolchain-*, and hostpkg to a compressed tarball."""
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

    saved = False
    if shutil.which("tar"):
        res = run_command(
            ["tar", "-czf", str(temp_archive), "-C", str(source_dir), *subdirs_to_pack],
            check=False,
            capture_output=True,
            echo=False,
        )
        if res.returncode == 0:
            saved = True

    if not saved:
        with tarfile.open(temp_archive, "w:gz") as tar:
            for rel_path in subdirs_to_pack:
                full_path = source_dir / rel_path
                if full_path.exists():
                    tar.add(full_path, arcname=rel_path)

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
    """Extract toolchain cache archive into source_dir and refresh stamps."""
    source_dir = source_dir.resolve()
    archive_path = archive_path.resolve()

    if not archive_path.exists():
        print(f"[TOOLCHAIN CACHE] Archive not found: {archive_path}", flush=True)
        return False

    size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"[TOOLCHAIN CACHE] Restoring toolchain cache from {archive_path} ({size_mb:.1f} MB)...", flush=True)

    ensure_directory(source_dir)

    extracted = False
    error_msg = ""

    # 1. Prefer system tar for speed and full preservation of symlinks/hardlinks
    if shutil.which("tar"):
        res = run_command(
            ["tar", "-xf", str(archive_path), "-C", str(source_dir)],
            check=False,
            capture_output=True,
            echo=False,
        )
        if res.returncode == 0:
            extracted = True
        else:
            error_msg = res.stderr.strip() or f"tar exited with code {res.returncode}"

    # 2. Fallback to Python tarfile with fully_trusted filter
    if not extracted:
        try:
            with tarfile.open(archive_path, "r:*") as tar:
                if hasattr(tarfile, "fully_trusted_filter"):
                    tar.extractall(path=source_dir, filter="fully_trusted")
                else:
                    tar.extractall(path=source_dir)
            extracted = True
        except Exception as exc:
            error_msg = str(exc)

    if not extracted:
        print(f"[TOOLCHAIN CACHE WARNING] Failed to extract archive {archive_path}: {error_msg}", flush=True)
        # Clean corrupted staging_dir
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
