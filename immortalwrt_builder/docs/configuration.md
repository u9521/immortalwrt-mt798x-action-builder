# Configuration Guide

## 1. Target Configurations

Target configurations are declared in TOML files under `immortalwrt_builder/configs/targets/<name>.toml`.

### Structure

```toml
name = "official-mt7981-ax3000m"   # Unique target name (required)
base = false                       # True if this is a template (cannot be directly built)
extends = "immortalwrt-base"       # Name of parent target config to inherit from

[source]
url = "https://github.com/immortalwrt/immortalwrt.git"  # Git repo URL
branch = "openwrt-25.12"                                # Branch name
tag = "v25.12.0"                                        # Optional Git tag
commit = "abc12345..."                                  # Optional Git commit SHA
depth = 1                                               # Shallow clone depth (default 1)
submodules = false                                      # Sync git submodules (default false)

[feeds]
update = true                                           # Run ./scripts/feeds update -a
install = true                                          # Run ./scripts/feeds install -a
custom_feeds = [                                        # Extra feed lines appended to feeds.conf.default
    "src-git extra https://github.com/example/extra_packages"
]
conf_file = "path/to/custom/feeds.conf.default"         # Optional custom feeds.conf.default

[patch]
pre_feeds_patches = ["patch1.py"]                       # Python patches executed before feeds update
post_feeds_patches = ["patch2.py", "patch3.py"]         # Python patches executed after feeds install
post_config_patches = ["post_config.py"]                # Python patches executed after make defconfig

[build]
defconfig = "ax3000m.config"                            # Path to defconfig file (e.g. from ./scripts/diffconfig.sh)
jobs = 16                                               # Parallel jobs (default: CPU threads count)
verbose = false                                         # Verbose compilation (V=s)
download = true                                         # Run make download (default: true)
ignore_errors = false                                   # Ignore compilation errors (default: false)

[ccache]
enabled = true                                          # Enable compiler cache (default: true)
dir = "/path/to/custom/ccache"                          # Custom CCACHE_DIR (default: cache/<target>/ccache)
max_size = "10G"                                        # CCACHE_MAXSIZE storage cap (default: 10G)
stats_log = false                                       # Export detailed per-file log to infos/ (default: false)

[output]
dist_dir = "official-mt7981-ax3000m"                    # Output subfolder in out/
target_dir = "bin/targets/mediatek/filogic"             # Target firmware directory in OpenWrt tree
packages_dir = "bin/packages"                           # Packages directory
calculate_digest = true                                 # Compute MD5/SHA256 checksums
firmware_patterns = [                                   # Glob patterns for firmware artifacts
    "*immortalwrt*.*",
    "*sysupgrade*.bin",
    "*factory*.bin",
    "*.itb",
    "*.ubi",
    "*.img.gz"
]
```

---

## 2. Global Configuration (`global.toml`)

Global settings are stored in `immortalwrt_builder/configs/global.toml`.

```toml
[general]
default_depth = 1
default_download = true

[workspace]
# Custom workspace root directory for source-code, cache, and outputs.
# Highly recommended for WSL environments to avoid slow Windows 9P filesystem (/mnt/c/...)
# by pointing work_root to native Linux ext4 path (e.g. /home/username/immortalwrt-build).
# work_root = "/home/username/immortalwrt-build"
```

### Workspace Resolution Order
1. CLI option `--work-root <path>`
2. Environment variable `IWB_WORK_ROOT` / `IMMORTALWRT_WORK_ROOT`
3. `global.toml` (`[workspace].work_root` or `[general].work_root`)
4. Current project directory (`Path.cwd()`)

---

## 3. Python Patch Script Specification

Every patch script is a Python 3.14+ script located in `immortalwrt_builder/configs/patchs/`. It receives a `PatchContext` object providing rich helper methods and access to the target configuration:

```python
# SPDX-License-Identifier: GPL-3.0-only
from immortalwrt_builder.builder.core.patch.interface import PatchContext


def patch(context: PatchContext) -> None:
    # 1. Access target config
    print(f"Applying patch for target: {context.target.name}")

    # 2. Modify files in source tree
    context.replace_text("package/base-files/files/bin/config_generate", "192.168.1.1", "192.168.10.1")
    context.append_text("package/base-files/files/etc/sysctl.conf", "vm.swappiness=10\n")
```
