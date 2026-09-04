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

            target = TargetConfig(
                name="test",
                source=GitSourceConfig(url="https://example.com"),
                patch_config={"router_ip": "192.168.10.1"},
            )
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=work_root)

            # Test target access
            self.assertEqual(ctx.target.name, "test")
            self.assertEqual(ctx.patch_config.get("router_ip"), "192.168.10.1")

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
    context.write_text("output.txt", f"Target: {context.target.name}, IP: {context.patch_config.get('ip')}")
""",
                encoding="utf-8",
            )

            target = TargetConfig(
                name="sample-target",
                source=GitSourceConfig(url="https://example.com"),
                patch_config={"ip": "10.0.0.1"},
            )
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=work_root)

            execute_python_patch(patch_file, ctx)

            self.assertTrue(ctx.exists("output.txt"))
            self.assertEqual(ctx.read_text("output.txt"), "Target: sample-target, IP: 10.0.0.1")

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

    def test_router_customization_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            work_root = Path(temp_dir)

            # Setup mock tree
            cfg_gen = source_dir / "package/base-files/files/bin/config_generate"
            cfg_gen.parent.mkdir(parents=True)
            cfg_gen.write_text(
                'case "$1" in\n\tlan) ipad=${ipaddr:-"192.168.1.1"} ;;\nesac\nset system.@system[-1].hostname=\'ImmortalWrt\'\n'
            )

            rel_file = source_dir / "package/base-files/files/etc/openwrt_release"
            rel_file.parent.mkdir(parents=True)
            rel_file.write_text("DISTRIB_DESCRIPTION='%D %V %C'\nDISTRIB_REVISION='%R'\n")

            mac_uc = source_dir / "package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc"
            mac_uc.parent.mkdir(parents=True)
            mac_uc.write_text(
                "set ${si}.ssid='${defaults?.ssid || \"ImmortalWrt\"}'\n"
                "set ${si}.encryption='${defaults?.encryption || encryption}'\n"
                "set ${si}.key='${defaults?.key || \"\"}'\n"
            )

            ttyd_cfg = source_dir / "feeds/packages/utils/ttyd/files/ttyd.config"
            ttyd_cfg.parent.mkdir(parents=True)
            ttyd_cfg.write_text("config ttyd\n\toption interface '@lan'\n")

            argon_cfg = source_dir / "feeds/luci/applications/luci-app-argon-config/root/etc/config/argon"
            argon_cfg.parent.mkdir(parents=True)
            argon_cfg.write_text("config global\n")

            stats_cfg = source_dir / "feeds/luci/applications/luci-app-statistics/root/etc/config/luci_statistics"
            stats_cfg.parent.mkdir(parents=True)
            stats_cfg.write_text(
                "config statistics 'collectd_iwinfo'\n\toption enable '1'\n"
                "config statistics 'collectd_interface'\n\toption enable '1'\n"
            )

            dhcp_cfg = source_dir / "package/network/services/dnsmasq/files/dhcp.conf"
            dhcp_cfg.parent.mkdir(parents=True)
            dhcp_cfg.write_text("config dnsmasq\n\toption dns_redirect\t1\n")

            target = TargetConfig(name="test", source=GitSourceConfig(url="https://example.com"), patch_config={})
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=work_root)

            patch_script = Path("immortalwrt_builder/configs/patchs/router_customization.py").resolve()
            execute_python_patch(patch_script, ctx)

            # Check defaults
            gen_text = cfg_gen.read_text()
            self.assertIn("192.168.10.1", gen_text)
            self.assertIn("hostname='uluaWrt'", gen_text)

            rel_text = rel_file.read_text()
            self.assertIn("DISTRIB_DESCRIPTION='uluaWrt-", rel_text)
            self.assertIn("DISTRIB_REVISION=' By ulua'", rel_text)

            mac_text = mac_uc.read_text()
            self.assertIn("uluaWrt-2.4G", mac_text)
            self.assertIn("uluaWrt-5G", mac_text)

            ttyd_text = ttyd_cfg.read_text()
            self.assertIn("option ssl '1'", ttyd_text)
            self.assertIn("option ssl_cert '/etc/nginx/conf.d/_lan.crt'", ttyd_text)

            argon_text = argon_cfg.read_text()
            self.assertIn("option primary '#5e72e4'", argon_text)
            self.assertIn("option mode 'normal'", argon_text)

            stats_text = stats_cfg.read_text()
            self.assertIn("config statistics 'collectd_iwinfo'\n\toption enable '0'", stats_text)
            self.assertIn("config statistics 'collectd_interface'\n\toption enable '0'", stats_text)

            dhcp_text = dhcp_cfg.read_text()
            self.assertIn("option dns_redirect\t0", dhcp_text)

    def test_router_customization_with_custom_config_and_idempotence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            work_root = Path(temp_dir)

            cfg_gen = source_dir / "package/base-files/files/bin/config_generate"
            cfg_gen.parent.mkdir(parents=True)
            cfg_gen.write_text(
                "lan) ipad=${ipaddr:-\"192.168.1.1\"} ;;\nset system.@system[-1].hostname='ImmortalWrt'\n"
            )

            rel_file = source_dir / "package/base-files/files/etc/openwrt_release"
            rel_file.parent.mkdir(parents=True)
            rel_file.write_text("DISTRIB_DESCRIPTION='%D %V %C'\nDISTRIB_REVISION='%R'\n")

            mac_uc = source_dir / "package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc"
            mac_uc.parent.mkdir(parents=True)
            mac_uc.write_text(
                "set ${si}.ssid='${defaults?.ssid || \"ImmortalWrt\"}'\n"
                "set ${si}.encryption='${defaults?.encryption || encryption}'\n"
                "set ${si}.key='${defaults?.key || \"\"}'\n"
            )

            ttyd_cfg = source_dir / "feeds/packages/utils/ttyd/files/ttyd.config"
            ttyd_cfg.parent.mkdir(parents=True)
            ttyd_cfg.write_text("config ttyd\n")

            argon_cfg = source_dir / "feeds/luci/applications/luci-app-argon-config/root/etc/config/argon"
            argon_cfg.parent.mkdir(parents=True)
            argon_cfg.write_text("config global\n")

            stats_cfg = source_dir / "feeds/luci/applications/luci-app-statistics/root/etc/config/luci_statistics"
            stats_cfg.parent.mkdir(parents=True)
            stats_cfg.write_text(
                "config statistics 'collectd_iwinfo'\n\toption enable '1'\n"
                "config statistics 'collectd_interface'\n\toption enable '1'\n"
            )

            dhcp_cfg = source_dir / "package/network/services/dnsmasq/files/dhcp.conf"
            dhcp_cfg.parent.mkdir(parents=True)
            dhcp_cfg.write_text("config dnsmasq\n\toption dns_redirect\t1\n")

            custom_config = {
                "router_ip": "10.0.0.1",
                "hostname": "CustomBox",
                "description_prefix": "MyRouterOS",
                "author": "By Ops",
                "include_date": False,
                "wifi_ssid": "HomeBox",
                "wifi_ssid_2g": "HomeBox-2G",
                "wifi_ssid_5g": "HomeBox-5G",
                "wifi_encryption": "sae-mixed",
                "wifi_key": "SuperSecretKey",
                "enable_ttyd_ssl": True,
                "ttyd_ssl_cert": "/custom/cert.crt",
                "ttyd_ssl_key": "/custom/key.key",
                "disable_collectd_stats": False,
                "disable_dns_redirect": False,
                "argon": {
                    "primary": "#112233",
                    "dark_primary": "#445566",
                    "mode": "dark",
                    "online_wallpaper": "bing",
                    "transparency": "0.8",
                },
            }

            target = TargetConfig(
                name="test", source=GitSourceConfig(url="https://example.com"), patch_config=custom_config
            )
            ctx = PatchContext(target=target, source_dir=source_dir, work_root=work_root)

            patch_script = Path("immortalwrt_builder/configs/patchs/router_customization.py").resolve()
            execute_python_patch(patch_script, ctx)

            # Check custom values
            gen_text = cfg_gen.read_text()
            self.assertIn("10.0.0.1", gen_text)
            self.assertIn("hostname='CustomBox'", gen_text)

            rel_text = rel_file.read_text()
            self.assertEqual("DISTRIB_DESCRIPTION='MyRouterOS'\nDISTRIB_REVISION=' By Ops'\n", rel_text)

            mac_text = mac_uc.read_text()
            self.assertIn("HomeBox-2G", mac_text)
            self.assertIn("HomeBox-5G", mac_text)
            self.assertIn("sae-mixed", mac_text)
            self.assertIn("SuperSecretKey", mac_text)

            ttyd_text = ttyd_cfg.read_text()
            self.assertIn("/custom/cert.crt", ttyd_text)
            self.assertIn("/custom/key.key", ttyd_text)

            argon_text = argon_cfg.read_text()
            self.assertIn("option primary '#112233'", argon_text)
            self.assertIn("option dark_primary '#445566'", argon_text)
            self.assertIn("option mode 'dark'", argon_text)
            self.assertIn("option transparency '0.8'", argon_text)

            # Statistics should remain enabled
            stats_text = stats_cfg.read_text()
            self.assertIn("config statistics 'collectd_iwinfo'\n\toption enable '1'", stats_text)

            # DNS redirect should remain enabled
            dhcp_text = dhcp_cfg.read_text()
            self.assertIn("option dns_redirect\t1", dhcp_text)

            # Execute a second time to verify idempotency
            execute_python_patch(patch_script, ctx)
            self.assertEqual(ttyd_cfg.read_text().count("option ssl '1'"), 1)
            self.assertEqual(cfg_gen.read_text().count("hostname='CustomBox'"), 1)


if __name__ == "__main__":
    unittest.main()
