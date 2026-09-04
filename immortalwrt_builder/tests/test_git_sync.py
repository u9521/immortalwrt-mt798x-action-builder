# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.config.schema import GitSourceConfig
from immortalwrt_builder.builder.core.sync import git


class GitSyncTests(unittest.TestCase):
    def test_clone_or_fetch_repo_inits_and_fetches_branch(self) -> None:
        source = GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", branch="openwrt-25.12", depth=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "source"
            with mock.patch("immortalwrt_builder.builder.core.sync.git.run_command") as mock_run:
                git.clone_or_fetch_repo(source, dest)

            commands = [call.args[0] for call in mock_run.call_args_list]
            self.assertEqual(commands[0], ["git", "init"])
            self.assertEqual(
                commands[1], ["git", "remote", "add", "origin", "https://github.com/immortalwrt/immortalwrt.git"]
            )
            self.assertEqual(commands[2], ["git", "fetch", "--depth", "1", "origin", "openwrt-25.12"])
            self.assertEqual(commands[3], ["git", "checkout", "-B", "openwrt-25.12", "FETCH_HEAD"])

    def test_clone_or_fetch_repo_shallow_fetches_exact_commit(self) -> None:
        source = GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", commit="abc123456789", depth=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "source"
            with mock.patch("immortalwrt_builder.builder.core.sync.git.run_command") as mock_run:
                git.clone_or_fetch_repo(source, dest)

            commands = [call.args[0] for call in mock_run.call_args_list]
            self.assertEqual(commands[0], ["git", "init"])
            self.assertEqual(
                commands[1], ["git", "remote", "add", "origin", "https://github.com/immortalwrt/immortalwrt.git"]
            )
            self.assertEqual(commands[2], ["git", "fetch", "--depth", "1", "origin", "abc123456789"])
            self.assertEqual(commands[3], ["git", "checkout", "FETCH_HEAD"])

    def test_clone_or_fetch_repo_fetches_tag(self) -> None:
        source = GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", tag="v25.12.0", depth=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "source"
            with mock.patch("immortalwrt_builder.builder.core.sync.git.run_command") as mock_run:
                git.clone_or_fetch_repo(source, dest)

            commands = [call.args[0] for call in mock_run.call_args_list]
            self.assertEqual(commands[0], ["git", "init"])
            self.assertEqual(
                commands[1], ["git", "remote", "add", "origin", "https://github.com/immortalwrt/immortalwrt.git"]
            )
            self.assertEqual(
                commands[2], ["git", "fetch", "--depth", "1", "origin", "refs/tags/v25.12.0:refs/tags/v25.12.0"]
            )
            self.assertEqual(commands[3], ["git", "checkout", "refs/tags/v25.12.0"])

    def test_clone_or_fetch_repo_updates_existing_repo(self) -> None:
        source = GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", branch="master", depth=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "source"
            (dest / ".git").mkdir(parents=True, exist_ok=True)
            with mock.patch("immortalwrt_builder.builder.core.sync.git.run_command") as mock_run:
                git.clone_or_fetch_repo(source, dest)

            commands = [call.args[0] for call in mock_run.call_args_list]
            self.assertEqual(
                commands[0], ["git", "remote", "set-url", "origin", "https://github.com/immortalwrt/immortalwrt.git"]
            )
            self.assertEqual(commands[1], ["git", "fetch", "--depth", "1", "origin", "master"])
            self.assertEqual(commands[2], ["git", "checkout", "-B", "master", "FETCH_HEAD"])

    def test_get_local_head_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            (repo_dir / ".git").mkdir()
            with mock.patch(
                "immortalwrt_builder.builder.core.sync.git.run_command",
                return_value=subprocess.CompletedProcess([], 0, stdout="abc12345\n"),
            ):
                commit = git.get_local_head_commit(repo_dir)

            self.assertEqual(commit, "abc12345")


if __name__ == "__main__":
    unittest.main()
