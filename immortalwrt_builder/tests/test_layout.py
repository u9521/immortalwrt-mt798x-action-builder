# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import unittest
from pathlib import Path

from immortalwrt_builder.builder import layout


class LayoutTests(unittest.TestCase):
    def test_project_package_root(self) -> None:
        root = Path("/test/work")
        self.assertEqual(layout.project_package_root(root), root / "immortalwrt_builder")

    def test_configs_and_targets_root(self) -> None:
        root = Path("/test/work")
        self.assertEqual(layout.project_configs_root(root), root / "immortalwrt_builder/configs")
        self.assertEqual(layout.target_configs_root(root), root / "immortalwrt_builder/configs/targets")
        self.assertEqual(
            layout.target_config_file(root, "sample"), root / "immortalwrt_builder/configs/targets/sample.toml"
        )
        self.assertEqual(layout.defconfigs_root(root), root / "immortalwrt_builder/configs/defconfigs")
        self.assertEqual(layout.patchs_root(root), root / "immortalwrt_builder/configs/patchs")

    def test_workspace_paths(self) -> None:
        root = Path("/test/work")
        self.assertEqual(layout.target_source_root(root, "sample"), root / "source-code/sample")
        self.assertEqual(layout.target_cache_root(root, "sample"), root / "cache/sample")
        self.assertEqual(layout.target_output_root(root, "sample"), root / "out/sample")
        self.assertEqual(layout.target_metadata_file(root, "sample"), root / "infos/sample/workspace.json")
        self.assertEqual(layout.digest_file(root), root / "filedigest.md")


if __name__ == "__main__":
    unittest.main()
