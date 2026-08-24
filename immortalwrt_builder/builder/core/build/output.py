# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path

from ... import layout
from ...utils import ensure_directory, format_bytes, md5_file, sha256_file
from ..config.schema import TargetConfig


def collect_outputs(
    target: TargetConfig,
    source_dir: Path,
    output_root: Path,
) -> list[dict[str, object]]:
    source_dir = source_dir.resolve()
    output_root = output_root.resolve()
    dist_dir = ensure_directory(output_root / target.output.dist_dir if target.output.dist_dir else output_root)

    bin_dir = source_dir / "bin"
    if not bin_dir.exists():
        print(f"Warning: bin directory not found at {bin_dir}", flush=True)
        return []

    # Identify search targets directory
    search_dirs: list[Path] = []
    if target.output.target_dir:
        specific_dir = source_dir / target.output.target_dir
        if specific_dir.exists():
            search_dirs.append(specific_dir)

    targets_root = bin_dir / "targets"
    if targets_root.exists() and targets_root not in search_dirs:
        # Search all subtarget directories under bin/targets/*/*
        for root, dirs, _ in os.walk(targets_root):
            if "packages" in dirs:
                dirs.remove("packages")
            current = Path(root)
            if current != targets_root:
                search_dirs.append(current)

    if not search_dirs:
        search_dirs.append(bin_dir)

    artifact_records: list[dict[str, object]] = []
    collected_names: set[str] = set()

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for item in search_dir.iterdir():
            if not item.is_file():
                continue
            if item.name in collected_names:
                continue

            matches = any(fnmatch.fnmatch(item.name, pattern) for pattern in target.output.firmware_patterns)
            if matches:
                dest_file = dist_dir / item.name
                shutil.copy2(item, dest_file)
                collected_names.add(item.name)

                size_bytes = dest_file.stat().st_size
                record: dict[str, object] = {
                    "filename": item.name,
                    "path": str(dest_file),
                    "size_bytes": size_bytes,
                    "size_formatted": format_bytes(size_bytes),
                    "md5": md5_file(dest_file),
                    "sha256": sha256_file(dest_file),
                }
                artifact_records.append(record)

    # Sort artifacts by name
    artifact_records.sort(key=lambda r: str(r["filename"]))
    return artifact_records


def generate_digest_table(artifacts: list[dict[str, object]]) -> str:
    lines = [
        "| File name | Size | MD5 | SHA256 |",
        "|:---|:---|:---|:---|",
    ]
    for art in artifacts:
        filename = str(art.get("filename", ""))
        size = str(art.get("size_formatted", ""))
        md5 = str(art.get("md5", ""))
        sha256 = str(art.get("sha256", ""))
        lines.append(f"| {filename} | {size} | `{md5}` | `{sha256}` |")
    return "\n".join(lines) + "\n"


def write_digest_summary(
    work_root: Path,
    artifacts: list[dict[str, object]],
) -> str:
    table = generate_digest_table(artifacts)
    digest_path = layout.digest_file(work_root)
    digest_path.write_text(table, encoding="utf-8")
    print(f"\nGenerated digest summary table at {digest_path}:\n", flush=True)
    print(table, flush=True)
    return table
