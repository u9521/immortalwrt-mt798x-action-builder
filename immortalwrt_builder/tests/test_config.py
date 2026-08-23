# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from immortalwrt_builder.builder.core.config.loader import load_mapping, parse_target_definition_file


class ConfigTests(unittest.TestCase):
    def test_load_mapping_parses_toml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.toml"
            file_path.write_text('name = "test-target"\nbase = false\n', encoding="utf-8")
            payload = load_mapping(file_path)
            self.assertEqual(payload.get("name"), "test-target")
            self.assertFalse(payload.get("base"))

    def test_parse_target_definition_file_basic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "sample.toml"
            file_path.write_text(
                """
name = "sample"

[source]
url = "https://github.com/immortalwrt/immortalwrt.git"
branch = "master"
depth = 1

[feeds]
update = true
install = true
custom_feeds = ["src-git extra https://github.com/example/repo"]

[build]
jobs = 4
verbose = true
""",
                encoding="utf-8",
            )
            target = parse_target_definition_file(file_path)
            self.assertEqual(target.name, "sample")
            self.assertFalse(target.base)
            self.assertEqual(target.source.url, "https://github.com/immortalwrt/immortalwrt.git")
            self.assertEqual(target.source.branch, "master")
            self.assertEqual(target.source.depth, 1)
            self.assertTrue(target.feeds.update)
            self.assertEqual(len(target.feeds.custom_feeds), 1)
            self.assertEqual(target.build.jobs, 4)
            self.assertTrue(target.build.verbose)

    def test_inheritance_with_extends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            base_file = dir_path / "base.toml"
            base_file.write_text(
                """
name = "base"
base = true

[source]
url = "https://github.com/immortalwrt/immortalwrt.git"
branch = "openwrt-23.05"

[build]
jobs = 8

[ccache]
enabled = true
""",
                encoding="utf-8",
            )

            child_file = dir_path / "child.toml"
            child_file.write_text(
                """
name = "child"
extends = "base"

[source]
branch = "master"

[build]
verbose = true
""",
                encoding="utf-8",
            )

            target = parse_target_definition_file(child_file)
            self.assertEqual(target.name, "child")
            self.assertFalse(target.base)
            self.assertEqual(target.source.url, "https://github.com/immortalwrt/immortalwrt.git")
            self.assertEqual(target.source.branch, "master")
            self.assertEqual(target.build.jobs, 8)
            self.assertTrue(target.ccache.enabled)
            self.assertTrue(target.build.verbose)

    def test_rejects_circular_extends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            (dir_path / "a.toml").write_text('name = "a"\nextends = "b"\n', encoding="utf-8")
            (dir_path / "b.toml").write_text('name = "b"\nextends = "a"\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Circular target inheritance"):
                parse_target_definition_file(dir_path / "a.toml")

    def test_rejects_missing_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.toml"
            file_path.write_text('[source]\nurl = "https://example.com"\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Missing required 'name'"):
                parse_target_definition_file(file_path)

    def test_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.toml"
            file_path.write_text('name = "test"\nunknown_field = 123\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unsupported target field"):
                parse_target_definition_file(file_path)

    def test_rejects_missing_source_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.toml"
            file_path.write_text('name = "test"\n[source]\nbranch = "main"\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "source.url"):
                parse_target_definition_file(file_path)


if __name__ == "__main__":
    unittest.main()
