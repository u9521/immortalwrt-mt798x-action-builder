# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .. import layout

DEFAULT_JOBS = os.cpu_count() or 1


def add_target_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", help="Target name; defaults to IWB_TARGET when set")


def add_jobs_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help=f"Build parallelism threads (default: from target config or CPU count {DEFAULT_JOBS})",
    )


def add_verbose_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=None,
        help="Enable verbose build log output (V=s)",
    )


def add_work_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--work-root",
        default=None,
        help="Custom workspace root directory (overrides global.toml, IWB_WORK_ROOT, and cwd)",
    )


def get_work_root(args: argparse.Namespace, project_root: Path | None = None) -> Path:
    cli_work_root = getattr(args, "work_root", None)
    return layout.resolve_work_root(project_root, cli_work_root)
