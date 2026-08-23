# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder import usage_report
from immortalwrt_builder.builder.core.config.schema import GitSourceConfig, TargetConfig


class UsageReportTests(unittest.TestCase):
    def test_analyze_workspace_usage_computes_sizes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            source_dir.mkdir()
            (source_dir / "file.txt").write_bytes(b"A" * 1024)

            cache_dir = temp_path / "cache"
            cache_dir.mkdir()
            (cache_dir / "cache.bin").write_bytes(b"B" * 2048)

            output_dir = temp_path / "out"
            output_dir.mkdir()
            (output_dir / "firmware.bin").write_bytes(b"C" * 4096)

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"))

            report = usage_report.analyze_workspace_usage(target, source_dir, cache_dir, output_dir)
            self.assertEqual(report["target"], "test")
            self.assertEqual(report["total_bytes"], 1024 + 2048 + 4096)

            stdout = io.StringIO()
            with mock.patch("sys.stdout", stdout):
                usage_report.print_usage_report(report)

            output_text = stdout.getvalue()
            self.assertIn("Disk Usage Report: test", output_text)
            self.assertIn("SOURCE", output_text)
            self.assertIn("CACHE", output_text)
            self.assertIn("OUTPUT", output_text)


if __name__ == "__main__":
    unittest.main()
