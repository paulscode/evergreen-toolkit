#!/usr/bin/env python3
"""
Promote durable facts from True Recall gems to PARA items.json.

Reads recent gems from Qdrant true_recall collection, uses an LLM to extract
atomic facts, and merges them into the user's PARA items.json with tiered
contradiction resolution.

Contradiction tiers:
  Tier 1 (auto-supersede): Timestamps, versions, counts — newer wins silently.
  Tier 2 (auto-supersede + log): Preferences, opinions — newer wins, logged.
  Tier 3 (conversational review): Relationships, identity — queued for human review.

Usage:
    python3 promote_to_para.py --user-id alice
    python3 promote_to_para.py --user-id alice --hours 168  # Last 7 days
    python3 promote_to_para.py --user-id alice --dry-run
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
TRUE_RECALL_COLLECTION = os.getenv("TRUE_RECALL_COLLECTION", "true_recall")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/").removesuffix("/v1")
CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3:4b")

# Paths
SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
PROJECT_DIR = SCRIPT_DIR.parent  # memory/
TOOLKIT_DIR = PROJECT_DIR.parent  # evergreen-toolkit/
PARA_DIR = Path(os.getenv("PARA_DIR", str(PROJECT_DIR / "para")))

# Contradiction tier categories
TIER1_CATEGORIES = {"timestamp", "version", "count", "date", "status", "metric"}
TIER2_CATEGORIES = {"preference", "opinion", "habit", "routine", "interest", "goal"}
TIER3_CATEGORIES = {"relationship", "identity", "role", "family", "medical", "legal"}

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

EXTRACTION_PROMPT = """You are a fact extractor. Given a set of conversation gems (curated memory highlights), extract atomic, durable facts worth preserving long-term.

For each fact, output a JSON array of objects with these fields:
- "fact": The atomic fact statement (one sentence, present tense)
- "category": One of: preference, relationship, identity, routine, goal, interest, opinion, medical, family, work, technical, status, metric, date, version, count, timestamp, habit, role, legal, other
- "confidence": 0.0 to 1.0 (how certain is this fact?)
- "tags": Array of keyword tags

Rules:
- Only extract facts that are DURABLE (likely true for weeks/months, not transient)
- One fact per object — no compound facts
- Present tense ("Alice likes X" not "Alice said she likes X")
- Include the person's name when relevant
- Skip greetings, pleasantries, and transient conversation details
- If no durable facts, return an empty array []

Output ONLY the JSON array, no other text.

Gems to process:
{gems}"""


def qdrant_request(method: str, path: str, data: Optional[dict] = None) -> dict:
    """Make a request to Qdrant API."""
    url = f"{QDRANT_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"ERROR: Qdrant request failed: {e}", file=sys.stderr)
        return {}


def fetch_recent_gems(user_id: str, hours: int = 168) -> List[Dict[str, Any]]:
    """Fetch recent gems from True Recall for a user."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    cutoff_str = cutoff.isoformat()

    data = {
        "limit": 200,
        "with_payload": True,
        "filter": {
            "must": [
                {"key": "user_id", "match": {"value": user_id}},
                {"key": "timestamp", "range": {"gte": cutoff_str}},
            ]
        },
    }
    result = qdrant_request("POST", f"/collections/{TRUE_RECALL_COLLECTION}/points/scroll", data)
    points = result.get("result", {}).get("points", [])
    return [p.get("payload", {}) for p in points]


