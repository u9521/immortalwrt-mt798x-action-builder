#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"

RECORD_FILE="installed-deps.txt"
PURGE=true
AUTOREMOVE=true
REMOVE_RECORD=false
DRY_RUN=false

show_help() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Uninstall ImmortalWrt build dependencies recorded by install-deps.sh.

Options:
  -f, --file <FILE>     Load recorded packages list from FILE (default: installed-deps.txt)
  --no-purge            Do not purge package configuration files
  --no-autoremove       Do not run apt-get autoremove after uninstallation
  --remove-record       Delete the record file after successful uninstallation
  -n, --dry-run         Show packages to be uninstalled without modifying system
  -h, --help            Show this help message and exit

Examples:
  sudo ./uninstall-deps.sh
  sudo ./uninstall-deps.sh -f /path/to/my-deps.txt
  sudo ./uninstall-deps.sh -f installed-deps.txt --remove-record
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file|-i|--input)
      RECORD_FILE="$2"
      shift 2
      ;;
    --no-purge)
      PURGE=false
      shift
      ;;
    --no-autoremove)
      AUTOREMOVE=false
      shift
      ;;
    --remove-record)
      REMOVE_RECORD=true
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

if [[ ! -f "$RECORD_FILE" ]]; then
  echo "Error: Record file not found: $RECORD_FILE" >&2
  echo "Hint: Specify record file with -f <FILE> or run install-deps.sh with --record first." >&2
  exit 1
fi

is_package_installed() {
  local pkg="$1"
  dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"
}

# Read package names from record file
RECORDED_PACKAGES=()
while IFS= read -r line || [[ -n "$line" ]]; do
  # Strip comments and whitespace
  clean_line="$(echo "$line" | sed 's/#.*//g' | xargs)"
  if [[ -n "$clean_line" ]]; then
    RECORDED_PACKAGES+=("$clean_line")
  fi
done < "$RECORD_FILE"

if [[ ${#RECORDED_PACKAGES[@]} -eq 0 ]]; then
  echo ">>> No packages found to uninstall in: $RECORD_FILE"
  exit 0
fi

echo ">>> Loaded ${#RECORDED_PACKAGES[@]} package(s) from: $RECORD_FILE"

# Filter only currently installed packages
PACKAGES_TO_REMOVE=()
NOT_INSTALLED=()

for pkg in "${RECORDED_PACKAGES[@]}"; do
  if is_package_installed "$pkg"; then
    PACKAGES_TO_REMOVE+=("$pkg")
  else
    NOT_INSTALLED+=("$pkg")
  fi
done

echo "  Currently installed to remove (${#PACKAGES_TO_REMOVE[@]}): ${PACKAGES_TO_REMOVE[*]:-(none)}"
if [[ ${#NOT_INSTALLED[@]} -gt 0 ]]; then
  echo "  Already absent/uninstalled     (${#NOT_INSTALLED[@]}): ${NOT_INSTALLED[*]}"
fi

if [[ ${#PACKAGES_TO_REMOVE[@]} -eq 0 ]]; then
  echo ">>> All recorded packages are already uninstalled."
  if [[ "$REMOVE_RECORD" == "true" ]]; then
    rm -f "$RECORD_FILE"
    echo ">>> Removed record file: $RECORD_FILE"
  fi
  exit 0
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo ">>> [Dry-Run] Would uninstall ${#PACKAGES_TO_REMOVE[@]} package(s): ${PACKAGES_TO_REMOVE[*]}"
  exit 0
fi

# Ensure root privileges
if [[ $EUID -ne 0 ]]; then
  echo "Error: This script must be run as root (use sudo)." >&2
  exit 1
fi

REMOVE_ARGS=(-y)
if [[ "$PURGE" == "true" ]]; then
  REMOVE_ARGS+=(--purge)
fi

echo ">>> Uninstalling packages: ${PACKAGES_TO_REMOVE[*]}..."
apt-get remove "${REMOVE_ARGS[@]}" "${PACKAGES_TO_REMOVE[@]}"

if [[ "$AUTOREMOVE" == "true" ]]; then
  echo ">>> Cleaning unused dependencies (apt-get autoremove)..."
  if [[ "$PURGE" == "true" ]]; then
    apt-get autoremove -y --purge
  else
    apt-get autoremove -y
  fi
fi

if [[ "$REMOVE_RECORD" == "true" ]]; then
  rm -f "$RECORD_FILE"
  echo ">>> Removed record file: $RECORD_FILE"
fi

echo ">>> Packages successfully uninstalled."
