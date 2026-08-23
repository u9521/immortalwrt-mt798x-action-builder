# Building Official ImmortalWrt Guide

This guide explains how to build official ImmortalWrt releases and branches using `immortalwrt-action-builder`.

## Official Branches & Repositories

The official ImmortalWrt repository is:
`https://github.com/immortalwrt/immortalwrt.git`

Common official branches:
- `openwrt-23.05`: Current stable release series.
- `openwrt-24.10`: Latest major release series.
- `master`: Development branch with the latest kernel and package versions.

## Building Official Targets

### 1. MediaTek MT7981 / Filogic (AX3000M / RAX3000M / 360 T7 / etc.)

```bash
uv run iwb run --target official-mt7981-ax3000m
```

This target builds MediaTek Filogic firmware using official ImmortalWrt `openwrt-23.05` branch with `ax3000m.config`.

### 2. x86_64 Router (UEFI / GPT / SquashFS / EXT4)

```bash
uv run iwb run --target official-x86-64
```

This target builds standard 64-bit x86 router images with EFI support, LuCI web interface, and Argon theme.

### 3. Adding a Custom Target

To add a new target (e.g. `official-mt7986-ax6000`), create `immortalwrt_builder/configs/targets/official-mt7986-ax6000.toml`:

```toml
name = "official-mt7986-ax6000"
extends = "immortalwrt-base"

[source]
branch = "openwrt-23.05"

[build]
defconfig = "ax6000.config"

[output]
dist_dir = "official-mt7986-ax6000"
target_dir = "bin/targets/mediatek/filogic"
```

And place your `.config` template in `immortalwrt_builder/configs/defconfigs/ax6000.config`.
Then build it with:

```bash
uv run iwb run --target official-mt7986-ax6000
```
