#!/usr/bin/env python3
"""
Archive old daily memory files after they've been processed.

Moves daily markdown files older than a threshold to an archive directory,
keeping the active memory directory clean. Files should only be archived
after True Recall has curated them and promotion to PARA has been attempted.

Usage:
    python3 archive_daily_notes.py --user-id alice
    python3 archive_daily_notes.py --user-id alice --days 30
    python3 archive_daily_notes.py --user-id alice --dry-run
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
PROJECT_DIR = SCRIPT_DIR.parent  # memory/
WORKSPACE_DIR = Path(os.getenv("OPENCLAW_WORKSPACE", str(PROJECT_DIR.parent.parent)))


def find_daily_files(user_dir: Path) -> list:
    """Find daily markdown files matching YYYY-MM-DD.md pattern."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
    files = []
    if not user_dir.exists():
        return files
    for f in user_dir.iterdir():
        if f.is_file() and pattern.match(f.name):
            try:
                date = datetime.strptime(f.stem, "%Y-%m-%d")
                files.append((date, f))
            except ValueError:
                continue
    return sorted(files, key=lambda x: x[0])


def archive_files(user_id: str, days: int = 30, dry_run: bool = False):
    """Move daily files older than `days` to archive/."""
    user_dir = PROJECT_DIR / user_id
    if not user_dir.exists():
        # Try workspace-level memory dir
        user_dir = WORKSPACE_DIR / "memory" / user_id
    if not user_dir.exists():
        print(f"ERROR: No memory directory found for user '{user_id}'", file=sys.stderr)
        sys.exit(1)

    archive_dir = user_dir / "archive"
    cutoff = datetime.now() - timedelta(days=days)
    daily_files = find_daily_files(user_dir)

    if not daily_files:
        print(f"No daily files found in {user_dir}")
        return

    to_archive = [(date, f) for date, f in daily_files if date < cutoff]

    if not to_archive:
        print(f"No files older than {days} days (cutoff: {cutoff.strftime('%Y-%m-%d')})")
        return

    print(f"Found {len(to_archive)} file(s) to archive (older than {cutoff.strftime('%Y-%m-%d')}):")

    if not dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)

    for date, filepath in to_archive:
        dest = archive_dir / filepath.name
        if dry_run:
            print(f"  [dry-run] {filepath.name} → archive/{filepath.name}")
        else:
            shutil.move(str(filepath), str(dest))
            print(f"  {filepath.name} → archive/{filepath.name}")

    if not dry_run:
        print(f"\nArchived {len(to_archive)} file(s) to {archive_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Archive old daily memory files"
    )
    parser.add_argument(
        "--user-id", required=True, help="User ID whose daily files to archive"
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="Archive files older than this many days (default: 30)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be archived without moving files"
    )
    args = parser.parse_args()

    archive_files(args.user_id, days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
