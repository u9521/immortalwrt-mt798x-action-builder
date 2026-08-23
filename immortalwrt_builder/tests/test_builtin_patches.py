# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from immortalwrt_builder.builder.core.config.schema import GitSourceConfig, PatchConfig, TargetConfig
from immortalwrt_builder.builder.core.patch import builtin


class BuiltinPatchesTests(unittest.TestCase):
    def test_wifi_ssid_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            mtwifi_path = source_dir / "package" / "mtk" / "applications" / "mtwifi-cfg" / "files" / "mtwifi.sh"
            mtwifi_path.parent.mkdir(parents=True, exist_ok=True)
            mtwifi_path.write_text("ssid_2g='ImmortalWrt-2.4G'\nssid_5g='ImmortalWrt-5G'\n", encoding="utf-8")

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                patch=PatchConfig(
                    wifi_ssid_2g="MyWiFi-2.4G",
                    wifi_ssid_5g="MyWiFi-5G",
                ),
            )

            builtin.apply_builtin_patches(target, source_dir)
            updated = mtwifi_path.read_text(encoding="utf-8")
            self.assertIn("MyWiFi-2.4G", updated)
            self.assertIn("MyWiFi-5G", updated)

    def test_luci_theme_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            mk_path = source_dir / "feeds" / "luci" / "collections" / "luci" / "Makefile"
            mk_path.parent.mkdir(parents=True, exist_ok=True)
            mk_path.write_text("LUCI_DEPENDS:=+luci-theme-bootstrap\n", encoding="utf-8")

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                patch=PatchConfig(default_theme="luci-theme-argon"),
            )

            builtin.apply_builtin_patches(target, source_dir)
            updated = mk_path.read_text(encoding="utf-8")
            self.assertIn("+luci-theme-argon", updated)

    def test_release_info_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            release_file = source_dir / "package" / "base-files" / "files" / "etc" / "openwrt_release"
            release_file.parent.mkdir(parents=True, exist_ok=True)
            release_file.write_text("DISTRIB_DESCRIPTION='OpenWrt'\nDISTRIB_REVISION='r0000'\n", encoding="utf-8")

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                patch=PatchConfig(
                    distrib_description="MyWrt-{date}",
                    distrib_revision="By User",
                ),
            )

            builtin.apply_builtin_patches(target, source_dir)
            updated = release_file.read_text(encoding="utf-8")
            self.assertIn("DISTRIB_DESCRIPTION='MyWrt-20", updated)
            self.assertIn("DISTRIB_REVISION='By User'", updated)


if __name__ == "__main__":
    unittest.main()
