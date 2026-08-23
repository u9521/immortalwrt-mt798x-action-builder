# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import re
from datetime import datetime

from immortalwrt_builder.builder.core.patch.interface import PatchContext


def patch(context: PatchContext) -> None:
    """Post-feeds patch: customize router configuration, network, and theme."""
    print("Executing patch2: applying router customizations and cleaning packages...", flush=True)

    # 1. Configure default LAN IP
    context.replace_text(
        "package/base-files/files/bin/config_generate",
        "192.168.1.1",
        "192.168.10.1",
    )

    # 2. Configure Hostname
    context.replace_text(
        "package/base-files/files/bin/config_generate",
        re.compile(r"hostname='.*?'"),
        "hostname='uluaWrt'",
    )

    # 3. Configure Author and Release Info
    date_str = datetime.now().strftime("%Y%m%d")
    context.replace_text(
        "package/base-files/files/etc/openwrt_release",
        re.compile(r"DISTRIB_DESCRIPTION='.*?'"),
        f"DISTRIB_DESCRIPTION='uluaWrt-{date_str}'",
    )
    context.replace_text(
        "package/base-files/files/etc/openwrt_release",
        re.compile(r"DISTRIB_REVISION='.*?'"),
        "DISTRIB_REVISION=' By ulua'",
    )

    # 4. Remove duplicate / conflicting themes and packages in extraipk
    unwanted_paths = [
        "feeds/extraipk/theme/luci-theme-argon-18.06",
        "feeds/extraipk/theme/luci-app-argon-config-18.06",
        "feeds/extraipk/theme/luci-theme-design",
        "feeds/extraipk/theme/luci-theme-edge",
        "feeds/extraipk/theme/luci-theme-ifit",
        "feeds/extraipk/theme/luci-theme-opentopd",
        "feeds/extraipk/theme/luci-theme-neobird",
        "package/feeds/extraipk/luci-theme-argon-18.06",
        "package/feeds/extraipk/luci-app-argon-config-18.06",
        "package/feeds/extraipk/theme/luci-theme-design",
        "package/feeds/extraipk/theme/luci-theme-edge",
        "package/feeds/extraipk/theme/luci-theme-ifit",
        "package/feeds/extraipk/theme/luci-theme-opentopd",
        "package/feeds/extraipk/theme/luci-theme-neobird",
    ]
    for p in unwanted_paths:
        context.remove(p)

    # 5. Remove samba4 and usbprinter from image makefile
    mk_file = "target/linux/mediatek/image/mt7981.mk"
    context.replace_text(mk_file, "luci-app-samba4", "")
    context.replace_text(mk_file, "luci-app-usb-printer", "")
    context.replace_text(mk_file, "luci-i18n-usb-printer-zh-cn", "")

    # 6. Change default theme to Argon
    context.replace_text(
        "feeds/luci/themes/luci-theme-bootstrap/root/etc/uci-defaults/30_luci-theme-bootstrap",
        "set luci.main.mediaurlbase=/luci-static/bootstrap\n",
        "",
    )
    context.replace_text(
        "feeds/luci/collections/luci/Makefile",
        "luci-theme-bootstrap",
        "luci-theme-argon",
    )
    context.replace_text(
        "feeds/luci/collections/luci-nginx/Makefile",
        "luci-theme-bootstrap",
        "luci-theme-argon",
    )

    # 7. Customize Wi-Fi SSIDs
    wifi_files = [
        "package/mtk/drivers/wifi-profile/files/mt7981/mt7981.dbdc.b0.dat",
        "package/mtk/drivers/wifi-profile/files/mt7981/mt7981.dbdc.b1.dat",
        "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh",
    ]
    for wf in wifi_files:
        context.replace_text(wf, "MT7981_AX3000_2.4G", "uluaWrt-2.4G")
        context.replace_text(wf, "MT7981_AX3000_5G", "uluaWrt-5G")
        context.replace_text(wf, "ImmortalWrt-2.4G", "uluaWrt-2.4G")
        context.replace_text(wf, "ImmortalWrt-5G", "uluaWrt-5G")

    # 8. ttyd SSL and Argon configuration
    context.append_text(
        "package/feeds/packages/ttyd/files/ttyd.config",
        "\toption ssl '1'\n\toption ssl_cert '/etc/nginx/conf.d/_lan.crt'\n\toption ssl_key '/etc/nginx/conf.d/_lan.key'\n",
    )
    argon_conf = (
        "config global\n"
        "\toption primary '#5e72e4'\n"
        "\toption dark_primary '#483d8b'\n"
        "\toption mode 'normal'\n"
        "\toption online_wallpaper 'none'\n"
        "\toption transparency '0.5'\n"
        "\toption blur '10'\n"
        "\toption blur_dark '10'\n"
        "\toption transparency_dark '0.5'\n"
    )
    context.write_text("package/feeds/luci/luci-app-argon-config/root/etc/config/argon", argon_conf)

    # 9. Disable collectd wireless and interface statistics
    stats_file = "package/feeds/luci/luci-app-statistics/root/etc/config/luci_statistics"
    context.replace_text(
        stats_file,
        re.compile(r"config statistics 'collectd_iwinfo'\n\toption enable '1'"),
        "config statistics 'collectd_iwinfo'\n\toption enable '0'",
    )
    context.replace_text(
        stats_file,
        re.compile(r"config statistics 'collectd_interface'\n\toption enable '1'"),
        "config statistics 'collectd_interface'\n\toption enable '0'",
    )
