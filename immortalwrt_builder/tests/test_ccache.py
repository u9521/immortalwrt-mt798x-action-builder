# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.build import ccache, engine
from immortalwrt_builder.builder.core.config.schema import BuildConfig, GitSourceConfig, TargetConfig


class CcacheTests(unittest.TestCase):
    def test_setup_ccache_environment_sets_env_vars_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(
                    use_ccache=True,
                    ccache_max_size="20G",
                ),
            )

            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.shutil.which", return_value="/usr/bin/ccache"
            ):
                env = ccache.setup_ccache_environment(target, work_root, base_env={"PATH": "/usr/bin:/bin"})

            self.assertIn("CCACHE_DIR", env)
            self.assertIn("CCACHE_MAXSIZE", env)
            self.assertEqual(env["CCACHE_MAXSIZE"], "20G")
            self.assertTrue(Path(env["CCACHE_DIR"]).exists())
            self.assertIn(".ccache-tools", env["PATH"])

            tools_dir = work_root / "cache" / "test" / ".ccache-tools"
            self.assertTrue((tools_dir / "gcc").is_symlink())
            self.assertTrue((tools_dir / "g++").is_symlink())
            self.assertTrue((tools_dir / "clang").is_symlink())

    def test_setup_ccache_environment_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(use_ccache=False),
            )

            env = ccache.setup_ccache_environment(target, work_root, base_env={"PATH": "/bin"})
            self.assertNotIn("CCACHE_DIR", env)

    def test_prepare_config_does_not_modify_dot_config_for_ccache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                build=BuildConfig(use_ccache=True),
            )

            with mock.patch("immortalwrt_builder.builder.core.build.engine.run_command"):
                engine.prepare_config(target, source_dir)

            dot_config = source_dir / ".config"
            if dot_config.exists():
                self.assertNotIn("CONFIG_CCACHE=y", dot_config.read_text(encoding="utf-8"))

    def test_show_ccache_stats_invokes_ccache_s(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir)
            with mock.patch("immortalwrt_builder.builder.core.build.ccache.is_ccache_available", return_value=True):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    mock_run.return_value = mock.MagicMock(stdout="cache hit (direct) 100\n")
                    out = ccache.show_ccache_stats(ccache_dir)
                    self.assertIn("cache hit", out)
                    mock_run.assert_called_once()
                    self.assertEqual(mock_run.call_args.args[0], ["ccache", "-s"])

    def test_clear_ccache_invokes_ccache_C(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir)
            with mock.patch("immortalwrt_builder.builder.core.build.ccache.is_ccache_available", return_value=True):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    ccache.clear_ccache(ccache_dir)
                    mock_run.assert_called_once()
                    self.assertEqual(mock_run.call_args.args[0], ["ccache", "-C"])


if __name__ == "__main__":
    unittest.main()
