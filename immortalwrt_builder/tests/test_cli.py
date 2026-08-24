# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.cli.app import main
from immortalwrt_builder.builder.core.config.schema import GitSourceConfig, TargetConfig


def _dummy_target(name: str) -> TargetConfig:
    return TargetConfig(
        name=name,
        source=GitSourceConfig(url="https://example.com/repo.git", branch="master"),
        config_path=Path(f"{name}.toml"),
    )


class CliTests(unittest.TestCase):
    def test_cli_help_displays_subcommands(self) -> None:
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout), self.assertRaises(SystemExit) as ctx:
            main(["--help"])

        self.assertEqual(ctx.exception.code, 0)
        output = stdout.getvalue()
        self.assertIn("show-target", output)
        self.assertIn("sync-source", output)
        self.assertIn("feeds-update", output)
        self.assertIn("feeds-install", output)
        self.assertIn("configure", output)
        self.assertIn("download", output)
        self.assertIn("build", output)
        self.assertIn("digest", output)
        self.assertIn("tools", output)
        self.assertNotIn("setup-feeds", output)

    def test_show_target_command_runs(self) -> None:
        target = _dummy_target("sample")
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            with mock.patch(
                "immortalwrt_builder.builder.cli.commands.show_target.TargetConfigProvider"
            ) as mock_provider:
                mock_provider.return_value.load.return_value = target
                ret = main(["show-target", "--target", "sample"])

        self.assertEqual(ret, 0)
        self.assertIn("Target: sample", stdout.getvalue())

    def test_sync_source_command_invokes_sync(self) -> None:
        target = _dummy_target("sample")
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            with mock.patch.object(Path, "cwd", return_value=work_root):
                with mock.patch(
                    "immortalwrt_builder.builder.cli.commands.sync_source.TargetConfigProvider"
                ) as mock_provider:
                    mock_provider.return_value.load.return_value = target
                    with mock.patch("immortalwrt_builder.builder.cli.commands.sync_source.sync_source") as mock_sync:
                        ret = main(["sync-source", "--target", "sample"])

        self.assertEqual(ret, 0)
        mock_sync.assert_called_once()

    def test_feeds_update_command_invokes_update(self) -> None:
        target = _dummy_target("sample")
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            (work_root / "source-code" / "sample").mkdir(parents=True, exist_ok=True)
            with mock.patch.object(Path, "cwd", return_value=work_root):
                with mock.patch("immortalwrt_builder.builder.cli.commands.feeds.TargetConfigProvider") as mock_provider:
                    mock_provider.return_value.load.return_value = target
                    with mock.patch("immortalwrt_builder.builder.cli.commands.feeds.update_feeds") as mock_update:
                        ret = main(["feeds-update", "--target", "sample"])

        self.assertEqual(ret, 0)
        mock_update.assert_called_once()

    def test_feeds_install_command_invokes_install(self) -> None:
        target = _dummy_target("sample")
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            (work_root / "source-code" / "sample").mkdir(parents=True, exist_ok=True)
            with mock.patch.object(Path, "cwd", return_value=work_root):
                with mock.patch("immortalwrt_builder.builder.cli.commands.feeds.TargetConfigProvider") as mock_provider:
                    mock_provider.return_value.load.return_value = target
                    with mock.patch("immortalwrt_builder.builder.cli.commands.feeds.install_feeds") as mock_install:
                        ret = main(["feeds-install", "--target", "sample"])

        self.assertEqual(ret, 0)
        mock_install.assert_called_once()

    def test_build_command_invokes_build(self) -> None:
        target = _dummy_target("sample")
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            (work_root / "source-code" / "sample").mkdir(parents=True, exist_ok=True)
            with mock.patch.object(Path, "cwd", return_value=work_root):
                with mock.patch("immortalwrt_builder.builder.cli.commands.build.TargetConfigProvider") as mock_provider:
                    mock_provider.return_value.load.return_value = target
                    with mock.patch("immortalwrt_builder.builder.cli.commands.build.build_firmware") as mock_build:
                        with mock.patch(
                            "immortalwrt_builder.builder.cli.commands.build.collect_outputs", return_value=[]
                        ):
                            with mock.patch("immortalwrt_builder.builder.cli.commands.build.write_usage_report"):
                                ret = main(["build", "--target", "sample", "-j", "4", "-v"])

        self.assertEqual(ret, 0)
        mock_build.assert_called_once_with(target, work_root / "source-code/sample", jobs=4, verbose=True)

    def test_toolchain_key_command(self) -> None:
        target = _dummy_target("sample")
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            with mock.patch("immortalwrt_builder.builder.cli.commands.toolchain.TargetConfigProvider") as mock_provider:
                mock_provider.return_value.load.return_value = target
                with mock.patch(
                    "immortalwrt_builder.builder.cli.commands.toolchain.compute_toolchain_key",
                    return_value="toolchain-sample-key-123",
                ):
                    ret = main(["toolchain-key", "--target", "sample"])

        self.assertEqual(ret, 0)
        self.assertEqual(stdout.getvalue().strip(), "toolchain-sample-key-123")

    def test_tools_ccache_dir_command(self) -> None:
        target = _dummy_target("sample")
        stdout = io.StringIO()
        with mock.patch("sys.stdout", stdout):
            with mock.patch("immortalwrt_builder.builder.cli.commands.tools.TargetConfigProvider") as mock_provider:
                mock_provider.return_value.load.return_value = target
                with mock.patch(
                    "immortalwrt_builder.builder.cli.commands.tools.resolve_effective_ccache_dir",
                    return_value=Path("/tmp/ccache/dir"),
                ):
                    ret = main(["tools", "ccache-dir", "--target", "sample"])

        self.assertEqual(ret, 0)
        self.assertEqual(stdout.getvalue().strip(), "/tmp/ccache/dir")


if __name__ == "__main__":
    unittest.main()
