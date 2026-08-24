# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 u9521

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_LIFECYCLES = {"proposed", "implemented", "rejected", "archived"}
ALLOWED_CLASSES = {"feature", "bug-fix", "simplification", "architecture", "process", "testing"}

REQUIRED_SECTIONS: dict[str, list[str]] = {
    "proposed": ["Problem", "Proposal", "Alternatives considered", "Acceptance criteria", "Risks"],
    "implemented": ["Problem", "Decision", "Alternatives considered", "Consequences"],
    "archived": ["Problem", "Decision", "Alternatives considered", "Consequences"],
    "rejected": ["Problem", "Alternatives considered"],
}

BUDGET_LIMITS: dict[str, int] = {
    "AGENTS.md": 1500,
    ".agents/notes/AGENTS.md": 600,
    ".agents/notes/implemented/AGENTS.md": 600,
}

IGNORE_DIRS = {".venv", ".git", "source-code", "cache", "out", "__pycache__", ".ruff_cache"}


def slugify_heading(heading: str) -> str:
    """Convert heading text to standard markdown anchor slug."""
    text = heading.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s]+", "-", text)


def count_words(text: str) -> int:
    """Count words in markdown text excluding code blocks."""
    cleaned = re.sub(r"```[\s\S]*?```", "", text)
    return len(re.findall(r"\b\w+\b", cleaned))


def check_agent_notes(repo_root: Path) -> list[str]:
    """Validate all Agent Notes under .agents/notes/."""
    errors: list[str] = []
    notes_dir = repo_root / ".agents" / "notes"
    if not notes_dir.is_dir():
        return errors

    for path in sorted(notes_dir.rglob("*.md")):
        rel = path.relative_to(notes_dir)
        parts = rel.parts

        # Skip README.md and AGENTS.md in notes root or subdirs
        if path.name in {"README.md", "AGENTS.md"}:
            continue

        if len(parts) != 3:
            errors.append(
                f"{path}: Note path must be '.agents/notes/<lifecycle>/<class>/YYYY-MM-DD-title.md' (got {rel})"
            )
            continue

        lifecycle, note_class, filename = parts
        if lifecycle not in ALLOWED_LIFECYCLES:
            errors.append(f"{path}: Invalid lifecycle '{lifecycle}', expected one of {sorted(ALLOWED_LIFECYCLES)}")
        if note_class not in ALLOWED_CLASSES:
            errors.append(f"{path}: Invalid class '{note_class}', expected one of {sorted(ALLOWED_CLASSES)}")

        if not re.match(r"^\d{4}-\d{2}-\d{2}-[\w-]+\.md$", filename):
            errors.append(
                f"{path}: Filename '{filename}' must start with YYYY-MM-DD date and kebab-case name (e.g. 2026-03-31-my-topic.md)"
            )

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        if not lines or not lines[0].startswith("# Agent Note: "):
            errors.append(f"{path}: Line 1 must start with '# Agent Note: <Title>'")

        if len(lines) < 3:
            errors.append(f"{path}: Missing status header")
            continue

        status_line = lines[2] if len(lines) > 2 else ""
        if not status_line.startswith("Status: "):
            errors.append(f"{path}: Line 3 must be 'Status: <status>' (found: '{status_line}')")
        else:
            status_val = status_line[len("Status: ") :].strip()
            if lifecycle == "proposed" and status_val != "proposed":
                errors.append(f"{path}: Status should be 'Status: proposed', got '{status_val}'")
            elif lifecycle == "implemented" and status_val != "implemented":
                errors.append(f"{path}: Status should be 'Status: implemented', got '{status_val}'")
            elif lifecycle == "rejected" and not status_val.startswith("rejected"):
                errors.append(f"{path}: Status should start with 'Status: rejected', got '{status_val}'")
            elif lifecycle == "archived":
                if status_val != "implemented":
                    errors.append(f"{path}: Archived status should be 'Status: implemented', got '{status_val}'")
                archived_line = lines[3] if len(lines) > 3 else ""
                if not re.match(r"^Archived:\s*\d{4}-\d{2}-\d{2}", archived_line):
                    errors.append(f"{path}: Archived notes must have 'Archived: YYYY-MM-DD' on line 4")

        # Check required sections
        headings = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", content, re.MULTILINE)]
        headings_set = set(headings)
        reqs = REQUIRED_SECTIONS.get(lifecycle, [])
        for req in reqs:
            if req not in headings_set:
                errors.append(f"{path}: Missing required section '## {req}'")

    return errors


