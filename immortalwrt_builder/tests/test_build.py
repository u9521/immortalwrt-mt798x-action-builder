# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.build import engine
from immortalwrt_builder.builder.core.config.schema import BuildConfig, GitSourceConfig, TargetConfig


class BuildTests(unittest.TestCase):
    def test_prepare_config_copies_defconfig_and_runs_make_defconfig(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            source_dir.mkdir()
            defconfig_file = temp_path / "sample.config"
            defconfig_file.write_text("CONFIG_TARGET_mediatek=y\n", encoding="utf-8")

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(
                    defconfig_path=defconfig_file,
                    extra_configs=["CONFIG_PACKAGE_luci=y"],
                ),
            )

            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command") as mock_run:
                engine.prepare_config(target, source_dir)

            dot_config = source_dir / ".config"
            self.assertTrue(dot_config.exists())
            content = dot_config.read_text(encoding="utf-8")
            self.assertIn("CONFIG_TARGET_mediatek=y", content)
            self.assertIn("CONFIG_PACKAGE_luci=y", content)
            mock_run.assert_called_once_with(["make", "defconfig"], cwd=source_dir)

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
            self.assertEqual(mock_run.call_args.args[0], ["make", "-j8"])
            self.assertEqual(mock_run.call_args.kwargs["cwd"], source_dir)
            self.assertTrue(mock_run.call_args.kwargs["check"])
            self.assertIn("CCACHE_DIR", mock_run.call_args.kwargs["env"])


if __name__ == "__main__":
    unittest.main()
