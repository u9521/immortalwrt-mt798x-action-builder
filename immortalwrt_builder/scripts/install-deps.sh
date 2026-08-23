#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"

DEFAULT_PACKAGES=(
  build-essential
  clang
  flex
  bison
  g++
  gawk
  gcc-multilib
  g++-multilib
  gettext
  git
  libncurses5-dev
  libncurses-dev
  libssl-dev
  python3-setuptools
  rsync
  swig
  unzip
  zlib1g-dev
  file
  wget
  ccache
  curl
  ca-certificates
  xz-utils
  patch
  util-linux
  time
)

RECORD_FILE="installed-deps.txt"
RECORD_MODE="new" # "new" (only newly installed packages) or "all" (all dependency packages)
DRY_RUN=false

show_help() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install ImmortalWrt build dependencies on Debian/Ubuntu systems and optionally export installed packages.

Options:
  -r, --record <FILE>   Export installed packages list to FILE (default: installed-deps.txt)
  --record-all          Record all dependency packages, not only newly installed ones
  --record-new-only     Record only newly installed packages that were absent before (default)
  --no-record           Do not export installed packages list
  -n, --dry-run         Show packages to be installed and recorded without modifying system
  -h, --help            Show this help message and exit

Examples:
  sudo ./install-deps.sh
  sudo ./install-deps.sh --record /path/to/my-deps.txt
  sudo ./install-deps.sh --record-all -r infos/all-deps.txt
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--record|--export|-o|--output)
      RECORD_FILE="$2"
      shift 2
      ;;
    --record-all)
      RECORD_MODE="all"
      shift
      ;;
    --record-new-only)
      RECORD_MODE="new"
      shift
      ;;
    --no-record)
      RECORD_FILE=""
      shift
      ;;
    -n|--dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Error: Unknown option '$1'" >&2
      show_help >&2
      exit 1
      ;;
  esac
done

is_package_installed() {
  local pkg="$1"
  dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"
}

echo ">>> Checking existing system packages..."
NEW_PACKAGES=()
ALREADY_INSTALLED=()

for pkg in "${DEFAULT_PACKAGES[@]}"; do
  if is_package_installed "$pkg"; then
    ALREADY_INSTALLED+=("$pkg")
  else
    NEW_PACKAGES+=("$pkg")
  fi
done

echo "  Already installed (${#ALREADY_INSTALLED[@]}): ${ALREADY_INSTALLED[*]:-(none)}"
echo "  To be installed   (${#NEW_PACKAGES[@]}): ${NEW_PACKAGES[*]:-(none)}"

# Determine which packages to record in output file
PACKAGES_TO_RECORD=()
if [[ "$RECORD_MODE" == "all" ]]; then
  PACKAGES_TO_RECORD=("${DEFAULT_PACKAGES[@]}")
else
  PACKAGES_TO_RECORD=("${NEW_PACKAGES[@]}")
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo ">>> [Dry-Run] Skipped package installation."
  if [[ -n "$RECORD_FILE" ]]; then
    echo ">>> [Dry-Run] Would record ${#PACKAGES_TO_RECORD[@]} packages to: $RECORD_FILE"
  fi
  exit 0
fi

# Ensure root privileges
if [[ $EUID -ne 0 ]]; then
  echo "Error: This script must be run as root (use sudo)." >&2
  exit 1
fi

echo ">>> Updating apt package repositories..."
apt-get update -y

echo ">>> Installing ImmortalWrt build dependencies..."
apt-get install -y --no-install-recommends "${DEFAULT_PACKAGES[@]}"

# Export record file if requested
if [[ -n "$RECORD_FILE" ]]; then
  mkdir -p "$(dirname "$RECORD_FILE")"
  {
    echo "# ImmortalWrt dependency packages recorded on $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Mode: $RECORD_MODE"
    for pkg in "${PACKAGES_TO_RECORD[@]}"; do
      echo "$pkg"
    done
  } > "$RECORD_FILE"
  echo ">>> Successfully exported ${#PACKAGES_TO_RECORD[@]} package(s) to: $RECORD_FILE"
fi

echo ">>> Build dependencies successfully installed."
