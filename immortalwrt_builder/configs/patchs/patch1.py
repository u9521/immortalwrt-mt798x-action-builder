# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from immortalwrt_builder.builder.core.patch.interface import PatchContext


def patch(context: PatchContext) -> None:
    """Pre-feeds patch: add custom package feed."""
    print("Executing patch1: adding custom extraipk feed...", flush=True)
    custom_feed = "\nsrc-git extraipk https://github.com/ulua3809/ulua_extra_ipk\n"
    current_content = context.read_text("feeds.conf.default") if context.exists("feeds.conf.default") else ""
    if "extraipk" not in current_content:
        context.append_text("feeds.conf.default", custom_feed)
        print("  + Added extraipk to feeds.conf.default", flush=True)
