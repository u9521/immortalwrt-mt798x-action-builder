# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import unittest

from immortalwrt_builder.builder.core.config.provider import TargetConfigProvider


class CheckedInTargetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = TargetConfigProvider()

    def test_list_targets_returns_expected_targets(self) -> None:
        targets = self.provider.list_targets()
        self.assertIn("official-mt7981-ax3000m", targets)
        self.assertIn("official-x86-64", targets)
        self.assertIn("official-generic", targets)
        self.assertIn("uluawrt-mt7981-ax3000m", targets)
        # Base targets must not be in selectable targets
        self.assertNotIn("immortalwrt-base", targets)
        self.assertNotIn("mt798x-base", targets)

    def test_load_official_mt7981_target(self) -> None:
        target = self.provider.load("official-mt7981-ax3000m")
        self.assertEqual(target.name, "official-mt7981-ax3000m")
        self.assertFalse(target.base)
        self.assertEqual(target.source.url, "https://github.com/immortalwrt/immortalwrt.git")
        self.assertEqual(target.source.branch, "openwrt-23.05")
        self.assertIsNotNone(target.build.defconfig_path)
        assert target.build.defconfig_path is not None
        self.assertTrue(target.build.defconfig_path.exists())

    def test_load_official_x86_64_target(self) -> None:
        target = self.provider.load("official-x86-64")
        self.assertEqual(target.name, "official-x86-64")
        self.assertFalse(target.base)
        self.assertEqual(target.source.url, "https://github.com/immortalwrt/immortalwrt.git")
        self.assertIsNotNone(target.build.defconfig_path)
        assert target.build.defconfig_path is not None
        self.assertTrue(target.build.defconfig_path.exists())

    def test_load_uluawrt_target(self) -> None:
        target = self.provider.load("uluawrt-mt7981-ax3000m")
        self.assertEqual(target.name, "uluawrt-mt7981-ax3000m")
        self.assertEqual(target.source.url, "https://github.com/hanwckf/immortalwrt-mt798x.git")
        self.assertEqual(len(target.patch.pre_feeds_patches), 1)
        self.assertEqual(len(target.patch.post_feeds_patches), 2)
        for p in target.patch.pre_feeds_patches:
            self.assertTrue(p.exists())
            self.assertEqual(p.suffix, ".py")
        for p in target.patch.post_feeds_patches:
            self.assertTrue(p.exists())
            self.assertEqual(p.suffix, ".py")


if __name__ == "__main__":
    unittest.main()
