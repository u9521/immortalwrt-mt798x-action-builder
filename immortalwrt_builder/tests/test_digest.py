# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from immortalwrt_builder.builder.core.build import output
from immortalwrt_builder.builder.core.config.schema import GitSourceConfig, OutputConfig, TargetConfig


class DigestTests(unittest.TestCase):
    def test_collect_outputs_finds_firmware_and_computes_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            target_bin_dir = source_dir / "bin" / "targets" / "mediatek" / "mt7981"
            target_bin_dir.mkdir(parents=True, exist_ok=True)
            output_root = temp_path / "out"

            firmware_file = target_bin_dir / "immortalwrt-mediatek-mt7981-squashfs-sysupgrade.bin"
            firmware_file.write_bytes(b"FIRMWARE_BINARY_DATA_SAMPLE")

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                output=OutputConfig(dist_dir="dist_test"),
            )

            artifacts = output.collect_outputs(target, source_dir, output_root)
            self.assertEqual(len(artifacts), 1)
            art = artifacts[0]
            self.assertEqual(art["filename"], "immortalwrt-mediatek-mt7981-squashfs-sysupgrade.bin")
            self.assertIsNotNone(art["md5"])
            self.assertIsNotNone(art["sha256"])

            table = output.generate_digest_table(artifacts)
            self.assertIn("File name", table)
            self.assertIn("immortalwrt-mediatek-mt7981-squashfs-sysupgrade.bin", table)
            self.assertIn(str(art["md5"]), table)


if __name__ == "__main__":
    unittest.main()
