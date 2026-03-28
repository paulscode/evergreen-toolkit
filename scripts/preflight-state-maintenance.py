#!/usr/bin/env python3
"""
Pre-session state maintenance for evergreen cycles.

Runs before the AI agent session to keep STATE.md lean and surface stuck work.
Called by evergreen-ai-runner.sh as part of the pre-flight phase.

Operations:
  1. Key Learnings compaction — entries older than 14 days are moved to
     a monthly archive file (LEARNINGS-ARCHIVE-YYYY-MM.md).
  2. Stale item detection — Next Steps items that appear in 3+ consecutive
     agenda-history archives are annotated with a staleness marker.

Usage:
    python3 scripts/preflight-state-maintenance.py <evergreen-dir>

Exit codes:
    0 — maintenance completed (or nothing to do)
    1 — fatal error (evergreen dir missing, STATE.md missing, etc.)
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_dated_learnings(state_text: str) -> tuple[str, list[tuple[str, str, str]], str]:
    """Extract Key Learnings section and parse dated entries.

    Returns (before_section, entries, after_section) where each entry is
    (full_line, date_str, content).
    """
    lines = state_text.split("\n")
    section_start = None
    section_end = None

    for i, line in enumerate(lines):
        if re.match(r"^##\s+Key\s+Learnings", line, re.IGNORECASE):
            section_start = i
        elif section_start is not None and re.match(r"^##\s+", line) and i > section_start:
            section_end = i
            break

    if section_start is None:
        return state_text, [], ""

    if section_end is None:
        section_end = len(lines)

    before = "\n".join(lines[: section_start + 1])
    after = "\n".join(lines[section_end:])
    section_lines = lines[section_start + 1 : section_end]

    # Parse entries like "- YYYY-MM-DD: ..." or "- [YYYY-MM-DD] ..."
    date_pattern = re.compile(
        r"^-\s+[\[\(]?(\d{4}-\d{2}-\d{2})[\]\)]?\s*:?\s*(.*)"
    )
    entries = []
    for line in section_lines:
        m = date_pattern.match(line.strip()) if line.strip() else None
        if m:
            entries.append((line, m.group(1), m.group(2)))
        elif line.strip():
            # Non-dated line — keep it (treat as undated, never archive)
            entries.append((line, "", ""))

    return before, entries, after


def compact_learnings(evergreen_dir: Path, max_age_days: int = 14) -> int:
    """Move Key Learnings older than max_age_days to monthly archive.

    Returns count of archived entries.
    """
    state_file = evergreen_dir / "STATE.md"
    state_text = state_file.read_text()

    before, entries, after = parse_dated_learnings(state_text)
    if not entries:
        return 0

    cutoff = datetime.now() - timedelta(days=max_age_days)
    keep = []
    archive: dict[str, list[str]] = {}  # month_key -> lines

    for full_line, date_str, _content in entries:
        if not date_str:
            # Undated entry — always keep
            keep.append(full_line)
            continue
        try:
            entry_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            keep.append(full_line)
            continue

        if entry_date < cutoff:
            month_key = entry_date.strftime("%Y-%m")
            archive.setdefault(month_key, []).append(full_line)
        else:
            keep.append(full_line)

    if not archive:
        return 0

    # Write archived entries to monthly files
    for month_key, lines in archive.items():
        archive_file = evergreen_dir / f"LEARNINGS-ARCHIVE-{month_key}.md"
        if archive_file.exists():
            existing = archive_file.read_text()
            if not existing.endswith("\n"):
                existing += "\n"
        else:
            existing = f"# Archived Key Learnings — {month_key}\n\n"
        existing += "\n".join(lines) + "\n"
        archive_file.write_text(existing)

    # Rebuild STATE.md with only recent learnings
    keep_section = "\n".join(keep)
    # Ensure proper spacing
    if keep_section.strip():
        new_state = f"{before}\n{keep_section}\n\n{after}"
    else:
        new_state = f"{before}\n\n{after}"

    # Normalize multiple blank lines to at most two
    new_state = re.sub(r"\n{3,}", "\n\n", new_state)
    state_file.write_text(new_state)

    total_archived = sum(len(v) for v in archive.values())
    return total_archived


def detect_stale_items(evergreen_dir: Path, threshold: int = 3) -> int:
    """Scan Next Steps for items stuck across multiple agenda archives.

    Annotates stale items in STATE.md with a marker like:
      ⚠️ STALE (5 cycles) — [original item]

    Returns count of newly-annotated items.
    """
    state_file = evergreen_dir / "STATE.md"
    history_dir = evergreen_dir / "agenda-history"

    if not history_dir.exists():
        return 0

    state_text = state_file.read_text()

    # Find Next Steps section
    lines = state_text.split("\n")
    section_start = None
    section_end = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Next\s+Steps", line, re.IGNORECASE):
            section_start = i
        elif section_start is not None and re.match(r"^##\s+", line) and i > section_start:
            section_end = i
            break

    if section_start is None:
        return 0
    if section_end is None:
        section_end = len(lines)

    # Extract current Next Steps items (stripped of checkboxes, numbers, markers)
    item_pattern = re.compile(r"^[\s]*(?:\d+\.?\s*)?(?:\[.\]\s*)?(?:⚠️\s*STALE\s*\(\d+\s*cycles?\)\s*)?(.+)")
    next_items = []
    for i in range(section_start + 1, section_end):
        line = lines[i].strip()
        if not line:
            continue
        m = item_pattern.match(line)
        if m:
            # Normalize: strip leading/trailing whitespace, lowercase for matching
            core_text = m.group(1).strip()
            next_items.append((i, core_text))

    if not next_items:
        return 0

    # Get recent agenda-history files sorted by date (newest first)
    archive_files = sorted(history_dir.glob("*.md"), reverse=True)
    # Only look at most recent 10 archives for performance
    archive_files = archive_files[:10]

    if not archive_files:
        return 0

    # Read archive contents
    archive_texts = []
    for af in archive_files:
        try:
            archive_texts.append(af.read_text())
        except OSError:
            continue

    # For each Next Steps item, count how many archives mention it
    annotated_count = 0
    for line_idx, core_text in next_items:
        # Build search terms: use significant words (>4 chars) from the item
        words = [w for w in re.findall(r"[a-zA-Z0-9_-]+", core_text) if len(w) > 4]
        if not words:
            continue

        # Count archives where a majority of significant words appear
        match_count = 0
        match_threshold = max(1, len(words) // 2)  # at least half the words must match
        for text in archive_texts:
            text_lower = text.lower()
            matching_words = sum(1 for w in words if w.lower() in text_lower)
            if matching_words >= match_threshold:
                match_count += 1

        if match_count >= threshold:
            original_line = lines[line_idx]
            # Don't double-annotate
            if "⚠️ STALE" in original_line:
                # Update the count if it changed
                old_marker = re.search(r"⚠️\s*STALE\s*\(\d+\s*cycles?\)", original_line)
                if old_marker:
                    new_marker = f"⚠️ STALE ({match_count} cycles)"
                    lines[line_idx] = original_line.replace(old_marker.group(), new_marker)
                continue

            # Insert marker before the item text
            # Preserve leading whitespace and checkbox
            prefix_match = re.match(r"^([\s]*(?:\d+\.?\s*)?(?:\[.\]\s*)?)", original_line)
            prefix = prefix_match.group(1) if prefix_match else ""
            rest = original_line[len(prefix):]
            lines[line_idx] = f"{prefix}⚠️ STALE ({match_count} cycles) {rest}"
            annotated_count += 1

    if annotated_count > 0:
        state_file.write_text("\n".join(lines))

    return annotated_count


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <evergreen-dir>", file=sys.stderr)
        return 1

    evergreen_dir = Path(sys.argv[1])
    if not evergreen_dir.is_dir():
        print(f"Error: not a directory: {evergreen_dir}", file=sys.stderr)
        return 1

    state_file = evergreen_dir / "STATE.md"
    if not state_file.exists():
        print(f"Error: STATE.md not found in {evergreen_dir}", file=sys.stderr)
        return 1

    name = evergreen_dir.name

    # P1 + P6: Compact old learnings into monthly archives
    archived = compact_learnings(evergreen_dir)
    if archived:
        print(f"[{name}] Archived {archived} old learning(s) to monthly file(s)")

    # P2: Detect stale Next Steps items
    stale = detect_stale_items(evergreen_dir)
    if stale:
        print(f"[{name}] Annotated {stale} stale Next Steps item(s)")

    if not archived and not stale:
        print(f"[{name}] No maintenance needed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
