# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from ..config.schema import TargetConfig


def apply_builtin_patches(target: TargetConfig, source_dir: Path) -> None:
    source_dir = source_dir.resolve()
    patch = target.patch

    if patch.ip_address:
        _set_ip_address(source_dir, patch.ip_address)

    if patch.hostname:
        _set_hostname(source_dir, patch.hostname)

    if patch.wifi_ssid_2g or patch.wifi_ssid_5g:
        _set_wifi_ssids(source_dir, patch.wifi_ssid_2g, patch.wifi_ssid_5g)

    if patch.default_theme:
        _set_default_theme(source_dir, patch.default_theme)

    if patch.distrib_description or patch.distrib_revision:
        _set_release_info(source_dir, patch.distrib_description, patch.distrib_revision)


def _set_ip_address(source_dir: Path, new_ip: str) -> None:
    config_generate = source_dir / "package" / "base-files" / "files" / "bin" / "config_generate"
    if config_generate.exists():
        content = config_generate.read_text(encoding="utf-8")
        updated = re.sub(r"192\.168\.1\.1", new_ip, content)
        if updated != content:
            config_generate.write_text(updated, encoding="utf-8")
            print(f"Applied builtin patch: default IP -> {new_ip}", flush=True)


def _set_hostname(source_dir: Path, new_hostname: str) -> None:
    config_generate = source_dir / "package" / "base-files" / "files" / "bin" / "config_generate"
    if config_generate.exists():
        content = config_generate.read_text(encoding="utf-8")
        updated = re.sub(r"hostname='.*?'", f"hostname='{new_hostname}'", content)
        if updated != content:
            config_generate.write_text(updated, encoding="utf-8")
            print(f"Applied builtin patch: hostname -> {new_hostname}", flush=True)


def _set_wifi_ssids(source_dir: Path, ssid_2g: str | None, ssid_5g: str | None) -> None:
    targets = [
        source_dir / "package" / "mtk" / "applications" / "mtwifi-cfg" / "files" / "mtwifi.sh",
        source_dir / "package" / "mtk" / "drivers" / "wifi-profile" / "files" / "mt7981" / "mt7981.dbdc.b0.dat",
        source_dir / "package" / "mtk" / "drivers" / "wifi-profile" / "files" / "mt7981" / "mt7981.dbdc.b1.dat",
    ]
    for file_path in targets:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            updated = content
            if ssid_2g:
                updated = re.sub(r"ImmortalWrt-2\.4G|MT7981_AX3000_2\.4G", ssid_2g, updated)
            if ssid_5g:
                updated = re.sub(r"ImmortalWrt-5G|MT7981_AX3000_5G", ssid_5g, updated)
            if updated != content:
                file_path.write_text(updated, encoding="utf-8")
                print(f"Applied builtin patch: Wi-Fi SSIDs in {file_path.name}", flush=True)


def _set_default_theme(source_dir: Path, theme_name: str) -> None:
    makefiles = [
        source_dir / "feeds" / "luci" / "collections" / "luci" / "Makefile",
        source_dir / "feeds" / "luci" / "collections" / "luci-nginx" / "Makefile",
    ]
    for mk in makefiles:
        if mk.exists():
            content = mk.read_text(encoding="utf-8")
            updated = re.sub(r"luci-theme-bootstrap", theme_name, content)
            if updated != content:
                mk.write_text(updated, encoding="utf-8")
                print(f"Applied builtin patch: default LuCI theme -> {theme_name} in {mk.name}", flush=True)


def _set_release_info(source_dir: Path, description: str | None, revision: str | None) -> None:
    release_file = source_dir / "package" / "base-files" / "files" / "etc" / "openwrt_release"
    if release_file.exists():
        content = release_file.read_text(encoding="utf-8")
        updated = content
        now_str = datetime.now().strftime("%Y%m%d")
        if description:
            desc_val = description.replace("{date}", now_str)
            updated = re.sub(r"DISTRIB_DESCRIPTION='.*?'", f"DISTRIB_DESCRIPTION='{desc_val}'", updated)
        if revision:
            rev_val = revision.replace("{date}", now_str)
            updated = re.sub(r"DISTRIB_REVISION='.*?'", f"DISTRIB_REVISION='{rev_val}'", updated)
        if updated != content:
            release_file.write_text(updated, encoding="utf-8")
            print("Applied builtin patch: release info in openwrt_release", flush=True)
