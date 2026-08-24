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

[patchConfig]
router_ip = "192.168.1.1"
enable_argon = true

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
            self.assertEqual(target.patch_config.get("router_ip"), "192.168.1.1")
            self.assertTrue(target.patch_config.get("enable_argon"))
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

[patchConfig]
base_var = "foo"
override_var = "from_base"

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

[patchConfig]
override_var = "from_child"
child_var = "bar"

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
            self.assertEqual(target.patch_config.get("base_var"), "foo")
            self.assertEqual(target.patch_config.get("override_var"), "from_child")
            self.assertEqual(target.patch_config.get("child_var"), "bar")

            # Test specifying tag in child overrides base branch
            child_tag_file = dir_path / "child_tag.toml"
            child_tag_file.write_text(
                """
name = "child_tag"
extends = "base"

[source]
tag = "v24.10.0"
""",
                encoding="utf-8",
            )
            target_tag = parse_target_definition_file(child_tag_file)
            self.assertEqual(target_tag.name, "child_tag")
            self.assertEqual(target_tag.source.tag, "v24.10.0")
            self.assertIsNone(target_tag.source.branch)
            self.assertIsNone(target_tag.source.commit)

            # Test specifying commit in child overrides base branch
            child_commit_file = dir_path / "child_commit.toml"
            child_commit_file.write_text(
                """
name = "child_commit"
extends = "base"

[source]
commit = "abc123456789"
""",
                encoding="utf-8",
            )
            target_commit = parse_target_definition_file(child_commit_file)
            self.assertEqual(target_commit.name, "child_commit")
            self.assertEqual(target_commit.source.commit, "abc123456789")
            self.assertIsNone(target_commit.source.branch)
            self.assertIsNone(target_commit.source.tag)

    def test_parse_advanced_ccache_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            file_path = dir_path / "custom.toml"
            file_path.write_text(
                """
name = "custom"
[source]
url = "https://example.com"
branch = "main"

[ccache]
enabled = true
max_size = "15G"
compiler_check = "%compiler% -v"
sloppiness = "time_macros,include_file_mtime"
hash_dir = true
base_dir = "/custom/base"
log_file = true
stats_log = true
""",
                encoding="utf-8",
            )
            target = parse_target_definition_file(file_path)
            self.assertTrue(target.ccache.enabled)
            self.assertEqual(target.ccache.max_size, "15G")
            self.assertEqual(target.ccache.compiler_check, "%compiler% -v")
            self.assertEqual(target.ccache.sloppiness, "time_macros,include_file_mtime")
            self.assertTrue(target.ccache.hash_dir)
            self.assertEqual(target.ccache.base_dir, Path("/custom/base"))
            self.assertTrue(target.ccache.log_file)
            self.assertTrue(target.ccache.stats_log)

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
