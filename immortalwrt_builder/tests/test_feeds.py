# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from immortalwrt_builder.builder.core.feeds import feeds


class FeedsTests(unittest.TestCase):
    def test_update_and_install_feeds_executes_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            feeds_script = source_dir / "scripts" / "feeds"
            feeds_script.parent.mkdir(parents=True, exist_ok=True)
            feeds_script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

            with mock.patch("immortalwrt_builder.builder.core.feeds.feeds.run_command") as mock_run:
                feeds.update_feeds(source_dir)
                feeds.install_feeds(source_dir)

            self.assertEqual(mock_run.call_count, 2)
            self.assertEqual(mock_run.call_args_list[0].args[0], ["./scripts/feeds", "update", "-a"])
            self.assertEqual(mock_run.call_args_list[1].args[0], ["./scripts/feeds", "install", "-a"])


if __name__ == "__main__":
    unittest.main()