def extract_facts_via_llm(gems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use LLM to extract atomic facts from gems."""
    if not gems:
        return []

    gems_text = "\n\n".join(
        f"- {g.get('text', g.get('content', g.get('fact', str(g))))}"
        for g in gems
    )

    prompt = EXTRACTION_PROMPT.format(gems=gems_text)

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
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            response_text = result.get("message", {}).get("content", "")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"ERROR: LLM request failed: {e}", file=sys.stderr)
        return []

    # Parse JSON from response (handle markdown code blocks)
    response_text = response_text.strip()
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if json_match:
        try:
            facts = json.loads(json_match.group())
            if isinstance(facts, list):
                return facts
        except json.JSONDecodeError:
            pass

    print(f"WARNING: Could not parse LLM response as JSON array", file=sys.stderr)
    return []


def load_items(user_id: str) -> List[Dict[str, Any]]:
    """Load existing items.json for a user."""
    items_path = PARA_DIR / user_id / "items.json"
    if not items_path.exists():
        return []
    try:
        with open(items_path) as f:
            items = json.load(f)
            return items if isinstance(items, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_items(user_id: str, items: List[Dict[str, Any]]) -> None:
    """Save items.json for a user."""
    items_path = PARA_DIR / user_id / "items.json"
    items_path.parent.mkdir(parents=True, exist_ok=True)
    with open(items_path, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def get_contradiction_tier(category: str) -> int:
    """Determine which contradiction resolution tier a category belongs to."""
    cat = category.lower()
    if cat in TIER1_CATEGORIES:
        return 1
    if cat in TIER2_CATEGORIES:
        return 2
    if cat in TIER3_CATEGORIES:
        return 3
    return 2  # Default to tier 2 for unknown categories


def find_contradictions(
    new_fact: Dict[str, Any], existing_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Find existing items that might contradict the new fact.

    Uses simple keyword overlap heuristic. A more sophisticated implementation
    could use embeddings for semantic similarity.
    """
    new_words = set(new_fact.get("fact", "").lower().split())
    # Remove very common words
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                 "to", "for", "of", "and", "or", "but", "not", "with", "has", "have"}
    new_words -= stopwords

    contradictions = []
    for item in existing_items:
        existing_words = set(item.get("fact", "").lower().split()) - stopwords
        overlap = new_words & existing_words
        # If >40% word overlap, likely same topic — potential contradiction
        if len(new_words) > 0 and len(overlap) / len(new_words) > 0.4:
            contradictions.append(item)

    return contradictions


def regenerate_summary(user_id: str, items: List[Dict[str, Any]]) -> bool:
    """Regenerate summary.md from current items.json via LLM."""
    if not items:
        return False
    facts_text = "\n".join(f"- {f.get('fact', '')}" for f in items[:50])
    prompt = SUMMARY_PROMPT.format(facts=facts_text)

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
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            summary_text = result.get("message", {}).get("content", "")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"WARNING: Could not regenerate summary.md: {e}", file=sys.stderr)
        return False

    if not summary_text.strip():
        print("WARNING: LLM returned empty summary, keeping existing summary.md", file=sys.stderr)
        return False

    summary_path = PARA_DIR / user_id / "summary.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"# {user_id} — Summary\n\n"
    header += f"*Auto-generated by promote_to_para.py on {now}*\n\n"
    with open(summary_path, "w") as f:
        f.write(header + summary_text.strip() + "\n")
    return True


def append_to_review_queue(user_id: str, new_fact: Dict, conflicts: List[Dict]) -> None:
    """Add a Tier 3 contradiction to the user's review queue."""
    queue_path = PARA_DIR / user_id / "review-queue.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    entry = f"\n## Review needed — {now}\n\n"
    entry += f"**New fact:** {new_fact.get('fact', '')}\n"
    entry += f"**Category:** {new_fact.get('category', 'unknown')}\n"
    entry += f"**Confidence:** {new_fact.get('confidence', '?')}\n\n"
    entry += "**Potentially conflicts with:**\n"
    for c in conflicts:
        entry += f"- [{c.get('id', '?')}] {c.get('fact', '')}\n"
    entry += "\n**Action needed:** Confirm which is correct during next conversation.\n"
    entry += "---\n"

    with open(queue_path, "a") as f:
        f.write(entry)


