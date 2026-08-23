# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from collections.abc import Callable
from typing import Any

CommandBuilder = Callable[[Any], None]

_REGISTRY: list[tuple[str, str, CommandBuilder]] = []


def register_command(name: str, help: str) -> Callable[[CommandBuilder], CommandBuilder]:
    def decorator(func: CommandBuilder) -> CommandBuilder:
        _REGISTRY.append((name, help, func))
        return func

    return decorator


def get_commands() -> list[tuple[str, str, CommandBuilder]]:
    return list(_REGISTRY)
