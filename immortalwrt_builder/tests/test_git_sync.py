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
    def test_clone_or_fetch_repo_clones_when_not_exists(self) -> None:
        source = GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", branch="master", depth=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "source"
            with mock.patch("immortalwrt_builder.builder.core.sync.git.run_command") as mock_run:
                git.clone_or_fetch_repo(source, dest)

            mock_run.assert_called_once()
            args = mock_run.call_args.args[0]
            self.assertEqual(args[0], "git")
            self.assertEqual(args[1], "clone")
            self.assertIn("--depth", args)
            self.assertIn("-b", args)
            self.assertIn("master", args)

    def test_clone_or_fetch_repo_fetches_when_exists(self) -> None:
        source = GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", branch="master")
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "source"
            (dest / ".git").mkdir(parents=True, exist_ok=True)
            with mock.patch("immortalwrt_builder.builder.core.sync.git.run_command") as mock_run:
                git.clone_or_fetch_repo(source, dest)

            self.assertEqual(mock_run.call_count, 2)
            first_cmd = mock_run.call_args_list[0].args[0]
            self.assertEqual(first_cmd, ["git", "fetch", "origin", "master"])

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
