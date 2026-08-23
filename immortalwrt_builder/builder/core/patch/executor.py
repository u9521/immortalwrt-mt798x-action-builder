# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .interface import PatchContext


def execute_python_patch(patch_path: Path, context: PatchContext) -> None:
    resolved_path = patch_path.resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Patch file not found: {resolved_path}")
    if resolved_path.suffix != ".py":
        raise ValueError(f"Invalid patch script: {resolved_path.name}. Only Python (.py) patch scripts are supported.")

    print(f"\n--- Running Python Patch: {resolved_path.name} ---", flush=True)

    module_name = f"iwb_patch_{resolved_path.stem}_{abs(hash(str(resolved_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, resolved_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load patch specification for {resolved_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise RuntimeError(f"Error loading patch module {resolved_path.name}: {exc}") from exc

    if hasattr(module, "patch") and callable(module.patch):
        module.patch(context)
    elif hasattr(module, "run") and callable(module.run):
        module.run(context)
    elif hasattr(module, "main") and callable(module.main):
        try:
            module.main(context)
        except TypeError:
            module.main()
    else:
        raise AttributeError(
            f"Patch script {resolved_path.name} must define a 'patch(context: PatchContext)' "
            "or 'run(context: PatchContext)' entry point."
        )

    print(f"--- Completed Python Patch: {resolved_path.name} ---\n", flush=True)


def execute_patches(patches: list[Path], context: PatchContext) -> None:
    for patch_path in patches:
        execute_python_patch(patch_path, context)
