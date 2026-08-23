# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import layout
from .utils import directory_size_bytes, format_bytes, write_json


def analyze_workspace_usage(
    target: Any,
    source_dir: Path,
    cache_dir: Path,
    output_dir: Path,
) -> dict[str, object]:
    sections: dict[str, object] = {
        "source": {
            "path": str(source_dir),
            "size_bytes": directory_size_bytes(source_dir),
            "size_formatted": format_bytes(directory_size_bytes(source_dir)),
        },
        "cache": {
            "path": str(cache_dir),
            "size_bytes": directory_size_bytes(cache_dir),
            "size_formatted": format_bytes(directory_size_bytes(cache_dir)),
        },
        "output": {
            "path": str(output_dir),
            "size_bytes": directory_size_bytes(output_dir),
            "size_formatted": format_bytes(directory_size_bytes(output_dir)),
        },
    }
    total_bytes = sum(
        section["size_bytes"]  # type: ignore[index]
        for section in sections.values()
    )
    return {
        "target": target.name if hasattr(target, "name") else str(target),
        "total_bytes": total_bytes,
        "total_formatted": format_bytes(total_bytes),
        "sections": sections,
    }


def print_usage_report(report: dict[str, object]) -> None:
    target_name = report.get("target", "unknown")
    total_formatted = report.get("total_formatted", "0 B")
    print(f"\n=== Disk Usage Report: {target_name} (Total: {total_formatted}) ===", flush=True)

    sections = report.get("sections", {})
    if isinstance(sections, dict):
        for name, data in sections.items():
            if isinstance(data, dict):
                path = data.get("path", "")
                size = data.get("size_formatted", "0 B")
                print(f"  [{name.upper():<7}] {size:<10} {path}", flush=True)
    print("=" * 60, flush=True)


def write_usage_report(
    target: Any,
    source_dir: Path,
    cache_dir: Path,
    output_dir: Path,
) -> dict[str, object]:
    report = analyze_workspace_usage(target, source_dir, cache_dir, output_dir)
    target_name = target.name if hasattr(target, "name") else str(target)
    work_root = source_dir.parent.parent if source_dir.parent.name == layout.SOURCE_CODE_DIR_NAME else Path.cwd()
    report_file = layout.target_disk_usage_file(work_root, target_name)
    write_json(report_file, report)
    return report
