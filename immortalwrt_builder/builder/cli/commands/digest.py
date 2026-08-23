# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ... import layout
from ...core.build import collect_outputs, write_digest_summary
from ...core.config import TargetConfigProvider
from ..common import add_target_argument
from ..registry import register_command


@register_command("digest", "Compute MD5 and SHA256 checksums of built firmware artifacts")
def build_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("digest", help="Compute MD5 and SHA256 checksums of built firmware artifacts")
    add_target_argument(parser)
    parser.add_argument("--summary-file", help="Path to markdown step summary file (or GITHUB_STEP_SUMMARY)")
    parser.set_defaults(handler=handle_digest)


def handle_digest(args: argparse.Namespace) -> int:
    work_root = Path.cwd()
    target = TargetConfigProvider(work_root).load(args.target)
    source_dir = layout.target_source_root(work_root, target.name)
    output_root = layout.target_output_root(work_root, target.name)

    artifacts = collect_outputs(target, source_dir, output_root)
    if not artifacts:
        print("No firmware artifacts found to compute digest for.", flush=True)
        return 0

    summary_file_path = Path(args.summary_file).resolve() if args.summary_file else None
    write_digest_summary(work_root, artifacts, summary_file_path=summary_file_path)
    return 0
