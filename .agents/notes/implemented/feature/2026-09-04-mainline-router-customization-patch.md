# Agent Note: Mainline Router Customization Patch and Configuration-Driven Design

Status: implemented

## Problem
The legacy patch script `patch2.py` was authored for the `hanwckf/immortalwrt-mt798x` vendor tree (OpenWrt 21.02). When migrating to upstream ImmortalWrt mainline (`openwrt-25.12` / `v25.12.1`), `patch2.py` suffered from multiple failure modes and architectural mismatches:
1. Hardcoded parameters: Router LAN IP (`192.168.10.1`), hostname (`uluaWrt`), release descriptions, and Wi-Fi SSIDs were tightly coupled to hardcoded Python strings rather than driven by target build configurations.
2. Missing vendor files: Proprietary MediaTek wireless driver files (`package/mtk/...`) and device Makefiles (`target/linux/mediatek/image/mt7981.mk`) do not exist in mainline ImmortalWrt, where MT7981 is part of `mediatek/filogic` and managed by the upstream `mac80211` / `kmod-mt7915e` driver.
3. Outdated theme replacement: Mainline ImmortalWrt already integrates `luci-theme-argon` by default. Legacy substitutions against `30_luci-theme-bootstrap` and `feeds/luci/collections/luci/Makefile` failed to match mainline syntax (`set_opt` structure and dependency on `luci-light`).
4. Non-existent feed conflicts: Mainline feeds do not include legacy `extraipk` theme packages, making unconditional removals unnecessary.

## Decision
The post-feeds patch logic is refactored into a semantic, configuration-driven patch script: `immortalwrt_builder/configs/patchs/router_customization.py`.

Key mechanisms:
1. **Target Configuration Integration (`context.patch_config`)**:
   - The patch reads user customization values directly from the target TOML file's `[patchConfig]` section, with robust defensive fallbacks:
     - `router_ip`: Configures default LAN IP in `package/base-files/files/bin/config_generate` (fallback `192.168.10.1`).
     - `hostname`: Configures system hostname in `config_generate` (fallback `uluaWrt`).
     - `description_prefix`, `author`, `include_date`: Configures `DISTRIB_DESCRIPTION` and `DISTRIB_REVISION` in `package/base-files/files/etc/openwrt_release`.
     - `wifi_ssid`, `wifi_ssid_2g`, `wifi_ssid_5g`, `wifi_encryption`, `wifi_key`: Dynamically configures mainline `package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc` based on active frequency bands (`2g` vs `5g`).
     - `enable_ttyd_ssl`, `ttyd_ssl_cert`, `ttyd_ssl_key`: Configures SSL options in `ttyd.config` idempotently.
     - `argon` table: Configures LuCI Argon styling options (`primary`, `dark_primary`, `mode`, `online_wallpaper`, `transparency`, `blur`).
     - `disable_collectd_stats`: Disables `collectd_iwinfo` and `collectd_interface` in `luci_statistics`.
     - `disable_dns_redirect`: Disables port 53 DNS hijacking/redirection (`option dns_redirect 0`) in `package/network/services/dnsmasq/files/dhcp.conf` (UCI `dhcp.@dnsmasq[0].dns_redirect`).
2. **Mainline OpenWrt Mac80211 Adaptations**:
   - Rewrites `mac80211.uc` SSID generation logic to assign band-aware SSIDs (`wifi_ssid_2g` and `wifi_ssid_5g`) while supporting optional encryption keys.
3. **Idempotence & Safety**:
   - All string and regex replacements check for existing configurations and use safe regex matches to prevent duplicated lines across repeated executions.
   - Removed obsolete patches for `extraipk`, `mt7981.mk`, and bootstrap theme replacement.
4. **Target Attachment**:
   - Configured `immortalwrt_builder/configs/targets/uluawrt-rax3000m.toml` to mount `router_customization.py` in `post_feeds_patches` with full `[patchConfig]` settings.

## Alternatives considered
1. *Modify `patch2.py` in place*:
   - Kept the numbered name `patch2.py` and added conditional branches for 21.02 vs 25.12.
   - Declined because numbered names (`patch1`, `patch2`, `patch3`) lack semantic clarity, and mixing legacy vendor SDK logic with upstream mac80211 creates dead code and maintenance confusion.
2. *Rely strictly on OpenWrt UCI-defaults scripts*:
   - Put all customizations into runtime `/etc/uci-defaults/` shell scripts installed into rootfs.
   - Declined because compile-time generation (such as `openwrt_release`, `mac80211.uc` defaults, and `config_generate`) allows first-boot defaults to apply before any user service runs and respects standard build artifact inspection.

## Consequences
- Mainline ImmortalWrt builds produce clean, personalized firmwares without patching non-existent files.
- Users can customize IP, hostname, Wi-Fi SSIDs, passwords, and themes simply by editing their target `.toml` without touching Python code.
- Target loading seamlessly supports both `uluawrt-rax3000m` and `uluawrt-rax3000m.toml` identifiers.
- Existing OpenWrt 21.02 targets (`uluawrt-mt7981-ax3000m`) remain unaffected and backward-compatible.
