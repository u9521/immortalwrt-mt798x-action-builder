#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def _normalize_github_url(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith("git@github.com:"):
        path_part = url[len("git@github.com:") :].removesuffix(".git")
        return f"https://github.com/{path_part}"
    if "github.com/" in url:
        clean_url = url.removesuffix(".git")
        if clean_url.startswith("http://"):
            clean_url = "https://" + clean_url[len("http://") :]
        return clean_url
    return None


def _format_repo_link(repo_url: str) -> str:
    if not repo_url:
        return "*(unknown)*"
    gh_url = _normalize_github_url(repo_url)
    if gh_url:
        owner_repo = gh_url.split("github.com/")[-1]
        return f"[{owner_repo}]({gh_url})"
    return f"`{repo_url}`"


def _format_commit_link(repo_url: str, commit_sha: str) -> str:
    if not commit_sha:
        return "*(unknown)*"
    short_sha = commit_sha[:7] if len(commit_sha) >= 7 else commit_sha
    gh_url = _normalize_github_url(repo_url)
    if gh_url:
        return f"[`{short_sha}`]({gh_url}/commit/{commit_sha})"
    return f"`{short_sha}`"


def _format_ref_link(repo_url: str, tag: str | None, branch: str | None, commit: str | None) -> str:
    gh_url = _normalize_github_url(repo_url)
    if tag:
        if gh_url:
            return f"[`{tag}`]({gh_url}/releases/tag/{tag}) *(Tag)*"
        return f"`{tag}` *(Tag)*"
    if branch:
        if gh_url:
            return f"[`{branch}`]({gh_url}/tree/{branch}) *(Branch)*"
        return f"`{branch}` *(Branch)*"
    if commit:
        return _format_commit_link(repo_url, commit) + " *(Commit)*"
    return "*(default HEAD)*"


