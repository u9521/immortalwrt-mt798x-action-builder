# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

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
            self.assertTrue(key.startswith("toolchain-test-target-aarch64-14.3.0-musl-"))
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
            self.assertTrue(key.startswith("toolchain-x86-target-x86_64-13.3.0-musl-"))

    def test_compute_toolchain_key_changes_on_patch_change(self) -> None:
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
            self.assertNotEqual(key1, key2)

    def test_touch_toolchain_stamps_refreshes_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            staging_dir = source_dir / "staging_dir"
            host_stamp_dir = staging_dir / "host" / "stamp"
            tc_stamp_dir = staging_dir / "toolchain-aarch64_cortex-a53_gcc-14.3.0_musl" / "stamp"
            host_stamp_dir.mkdir(parents=True)
            tc_stamp_dir.mkdir(parents=True)

            host_stamp = host_stamp_dir / ".tools_compile_123"
            host_stamp.write_text("", encoding="utf-8")
            tc_stamp = tc_stamp_dir / ".toolchain_compile"
            tc_stamp.write_text("", encoding="utf-8")

            # Set past mtime
            past_time = time.time() - 3600
            import os

            os.utime(host_stamp, (past_time, past_time))
            os.utime(tc_stamp, (past_time, past_time))

            touched = touch_toolchain_stamps(source_dir)
            self.assertEqual(touched, 2)

            now = time.time()
            self.assertGreater(host_stamp.stat().st_mtime, now)
            self.assertGreater(tc_stamp.stat().st_mtime, now)

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
            new_gcc = new_source_dir / "staging_dir" / "toolchain-aarch64_musl" / "bin" / "aarch64-gcc"
            new_stamp = new_source_dir / "staging_dir" / "host" / "stamp" / ".tools_compile_xyz"

            self.assertTrue(new_cmake.exists())
            self.assertEqual(new_cmake.read_text(encoding="utf-8"), "dummy-cmake")
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

    def test_resolve_and_clear_toolchain_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_root = Path(temp_dir)
            archive_path = resolve_toolchain_archive_path(self.target, work_root)
            self.assertEqual(
                archive_path,
                (work_root / "cache" / "test-target" / "toolchain" / "toolchain-test-target.tar.gz").resolve(),
            )

            archive_path.parent.mkdir(parents=True, exist_ok=True)
            archive_path.write_text("dummy", encoding="utf-8")
            self.assertTrue(archive_path.exists())

            removed = clear_toolchain_cache(self.target, work_root)
            self.assertTrue(removed)
            self.assertFalse(archive_path.exists())


if __name__ == "__main__":
    unittest.main()
