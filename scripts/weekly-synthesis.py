#!/usr/bin/env python3
"""
Cross-evergreen weekly synthesis.

Scans all evergreens' agenda-history from the past 7 days, extracts cycle
summaries, and identifies shared themes via keyword overlap.

Output: evergreens/weekly-synthesis-YYYYMMDD.md

This runs as a standalone cron job (e.g., Sunday after daily cycles) or
can be called by the final-check script.

Usage:
    python3 scripts/weekly-synthesis.py [--days 7]
"""

import argparse
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from evergreen_utils import discover_evergreens, WORKSPACE, EVERGREENS_DIR

# Words to ignore when looking for cross-evergreen overlap
STOPWORDS = {
    "about", "above", "after", "again", "against", "before", "being",
    "below", "between", "could", "doing", "during", "every", "found",
    "further", "having", "itself", "might", "other", "should", "still",
    "their", "there", "these", "those", "through", "under", "until",
    "where", "which", "while", "would", "agenda", "cycle", "status",
    "completed", "started", "findings", "research", "analysis", "summary",
    "section", "tasks", "updated", "checked", "review", "notes",
    "details", "current", "previous", "today", "results", "tested",
    "running", "configuration", "successfully", "identified", "documented",
}

MIN_WORD_LEN = 6


def extract_summary_from_agenda(text: str) -> str:
    """Extract Cycle Summary or Research Findings section from an agenda."""
    for heading in ("Cycle Summary", "Research Findings", "Key Insights"):
        pattern = re.compile(
            rf"^##\s+{re.escape(heading)}\b.*$", re.MULTILINE
        )
        match = pattern.search(text)
        if not match:
            continue
        start = match.end()
        # Find next heading
        next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
        end = start + next_heading.start() if next_heading else len(text)
        content = text[start:end].strip()
        # Skip if essentially empty
        stripped = re.sub(r"[\s\-\*]", "", content)
        if len(stripped) > 20:
            # Cap at ~20 lines
            lines = content.split("\n")[:20]
            return "\n".join(lines)
    return ""


def get_significant_words(text: str) -> set[str]:
    """Extract significant words for overlap detection."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]*", text.lower())
    return {
        w for w in words
        if len(w) >= MIN_WORD_LEN and w not in STOPWORDS
    }


def main():
    parser = argparse.ArgumentParser(description="Cross-evergreen weekly synthesis")
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    args = parser.parse_args()

    cutoff = datetime.now() - timedelta(days=args.days)
    today = datetime.now().strftime("%Y%m%d")
    today_iso = datetime.now().strftime("%Y-%m-%d")

    evergreens = discover_evergreens()
    if not evergreens:
        print("No evergreens found", file=sys.stderr)
        return 1

    # Collect summaries per evergreen
    findings: dict[str, list[tuple[str, str]]] = {}  # name -> [(date, summary)]
    words_per_evergreen: dict[str, set[str]] = {}

    for name in evergreens:
        history_dir = EVERGREENS_DIR / name / "agenda-history"
        if not history_dir.exists():
            continue

        summaries = []
        all_words: set[str] = set()

        for archive_file in sorted(history_dir.glob("*.md")):
            # Try to extract date from filename
            date_match = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", archive_file.stem)
            if not date_match:
                continue
            try:
                file_date = datetime(
                    int(date_match.group(1)),
                    int(date_match.group(2)),
                    int(date_match.group(3)),
                )
            except ValueError:
                continue

            if file_date < cutoff:
                continue

            try:
                text = archive_file.read_text()
            except OSError:
                continue

            summary = extract_summary_from_agenda(text)
            if summary:
                date_str = file_date.strftime("%Y-%m-%d")
                summaries.append((date_str, summary))
                all_words |= get_significant_words(summary)

        if summaries:
            findings[name] = summaries
            words_per_evergreen[name] = all_words

    if not findings:
        print("No recent agenda summaries found across any evergreen")
        return 0

    # Detect keyword overlap across evergreens
    word_sources: dict[str, list[str]] = {}  # word -> [evergreen names]
    for name, words in words_per_evergreen.items():
        for w in words:
            word_sources.setdefault(w, []).append(name)

    shared_keywords = {
        word: sources
        for word, sources in word_sources.items()
        if len(sources) >= 2
    }

    # Rank by how many evergreens share the keyword
    ranked_shared = sorted(
        shared_keywords.items(),
        key=lambda x: (-len(x[1]), x[0]),
    )

    # Build output
    output_lines = [
        f"# Weekly Synthesis — {today_iso}",
        "",
        f"_Auto-generated from agenda-history across {len(findings)} evergreen(s) "
        f"(past {args.days} days). Read during Level-Set for cross-cutting context._",
        "",
    ]

    # Cross-cutting themes section
    if ranked_shared:
        output_lines.append("## Cross-Cutting Themes")
        output_lines.append("")
        output_lines.append(
            "Keywords appearing in 2+ evergreens' findings this week:"
        )
        output_lines.append("")
        shown = 0
        for word, sources in ranked_shared:
            if shown >= 15:
                break
            source_str = ", ".join(sorted(sources))
            output_lines.append(f"- **{word}** — {source_str}")
            shown += 1
        output_lines.append("")
    else:
        output_lines.append("## Cross-Cutting Themes")
        output_lines.append("")
        output_lines.append("_No significant keyword overlap detected this week._")
        output_lines.append("")

    # Per-evergreen summaries
    output_lines.append("## Per-Evergreen Highlights")
    output_lines.append("")

    for name in evergreens:
        if name not in findings:
            continue
        output_lines.append(f"### {name}")
        output_lines.append("")
        for date_str, summary in findings[name]:
            output_lines.append(f"**{date_str}:**")
            # Indent summary lines for readability
            for line in summary.split("\n")[:10]:
                if line.strip():
                    output_lines.append(f"> {line}")
            output_lines.append("")
        output_lines.append("")

    output_lines.append(
        f"---\n_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by weekly-synthesis.py_"
    )

    # Write output
    output_file = EVERGREENS_DIR / f"weekly-synthesis-{today}.md"
    output_file.write_text("\n".join(output_lines))
    print(f"Weekly synthesis written to {output_file}")

    # Clean up old synthesis files (>30 days)
    for old_file in EVERGREENS_DIR.glob("weekly-synthesis-*.md"):
        date_match = re.search(r"(\d{8})", old_file.name)
        if date_match:
            try:
                file_date = datetime.strptime(date_match.group(1), "%Y%m%d")
                if file_date < datetime.now() - timedelta(days=30):
                    old_file.unlink()
                    print(f"Cleaned up old synthesis: {old_file.name}")
            except ValueError:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
