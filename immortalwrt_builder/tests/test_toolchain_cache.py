# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from immortalwrt_builder.builder.core.build import (
    clear_toolchain_cache,
    compute_toolchain_key,
    is_toolchain_cached,
    resolve_toolchain_archive_path,
    restore_toolchain_cache,
    save_toolchain_cache,
    touch_toolchain_stamps,
)
from immortalwrt_builder.builder.core.config.schema import (
    BuildConfig,
    GitSourceConfig,
    PatchConfig,
    TargetConfig,
    ToolchainCacheConfig,
)


class ToolchainCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target = TargetConfig(
            name="test-target",
            source=GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", branch="openwrt-23.05"),
            build=BuildConfig(),
            toolchain_cache=ToolchainCacheConfig(enabled=True),
        )

    def test_compute_toolchain_key_with_dot_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            dot_config = source_dir / ".config"
            dot_config.write_text(
                'CONFIG_ARCH="aarch64"\n'
                'CONFIG_TARGET_BOARD="mediatek"\n'
                'CONFIG_TARGET_SUBTARGET="filogic"\n'
                'CONFIG_GCC_VERSION="14.3.0"\n'
                'CONFIG_LIBC="musl"\n'
                'CONFIG_BINUTILS_VERSION="2.44"\n',
                encoding="utf-8",
            )

            key = compute_toolchain_key(self.target, source_dir)
            self.assertTrue(key.startswith("toolchain-mediatek-filogic-aarch64-musl-14.3.0-"))
            self.assertIn("aarch64", key)
            self.assertIn("14.3.0", key)
            self.assertIn("musl", key)

    def test_compute_toolchain_key_with_defconfig_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            defconfig = Path(temp_dir) / "test.config"
            defconfig.write_text(
                'CONFIG_ARCH="x86_64"\nCONFIG_GCC_VERSION="13.3.0"\nCONFIG_LIBC="musl"\n',
                encoding="utf-8",
            )

            target = TargetConfig(
                name="x86-target",
                source=GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git", branch="master"),
                build=BuildConfig(defconfig_path=defconfig),
                toolchain_cache=ToolchainCacheConfig(),
            )

            key = compute_toolchain_key(target, source_dir)
            self.assertTrue(key.startswith("toolchain-generic-generic-x86_64-musl-13.3.0-"))

    def test_compute_toolchain_key_cross_target_sharing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            dot_config = source_dir / ".config"
            dot_config.write_text(
                'CONFIG_ARCH="aarch64"\n'
                'CONFIG_TARGET_BOARD="mediatek"\n'
                'CONFIG_TARGET_SUBTARGET="filogic"\n'
                'CONFIG_GCC_VERSION="14.3.0"\n'
                'CONFIG_LIBC="musl"\n',
                encoding="utf-8",
            )

            target_a = TargetConfig(
                name="target-360t7",
                source=GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git"),
            )
            target_b = TargetConfig(
                name="target-ax3000m",
                source=GitSourceConfig(url="https://github.com/immortalwrt/immortalwrt.git"),
            )

            key_a = compute_toolchain_key(target_a, source_dir)
            key_b = compute_toolchain_key(target_b, source_dir)

            # Different target names share the exact same toolchain key
            self.assertEqual(key_a, key_b)
            self.assertTrue(key_a.startswith("toolchain-mediatek-filogic-aarch64-musl-14.3.0-"))

    def test_compute_toolchain_key_ignores_patch_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            patch_file = Path(temp_dir) / "p1.py"
            patch_file.write_text("# patch 1\n", encoding="utf-8")

            target1 = TargetConfig(
                name="test-target",
                source=GitSourceConfig(url="https://example.com"),
                patch=PatchConfig(pre_feeds_patches=[patch_file]),
            )
            key1 = compute_toolchain_key(target1, source_dir)

            patch_file.write_text("# patch 1 modified\n", encoding="utf-8")
            key2 = compute_toolchain_key(target1, source_dir)
            # Patch modifications do not invalidate toolchain cache
            self.assertEqual(key1, key2)

    def test_touch_toolchain_stamps_refreshes_mtime_without_clock_skew(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            staging_dir = source_dir / "staging_dir"
            host_stamp_dir = staging_dir / "host" / "stamp"
            tc_stamp_dir = staging_dir / "toolchain-aarch64_cortex-a53_gcc-14.3.0_musl" / "stamp"
            target_stamp_dir = staging_dir / "target-aarch64_cortex-a53_musl" / "stamp"
            host_stamp_dir.mkdir(parents=True)
            tc_stamp_dir.mkdir(parents=True)
            target_stamp_dir.mkdir(parents=True)

            host_stamp = host_stamp_dir / ".tools_compile_123"
            host_stamp.write_text("", encoding="utf-8")
            tc_stamp = tc_stamp_dir / ".toolchain_compile"
            tc_stamp.write_text("", encoding="utf-8")
            target_stamp = target_stamp_dir / ".target_prereq"
            target_stamp.write_text("", encoding="utf-8")

            # Set past mtime
            past_time = time.time() - 3600
            os.utime(host_stamp, (past_time, past_time))
            os.utime(tc_stamp, (past_time, past_time))
            os.utime(target_stamp, (past_time, past_time))

            before = time.time()
            touched = touch_toolchain_stamps(source_dir)
            after = time.time()

            # Only toolchain components (host and toolchain-*) are touched, target-* is untouched
            self.assertEqual(touched, 2)
            self.assertGreaterEqual(host_stamp.stat().st_mtime, before - 1)
            self.assertLessEqual(host_stamp.stat().st_mtime, after + 1)
            self.assertGreaterEqual(tc_stamp.stat().st_mtime, before - 1)
            self.assertLessEqual(tc_stamp.stat().st_mtime, after + 1)
            self.assertAlmostEqual(target_stamp.stat().st_mtime, past_time, delta=2)

    def test_is_toolchain_cached_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            self.assertFalse(is_toolchain_cached(source_dir))

            staging_dir = source_dir / "staging_dir"
            host_bin = staging_dir / "host" / "bin"
            host_bin.mkdir(parents=True)
            (host_bin / "cmake").write_text("", encoding="utf-8")

            tc_bin = staging_dir / "toolchain-aarch64_gcc-14_musl" / "bin"
            tc_bin.mkdir(parents=True)
            (tc_bin / "aarch64-openwrt-linux-musl-gcc").write_text("", encoding="utf-8")

            self.assertTrue(is_toolchain_cached(source_dir))

    def test_save_and_restore_toolchain_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_dir = temp_root / "source"
            staging_dir = source_dir / "staging_dir"
            host_bin = staging_dir / "host" / "bin"
            host_stamp = staging_dir / "host" / "stamp"
            tc_bin = staging_dir / "toolchain-aarch64_musl" / "bin"
            tc_stamp = staging_dir / "toolchain-aarch64_musl" / "stamp"

            host_bin.mkdir(parents=True)
            host_stamp.mkdir(parents=True)
            tc_bin.mkdir(parents=True)
            tc_stamp.mkdir(parents=True)

            (host_bin / "cmake").write_text("dummy-cmake", encoding="utf-8")
            (host_bin / "awk").symlink_to("/usr/bin/gawk")
            (host_stamp / ".tools_compile_xyz").write_text("", encoding="utf-8")
            (tc_bin / "aarch64-gcc").write_text("dummy-gcc", encoding="utf-8")
            (tc_stamp / ".toolchain_compile").write_text("", encoding="utf-8")

            archive_path = temp_root / "cache" / "toolchain-test.tar.gz"
            saved_path = save_toolchain_cache(self.target, source_dir, archive_path)
            self.assertTrue(saved_path.exists())
            self.assertGreater(saved_path.stat().st_size, 0)

            # Test restoring into a fresh source directory
            new_source_dir = temp_root / "new_source"
            success = restore_toolchain_cache(self.target, new_source_dir, archive_path)
            self.assertTrue(success)

            new_cmake = new_source_dir / "staging_dir" / "host" / "bin" / "cmake"
            new_awk = new_source_dir / "staging_dir" / "host" / "bin" / "awk"
            new_gcc = new_source_dir / "staging_dir" / "toolchain-aarch64_musl" / "bin" / "aarch64-gcc"
            new_stamp = new_source_dir / "staging_dir" / "host" / "stamp" / ".tools_compile_xyz"

            self.assertTrue(new_cmake.exists())
            self.assertEqual(new_cmake.read_text(encoding="utf-8"), "dummy-cmake")
            self.assertTrue(new_awk.is_symlink())
            self.assertTrue(new_gcc.exists())
            self.assertTrue(new_stamp.exists())

    def test_restore_toolchain_cache_corrupted_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_dir = temp_root / "source"
            corrupted_archive = temp_root / "corrupted.tar.gz"
            corrupted_archive.write_bytes(b"not a real tar.gz file")

            success = restore_toolchain_cache(self.target, source_dir, corrupted_archive)
            self.assertFalse(success)

    def test_clear_toolchain_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            archive = resolve_toolchain_archive_path(self.target, work_root)
            archive.parent.mkdir(parents=True)
            archive.write_text("dummy", encoding="utf-8")

            removed = clear_toolchain_cache(self.target, work_root)
            self.assertTrue(removed)
            self.assertFalse(archive.exists())


if __name__ == "__main__":
    unittest.main()
