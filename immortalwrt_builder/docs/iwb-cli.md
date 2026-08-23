# `iwb` Command Line Interface Reference

The `iwb` CLI is the main orchestration command for `immortalwrt-action-builder`.

## Global Options & Targets

Every command accepts:
- `--target <name>`: Target config name. If omitted, checks `IWB_TARGET`, `IMMORTALWRT_TARGET`, or auto-selects if only one target exists.
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

### 3. `setup-feeds`
Configure `feeds.conf.default`, execute pre-feeds Python patches, run `./scripts/feeds update -a` and `./scripts/feeds install -a`, and apply post-feeds Python patches.

```bash
uv run iwb setup-feeds --target official-mt7981-ax3000m
uv run iwb setup-feeds --target official-mt7981-ax3000m --skip-patches
```

### 4. `configure`
Apply the target's defconfig file, run `make defconfig`, and execute post-config Python patches.

```bash
uv run iwb configure --target official-mt7981-ax3000m
```

### 5. `download`
Pre-download all package source archives using `make download -j<jobs>`.

```bash
uv run iwb download --target official-mt7981-ax3000m -j$(nproc) -v
```

### 6. `build`
Compile the firmware using `make -j<jobs> [V=s]`, collect output binaries, and compute checksums.

```bash
uv run iwb build --target official-mt7981-ax3000m -j$(nproc)
```

### 7. `digest`
Scan `bin/targets/` (or `out/<target>`), compute MD5 and SHA256 checksums, generate `filedigest.md`, and append to `$GITHUB_STEP_SUMMARY`.

```bash
uv run iwb digest --target official-mt7981-ax3000m
```

### 8. `run`
Execute the entire pipeline end-to-end:
1. `sync-source`
2. `setup-feeds` (pre-feeds patches + feeds install + post-feeds patches)
3. `configure` (defconfig + make defconfig + post-config patches)
4. `download` (make download)
5. `build` (make -jN)
6. `digest` (checksums table & summary)
7. `usage` (disk space report)

```bash
uv run iwb run --target official-mt7981-ax3000m
```

### 9. `check-update`
Compare local repository commit and remote upstream commit against cached build information to determine whether a rebuild is required. Returns exit code 0 if build needed, 1 if up-to-date.

```bash
uv run iwb check-update --target official-mt7981-ax3000m
```

### 10. `tools`
Maintenance helpers:

```bash
# Add directory to git safe.directory
uv run iwb tools add-git-safe /path/to/workspace -r

# View ccache statistics
uv run iwb tools ccache-stats --target official-mt7981-ax3000m

# Clear ccache
uv run iwb tools ccache-clean --target official-mt7981-ax3000m

# Clean OpenWrt build tree
uv run iwb tools clean --target official-mt7981-ax3000m
uv run iwb tools clean --target official-mt7981-ax3000m --dirclean
uv run iwb tools clean --target official-mt7981-ax3000m --all
```

### 11. `usage`
Print workspace disk usage for `source-code/`, `cache/`, and `out/`.

```bash
uv run iwb usage
```
