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

[patch]
pre_feeds_patches = ["patch1.py"]                       # Python patches executed before feeds update
post_feeds_patches = ["patch2.py", "patch3.py"]         # Python patches executed after feeds install
post_config_patches = ["post_config.py"]                # Python patches executed after make defconfig

[patchConfig]
# Arbitrary user-defined key-values accessible in Python patches via context.patch_config
custom_router_ip = "192.168.10.1"
enable_extra_theme = true

[build]
defconfig = "ax3000m.config"                            # Path to defconfig file (e.g. from ./scripts/diffconfig.sh)
jobs = 16                                               # Parallel jobs (default: CPU threads count)
verbose = false                                         # Verbose compilation (V=s)
download = true                                         # Run make download (default: true)
ignore_errors = false                                   # Ignore compilation errors (default: false)

[ccache]
enabled = true                                          # Enable compiler cache (default: true)
dir = "/path/to/custom/ccache"                          # Custom CCACHE_DIR (default: cache/ccache/<arch_sig>)
max_size = "3.5G"                                       # CCACHE_MAXSIZE storage cap (default: 3.5G)
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
[workspace]
# Custom workspace root directory for source-code, cache, and outputs.
# Highly recommended for WSL environments to avoid slow Windows 9P filesystem (/mnt/c/...)
# by pointing work_root to native Linux ext4 path (e.g. /home/username/immortalwrt-build).
# work_root = "/home/username/immortalwrt-build"
```

### Workspace Resolution Order
1. CLI option `--work-root <path>`
2. Environment variable `IWB_WORK_ROOT`
3. `global.toml` (`[workspace].work_root`)
4. Current project directory (`Path.cwd()`)

---

## 3. Toolchain & ccache Cross-Target Cache Sharing

- **Toolchain Cache**:
  - Key calculation formula: `toolchain-{arch_signature}-{upstream_tree_hash}`
  - Where `arch_signature` is `board-subtarget-arch-libc-gcc` and `upstream_tree_hash` is the tree hash of `tools/`, `toolchain/`, and `include/`.
  - Multiple target definitions sharing the same hardware platform/architecture and upstream version (e.g. `360T7`, `AX3000M`, `WR30U` on `mediatek/filogic`) share the exact same toolchain cache, avoiding redundant GCC compilations.
  - **Limitation Note**: Custom Python patch scripts are intentionally excluded from the toolchain cache key. If a patch script modifies underlying cross-compiler/toolchain source code, you must manually clear the toolchain cache or adjust `defconfig` to trigger a recompile.

- **ccache Acceleration**:
  - Automatically partitioned by `arch_signature` (`cache/ccache/<arch_sig>`) and shared across targets of the same architecture.
  - Default cache cap is `3.5G`, managed automatically by ccache's built-in LRU eviction.

---

## 4. Python Patch Script Specification

Every patch script is a Python 3.14+ script located in `immortalwrt_builder/configs/patchs/`. It receives a `PatchContext` object providing rich helper methods and access to the target configuration and `[patchConfig]` custom values:

```python
# SPDX-License-Identifier: GPL-3.0-only
from immortalwrt_builder.builder.core.patch.interface import PatchContext


def patch(context: PatchContext) -> None:
    # 1. Access target config & custom patchConfig values
    print(f"Applying patch for target: {context.target.name}")
    router_ip = context.patch_config.get("custom_router_ip", "192.168.1.1")

    # 2. Modify files in source tree
    context.replace_text("package/base-files/files/bin/config_generate", "192.168.1.1", router_ip)
    context.append_text("package/base-files/files/etc/sysctl.conf", "vm.swappiness=10\n")
```
