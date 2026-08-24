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

    def test_configure_ccache_in_dot_config_writes_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dot_config = Path(temp_dir) / ".config"
            dot_config.write_text("CONFIG_TARGET_mediatek=y\n", encoding="utf-8")
            ccache_dir = Path(temp_dir) / "my_ccache"

            ccache.configure_ccache_in_dot_config(dot_config, ccache_dir)

            content = dot_config.read_text(encoding="utf-8")
            self.assertIn("CONFIG_DEVEL=y", content)
            self.assertIn("CONFIG_CCACHE=y", content)
            self.assertIn(f'CONFIG_CCACHE_DIR="{ccache_dir.resolve()}"', content)

    def test_check_ccache_config_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dot_config = Path(temp_dir) / ".config"
            ccache_dir = Path(temp_dir) / "my_ccache"

            # 1. Matching explicit directory
            dot_config.write_text(
                f'CONFIG_CCACHE=y\nCONFIG_CCACHE_DIR="{ccache_dir.resolve()}"\n',
                encoding="utf-8",
            )
            matched, reason = ccache.check_ccache_config_match(dot_config, ccache_dir)
            self.assertTrue(matched)
            self.assertEqual(reason, "matched")

            # 2. Matching when expected_ccache_dir is None (no dir specified in TOML)
            matched_none, reason_none = ccache.check_ccache_config_match(dot_config, None)
            self.assertTrue(matched_none)
            self.assertEqual(reason_none, "matched")

            # 3. Mismatched explicit directory
            other_dir = Path(temp_dir) / "other_ccache"
            matched2, reason2 = ccache.check_ccache_config_match(dot_config, other_dir)
            self.assertFalse(matched2)
            self.assertIn("mismatched", reason2)

    def test_resolve_effective_ccache_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            source_dir = work_root / "source"
            source_dir.mkdir()

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))

            # 1. Resolves to target cache directory when target.ccache.dir is None
            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                resolved = ccache.resolve_effective_ccache_dir(target, work_root, warn_if_unset=True)
            self.assertEqual(resolved, (work_root / "cache/test/ccache").resolve())
            self.assertIn("[CCACHE WARNING]", stdout.getvalue())

            # 2. Resolves from .config when source_dir has dot_config
            dot_config = source_dir / ".config"
            dot_config.write_text('CONFIG_CCACHE=y\nCONFIG_CCACHE_DIR="/custom/from/dot_config"\n', encoding="utf-8")
            resolved_from_config = ccache.resolve_effective_ccache_dir(target, work_root, source_dir)
            self.assertEqual(resolved_from_config, Path("/custom/from/dot_config").resolve())

            # 3. Overridden when target.ccache.dir is explicitly specified (no warning)
            target.ccache.dir = Path("/custom/cache/dir")
            stdout2 = io.StringIO()
            with mock.patch("sys.stdout", stdout2):
                resolved_custom = ccache.resolve_effective_ccache_dir(target, work_root, source_dir)
            self.assertEqual(resolved_custom, Path("/custom/cache/dir").resolve())
            self.assertNotIn("[CCACHE WARNING]", stdout2.getvalue())

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

    def test_get_ccache_binary_finds_staging_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            staging_ccache = source_dir / "staging_dir" / "host" / "bin" / "ccache"
            staging_ccache.parent.mkdir(parents=True)
            staging_ccache.touch()

            found = ccache.get_ccache_binary(source_dir)
            self.assertEqual(found, str(staging_ccache.resolve()))

    def test_export_ccache_stats_saves_text_to_infos_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            ccache_dir = work_root / "cache"
            ccache_dir.mkdir()
            infos_dir = work_root / "infos"

            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.get_ccache_binary",
                return_value="/usr/bin/ccache",
            ):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    mock_run.return_value = mock.MagicMock(
                        returncode=0,
                        stdout="cache hit (direct) 100\ncache size: 1.5 GB\n",
                    )
                    stats_file = ccache.export_ccache_stats(ccache_dir, infos_dir)

            self.assertIsNotNone(stats_file)
            txt_file = infos_dir / "ccache-stats.txt"
            self.assertTrue(txt_file.exists())
            content = txt_file.read_text(encoding="utf-8")
            self.assertIn("ccache binary:   /usr/bin/ccache", content)
            self.assertIn("cache size: 1.5 GB", content)

            json_file = infos_dir / "ccache-stats.json"
            self.assertFalse(json_file.exists())

    def test_show_ccache_stats_returns_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir) / "ccache"
            ccache_dir.mkdir()
            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.get_ccache_binary",
                return_value="/usr/bin/ccache",
            ):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    mock_run.return_value = mock.MagicMock(returncode=0, stdout="cache hit: 85%\n")
                    output = ccache.show_ccache_stats(ccache_dir)
                    self.assertIn("ccache binary:   /usr/bin/ccache", output)
                    self.assertIn("cache hit: 85%", output)

    def test_clear_ccache_invokes_ccache_C(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir)
            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.get_ccache_binary",
                return_value="/usr/bin/ccache",
            ):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    ccache.clear_ccache(ccache_dir)
                    mock_run.assert_called_once()
                    self.assertEqual(mock_run.call_args.args[0], ["/usr/bin/ccache", "-C"])


if __name__ == "__main__":
    unittest.main()
