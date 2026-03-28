#!/usr/bin/env python3
"""
Seed PARA directories for household members.

Creates memory/para/<user>/ directories from templates for each specified user,
plus a shared/ directory for household-wide facts. Safe to run multiple times —
will not overwrite existing files.

Usage:
    python3 seed_para.py --users alice bob
    python3 seed_para.py --users alice bob --dry-run
    python3 seed_para.py --users alice bob --force  # Overwrite existing files
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
PROJECT_DIR = SCRIPT_DIR.parent  # memory/
TOOLKIT_DIR = PROJECT_DIR.parent  # evergreen-toolkit/

PARA_DIR = PROJECT_DIR / "para"
TEMPLATES_DIR = PARA_DIR / "templates"

TEMPLATE_FILES = {
    "summary-template.md": "summary.md",
    "items-template.json": "items.json",
    "review-queue-template.md": "review-queue.md",
}


def seed_user(user_id: str, dry_run: bool = False, force: bool = False) -> bool:
    """Create PARA directory for a single user from templates.

    Returns True if any files were created/updated."""
    user_dir = PARA_DIR / user_id
    changed = False

    if dry_run:
        print(f"  [dry-run] Would create directory: {user_dir}")
    else:
        user_dir.mkdir(parents=True, exist_ok=True)

    for template_name, target_name in TEMPLATE_FILES.items():
        src = TEMPLATES_DIR / template_name
        dst = user_dir / target_name

        if not src.exists():
            print(f"  WARNING: Template {src} not found, skipping {target_name}")
            continue

        if dst.exists() and not force:
            print(f"  SKIP: {dst} already exists (use --force to overwrite)")
            continue

        if dry_run:
            print(f"  [dry-run] Would copy {template_name} → {user_id}/{target_name}")
        else:
            shutil.copy2(src, dst)
            print(f"  Created: {dst.relative_to(TOOLKIT_DIR)}")

        changed = True

    return changed


def main():
    parser = argparse.ArgumentParser(
        description="Seed PARA directories for household members"
    )
    parser.add_argument(
        "--users",
        nargs="+",
        required=True,
        help="User IDs to create PARA directories for (e.g., alice bob)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files (default: skip existing)",
    )
    args = parser.parse_args()

    # Validate templates exist
    if not TEMPLATES_DIR.exists():
        print(f"ERROR: Templates directory not found: {TEMPLATES_DIR}", file=sys.stderr)
        print("Run this script from the evergreen-toolkit root.", file=sys.stderr)
        sys.exit(1)

    missing = [t for t in TEMPLATE_FILES if not (TEMPLATES_DIR / t).exists()]
    if missing:
        print(f"ERROR: Missing templates: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Always include 'shared' directory
    users = list(dict.fromkeys(args.users + ["shared"]))  # deduplicate, preserve order

    print(f"Seeding PARA directories for: {', '.join(users)}")
    if args.dry_run:
        print("(dry run — no changes will be made)\n")
    else:
        print()

    total_changed = 0
    for user_id in users:
        print(f"[{user_id}]")
        if seed_user(user_id, dry_run=args.dry_run, force=args.force):
            total_changed += 1
        print()

    if args.dry_run:
        print("Dry run complete. No files were created.")
    elif total_changed > 0:
        print(f"Done. PARA directories seeded for {total_changed} user(s).")
        print(f"Next: populate summary.md files with known facts about each user.")
    else:
        print("No changes needed — all directories already exist.")
        print("Use --force to overwrite existing files.")


if __name__ == "__main__":
    main()
