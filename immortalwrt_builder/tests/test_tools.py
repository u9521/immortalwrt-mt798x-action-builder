# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.cli.commands import tools
from immortalwrt_builder.builder.core.config.schema import BuildConfig, GitSourceConfig, TargetConfig


class ToolsTests(unittest.TestCase):
    def test_handle_ccache_dir(self) -> None:
        target = TargetConfig(name="sample-target", source=GitSourceConfig(url="https://example.com"), build=BuildConfig())
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            with mock.patch("immortalwrt_builder.builder.cli.commands.tools.TargetConfigProvider") as mock_provider:
                mock_provider.return_value.load.return_value = target
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    args = mock.MagicMock(target="sample-target", work_root=str(work_root))
                    ret = tools.handle_ccache_dir(args)

            self.assertEqual(ret, 0)
            self.assertIn("ccache", stdout.getvalue())

    def test_handle_clean_all(self) -> None:
        target = TargetConfig(name="sample-target", source=GitSourceConfig(url="https://example.com"), build=BuildConfig())
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            source_dir = work_root / "source-code" / "sample-target"
            source_dir.mkdir(parents=True)
            cache_dir = work_root / "cache" / "sample-target"
            cache_dir.mkdir(parents=True)

            with mock.patch("immortalwrt_builder.builder.cli.commands.tools.TargetConfigProvider") as mock_provider:
                mock_provider.return_value.load.return_value = target
                args = mock.MagicMock(target="sample-target", work_root=str(work_root), all=True, dirclean=False)
                ret = tools.handle_clean(args)

            self.assertEqual(ret, 0)
            self.assertFalse(source_dir.exists())
            self.assertFalse(cache_dir.exists())

    def test_handle_check_update_detects_changes(self) -> None:
        target = TargetConfig(
            name="sample-target",
            source=GitSourceConfig(url="https://example.com", branch="main"),
            build=BuildConfig(),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            with mock.patch("immortalwrt_builder.builder.cli.commands.tools.TargetConfigProvider") as mock_provider:
                mock_provider.return_value.load.return_value = target
                with mock.patch("immortalwrt_builder.builder.cli.commands.tools.get_local_head_commit", return_value="c1"):
                    with mock.patch(
                        "immortalwrt_builder.builder.cli.commands.tools.get_remote_head_commit", return_value="c2"
                    ):
                        stdout = io.StringIO()
                        with mock.patch("sys.stdout", stdout):
                            args = mock.MagicMock(target="sample-target", work_root=str(work_root))
                            ret = tools.handle_check_update(args)

            self.assertEqual(ret, 0)
            self.assertIn("Build required", stdout.getvalue())

    def test_handle_usage_prints_report(self) -> None:
        target = TargetConfig(name="sample-target", source=GitSourceConfig(url="https://example.com"), build=BuildConfig())
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            with mock.patch("immortalwrt_builder.builder.cli.commands.tools.TargetConfigProvider") as mock_provider:
                mock_provider.return_value.load.return_value = target
                stdout = io.StringIO()
                with mock.patch("sys.stdout", stdout):
                    args = mock.MagicMock(target="sample-target", work_root=str(work_root))
                    ret = tools.handle_usage(args)

            self.assertEqual(ret, 0)
            self.assertIn("Disk Usage Report", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
