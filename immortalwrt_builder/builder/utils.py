# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def directory_size_bytes(path: Path, *, exclude_names: set[str] | None = None) -> int:
    if not path.exists():
        return 0

    excluded = exclude_names or set()
    total = 0
    for root, dirnames, filenames in os.walk(path):
        dirnames[:] = [dirname for dirname in dirnames if dirname not in excluded]
        root_path = Path(root)

        for filename in filenames:
            file_path = root_path / filename
            if file_path.name in excluded or file_path.is_symlink():
                continue
            total += file_path.stat().st_size
    return total


def format_bytes(size: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} {units[-1]}"


def resolve_path(base_dir: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    printable = " ".join(command)
    cwd_display = str(cwd.resolve()) if cwd else os.getcwd()
    print(f"+ {printable}", flush=True)
    if capture_output:
        try:
            return subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                env=env,
                check=check,
                text=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"\nCommand failed with exit code {exc.returncode}: {printable}\nWorking directory: {cwd_display}",
                file=sys.stderr,
                flush=True,
            )
            raise

    process = subprocess.Popen(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None

    output_lines: list[str] = []
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        output_lines.append(line)

    process.wait()
    stdout = "".join(output_lines)
    completed = subprocess.CompletedProcess(
        command,
        process.returncode,
        stdout=stdout,
        stderr=None,
    )
    if check and process.returncode != 0:
        print(
            f"\nCommand failed with exit code {process.returncode}: {printable}\nWorking directory: {cwd_display}",
            file=sys.stderr,
            flush=True,
        )
        raise subprocess.CalledProcessError(
            process.returncode,
            command,
            output=stdout,
        )
    return completed


def copy_directory_contents(source: Path, destination: Path) -> None:
    ensure_directory(destination)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            ensure_directory(target)
            copy_directory_contents(child, target)
            continue
        target.write_bytes(child.read_bytes())


def current_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if extra:
        env.update(extra)
    return env


def format_command(command: Iterable[str]) -> str:
    return " ".join(command)
