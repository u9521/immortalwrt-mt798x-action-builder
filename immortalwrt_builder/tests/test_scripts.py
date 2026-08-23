# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from immortalwrt_builder.builder import layout


class ScriptsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.scripts_dir = layout.scripts_root(self.project_root)
        self.install_script = self.scripts_dir / "install-deps.sh"
        self.uninstall_script = self.scripts_dir / "uninstall-deps.sh"

    def test_scripts_exist_and_are_executable(self) -> None:
        self.assertTrue(self.install_script.exists())
        self.assertTrue(self.uninstall_script.exists())
        self.assertTrue(os.access(self.install_script, os.X_OK))
        self.assertTrue(os.access(self.uninstall_script, os.X_OK))

    def test_install_script_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            record_file = Path(temp_dir) / "deps.txt"
            res = subprocess.run(
                [str(self.install_script), "--dry-run", "--record", str(record_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("[Dry-Run]", res.stdout)
            self.assertIn("Checking existing system packages", res.stdout)

    def test_uninstall_script_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            record_file = Path(temp_dir) / "deps.txt"
            record_file.write_text("# Comment\ngit\ncurl\n", encoding="utf-8")
            res = subprocess.run(
                [str(self.uninstall_script), "-f", str(record_file), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("[Dry-Run]", res.stdout)
            self.assertIn("Loaded 2 package(s)", res.stdout)


if __name__ == "__main__":
    unittest.main()
