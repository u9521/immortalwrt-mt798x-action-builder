# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os


def build_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("LC_ALL", "C")
    env.setdefault("LANG", "C.UTF-8")
    env.setdefault("FORCE_UNSAFE_CONFIGURE", "1")
    if extra:
        env.update(extra)
    return env
