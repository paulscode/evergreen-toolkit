#!/usr/bin/env python3
"""
One-time migration: Extract durable facts from existing memory into PARA.

Reads a user's existing daily markdown files and/or an existing MEMORY.md,
uses an LLM to draft structured facts, and populates PARA items.json + summary.md.

This is a DRAFT tool — outputs are meant for human review before finalization.
Generated files are written with a .draft suffix for review.

Usage:
    python3 migrate_memory_to_para.py --user-id alice
    python3 migrate_memory_to_para.py --user-id alice --source-dir memory/alice
    python3 migrate_memory_to_para.py --from-memory-md /path/to/MEMORY.md --user-id alice
    python3 migrate_memory_to_para.py --user-id alice --dry-run
"""

import argparse
import json
import os
import re
import sys
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/").removesuffix("/v1")
CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3:4b")

# Paths
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
PROJECT_DIR = SCRIPT_DIR.parent  # memory/
TOOLKIT_DIR = PROJECT_DIR.parent  # evergreen-toolkit/
PARA_DIR = PROJECT_DIR / "para"
WORKSPACE_DIR = Path(os.getenv("OPENCLAW_WORKSPACE", str(TOOLKIT_DIR.parent)))

EXTRACTION_PROMPT = """You are migrating an AI agent's memory into a structured knowledge base.
Given the following memory content about a user, extract ALL durable facts worth preserving.

For each fact, output a JSON array of objects with:
- "fact": Atomic fact statement (one sentence, present tense)
- "category": One of: preference, relationship, identity, routine, goal, interest, opinion, medical, family, work, technical, status, other
- "confidence": 0.0 to 1.0
- "tags": Array of keyword tags

Rules:
- Extract ALL facts, even minor ones — the user prefers comprehensive capture
- One fact per object — no compound facts
- Present tense ("User likes X" not "User said they like X")
- Include names and specifics when available
- Skip transient details (weather, what was for lunch today, etc.)

Output ONLY the JSON array, no other text.

Memory content:
{content}"""

SUMMARY_PROMPT = """You are writing a brief profile summary for a user based on extracted facts.

Write a concise markdown document with these sections:
- **Key Facts** (bullet points — the most important things to know)
- **Relationships** (family, friends, colleagues mentioned)
- **Active Focus** (current projects, goals, interests)
- **Communication Style** (how they prefer to interact, if known)

Keep each section to 3-5 bullet points max. If a section has no data, write "Not yet known."

Facts:
{facts}

Output ONLY the markdown content (no code fences), starting with the first section header."""

MAX_CONTENT_PER_BATCH = 4000  # Characters per LLM batch (conservative for cloud models)


def llm_generate(prompt: str) -> str:
    """Call Ollama to generate text. Uses chat API for cloud model compatibility."""
    payload = {
        "model": CURATION_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.1, "num_predict": 4096},
    }
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", "")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"ERROR: LLM request failed: {e}", file=sys.stderr)
        return ""


def read_daily_files(source_dir: Path, limit: int = 30) -> str:
    """Read the most recent daily markdown files from a user's memory directory."""
    md_files = sorted(source_dir.glob("*.md"), reverse=True)[:limit]
    content_parts = []
    for f in md_files:
        try:
            text = f.read_text(encoding="utf-8")
            if text.strip():
                content_parts.append(f"### {f.name}\n{text}")
        except OSError:
            continue
    return "\n\n".join(content_parts)


