# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.cli.commands import tools


class ToolsTests(unittest.TestCase):
    def test_add_git_safe_adds_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            completed = subprocess.CompletedProcess([], 0, stdout="")
            with mock.patch(
                "immortalwrt_builder.builder.cli.commands.tools.run_command", return_value=completed
            ) as mock_run:
                args = mock.MagicMock(path=str(path), recursive=False)
                ret = tools.handle_add_git_safe(args)

            self.assertEqual(ret, 0)
            self.assertGreaterEqual(mock_run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
