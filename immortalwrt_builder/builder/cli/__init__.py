# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from .app import build_app, main
from .registry import get_commands, register_command

__all__ = [
    "build_app",
    "get_commands",
    "main",
    "register_command",
]
