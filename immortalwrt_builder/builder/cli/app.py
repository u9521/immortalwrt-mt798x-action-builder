# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import sys

# Import command modules for registration side effects
from .commands import (
    build,  # noqa: F401
    check_update,  # noqa: F401
    configure,  # noqa: F401
    digest,  # noqa: F401
    download,  # noqa: F401
    run_all,  # noqa: F401
    setup_feeds,  # noqa: F401
    show_target,  # noqa: F401
    sync_source,  # noqa: F401
    tools,  # noqa: F401
    usage,  # noqa: F401
)
from .registry import get_commands


def build_app() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iwb",
        description="ImmortalWrt Action Builder CLI - Build official and custom ImmortalWrt firmwares",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for _, _, build_command in get_commands():
        build_command(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_app()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except Exception as exc:
        print(f"\n[Error] {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
