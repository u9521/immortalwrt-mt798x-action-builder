# ImmortalWrt Action Builder

A modular, production-grade Python orchestration CLI (`iwb`) and GitHub Actions build framework for building **official ImmortalWrt** and customized OpenWrt/ImmortalWrt router firmwares.

Re-architected and patterned after [Android-Kernel-Builder](https://github.com/u9521/Android-Kernel-Builder) with a pure Python 3.14+ standard library implementation, declarative TOML target configuration system, dynamic Python patch plugin system, fragment configurations, and GitHub Actions CI automation.

---

## Key Features

- **Official ImmortalWrt Native Support**: Build directly from official [`immortalwrt/immortalwrt`](https://github.com/immortalwrt/immortalwrt) (`master`, `openwrt-24.10`, `openwrt-23.05`) as well as vendor trees (e.g. `hanwckf/immortalwrt-mt798x`).
- **Declarative TOML Targets with Inheritance**: Define router targets concisely with `extends` inheritance, default templates (`base = true`), deep table merging, and strict schema validation.
- **Defconfig Management**: Supports minimal defconfig files generated with OpenWrt's native `./scripts/diffconfig.sh` or full configurations.
- **Pure Python Patch Plugins (`importlib`)**:
  - Customizations are implemented as Python patch scripts in `immortalwrt_builder/configs/patchs/`.
  - Rich `PatchContext` provides full access to target configuration (`context.target`), source tree path helpers, file reading/writing/appending, string and regex replacements, directory removals, and command execution.
  - Multi-stage hooks: `pre_feeds_patches`, `post_feeds_patches`, `post_config_patches`.
- **Transparent ccache Acceleration**: Automatically prepends symlink compiler wrappers (`gcc`, `g++`, `clang`, etc.) to `PATH` without modifying `.config`.
- **Host & CI First**: Runs cleanly in local Linux / WSL host environments and GitHub Actions runners without container lock-in.
- **Zero Runtime Dependencies**: Written entirely in pure Python 3.14+ standard library (`tomllib`, `pathlib`, `dataclasses`, `argparse`, `hashlib`, `json`, `subprocess`, `shutil`, `importlib`).
- **Automated Digest & Release**: Computes MD5 and SHA256 checksums for all generated firmwares and generates markdown tables for GitHub Step Summaries and GitHub Releases.

---

## Repository Layout

```text
immortalwrt-action-builder/
├── pyproject.toml                         # uv build configuration and CLI entry points
├── AGENTS.md                              # Coding agent guidelines
├── immortalwrt_builder/
│   ├── builder/
│   │   ├── layout.py                      # Workspace paths resolution
│   │   ├── utils.py                       # Subprocess execution & checksum utilities
│   │   ├── usage_report.py                # Disk space analysis & reporting
│   │   ├── cli/
│   │   │   ├── app.py                     # CLI entry point (iwb)
│   │   │   ├── registry.py                # Command decorator registry
│   │   │   └── commands/                  # Subcommands (sync, feeds, config, build, run, etc.)
│   │   └── core/
│   │       ├── config/                    # TOML loader, inheritance, schema, validator
│   │       ├── sync/                      # Git clone, shallow sync, commit comparison
│   │       ├── feeds/                     # Feeds configuration & installation
│   │       ├── patch/                     # Python patch interface (PatchContext) & importlib executor
│   │       └── build/                     # OpenWrt make engine & output digest collector
│   ├── configs/
│   │   ├── global.toml                    # Global build settings
│   │   ├── targets/                       # Checked-in target definitions (*.toml)
│   │   │   ├── immortalwrt-base.toml      # Official ImmortalWrt base template
│   │   │   ├── official-mt7981-ax3000m.toml # MediaTek Filogic MT7981 (AX3000M / RAX3000M)
│   │   │   ├── official-x86-64.toml       # x86_64 UEFI/GPT router target
│   │   │   ├── official-generic.toml      # Generic official target
│   │   │   └── uluawrt-mt7981-ax3000m.toml # Custom MT7981 with Python patches
│   │   ├── defconfigs/                    # OpenWrt .config & fragment templates (*.config)
│   │   └── patchs/                        # Python patch plugins (*.py)
│   ├── scripts/
│   │   ├── install-deps.sh                # Host/CI system build dependencies installer
│   │   └── write-ci-build-summary.py      # GitHub Step Summary markdown writer
│   ├── docs/                              # Reference documentation
│   └── tests/                             # Full unittest test suite
└── .github/
    └── workflows/
        └── build.yml                      # Parameterized firmware build workflow
```

---

## Setup & Quick Start

Requires **Python 3.14+** and [uv](https://docs.astral.sh/uv/).

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install editable package with dev dependencies
uv sync --dev

# 3. View CLI help
uv run iwb --help

# 4. Show available targets
uv run iwb show-target --target official-mt7981-ax3000m
```

### Install / Uninstall Host Build Dependencies

On Ubuntu 22.04 or 24.04:

```bash
# Install dependencies and record newly installed packages to installed-deps.txt
sudo ./immortalwrt_builder/scripts/install-deps.sh --record installed-deps.txt

# Later, uninstall only the dependencies recorded in that file
sudo ./immortalwrt_builder/scripts/uninstall-deps.sh --file installed-deps.txt
```

---

## Common CLI Commands

| Command | Description | Example |
|:---|:---|:---|
| `iwb show-target` | Display resolved target configuration | `uv run iwb show-target --target official-mt7981-ax3000m` |
| `iwb sync-source` | Clone or update target source code | `uv run iwb sync-source --target official-mt7981-ax3000m` |
| `iwb feeds-update` | Update feeds & apply pre-feeds patches | `uv run iwb feeds-update --target official-mt7981-ax3000m` |
| `iwb feeds-install` | Install feeds & apply post-feeds patches | `uv run iwb feeds-install --target official-mt7981-ax3000m` |
| `iwb configure` | Apply defconfig & post-config patches | `uv run iwb configure --target official-mt7981-ax3000m` |
| `iwb download` | Pre-download packages (`make download`) | `uv run iwb download --target official-mt7981-ax3000m -j$(nproc)` |
| `iwb build` | Build firmware (`make -jN`) | `uv run iwb build --target official-mt7981-ax3000m -j$(nproc) -v` |
| `iwb digest` | Compute MD5/SHA256 checksums table | `uv run iwb digest --target official-mt7981-ax3000m` |
| `iwb tools check-update` | Check if repo has upstream/local changes | `uv run iwb tools check-update --target official-mt7981-ax3000m` |
| `iwb tools ccache-stats` | Show ccache hit rate and stats | `uv run iwb tools ccache-stats --target official-mt7981-ax3000m` |
| `iwb tools clean` | Clean build tree (`make clean/dirclean`) | `uv run iwb tools clean --target official-mt7981-ax3000m` |
| `iwb tools usage` | Display workspace disk space usage | `uv run iwb tools usage --target official-mt7981-ax3000m` |

---

## Target Configuration Example

Target definitions live under `immortalwrt_builder/configs/targets/<name>.toml`:

```toml
name = "official-mt7981-ax3000m"
extends = "immortalwrt-base"

[source]
branch = "openwrt-25.12"

[patch]
post_feeds_patches = ["custom_tweaks.py"]

[build]
defconfig = "ax3000m.config"

[ccache]
enabled = true
max_size = "3.5G"

[output]
dist_dir = "official-mt7981-ax3000m"
target_dir = "bin/targets/mediatek/filogic"
```

---

## Running Unit Tests

```bash
uv run python -m unittest discover -s immortalwrt_builder/tests
```

---

## GitHub Actions CI Workflow

The workflow at `.github/workflows/build.yml` provides a parameterized build runner:
- **`target`**: Select target name (e.g. `official-mt7981-ax3000m`, `official-x86-64`, `uluawrt-mt7981-ax3000m`).
- **`verboseBuildlog`**: Enable `V=s` compiler output for debugging.
- **`skipUpdateCheck`**: Force build even if upstream repository has not changed.
- **`releaseAfterBuild`**: Automatically publish GitHub Release with binary firmwares and MD5/SHA256 checksums table.

---

## License

Licensed under the **GNU General Public License v3.0 (GPL-3.0-only)**. See [LICENSE](LICENSE).
