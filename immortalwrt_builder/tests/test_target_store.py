# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder import layout
from immortalwrt_builder.builder.core.config import resolver


class TargetStoreTests(unittest.TestCase):
    def test_resolve_target_uses_env_variable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self._write_target(
                project_root,
                "my-target",
                """
name = "my-target"
[source]
url = "https://github.com/immortalwrt/immortalwrt.git"
branch = "master"
""",
            )

            with mock.patch.dict(os.environ, {"IWB_TARGET": "my-target"}):
                target = resolver.resolve_target(project_root)

            self.assertEqual(target.name, "my-target")

    def test_target_config_path_rejects_base_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self._write_target(
                project_root,
                "base-template",
                """
name = "base-template"
base = true
[source]
url = "https://github.com/immortalwrt/immortalwrt.git"
""",
            )

            with self.assertRaisesRegex(ValueError, "base config"):
                resolver.target_config_path(project_root, "base-template")

    def test_target_config_path_falls_back_to_declared_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self._write_target(
                project_root,
                "different_filename",
                """
name = "declared-name"
[source]
url = "https://github.com/immortalwrt/immortalwrt.git"
branch = "master"
""",
            )

            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                target = resolver.load_project_target(project_root, "declared-name")

            self.assertEqual(target.name, "declared-name")

    def _write_target(self, project_root: Path, target_name: str, content: str) -> None:
        file_path = layout.target_config_file(project_root, target_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content.strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