def read_memory_md(path: Path) -> str:
    """Read an existing MEMORY.md file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"ERROR: Cannot read {path}: {e}", file=sys.stderr)
        return ""


def extract_facts_from_content(content: str) -> List[Dict[str, Any]]:
    """Extract facts from content using LLM, processing in batches."""
    all_facts = []

    # Split content into batches
    batches = []
    current = ""
    for line in content.split("\n"):
        if len(current) + len(line) > MAX_CONTENT_PER_BATCH and current:
            batches.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        batches.append(current)

    for i, batch in enumerate(batches):
        print(f"  Processing batch {i + 1}/{len(batches)}...")
        prompt = EXTRACTION_PROMPT.format(content=batch)
        response = llm_generate(prompt)

        # Parse JSON from response
        response = response.strip()
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                facts = json.loads(json_match.group())
                if isinstance(facts, list):
                    all_facts.extend(facts)
                    print(f"    Extracted {len(facts)} fact(s)")
                    continue
            except json.JSONDecodeError:
                pass
        print(f"    WARNING: Could not parse batch {i + 1} response")

    return all_facts


def generate_summary(facts: List[Dict[str, Any]]) -> str:
    """Generate a summary.md from extracted facts."""
    facts_text = "\n".join(f"- {f.get('fact', '')}" for f in facts[:50])
    prompt = SUMMARY_PROMPT.format(facts=facts_text)
    return llm_generate(prompt).strip()


def deduplicate_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove near-duplicate facts based on normalized text."""
    seen = set()
    unique = []
    for f in facts:
        # Normalize: lowercase, strip punctuation, collapse whitespace
        key = re.sub(r'[^\w\s]', '', f.get("fact", "").lower())
        key = re.sub(r'\s+', ' ', key).strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def main():
    parser = argparse.ArgumentParser(
        description="Migrate existing memory data into PARA (draft output for review)"
    )
    parser.add_argument(
        "--user-id", required=True, help="User ID to migrate facts for"
    )
    parser.add_argument(
        "--source-dir",
        help="Directory containing daily markdown files (default: memory/<user-id>)",
    )
    parser.add_argument(
        "--from-memory-md",
        help="Path to an existing MEMORY.md to extract facts from",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=30,
        help="Maximum number of daily files to process (default: 30, most recent)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without writing files",
    )
    args = parser.parse_args()

    user_id = args.user_id
    para_user_dir = PARA_DIR / user_id

    if not para_user_dir.exists():
        print(f"ERROR: PARA directory not found: {para_user_dir}", file=sys.stderr)
        print(f"Run seed_para.py --users {user_id} first.", file=sys.stderr)
        sys.exit(1)

    # Collect source content
    content = ""
    if args.from_memory_md:
        md_path = Path(args.from_memory_md)
        print(f"Reading MEMORY.md from {md_path}...")
        content = read_memory_md(md_path)
    else:
        source = Path(args.source_dir) if args.source_dir else PROJECT_DIR / user_id
        if source.exists():
            print(f"Reading daily files from {source} (max {args.max_files})...")
            content = read_daily_files(source, limit=args.max_files)
        else:
            print(f"WARNING: Source directory not found: {source}", file=sys.stderr)

    if not content.strip():
        print("No content found to migrate. Provide --source-dir or --from-memory-md.")
        sys.exit(1)

    print(f"Collected {len(content)} characters of source content.")

    # Extract facts
    print("Extracting facts via LLM...")
    raw_facts = extract_facts_from_content(content)
    if not raw_facts:
        print("No facts extracted. The source content may be too sparse.")
        sys.exit(1)

    # Deduplicate
    facts = deduplicate_facts(raw_facts)
    print(f"Extracted {len(raw_facts)} raw facts, {len(facts)} after deduplication.")

    # Build items.json entries
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items = []
    for f in facts:
        items.append({
            "id": str(uuid.uuid4())[:8],
            "fact": f.get("fact", ""),
            "category": f.get("category", "other"),
            "source": "migration",
            "confidence": f.get("confidence", 0.6),
            "supersedes": None,
            "added": now,
            "last_verified": now,
            "tags": f.get("tags", []),
        })

    if args.dry_run:
        print(f"\n[dry-run] Would write {len(items)} items to items.json.draft")
        for item in items[:10]:
            print(f"  - [{item['category']}] {item['fact'][:80]}")
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more")
        return

    # Write draft files
    items_draft = para_user_dir / "items.json.draft"
    with open(items_draft, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(items)} items to {items_draft.relative_to(TOOLKIT_DIR)}")

    # Generate summary draft
    print("Generating summary draft...")
    summary = generate_summary(facts)
    if summary:
        summary_draft = para_user_dir / "summary.md.draft"
        header = f"# {user_id} — Summary\n\n"
        header += f"*Auto-generated by migrate_memory_to_para.py on {now}*\n"
        header += "*Review and edit before renaming to summary.md*\n\n"
        with open(summary_draft, "w") as f:
            f.write(header + summary + "\n")
        print(f"Wrote summary to {summary_draft.relative_to(TOOLKIT_DIR)}")

    print(f"\n{'='*60}")
    print("REVIEW REQUIRED: Draft files created with .draft suffix.")
    print("Steps:")
    print(f"  1. Review {items_draft.name} — remove incorrect facts, adjust confidence")
    print(f"  2. Review {para_user_dir.name}/summary.md.draft — edit for accuracy")
    print(f"  3. Rename: mv items.json.draft items.json")
    print(f"  4. Rename: mv summary.md.draft summary.md")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
