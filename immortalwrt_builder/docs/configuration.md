# Target Configuration Guide

Target configurations are declared in TOML files under `immortalwrt_builder/configs/targets/<name>.toml`.

## Structure

```toml
name = "official-mt7981-ax3000m"   # Unique target name (required)
base = false                       # True if this is a template (cannot be directly built)
extends = "immortalwrt-base"       # Name of parent target config to inherit from

[source]
url = "https://github.com/immortalwrt/immortalwrt.git"  # Git repo URL
branch = "openwrt-23.05"                                # Branch name
tag = "v23.05.3"                                        # Optional Git tag
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
pre_feeds_scripts = ["diy1.sh"]                         # Scripts executed before feeds update
post_feeds_scripts = ["diy2.sh", "diy3.sh"]             # Scripts executed after feeds install
post_config_scripts = ["post_config.sh"]                # Scripts executed after make defconfig
custom_files = "path/to/files"                          # Overlay files directory
ip_address = "192.168.10.1"                             # Builtin patch: default LAN IP
hostname = "ImmortalWrt"                                # Builtin patch: default hostname
wifi_ssid_2g = "MyRouter-2.4G"                          # Builtin patch: 2.4G Wi-Fi SSID
wifi_ssid_5g = "MyRouter-5G"                            # Builtin patch: 5G Wi-Fi SSID
default_theme = "luci-theme-argon"                      # Builtin patch: default LuCI theme
distrib_description = "ImmortalWrt-{date}"              # Builtin patch: release description
distrib_revision = "By Author"                          # Builtin patch: release revision

[build]
defconfig = "ax3000m.config"                            # Path to defconfig file in defconfigs/
target_profile = "mediatek/mt7981/cmcc_rax3000m"        # Optional target profile string
extra_configs = [                                       # Extra .config lines appended before make defconfig
    "CONFIG_PACKAGE_luci-app-argon-config=y"
]
jobs = 16                                               # Parallel jobs (default: CPU threads count)
verbose = false                                         # Verbose compilation (V=s)
download = true                                         # Run make download (default: true)
use_ccache = true                                       # Enable compiler cache (default: true)
ignore_errors = false                                   # Ignore compilation errors (default: false)

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
