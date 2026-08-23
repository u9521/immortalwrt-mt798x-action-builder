# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder import layout
from immortalwrt_builder.builder.core.config.global_config import load_global_config


class GlobalConfigTests(unittest.TestCase):
    def test_load_global_config_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cfg = load_global_config(project_root)
            self.assertEqual(cfg.default_depth, 1)
            self.assertTrue(cfg.default_download)
            self.assertIsNone(cfg.work_root)

    def test_load_global_config_with_workspace_work_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            global_file = layout.global_config_file(project_root)
            global_file.parent.mkdir(parents=True, exist_ok=True)
            global_file.write_text(
                """
[general]
default_depth = 2

[workspace]
work_root = "/tmp/custom-work"
""",
                encoding="utf-8",
            )

            cfg = load_global_config(project_root)
            self.assertEqual(cfg.default_depth, 2)
            self.assertEqual(cfg.work_root, Path("/tmp/custom-work").resolve())

    def test_resolve_work_root_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            global_file = layout.global_config_file(project_root)
            global_file.parent.mkdir(parents=True, exist_ok=True)
            global_file.write_text(
                """
[workspace]
work_root = "/tmp/from-global-toml"
""",
                encoding="utf-8",
            )

            # 1. Default from global.toml
            res1 = layout.resolve_work_root(project_root)
            self.assertEqual(res1, Path("/tmp/from-global-toml").resolve())

            # 2. Env variable overrides global.toml
            with mock.patch.dict(os.environ, {"IWB_WORK_ROOT": "/tmp/from-env"}):
                res2 = layout.resolve_work_root(project_root)
                self.assertEqual(res2, Path("/tmp/from-env").resolve())

                # 3. CLI argument overrides env variable
                res3 = layout.resolve_work_root(project_root, cli_work_root="/tmp/from-cli")
                self.assertEqual(res3, Path("/tmp/from-cli").resolve())


if __name__ == "__main__":
    unittest.main()
