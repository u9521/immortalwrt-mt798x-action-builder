# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from immortalwrt_builder.builder.core.config.schema import GitSourceConfig, TargetConfig
from immortalwrt_builder.builder.core.patch.executor import execute_python_patch
from immortalwrt_builder.builder.core.patch.interface import PatchContext


class PatchTests(unittest.TestCase):
    def test_patch_context_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            work_root = Path(temp_dir)

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=work_root)

            # Test target access
            self.assertEqual(ctx.target.name, "test")

            # Test write_text, read_text, exists
            ctx.write_text("package/test.txt", "hello world\n")
            self.assertTrue(ctx.exists("package/test.txt"))
            self.assertEqual(ctx.read_text("package/test.txt"), "hello world\n")

            # Test append_text
            ctx.append_text("package/test.txt", "line 2\n")
            self.assertEqual(ctx.read_text("package/test.txt"), "hello world\nline 2\n")

            # Test replace_text with string
            modified = ctx.replace_text("package/test.txt", "world", "openwrt")
            self.assertTrue(modified)
            self.assertEqual(ctx.read_text("package/test.txt"), "hello openwrt\nline 2\n")

            # Test replace_text with regex
            modified_re = ctx.replace_text("package/test.txt", re.compile(r"line \d+"), "line 99")
            self.assertTrue(modified_re)
            self.assertEqual(ctx.read_text("package/test.txt"), "hello openwrt\nline 99\n")

            # Test copy
            ctx.copy(source_dir / "package/test.txt", "package/copy.txt")
            self.assertTrue(ctx.exists("package/copy.txt"))

            # Test remove
            ctx.remove("package/copy.txt")
            self.assertFalse(ctx.exists("package/copy.txt"))

    def test_execute_python_patch_with_importlib(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            work_root = Path(temp_dir)

            # Create a dynamic python patch file
            patch_file = Path(temp_dir) / "my_patch.py"
            patch_file.write_text(
                """
from immortalwrt_builder.builder.core.patch.interface import PatchContext

def patch(context: PatchContext) -> None:
    context.write_text("output.txt", f"Target: {context.target.name}")
""",
                encoding="utf-8",
            )

            target = TargetConfig(name="sample-target", source=GitSourceConfig(url="https://example.com"))
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=work_root)

            execute_python_patch(patch_file, ctx)

            self.assertTrue(ctx.exists("output.txt"))
            self.assertEqual(ctx.read_text("output.txt"), "Target: sample-target")

    def test_execute_python_patch_rejects_non_python_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            sh_file = Path(temp_dir) / "legacy.sh"
            sh_file.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "Only Python \\(\\.py\\) patch scripts are supported"):
                execute_python_patch(sh_file, ctx)

    def test_execute_python_patch_rejects_missing_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            bad_file = Path(temp_dir) / "no_func.py"
            bad_file.write_text("# No patch or run function\nx = 1\n", encoding="utf-8")

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=Path(temp_dir))

            with self.assertRaisesRegex(AttributeError, "must define a 'patch.*' or 'run.*' entry point"):
                execute_python_patch(bad_file, ctx)


if __name__ == "__main__":
    unittest.main()
