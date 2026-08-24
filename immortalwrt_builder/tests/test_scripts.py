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
        self.summary_script = self.scripts_dir / "write-ci-build-summary.py"

    def test_scripts_exist_and_are_executable(self) -> None:
        self.assertTrue(self.install_script.exists())
        self.assertTrue(self.uninstall_script.exists())
        self.assertTrue(self.summary_script.exists())
        self.assertTrue(os.access(self.install_script, os.X_OK))
        self.assertTrue(os.access(self.uninstall_script, os.X_OK))
        self.assertTrue(os.access(self.summary_script, os.X_OK))

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

    def test_write_ci_build_summary_full(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            infos_dir = root / "infos" / "official-mt7981-ax3000m"
            infos_dir.mkdir(parents=True, exist_ok=True)
            (infos_dir / "workspace.json").write_text(
                json.dumps(
                    {
                        "target": "official-mt7981-ax3000m",
                        "repo_url": "https://github.com/immortalwrt/immortalwrt.git",
                        "repo_tag": "v25.12.1",
                        "last_upstream_commit": "7a8b9c0d1e2f34567890abcdef1234567890abcd",
                        "last_local_commit": "1a2b3c4d5e6f7890abcdef1234567890abcdef12",
                    }
                ),
                encoding="utf-8",
            )
            (infos_dir / "disk-usage.json").write_text(
                json.dumps(
                    {
                        "total_formatted": "5.2 GB",
                        "sections": {
                            "source": {"size_formatted": "4.1 GB"},
                            "cache": {"size_formatted": "1.0 GB"},
                            "output": {"size_formatted": "68.5 MB"},
                        },
                    }
                ),
                encoding="utf-8",
            )
            (infos_dir / "ccache-stats.txt").write_text("cache hit (direct): 85%\ncache size: 1.2 GB", encoding="utf-8")
            (root / "filedigest.md").write_text(
                "| File name | Size | MD5 | SHA256 |\n|:---|:---|:---|:---|\n| `firmware.bin` | 32.5 MB | `md5` | `sha256` |\n",
                encoding="utf-8",
            )

            summary_file = root / "step_summary.md"
            cmd = [
                "python3",
                str(self.summary_script),
                "--target",
                "official-mt7981-ax3000m",
                "--outcome",
                "success",
                "--duration-seconds",
                "754",
                "--summary-file",
                str(summary_file),
                "--toolchain-key",
                "toolchain-mediatek_filogic-a1b2c3d4e5f6",
                "--release-tag",
                "official-mt7981-ax3000m-20260401080000",
                "--release-name",
                "ImmortalWrt-official-mt7981-ax3000m-20260401",
            ]
            env = os.environ.copy()
            env.update(
                {
                    "GITHUB_SERVER_URL": "https://github.com",
                    "GITHUB_REPOSITORY": "u9521/immortalwrt-action-builder",
                    "GITHUB_RUN_ID": "123456789",
                    "GITHUB_RUN_NUMBER": "42",
                    "GITHUB_EVENT_NAME": "workflow_dispatch",
                    "GITHUB_ACTOR": "u9521",
                    "GITHUB_SHA": "1a2b3c4d5e6f7890abcdef1234567890abcdef12",
                }
            )
            res = subprocess.run(cmd, env=env, cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(summary_file.exists())

            content = summary_file.read_text(encoding="utf-8")
            self.assertIn("## ✅ ImmortalWrt Build Summary: `official-mt7981-ax3000m`", content)
            self.assertIn("12m 34s", content)
            self.assertIn("[#42](https://github.com/u9521/immortalwrt-action-builder/actions/runs/123456789)", content)
            self.assertIn("[immortalwrt/immortalwrt](https://github.com/immortalwrt/immortalwrt)", content)
            self.assertIn("[`v25.12.1`](https://github.com/immortalwrt/immortalwrt/releases/tag/v25.12.1)", content)
            self.assertIn(
                "[`7a8b9c0`](https://github.com/immortalwrt/immortalwrt/commit/7a8b9c0d1e2f34567890abcdef1234567890abcd)",
                content,
            )
            self.assertIn("`firmware.bin`", content)
            self.assertIn("toolchain-mediatek_filogic-a1b2c3d4e5f6", content)
            self.assertIn("cache hit (direct): 85%", content)
            self.assertIn("Workspace Disk Usage", content)

    def test_write_ci_build_summary_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            summary_file = root / "step_summary.md"
            cmd = [
                "python3",
                str(self.summary_script),
                "--target",
                "official-mt7981-ax3000m",
                "--outcome",
                "failure",
                "--duration-seconds",
                "45",
                "--summary-file",
                str(summary_file),
            ]
            res = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(summary_file.exists())

            content = summary_file.read_text(encoding="utf-8")
            self.assertIn("## ❌ ImmortalWrt Build Summary: `official-mt7981-ax3000m`", content)
            self.assertIn("FAILURE", content)
            self.assertIn("00m 45s", content)

    def test_write_ci_build_summary_no_summary_path(self) -> None:
        env = os.environ.copy()
        env.pop("GITHUB_STEP_SUMMARY", None)
        cmd = [
            "python3",
            str(self.summary_script),
            "--target",
            "official-mt7981-ax3000m",
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(res.returncode, 0)
        self.assertIn("No summary file specified or found", res.stdout)


if __name__ == "__main__":
    unittest.main()
