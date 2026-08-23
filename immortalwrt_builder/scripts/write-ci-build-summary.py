#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write GitHub Actions CI build summary")
    parser.add_argument("--target", required=True, help="Built target name")
    parser.add_argument("--outcome", default="success", help="Build step outcome (success/failure)")
    parser.add_argument("--duration-seconds", type=int, default=0, help="Build duration in seconds")
    parser.add_argument("--summary-file", default=None, help="Output markdown summary file path")
    args = parser.parse_args()

    summary_file_path = args.summary_file or os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file_path:
        print("No summary file specified or found in GITHUB_STEP_SUMMARY.", flush=True)
        return 0

    minutes, seconds = divmod(args.duration_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    duration_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s" if hours else f"{minutes:02d}m {seconds:02d}s"
    status_icon = "✅" if args.outcome == "success" else "❌"

    summary_content = [
        f"## {status_icon} ImmortalWrt Build Summary: `{args.target}`\n",
        f"- **Status**: `{args.outcome.upper()}`",
        f"- **Duration**: `{duration_str}` ({args.duration_seconds}s)",
        f"- **Target**: `{args.target}`\n",
    ]

    # Append filedigest.md if exists
    digest_path = Path("filedigest.md")
    if digest_path.exists():
        summary_content.append("### Firmware Artifacts\n")
        summary_content.append(digest_path.read_text(encoding="utf-8"))

    summary_path = Path(summary_file_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(summary_content) + "\n")

    print(f"Build summary written to {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
