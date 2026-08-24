# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

from pathlib import Path


def extract_arch_signature(source_dir: Path, defconfig_path: Path | None = None) -> str:
    """Extract canonical architecture & toolchain signature (board-subtarget-arch-libc-gcc)."""
    source_dir = source_dir.resolve()
    dot_config = source_dir / ".config"
    config_content = ""
    if dot_config.exists():
        config_content = dot_config.read_text(encoding="utf-8", errors="replace")
    elif defconfig_path is not None and defconfig_path.exists():
        config_content = defconfig_path.read_text(encoding="utf-8", errors="replace")

    board = "generic"
    subtarget = "generic"
    arch = "generic"
    libc = "musl"
    gcc_ver = "default"

    for line in config_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("CONFIG_TARGET_BOARD="):
            board = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_TARGET_SUBTARGET="):
            subtarget = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_ARCH="):
            arch = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_LIBC="):
            libc = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_GCC_VERSION="):
            gcc_ver = line.split("=", 1)[1].strip("\"'")
        elif line.startswith("CONFIG_TARGET_") and line.endswith("=y"):
            parts = line[len("CONFIG_TARGET_") : -2].split("_")
            if board == "generic" and len(parts) >= 1:
                board = parts[0]
            if subtarget == "generic" and len(parts) >= 2 and parts[1] != "DEVICE":
                subtarget = parts[1]

    # Sanitize components for safe directory and key usage
    board = "".join(c for c in board if c.isalnum() or c in ("-", "_")).strip("-_") or "generic"
    subtarget = "".join(c for c in subtarget if c.isalnum() or c in ("-", "_")).strip("-_") or "generic"
    arch = "".join(c for c in arch if c.isalnum() or c in ("-", "_")).strip("-_") or "generic"
    libc = "".join(c for c in libc if c.isalnum() or c in ("-", "_")).strip("-_") or "musl"
    gcc_ver = "".join(c for c in gcc_ver if c.isalnum() or c in (".", "-", "_")).strip("-_") or "default"

    return f"{board}-{subtarget}-{arch}-{libc}-{gcc_ver}"
