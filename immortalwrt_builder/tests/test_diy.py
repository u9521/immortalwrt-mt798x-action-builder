# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.config.schema import GitSourceConfig, PatchConfig, TargetConfig
from immortalwrt_builder.builder.core.patch import builtin, diy


class DiyTests(unittest.TestCase):
    def test_run_diy_scripts_executes_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            script_file = Path(temp_dir) / "test_diy.sh"
            script_file.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")

            with mock.patch("immortalwrt_builder.builder.core.patch.diy.run_command") as mock_run:
                diy.run_diy_scripts([script_file], source_dir)

            mock_run.assert_called_once_with(["bash", str(script_file.resolve())], cwd=source_dir)

    def test_builtin_patch_modifies_ip_and_hostname(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            cfg_gen = source_dir / "package" / "base-files" / "files" / "bin" / "config_generate"
            cfg_gen.parent.mkdir(parents=True, exist_ok=True)
            cfg_gen.write_text(
                "ipad='192.168.1.1'\nhostname='ImmortalWrt'\n",
                encoding="utf-8",
            )

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                patch=PatchConfig(
                    ip_address="192.168.10.1",
                    hostname="MyRouter",
                ),
            )

            builtin.apply_builtin_patches(target, source_dir)

            updated = cfg_gen.read_text(encoding="utf-8")
            self.assertIn("192.168.10.1", updated)
            self.assertIn("hostname='MyRouter'", updated)


if __name__ == "__main__":
    unittest.main()
