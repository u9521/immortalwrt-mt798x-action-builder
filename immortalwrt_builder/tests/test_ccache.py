# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.build import ccache
from immortalwrt_builder.builder.core.config.schema import CcacheConfig, GitSourceConfig, TargetConfig


class CcacheTests(unittest.TestCase):
    def test_is_openwrt_ccache_enabled_detects_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dot_config = Path(temp_dir) / ".config"
            dot_config.write_text('CONFIG_CCACHE=y\nCONFIG_CCACHE_DIR="/opt/ccache"\n', encoding="utf-8")

            enabled, config_dir = ccache.is_openwrt_ccache_enabled(dot_config)
            self.assertTrue(enabled)
            self.assertEqual(config_dir, "/opt/ccache")

    def test_is_openwrt_ccache_enabled_when_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dot_config = Path(temp_dir) / ".config"
            dot_config.write_text("# CONFIG_CCACHE is not set\n", encoding="utf-8")

            enabled, config_dir = ccache.is_openwrt_ccache_enabled(dot_config)
            self.assertFalse(enabled)
            self.assertIsNone(config_dir)

    def test_resolve_effective_ccache_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            source_dir = work_root / "source"
            source_dir.mkdir()
            dot_config = source_dir / ".config"
            dot_config.write_text('CONFIG_CCACHE=y\nCONFIG_CCACHE_DIR="./.my_ccache"\n', encoding="utf-8")

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))

            # 1. Resolves from .config when target.ccache.dir is None
            resolved = ccache.resolve_effective_ccache_dir(target, work_root, source_dir)
            self.assertEqual(resolved, (source_dir / ".my_ccache").resolve())

            # 2. Overridden when target.ccache.dir is explicitly specified
            target.ccache.dir = Path("/custom/cache/dir")
            resolved_custom = ccache.resolve_effective_ccache_dir(target, work_root, source_dir)
            self.assertEqual(resolved_custom, Path("/custom/cache/dir").resolve())

    def test_print_ccache_banner_displays_prominent_message(self) -> None:
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            ccache.print_ccache_banner(Path("/tmp/ccache"), max_size="25G")

        output = stdout.getvalue()
        self.assertIn("[CCACHE ENABLED]", output)
        self.assertIn("/tmp/ccache", output)
        self.assertIn("25G", output)

    def test_setup_ccache_environment_sets_env_and_stats_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            ccache_dir = work_root / "cache"
            infos_dir = work_root / "infos"
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                ccache=CcacheConfig(
                    enabled=True,
                    max_size="20G",
                    stats_log=True,
                ),
            )

            env = ccache.setup_ccache_environment(target, ccache_dir, infos_dir, base_env={"PATH": "/usr/bin"})
            self.assertEqual(env["CCACHE_DIR"], str(ccache_dir.resolve()))
            self.assertEqual(env["CCACHE_MAXSIZE"], "20G")
            self.assertEqual(env["CCACHE_STATS_LOG"], str((infos_dir / "ccache-stats.log").resolve()))

    def test_export_ccache_stats_saves_to_infos_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            ccache_dir = work_root / "cache"
            infos_dir = work_root / "infos"

            with mock.patch("immortalwrt_builder.builder.core.build.ccache.is_ccache_available", return_value=True):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    mock_run.side_effect = [
                        # First call: ccache --show-stats --format=json
                        mock.MagicMock(returncode=0, stdout='{"direct_hit_rate_pct": 85.5, "hits": 100}\n'),
                        # Second call: ccache -s
                        mock.MagicMock(returncode=0, stdout="cache hit (direct) 100\ncache size: 1.5 GB\n"),
                    ]

                    stats = ccache.export_ccache_stats(ccache_dir, infos_dir)

            self.assertIsNotNone(stats)
            assert stats is not None
            self.assertEqual(stats.get("direct_hit_rate_pct"), 85.5)

            # Verify files in infos_dir
            json_file = infos_dir / "ccache-stats.json"
            txt_file = infos_dir / "ccache-stats.txt"
            self.assertTrue(json_file.exists())
            self.assertTrue(txt_file.exists())
            self.assertIn("direct_hit_rate_pct", json_file.read_text(encoding="utf-8"))

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
