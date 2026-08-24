# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.build import engine
from immortalwrt_builder.builder.core.config.schema import BuildConfig, CcacheConfig, GitSourceConfig, TargetConfig


class BuildTests(unittest.TestCase):
    def test_prepare_config_configures_ccache_and_runs_make_defconfig(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            source_dir.mkdir()
            defconfig_file = temp_path / "sample.config"
            defconfig_file.write_text("CONFIG_TARGET_mediatek=y\n", encoding="utf-8")

            # 1. With explicit ccache dir
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(defconfig_path=defconfig_file),
                ccache=CcacheConfig(enabled=True, dir=Path("cache/test/ccache")),
            )

            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command") as mock_run:
                engine.prepare_config(target, source_dir)

            dot_config = source_dir / ".config"
            self.assertTrue(dot_config.exists())
            content = dot_config.read_text(encoding="utf-8")
            self.assertIn("CONFIG_TARGET_mediatek=y", content)
            self.assertIn("CONFIG_CCACHE=y", content)
            self.assertIn("CONFIG_CCACHE_DIR=", content)
            mock_run.assert_called_once_with(["make", "defconfig"], cwd=source_dir)

            # 2. Without explicit ccache dir (defaults to OpenWrt default, no CONFIG_CCACHE_DIR written)
            target_no_dir = TargetConfig(
                name="test_no_dir",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(defconfig_path=defconfig_file),
                ccache=CcacheConfig(enabled=True, dir=None),
            )
            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command"):
                engine.prepare_config(target_no_dir, source_dir)

            content_no_dir = dot_config.read_text(encoding="utf-8")
            self.assertIn("CONFIG_CCACHE=y", content_no_dir)
            self.assertNotIn("CONFIG_CCACHE_DIR=", content_no_dir)

    def test_download_packages_runs_make_download(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(jobs=4, verbose=True),
            )

            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command") as mock_run:
                engine.download_packages(target, source_dir)

            mock_run.assert_called_once_with(["make", "download", "-j4", "V=s"], cwd=source_dir)

    def test_build_firmware_runs_make(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(jobs=8, verbose=False),
            )

            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command") as mock_run:
                engine.build_firmware(target, source_dir)

            mock_run.assert_called_once()
            args = mock_run.call_args.args[0]
            self.assertEqual(args, ["make", "-j8"])
            self.assertEqual(mock_run.call_args.kwargs["cwd"], source_dir)
            self.assertTrue(mock_run.call_args.kwargs["check"])

    def test_build_firmware_ccache_activation_without_explicit_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            dot_config = source_dir / ".config"
            dot_config.write_text("CONFIG_CCACHE=y\n", encoding="utf-8")

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(jobs=4),
                ccache=CcacheConfig(enabled=True, dir=None),
            )

            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command") as mock_run:
                with mock.patch("immortalwrt_builder.builder.core.build.engine.print_ccache_banner") as mock_banner:
                    engine.build_firmware(target, source_dir)

            mock_banner.assert_called_once()
            # Passed the default .ccache directory without mismatch error
            self.assertEqual(mock_banner.call_args.args[0], (source_dir / ".ccache").resolve())
            mock_run.assert_called()


if __name__ == "__main__":
    unittest.main()
