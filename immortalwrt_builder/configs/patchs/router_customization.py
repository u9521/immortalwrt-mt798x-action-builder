# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from immortalwrt_builder.builder.core.patch.interface import PatchContext


def patch(context: PatchContext) -> None:
    """Post-feeds patch: customize router configuration, network, Wi-Fi, and theme."""
    print("Executing router_customization: applying configuration-driven customizations...", flush=True)

    _configure_lan_ip(context)
    _configure_hostname(context)
    _configure_release_info(context)
    _configure_wireless(context)
    _configure_ttyd(context)
    _configure_argon(context)
    _configure_statistics(context)
    _configure_dns_redirect(context)


def _configure_lan_ip(context: PatchContext) -> None:
    router_ip = str(
        context.patch_config.get("router_ip") or context.patch_config.get("custom_router_ip") or "192.168.10.1"
    ).strip()
    target_file = "package/base-files/files/bin/config_generate"
    if not context.exists(target_file):
        return

    pattern = re.compile(r'lan\)\s*ipad=\$\{ipaddr:-"[0-9\.]+"\}\s*;;')
    replacement = f'lan) ipad=${{ipaddr:-"{router_ip}"}} ;;'
    if not context.replace_text(target_file, pattern, replacement):
        context.replace_text(target_file, "192.168.1.1", router_ip)

    print(f"  + Configured LAN IP: {router_ip}", flush=True)


def _configure_hostname(context: PatchContext) -> None:
    hostname = str(context.patch_config.get("hostname", "uluaWrt")).strip()
    target_file = "package/base-files/files/bin/config_generate"
    if not context.exists(target_file):
        return

    context.replace_text(target_file, re.compile(r"hostname='.*?'"), f"hostname='{hostname}'")
    print(f"  + Configured Hostname: {hostname}", flush=True)


def _configure_release_info(context: PatchContext) -> None:
    desc_prefix = str(context.patch_config.get("description_prefix", "uluaWrt")).strip()
    author = str(context.patch_config.get("author", "By ulua")).strip()
    include_date = bool(context.patch_config.get("include_date", True))
    target_file = "package/base-files/files/etc/openwrt_release"
    if not context.exists(target_file):
        return

    date_str = datetime.now().strftime("%Y%m%d")
    description = f"{desc_prefix}-{date_str}" if include_date else desc_prefix
    author_revision = f" {author}" if not author.startswith(" ") else author

    context.replace_text(
        target_file,
        re.compile(r"DISTRIB_DESCRIPTION='.*?'"),
        f"DISTRIB_DESCRIPTION='{description}'",
    )
    context.replace_text(
        target_file,
        re.compile(r"DISTRIB_REVISION='.*?'"),
        f"DISTRIB_REVISION='{author_revision}'",
    )
    print(f"  + Configured Release Info: {description} ({author_revision.strip()})", flush=True)


def _configure_wireless(context: PatchContext) -> None:
    wifi_ssid = str(context.patch_config.get("wifi_ssid", "uluaWrt")).strip()
    wifi_ssid_2g = str(context.patch_config.get("wifi_ssid_2g") or f"{wifi_ssid}-2.4G").strip()
    wifi_ssid_5g = str(context.patch_config.get("wifi_ssid_5g") or f"{wifi_ssid}-5G").strip()
    wifi_encryption = context.patch_config.get("wifi_encryption")
    wifi_key = context.patch_config.get("wifi_key")

    mac80211_uc = "package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc"
    if context.exists(mac80211_uc):
        ssid_pattern = re.compile(r"set \$\{si\}\.ssid='\$\{defaults\?\.ssid \|\| .*?\}'")
        ssid_replacement = (
            f"set ${{si}}.ssid='${{defaults?.ssid || "
            f'(band_name == "2g" ? "{wifi_ssid_2g}" : '
            f'(band_name == "5g" ? "{wifi_ssid_5g}" : "{wifi_ssid}"))}}\''
        )
        context.replace_text(mac80211_uc, ssid_pattern, ssid_replacement)

        if wifi_encryption:
            enc_pattern = re.compile(r"set \$\{si\}\.encryption='\$\{defaults\?\.encryption \|\| .*?\}'")
            enc_replacement = f"set ${{si}}.encryption='${{defaults?.encryption || \"{wifi_encryption}\"}}'"
            context.replace_text(mac80211_uc, enc_pattern, enc_replacement)

        if wifi_key:
            key_pattern = re.compile(r"set \$\{si\}\.key='\$\{defaults\?\.key \|\| .*?\}'")
            key_replacement = f"set ${{si}}.key='${{defaults?.key || \"{wifi_key}\"}}'"
            context.replace_text(mac80211_uc, key_pattern, key_replacement)

        print(f"  + Configured Wi-Fi SSIDs: 2.4G={wifi_ssid_2g}, 5G={wifi_ssid_5g}", flush=True)

    # Legacy support if mtk-wifi files exist
    wifi_files = [
        "package/mtk/drivers/wifi-profile/files/mt7981/mt7981.dbdc.b0.dat",
        "package/mtk/drivers/wifi-profile/files/mt7981/mt7981.dbdc.b1.dat",
        "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh",
    ]
    for wf in wifi_files:
        if context.exists(wf):
            context.replace_text(wf, "MT7981_AX3000_2.4G", wifi_ssid_2g)
            context.replace_text(wf, "MT7981_AX3000_5G", wifi_ssid_5g)
            context.replace_text(wf, "ImmortalWrt-2.4G", wifi_ssid_2g)
            context.replace_text(wf, "ImmortalWrt-5G", wifi_ssid_5g)


