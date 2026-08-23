#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"

echo ">>> Updating apt package repositories..."
apt-get update -y

echo ">>> Installing ImmortalWrt build dependencies..."
apt-get install -y --no-install-recommends \
  build-essential \
  clang \
  flex \
  bison \
  g++ \
  gawk \
  gcc-multilib \
  g++-multilib \
  gettext \
  git \
  libncurses5-dev \
  libncurses-dev \
  libssl-dev \
  python3-setuptools \
  rsync \
  swig \
  unzip \
  zlib1g-dev \
  file \
  wget \
  ccache \
  curl \
  ca-certificates \
  xz-utils \
  patch \
  util-linux \
  time

echo ">>> Build dependencies successfully installed."