def _get_git_commit_summary(repo_dir: Path) -> str:
    if not (repo_dir / ".git").exists() and not (repo_dir / "HEAD").exists():
        return ""
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%s (%cd)", "--date=short"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Write GitHub Actions CI build summary")
    parser.add_argument("--target", required=True, help="Built target name")
    parser.add_argument("--outcome", default="success", help="Build step outcome (success/failure)")
    parser.add_argument("--duration-seconds", type=int, default=0, help="Build duration in seconds")
    parser.add_argument("--summary-file", default=None, help="Output markdown summary file path")
    parser.add_argument("--toolchain-key", default="", help="Toolchain cache key")
    parser.add_argument("--release-tag", default="", help="Generated GitHub Release tag")
    parser.add_argument("--release-name", default="", help="Generated GitHub Release name")
    args = parser.parse_args()

    summary_file_path = args.summary_file or os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file_path:
        print("No summary file specified or found in GITHUB_STEP_SUMMARY.", flush=True)
        return 0

    minutes, seconds = divmod(args.duration_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    duration_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s" if hours else f"{minutes:02d}m {seconds:02d}s"

    outcome_upper = args.outcome.upper()
    if args.outcome == "success":
        status_icon = "✅"
    elif args.outcome == "skipped":
        status_icon = "⚠️"
    else:
        status_icon = "❌"

    # 1. Load workspace metadata if available
    metadata_file = Path(f"infos/{args.target}/workspace.json")
    meta: dict[str, object] = {}
    if metadata_file.exists():
        try:
            meta = json.loads(metadata_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    repo_url = str(meta.get("repo_url", ""))
    repo_branch = meta.get("repo_branch")
    repo_tag = meta.get("repo_tag")
    repo_commit = meta.get("repo_commit")
    upstream_commit = str(meta.get("last_upstream_commit", ""))
    local_commit = str(meta.get("last_local_commit", ""))

    # If repo_url was not in metadata, attempt fallback from target TOML
    if not repo_url:
        try:
            import sys

            sys.path.insert(0, str(Path.cwd()))
            from immortalwrt_builder.builder.core.config import TargetConfigProvider

            target_cfg = TargetConfigProvider(Path.cwd()).load(args.target)
            repo_url = target_cfg.source.url or ""
            repo_branch = target_cfg.source.branch
            repo_tag = target_cfg.source.tag
            repo_commit = target_cfg.source.commit
        except Exception:
            pass

    # Source commit message extraction
    source_dir = Path(str(meta.get("source_dir", f"source-code/{args.target}")))
    commit_summary = _get_git_commit_summary(source_dir) if source_dir.exists() else ""

    # CI Environment context
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    gh_repo = os.environ.get("GITHUB_REPOSITORY", "")
    gh_repo_url = f"{server_url}/{gh_repo}" if gh_repo else ""
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    actor = os.environ.get("GITHUB_ACTOR", "")
    gh_sha = os.environ.get("GITHUB_SHA", "")

    builder_commit = local_commit or gh_sha

    # Format build information rows
    build_info_rows: list[tuple[str, str]] = [
        ("Target", f"`{args.target}`"),
        ("Status", f"`{outcome_upper}`"),
        ("Duration", f"`{duration_str}` ({args.duration_seconds}s)"),
    ]

    if run_id and gh_repo:
        run_label = f"#{run_number}" if run_number else f"#{run_id}"
        run_link = f"[{run_label}]({gh_repo_url}/actions/runs/{run_id})"
        trigger_detail = f" ({event_name} by @{actor})" if actor and event_name else ""
        build_info_rows.append(("Workflow Run", f"{run_link}{trigger_detail}"))

    if args.release_tag:
        rel_label = args.release_name or args.release_tag
        if gh_repo:
            rel_link = f"[{rel_label}]({gh_repo_url}/releases/tag/{args.release_tag})"
        else:
            rel_link = f"`{rel_label}`"
        build_info_rows.append(("Release", rel_link))

    # Format source repository rows
    source_commit_rendered = _format_commit_link(repo_url, upstream_commit)
    if commit_summary:
        source_commit_rendered += f" *{commit_summary}*"

    builder_commit_rendered = _format_commit_link(gh_repo_url or "https://github.com", builder_commit)

    source_info_rows: list[tuple[str, str]] = [
        ("Source Repo", _format_repo_link(repo_url)),
        (
            "Branch / Tag",
            _format_ref_link(
                repo_url,
                str(repo_tag) if repo_tag else None,
                str(repo_branch) if repo_branch else None,
                str(repo_commit) if repo_commit else None,
            ),
        ),
        ("Source Commit", source_commit_rendered),
    ]
    if builder_commit:
        source_info_rows.append(("Builder Commit", builder_commit_rendered))

    # Construct Markdown output
    summary_content: list[str] = [
        f"## {status_icon} ImmortalWrt Build Summary: `{args.target}`",
        "",
        "### 🚀 Build Information",
        "| Item | Details |",
        "|:---|:---|",
    ]
    for key, val in build_info_rows:
        summary_content.append(f"| **{key}** | {val} |")
    summary_content.append("")

    summary_content.append("### 📦 Source Repository")
    summary_content.append("| Item | Details |")
    summary_content.append("|:---|:---|")
    for key, val in source_info_rows:
        summary_content.append(f"| **{key}** | {val} |")
    summary_content.append("")

    # Firmware Artifacts table
    digest_path = Path("filedigest.md")
    if digest_path.exists() and digest_path.stat().st_size > 0:
        summary_content.append("### 💾 Firmware Artifacts")
        summary_content.append(digest_path.read_text(encoding="utf-8").strip())
        summary_content.append("")
    elif args.outcome == "success":
        summary_content.append("### 💾 Firmware Artifacts")
        summary_content.append("*No firmware artifacts collected.*")
        summary_content.append("")

    # Caching & Storage
    caching_lines: list[str] = []
    if args.toolchain_key:
        caching_lines.append(f"- **Toolchain Cache Key**: `{args.toolchain_key}`")

    # Disk usage
    disk_usage_file = Path(f"infos/{args.target}/disk-usage.json")
    if disk_usage_file.exists():
        try:
            du = json.loads(disk_usage_file.read_text(encoding="utf-8"))
            sections = du.get("sections", {})
            src_sz = sections.get("source", {}).get("size_formatted", "N/A")
            cache_sz = sections.get("cache", {}).get("size_formatted", "N/A")
            out_sz = sections.get("output", {}).get("size_formatted", "N/A")
            total_sz = du.get("total_formatted", "N/A")
            caching_lines.append(
                f"- **Workspace Disk Usage**: Source `{src_sz}` | Cache `{cache_sz}` | Output `{out_sz}` | Total `{total_sz}`"
            )
        except Exception:
            pass

    ccache_stats_path = Path(f"infos/{args.target}/ccache-stats.txt")
    if ccache_stats_path.exists():
        ccache_text = ccache_stats_path.read_text(encoding="utf-8").strip()
        if ccache_text:
            caching_lines.append("\n**ccache Statistics**:")
            caching_lines.append("```text")
            caching_lines.append(ccache_text)
            caching_lines.append("```")

    if caching_lines:
        summary_content.append("### ⚡ Caching & Storage")
        summary_content.extend(caching_lines)
        summary_content.append("")

    # Write summary
    summary_path = Path(summary_file_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(summary_content) + "\n")

    print(f"Build summary written to {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
