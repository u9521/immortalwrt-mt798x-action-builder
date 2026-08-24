# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...utils import ensure_directory, run_command

if TYPE_CHECKING:
    from ..config.schema import TargetConfig


@dataclass(slots=True)
class PatchContext:
    target: TargetConfig
    source_dir: Path
    work_root: Path

    @property
    def patch_config(self) -> dict[str, Any]:
        """Access target-specific [patchConfig] mapping."""
        return self.target.patch_config

    def path(self, relative_path: str | Path) -> Path:
        """Resolve a path relative to source_dir."""
        p = Path(relative_path)
        if p.is_absolute():
            return p
        return (self.source_dir / p).resolve()

    def exists(self, relative_path: str | Path) -> bool:
        """Check if a file or directory exists in the source tree."""
        return self.path(relative_path).exists()

    def read_text(self, relative_path: str | Path) -> str:
        """Read full text of a file in the source tree."""
        return self.path(relative_path).read_text(encoding="utf-8")

    def write_text(self, relative_path: str | Path, content: str) -> None:
        """Write text content to a file in the source tree."""
        target_path = self.path(relative_path)
        ensure_directory(target_path.parent)
        target_path.write_text(content, encoding="utf-8")

    def append_text(self, relative_path: str | Path, content: str) -> None:
        """Append text content to a file in the source tree."""
        target_path = self.path(relative_path)
        ensure_directory(target_path.parent)
        with target_path.open("a", encoding="utf-8") as f:
            f.write(content)

    def replace_text(
        self,
        relative_path: str | Path,
        pattern: str | re.Pattern[str],
        replacement: str,
    ) -> bool:
        """
        Replace occurrences of pattern with replacement in the target file.
        Supports both literal string matching and regular expression objects.
        Returns True if content was modified.
        """
        target_path = self.path(relative_path)
        if not target_path.exists():
            return False

        content = target_path.read_text(encoding="utf-8")
        if isinstance(pattern, str):
            new_content = content.replace(pattern, replacement)
        else:
            new_content = pattern.sub(replacement, content)

        if new_content != content:
            target_path.write_text(new_content, encoding="utf-8")
            return True
        return False

    def remove(self, relative_path: str | Path) -> None:
        """Remove a file or directory in the source tree."""
        target_path = self.path(relative_path)
        if target_path.is_dir() and not target_path.is_symlink():
            shutil.rmtree(target_path)
        elif target_path.exists():
            target_path.unlink()

    def copy(self, src: str | Path, dst: str | Path) -> None:
        """Copy a file or directory into the source tree."""
        src_path = Path(src)
        dst_path = self.path(dst)
        ensure_directory(dst_path.parent)
        if src_path.is_dir():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

    def run_command(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a command in the source directory."""
        return run_command(
            command,
            cwd=cwd or self.source_dir,
            check=check,
            capture_output=capture_output,
        )
