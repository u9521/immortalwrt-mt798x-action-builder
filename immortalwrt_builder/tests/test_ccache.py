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

    def test_resolve_effective_ccache_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            source_dir = work_root / "source"
            source_dir.mkdir()

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))

            # 1. Resolves from .config arch_signature when source_dir has dot_config
            dot_config = source_dir / ".config"
            dot_config.write_text(
                'CONFIG_ARCH="aarch64"\n'
                'CONFIG_TARGET_BOARD="mediatek"\n'
                'CONFIG_TARGET_SUBTARGET="filogic"\n'
                'CONFIG_GCC_VERSION="14.3.0"\n'
                'CONFIG_LIBC="musl"\n',
                encoding="utf-8",
            )
            resolved_from_config = ccache.resolve_effective_ccache_dir(target, work_root, source_dir)
            self.assertEqual(
                resolved_from_config,
                (work_root / "cache/ccache/mediatek-filogic-aarch64-musl-14.3.0").resolve(),
            )

            # 2. Overridden when target.ccache.dir is explicitly specified
            target.ccache.dir = Path("/custom/cache/dir")
            resolved_custom = ccache.resolve_effective_ccache_dir(target, work_root, source_dir)
            self.assertEqual(resolved_custom, Path("/custom/cache/dir").resolve())

    def test_print_ccache_banner_displays_prominent_message(self) -> None:
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            ccache.print_ccache_banner(Path("/tmp/ccache"), max_size="3.5G")

        output = stdout.getvalue()
        self.assertIn("[CCACHE ENABLED]", output)
        self.assertIn("/tmp/ccache", output)
        self.assertIn("3.5G", output)

    def test_setup_ccache_environment_sets_env_and_stats_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            source_dir = work_root / "source"
            source_dir.mkdir()
            ccache_dir = work_root / "cache"
            infos_dir = work_root / "infos"
            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                ccache=CcacheConfig(
                    enabled=True,
                    max_size="3.5G",
                    stats_log=True,
                    compiler_check="%compiler% -v",
                    sloppiness="time_macros,include_file_mtime,include_file_ctime,file_macro",
                    hash_dir=False,
                    log_file=True,
                ),
            )

            env = ccache.setup_ccache_environment(
                target, ccache_dir, infos_dir, source_dir=source_dir, base_env={"PATH": "/usr/bin"}
            )
            self.assertEqual(env["CCACHE_DIR"], str(ccache_dir.resolve()))
            self.assertEqual(env["CCACHE_MAXSIZE"], "3.5G")
            self.assertEqual(env["CCACHE_COMPILERCHECK"], "%compiler% -v")
            self.assertEqual(env["CCACHE_SLOPPINESS"], "time_macros,include_file_mtime,include_file_ctime,file_macro")
            self.assertEqual(env["CCACHE_NOHASHDIR"], "1")
            self.assertEqual(env["CCACHE_BASEDIR"], str(source_dir.resolve()))
            self.assertEqual(env["CCACHE_LOGFILE"], str((infos_dir / "ccache.log").resolve()))
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

    def test_show_ccache_stats_returns_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir) / "ccache"
            ccache_dir.mkdir()
            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.get_ccache_binary",
                return_value="/usr/bin/ccache",
            ):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    mock_run.return_value = mock.MagicMock(
                        returncode=0,
                        stdout="cache hit: 85%\n",
                    )
                    out = ccache.show_ccache_stats(ccache_dir)
                    self.assertIn("cache hit: 85%", out)

    def test_clear_ccache_runs_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir) / "ccache"
            ccache_dir.mkdir()
            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.get_ccache_binary",
                return_value="/usr/bin/ccache",
            ):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    ccache.clear_ccache(ccache_dir)
                    mock_run.assert_called_once_with(["/usr/bin/ccache", "-C"], env=mock.ANY, check=False)

    def test_zero_ccache_stats_runs_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ccache_dir = Path(temp_dir) / "ccache"
            ccache_dir.mkdir()
            with mock.patch(
                "immortalwrt_builder.builder.core.build.ccache.get_ccache_binary",
                return_value="/usr/bin/ccache",
            ):
                with mock.patch("immortalwrt_builder.builder.core.build.ccache.run_command") as mock_run:
                    mock_run.return_value = mock.MagicMock(returncode=0)
                    success = ccache.zero_ccache_stats(ccache_dir)
                    self.assertTrue(success)
                    mock_run.assert_called_once_with(
                        ["/usr/bin/ccache", "-z"],
                        env=mock.ANY,
                        check=False,
                        capture_output=True,
                    )


if __name__ == "__main__":
    unittest.main()
