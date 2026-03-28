#!/usr/bin/env python3
"""
Validate that all placeholder values have been customized.

Scans key files for remaining <angle-bracket> placeholders and known
example values that should have been replaced during setup.

Usage:
    python3 scripts/validate-customization.py
    python3 scripts/validate-customization.py --strict   # treat persona warnings as errors
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent

# Files to scan for remaining placeholders
KEY_FILES = [
    "memory/SKILL.md",
    "memory/settings.md",
    "memory/README.md",
    "memory/curator_prompts/base.md",
    "memory/UPSTREAM-CREDITS.md",
    "memory/MULTI-USER-GUIDE.md",
    "config/crontab.generated",
    "scripts/health_check.sh",
    "scripts/evergreen-ai-runner.sh",
    "evergreens/household-memory/TESTS.md",
    "ARCHITECTURE.md",
    "AGENT-ONBOARDING.md",
    "README.md",
    "QUICKSTART.md",
    "CONTRIBUTING.md",
    "PUBLISHING.md",
    "docs/SETUP-GUIDE.md",
    "docs/TROUBLESHOOTING.md",
    "evergreens/system-health/STATE.md",
    "evergreens/household-memory/STATE.md",
    "evergreens/prompt-injection/STATE.md",
    "evergreens/upstream-architecture/STATE.md",
    "memory/APPROVED-CONTACTS.json",
]

# Also check .memory_env if it exists (created from config/memory_env.example)
OPTIONAL_FILES = [
    ".memory_env",
]

# Patterns that indicate uncustomized placeholders
PLACEHOLDER_PATTERNS = [
    (r"<user1>", "User 1 placeholder not replaced"),
    (r"<user2>", "User 2 placeholder not replaced"),
    (r"<agent>", "Agent name placeholder not replaced"),
    (r"<default-user-id>", "Default user ID placeholder not replaced"),
    (r"<your-[a-z-]+>", "Uncustomized placeholder found"),
]

# Example persona names that should be replaced during setup.
# These are warnings (not errors) since some docs intentionally reference
# them as illustrative examples with context.
# Note: "Eve" is used as the default example agent name throughout the
# documentation, so many matches will be false positives in docs that
# explain the system using Eve as an example. Rename Eve to your agent's
# name only in files you actually deploy (SKILL.md, settings.md, etc.).
EXAMPLE_PERSONA_PATTERNS = [
    (r"\bAlice\b", "Example persona 'Alice' still present"),
    (r"\bBob\b", "Example persona 'Bob' still present"),
    (r"\bEve\b", "Example agent name 'Eve' still present"),
    (r"\bSmith\b", "Example surname 'Smith' still present"),
    (r"\bAcme Bookkeeping\b", "Example business 'Acme Bookkeeping' still present"),
]

# Files that intentionally contain example persona names as documentation.
# These are excluded from persona warnings to reduce false positives.
PERSONA_EXCLUDE_FILES = {
    "README.md",
    "AGENT-ONBOARDING.md",
    "QUICKSTART.md",
    "CONTRIBUTING.md",
    "PUBLISHING.md",
    "GLOSSARY.md",
    "PROJECT-REVIEW-AND-IMPROVEMENT-PLAN.md",
    "docs/NAME-CUSTOMIZATION.md",
    "docs/SETUP-GUIDE.md",
    "docs/TROUBLESHOOTING.md",
}


def check_file(filepath: Path) -> list[str]:
    """Check a single file for remaining placeholders."""
    issues = []
    if not filepath.exists():
        return issues

    content = filepath.read_text()
    rel = filepath.relative_to(WORKSPACE)

    for pattern, message in PLACEHOLDER_PATTERNS:
        matches = [
            i + 1
            for i, line in enumerate(content.splitlines())
            if re.search(pattern, line)
        ]
        if matches:
            lines_str = ", ".join(str(m) for m in matches[:5])
            issues.append(f"  {rel}:{lines_str} — {message} ({pattern})")

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Validate that all placeholder values have been customized."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat example persona names in non-documentation files as errors (exit 1)",
    )
    args = parser.parse_args()

    print("=== Evergreen Toolkit Customization Validator ===")
    if args.strict:
        print("(strict mode: persona warnings are errors)")
    print()

    all_issues: list[str] = []
    all_warnings: list[str] = []

    for rel_path in KEY_FILES:
        filepath = WORKSPACE / rel_path
        issues = check_file(filepath)
        all_issues.extend(issues)

    # Check optional files (e.g., .memory_env) if they exist
    for rel_path in OPTIONAL_FILES:
        filepath = WORKSPACE / rel_path
        if filepath.exists():
            issues = check_file(filepath)
            all_issues.extend(issues)

    # Check for example persona names (warnings only)
    for rel_path in KEY_FILES:
        if rel_path in PERSONA_EXCLUDE_FILES:
            continue  # Skip docs that intentionally explain the convention
        filepath = WORKSPACE / rel_path
        if not filepath.exists():
            continue
        content = filepath.read_text()
        rel = filepath.relative_to(WORKSPACE)
        for pattern, message in EXAMPLE_PERSONA_PATTERNS:
            matches = [
                i + 1
                for i, line in enumerate(content.splitlines())
                if re.search(pattern, line)
            ]
            if matches:
                lines_str = ", ".join(str(m) for m in matches[:5])
                all_warnings.append(f"  {rel}:{lines_str} — {message}")

    # Check that at least one per-user memory directory exists
    memory_dir = WORKSPACE / "memory"
    user_dirs = [
        d for d in memory_dir.iterdir()
        if d.is_dir() and d.name not in ("scripts", "docs", "curator_prompts")
    ]
    missing_user_dirs = not user_dirs

    # --- Output ---
    files_checked = len(KEY_FILES) + sum(
        1 for f in OPTIONAL_FILES if (WORKSPACE / f).exists()
    )

    if all_issues:
        print(f"ERRORS — {len(all_issues)} uncustomized placeholder(s):\n")
        for issue in all_issues:
            print(issue)
        print("\nReplace these placeholders with your actual values.")
        print("See QUICKSTART.md for customization instructions.")

    if all_warnings:
        label = "ERRORS (strict)" if args.strict else "WARNINGS"
        print(f"\n{label} — {len(all_warnings)} example persona name(s) (may need replacement):\n")
        for warning in all_warnings:
            print(warning)
        print("\nThese are example names — replace with your household's actual names.")
        print("See docs/NAME-CUSTOMIZATION.md for the full replacement workflow.")

    if missing_user_dirs:
        print("\n⚠️  No per-user memory directories found under memory/.")
        print("   Create them with: mkdir -p memory/<user1> memory/<user2>")
        print("   See docs/SETUP-GUIDE.md for setup instructions.")

    # Summary
    print(f"\n--- Summary ---")
    print(f"Files checked: {files_checked}")
    print(f"Errors (placeholders): {len(all_issues)}")
    print(f"Warnings (persona names): {len(all_warnings)}")
    print(f"User memory dirs: {'none found' if missing_user_dirs else ', '.join(d.name for d in user_dirs)}")

    if all_issues:
        print("\nResult: FAIL — fix placeholder errors above before deploying.")
        sys.exit(1)
    elif all_warnings and args.strict:
        print("\nResult: FAIL (strict) — persona names still present in non-doc files.")
        sys.exit(1)
    elif all_warnings:
        print("\nResult: PASS (with warnings) — no placeholders remaining. ✓")
        print("Review persona warnings above if this is a new deployment.")
        sys.exit(0)
    else:
        print("\nResult: PASS — all placeholders have been customized. ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