def check_word_budgets(repo_root: Path) -> list[str]:
    """Check word count limits on documented files."""
    errors: list[str] = []
    for rel_path_str, limit in BUDGET_LIMITS.items():
        file_path = repo_root / rel_path_str
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        count = count_words(text)
        if count > limit:
            errors.append(f"{rel_path_str}: Word count {count} exceeds limit of {limit} words")
    return errors


def check_markdown_links(repo_root: Path) -> list[str]:
    """Validate relative markdown links across the repository."""
    errors: list[str] = []
    md_files: list[Path] = []

    for path in repo_root.rglob("*.md"):
        if any(ignored in path.parts for ignored in IGNORE_DIRS):
            continue
        md_files.append(path)

    # Link regex: [label](target)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        # Remove code blocks so code snippets with markdown syntax are ignored
        clean_content = re.sub(r"```[\s\S]*?```", "", content)

        for match in link_pattern.finditer(clean_content):
            target = match.group(2).strip()

            # Ignore external or special protocol links
            if re.match(r"^(https?://|mailto:|ftp:|data:)", target):
                continue

            # Handle anchor only
            if target.startswith("#"):
                anchor = target[1:]
                headings = [slugify_heading(h.group(1)) for h in re.finditer(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)]
                if anchor and anchor not in headings:
                    errors.append(f"{md_file.relative_to(repo_root)}: Target anchor '#{anchor}' not found in file")
                continue

            # Target has path and optional anchor
            parts = target.split("#", 1)
            target_path_str = parts[0]
            anchor = parts[1] if len(parts) > 1 else None

            if not target_path_str:
                continue

            # Resolve target path relative to current md file
            target_path = (md_file.parent / target_path_str).resolve()
            if not target_path.exists():
                errors.append(
                    f"{md_file.relative_to(repo_root)}: Broken link to '{target_path_str}' (resolved to {target_path})"
                )
                continue

            # If anchor exists on a target markdown file, verify anchor in target
            if anchor and target_path.suffix == ".md" and target_path.is_file():
                target_content = target_path.read_text(encoding="utf-8")
                headings = [
                    slugify_heading(h.group(1)) for h in re.finditer(r"^#{1,6}\s+(.+)$", target_content, re.MULTILINE)
                ]
                if anchor not in headings:
                    errors.append(f"{md_file.relative_to(repo_root)}: Broken anchor '#{anchor}' in '{target_path_str}'")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Agent-Native repository governance gates")
    parser.add_argument("--notes-only", action="store_true", help="Only verify Agent Notes")
    parser.add_argument("--budgets-only", action="store_true", help="Only verify word budgets")
    parser.add_argument("--links-only", action="store_true", help="Only verify markdown links")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    run_all = not (args.notes_only or args.budgets_only or args.links_only)

    all_errors: list[str] = []

    print(f"=== Agent-Native Governance Gates Verification [{repo_root.name}] ===")

    if run_all or args.notes_only:
        print("[1/3] Checking Agent Note formats and section integrity...")
        note_errors = check_agent_notes(repo_root)
        if note_errors:
            print(f"  FAILED: {len(note_errors)} note format errors:")
            for err in note_errors:
                print(f"    - {err}")
            all_errors.extend(note_errors)
        else:
            print("  PASSED: All Agent Notes adhere to format specification.")

    if run_all or args.budgets_only:
        print("[2/3] Checking documentation wordcount budgets...")
        budget_errors = check_word_budgets(repo_root)
        if budget_errors:
            print(f"  FAILED: {len(budget_errors)} budget overruns:")
            for err in budget_errors:
                print(f"    - {err}")
            all_errors.extend(budget_errors)
        else:
            print("  PASSED: All documents are within word budgets.")

    if run_all or args.links_only:
        print("[3/3] Checking Markdown relative link integrity...")
        link_errors = check_markdown_links(repo_root)
        if link_errors:
            print(f"  FAILED: {len(link_errors)} broken links detected:")
            for err in link_errors:
                print(f"    - {err}")
            all_errors.extend(link_errors)
        else:
            print("  PASSED: All markdown links and anchors resolved successfully.")

    print("-" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} gate violation(s) found.")
        return 1

    print("ALL GATES PASSED (Green).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