def merge_fact(
    new_fact: Dict[str, Any],
    existing_items: List[Dict[str, Any]],
    user_id: str,
    dry_run: bool = False,
) -> tuple:
    """Merge a new fact into existing items with contradiction resolution.

    Returns (action, item) where action is 'added', 'superseded', 'queued', or 'skipped'.
    """
    category = new_fact.get("category", "other")
    tier = get_contradiction_tier(category)
    conflicts = find_contradictions(new_fact, existing_items)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    item = {
        "id": str(uuid.uuid4())[:8],
        "fact": new_fact.get("fact", ""),
        "category": category,
        "source": "promote_to_para",
        "confidence": new_fact.get("confidence", 0.7),
        "supersedes": None,
        "added": now,
        "last_verified": now,
        "tags": new_fact.get("tags", []),
    }

    if not conflicts:
        if not dry_run:
            existing_items.append(item)
        return "added", item

    if tier == 1:
        # Auto-supersede silently — newer wins
        for c in conflicts:
            item["supersedes"] = c.get("id")
            if not dry_run:
                existing_items.remove(c)
        if not dry_run:
            existing_items.append(item)
        return "superseded", item

    if tier == 2:
        # Auto-supersede with logging
        for c in conflicts:
            item["supersedes"] = c.get("id")
            if not dry_run:
                existing_items.remove(c)
        if not dry_run:
            existing_items.append(item)
        return "superseded", item

    # Tier 3 — queue for review
    if not dry_run:
        append_to_review_queue(user_id, new_fact, conflicts)
    return "queued", item


def main():
    parser = argparse.ArgumentParser(
        description="Promote durable facts from True Recall gems to PARA"
    )
    parser.add_argument(
        "--user-id", required=True, help="User ID to promote facts for"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=168,
        help="Look back this many hours for gems (default: 168 = 7 days)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be promoted without making changes",
    )
    args = parser.parse_args()

    user_id = args.user_id
    para_user_dir = PARA_DIR / user_id

    if not para_user_dir.exists():
        print(f"ERROR: PARA directory not found: {para_user_dir}", file=sys.stderr)
        print(f"Run seed_para.py --users {user_id} first.", file=sys.stderr)
        sys.exit(1)

    # 1. Fetch recent gems
    print(f"Fetching gems for [{user_id}] from last {args.hours}h...")
    gems = fetch_recent_gems(user_id, args.hours)
    if not gems:
        print("No recent gems found. Nothing to promote.")
        return

    print(f"Found {len(gems)} gem(s). Extracting facts via LLM...")

    # 2. Extract atomic facts
    new_facts = extract_facts_via_llm(gems)
    if not new_facts:
        print("No durable facts extracted. Nothing to promote.")
        return

    print(f"Extracted {len(new_facts)} fact(s).")

    # 3. Load existing items
    existing_items = load_items(user_id)
    print(f"Existing PARA items: {len(existing_items)}")

    # 4. Merge with contradiction resolution
    stats = {"added": 0, "superseded": 0, "queued": 0, "skipped": 0}
    for fact in new_facts:
        action, item = merge_fact(fact, existing_items, user_id, dry_run=args.dry_run)
        stats[action] += 1
        prefix = "[dry-run] " if args.dry_run else ""
        if action == "added":
            print(f"  {prefix}+ Added: {item['fact'][:80]}")
        elif action == "superseded":
            print(f"  {prefix}↻ Superseded: {item['fact'][:80]}")
        elif action == "queued":
            print(f"  {prefix}? Queued for review: {item['fact'][:80]}")

    # 5. Save
    if not args.dry_run:
        save_items(user_id, existing_items)
        print(f"\nSaved {len(existing_items)} items to {para_user_dir / 'items.json'}")

        # 6. Regenerate summary.md if facts changed
        if stats['added'] > 0 or stats['superseded'] > 0:
            print("Regenerating summary.md...")
            if regenerate_summary(user_id, existing_items):
                print(f"Updated {para_user_dir / 'summary.md'}")
            else:
                print("Summary regeneration skipped (LLM unavailable or empty response)")

    print(f"\nSummary: +{stats['added']} added, ↻{stats['superseded']} superseded, "
          f"?{stats['queued']} queued for review")


if __name__ == "__main__":
    main()
