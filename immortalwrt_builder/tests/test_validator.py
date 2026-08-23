# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import unittest
from pathlib import Path

from immortalwrt_builder.builder.core.config.schema import BuildConfig, GitSourceConfig, PatchConfig, TargetConfig
from immortalwrt_builder.builder.core.config.validator import validate_target


class ValidatorTests(unittest.TestCase):
    def test_rejects_missing_url(self) -> None:
        target = TargetConfig(
            name="test",
            source=GitSourceConfig(url=None, branch="master"),
        )
        with self.assertRaisesRegex(ValueError, "source.url"):
            validate_target(target, Path("test.toml"))

    def test_rejects_missing_branch_and_tag(self) -> None:
        target = TargetConfig(
            name="test",
            source=GitSourceConfig(url="https://example.com", branch=None, tag=None, commit=None),
        )
        with self.assertRaisesRegex(ValueError, "source.branch, source.tag, or source.commit"):
            validate_target(target, Path("test.toml"))

    def test_rejects_negative_depth(self) -> None:
        target = TargetConfig(
            name="test",
            source=GitSourceConfig(url="https://example.com", branch="main", depth=-1),
        )
        with self.assertRaisesRegex(ValueError, "source.depth"):
            validate_target(target, Path("test.toml"))

    def test_rejects_non_positive_jobs(self) -> None:
        target = TargetConfig(
            name="test",
            source=GitSourceConfig(url="https://example.com", branch="main"),
            build=BuildConfig(jobs=0),
        )
        with self.assertRaisesRegex(ValueError, "Build jobs must be positive"):
            validate_target(target, Path("test.toml"))

    def test_rejects_missing_defconfig_file(self) -> None:
        target = TargetConfig(
            name="test",
            source=GitSourceConfig(url="https://example.com", branch="main"),
            build=BuildConfig(defconfig_path=Path("/non/existent/defconfig.config")),
        )
        with self.assertRaises(FileNotFoundError):
            validate_target(target, Path("test.toml"))

    def test_rejects_missing_diy_script(self) -> None:
        target = TargetConfig(
            name="test",
            source=GitSourceConfig(url="https://example.com", branch="main"),
            patch=PatchConfig(pre_feeds_scripts=[Path("/non/existent/script.sh")]),
        )
        with self.assertRaises(FileNotFoundError):
            validate_target(target, Path("test.toml"))


if __name__ == "__main__":
    unittest.main()