def _configure_ttyd(context: PatchContext) -> None:
    if not bool(context.patch_config.get("enable_ttyd_ssl", True)):
        return

    cert = str(context.patch_config.get("ttyd_ssl_cert", "/etc/nginx/conf.d/_lan.crt")).strip()
    key = str(context.patch_config.get("ttyd_ssl_key", "/etc/nginx/conf.d/_lan.key")).strip()

    ttyd_candidates = [
        "package/feeds/packages/ttyd/files/ttyd.config",
        "feeds/packages/utils/ttyd/files/ttyd.config",
    ]
    for ttyd_file in ttyd_candidates:
        if context.exists(ttyd_file):
            content = context.read_text(ttyd_file)
            if "option ssl " not in content:
                context.append_text(
                    ttyd_file,
                    f"\toption ssl '1'\n\toption ssl_cert '{cert}'\n\toption ssl_key '{key}'\n",
                )
                print(f"  + Configured ttyd SSL in {ttyd_file}", flush=True)
            break


def _configure_argon(context: PatchContext) -> None:
    argon_raw = context.patch_config.get("argon")
    argon_cfg: dict[str, Any] = argon_raw if isinstance(argon_raw, dict) else {}

    primary = argon_cfg.get("primary", context.patch_config.get("argon_primary", "#5e72e4"))
    dark_primary = argon_cfg.get("dark_primary", context.patch_config.get("argon_dark_primary", "#483d8b"))
    mode = argon_cfg.get("mode", context.patch_config.get("argon_mode", "normal"))
    online_wallpaper = argon_cfg.get("online_wallpaper", context.patch_config.get("argon_online_wallpaper", "none"))
    transparency = argon_cfg.get("transparency", context.patch_config.get("argon_transparency", "0.5"))
    blur = argon_cfg.get("blur", context.patch_config.get("argon_blur", "10"))
    blur_dark = argon_cfg.get("blur_dark", context.patch_config.get("argon_blur_dark", "10"))
    transparency_dark = argon_cfg.get("transparency_dark", context.patch_config.get("argon_transparency_dark", "0.5"))

    argon_conf = (
        "config global\n"
        f"\toption primary '{primary}'\n"
        f"\toption dark_primary '{dark_primary}'\n"
        f"\toption mode '{mode}'\n"
        f"\toption online_wallpaper '{online_wallpaper}'\n"
        f"\toption transparency '{transparency}'\n"
        f"\toption blur '{blur}'\n"
        f"\toption blur_dark '{blur_dark}'\n"
        f"\toption transparency_dark '{transparency_dark}'\n"
    )

    argon_candidates = [
        "feeds/luci/applications/luci-app-argon-config/root/etc/config/argon",
        "package/feeds/luci/luci-app-argon-config/root/etc/config/argon",
    ]
    for argon_file in argon_candidates:
        if context.exists(argon_file):
            context.write_text(argon_file, argon_conf)
            print(f"  + Configured Argon theme style in {argon_file}", flush=True)
            break


def _configure_statistics(context: PatchContext) -> None:
    if not bool(context.patch_config.get("disable_collectd_stats", True)):
        return

    stats_candidates = [
        "feeds/luci/applications/luci-app-statistics/root/etc/config/luci_statistics",
        "package/feeds/luci/luci-app-statistics/root/etc/config/luci_statistics",
    ]
    for stats_file in stats_candidates:
        if context.exists(stats_file):
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
            print(f"  + Disabled collectd wireless and interface statistics in {stats_file}", flush=True)
            break


def _configure_dns_redirect(context: PatchContext) -> None:
    disable_dns = bool(context.patch_config.get("disable_dns_redirect", True))
    dhcp_conf = "package/network/services/dnsmasq/files/dhcp.conf"
    if not context.exists(dhcp_conf):
        return

    val = "0" if disable_dns else "1"
    pattern = re.compile(r"option\s+dns_redirect\s+['\"]?[01]['\"]?")
    if not context.replace_text(dhcp_conf, pattern, f"option dns_redirect\t{val}"):
        if disable_dns:
            context.replace_text(dhcp_conf, "config dnsmasq", f"config dnsmasq\n\toption dns_redirect\t{val}")

    print(f"  + Configured DNS redirect (hijack: {not disable_dns}, dns_redirect={val})", flush=True)
