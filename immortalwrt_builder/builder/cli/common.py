# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import os

DEFAULT_JOBS = os.cpu_count() or 1


def add_target_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", help="Target name; defaults to IWB_TARGET or IMMORTALWRT_TARGET when set")


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
