# `iwb` Command Line Interface Reference

The `iwb` CLI is the main orchestration command for `immortalwrt-action-builder`.

## Global Options & Targets

Every command accepts:
- `--target <name>`: Target config name. If omitted, checks `IWB_TARGET` or auto-selects if only one target exists.
- `--work-root <path>`: Custom workspace root directory for source code, build cache, and output artifacts (overrides `global.toml` and `IWB_WORK_ROOT`).

## Subcommands

### 1. `show-target`
Inspect the resolved target configuration including inherited fields.

```bash
uv run iwb show-target --target official-mt7981-ax3000m
uv run iwb show-target --target official-mt7981-ax3000m --json
```

### 2. `sync-source`
Clone or fetch the target's Git source repository into `source-code/<target>`.

```bash
uv run iwb sync-source --target official-mt7981-ax3000m
```

### 3. `feeds-update`
Execute pre-feeds Python patches (e.g. adding custom feed lines to `feeds.conf.default`), then run `./scripts/feeds update -a`.

```bash
uv run iwb feeds-update --target official-mt7981-ax3000m
uv run iwb feeds-update --target official-mt7981-ax3000m --skip-patches
```

### 4. `feeds-install`
Run `./scripts/feeds install -a`, then execute post-feeds Python patches.

```bash
uv run iwb feeds-install --target official-mt7981-ax3000m
uv run iwb feeds-install --target official-mt7981-ax3000m --skip-patches
```

### 5. `configure`
Apply the target's defconfig file, run `make defconfig`, and execute post-config Python patches.

```bash
uv run iwb configure --target official-mt7981-ax3000m
uv run iwb configure --target official-mt7981-ax3000m --skip-patches
```

### 6. `download`
Pre-download all package source archives using `make download -j<jobs>`.

```bash
uv run iwb download --target official-mt7981-ax3000m -j$(nproc) -v
```

### 7. `build`
Compile the firmware using `make -j<jobs> [V=s]`, collect output binaries, and compute checksums.

```bash
uv run iwb build --target official-mt7981-ax3000m -j$(nproc)
```

### 8. `digest`
Scan `bin/targets/` (or `out/<target>`), compute MD5 and SHA256 checksums, and generate `filedigest.md`.

```bash
uv run iwb digest --target official-mt7981-ax3000m
```

### 9. `tools`
Maintenance and analysis helpers:

```bash
# Check if upstream source or local repository has changes compared to last build
uv run iwb tools check-update --target official-mt7981-ax3000m

# Print workspace disk usage report
uv run iwb tools usage --target official-mt7981-ax3000m

# View ccache statistics
uv run iwb tools ccache-stats --target official-mt7981-ax3000m

# Print ccache directory path (used for CI caching)
uv run iwb tools ccache-dir --target official-mt7981-ax3000m

# Clear ccache
uv run iwb tools ccache-clean --target official-mt7981-ax3000m

# Clean OpenWrt build tree
uv run iwb tools clean --target official-mt7981-ax3000m
uv run iwb tools clean --target official-mt7981-ax3000m --dirclean
uv run iwb tools clean --target official-mt7981-ax3000m --all
```

### 10. `toolchain-*` Cache Management
Subsystem for archiving, restoring, and managing compiled host tools and cross-compiler toolchains:

```bash
# Print calculated toolchain cache fingerprint key
uv run iwb toolchain-key --target official-mt7981-ax3000m

# Archive and save toolchain
uv run iwb toolchain-save --target official-mt7981-ax3000m

# Restore toolchain and touch timestamps
uv run iwb toolchain-restore --target official-mt7981-ax3000m

# Touch stamp files to prevent OpenWrt Makefile rebuilds
uv run iwb toolchain-touch --target official-mt7981-ax3000m

# Remove saved toolchain archive
uv run iwb toolchain-clean --target official-mt7981-ax3000m
```
