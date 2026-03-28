#!/usr/bin/env python3
"""
Retrieve all turns from a specific session, ordered chronologically.

Given a session_id, queries both Qdrant collections (raw archive and true_recall)
to reconstruct the full conversation context for that session.

Usage:
    python3 get_session_context.py --session-id abc123
    python3 get_session_context.py --session-id abc123 --user-id alice --json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from typing import List, Dict, Any

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
RAW_COLLECTION = os.getenv("QDRANT_COLLECTION", "agent-memories")
GEM_COLLECTION = os.getenv("TRUE_RECALL_COLLECTION", "true_recall")


def qdrant_scroll(collection: str, filters: List[dict], limit: int = 200) -> List[dict]:
    """Scroll through Qdrant points matching the given filters."""
    data = {
        "limit": limit,
        "with_payload": True,
        "filter": {"must": filters},
    }
    try:
        req = urllib.request.Request(
            f"{QDRANT_URL}/collections/{collection}/points/scroll",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("result", {}).get("points", [])
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"WARNING: Failed to query {collection}: {e}", file=sys.stderr)
        return []


def get_session_turns(session_id: str, user_id: str = None) -> List[Dict[str, Any]]:
    """Get all turns from a session, ordered by timestamp."""
    filters = [{"key": "session_id", "match": {"value": session_id}}]
    if user_id:
        filters.append({"key": "user_id", "match": {"value": user_id}})

    # Query raw archive (full turns)
    raw_points = qdrant_scroll(RAW_COLLECTION, filters)

    turns = []
    for point in raw_points:
        payload = point.get("payload", {})
        turns.append({
            "text": payload.get("text", ""),
            "timestamp": payload.get("timestamp", ""),
            "source_type": payload.get("source_type", "unknown"),
            "user_id": payload.get("user_id", ""),
            "source": "raw_archive",
        })

    # Also check for gems from this session
    gem_points = qdrant_scroll(GEM_COLLECTION, filters)
    gems = []
    for point in gem_points:
        payload = point.get("payload", {})
        gems.append({
            "text": payload.get("gem", payload.get("text", "")),
            "timestamp": payload.get("timestamp", ""),
            "importance": payload.get("importance", "medium"),
            "confidence": payload.get("confidence", 0),
            "categories": payload.get("categories", []),
            "source": "true_recall",
        })

    # Sort turns by timestamp
    turns.sort(key=lambda t: t.get("timestamp", ""))
    gems.sort(key=lambda g: g.get("timestamp", ""))

    return turns, gems


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve full session context by session_id"
    )
    parser.add_argument("--session-id", required=True, help="Session ID to retrieve")
    parser.add_argument("--user-id", help="Filter to specific user")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    turns, gems = get_session_turns(args.session_id, args.user_id)

    if not turns and not gems:
        print(f"No data found for session: {args.session_id}")
        sys.exit(0)

    if args.json:
        print(json.dumps({"turns": turns, "gems": gems}, indent=2))
    else:
        print(f"Session: {args.session_id}")
        print(f"Turns: {len(turns)}, Gems: {len(gems)}")
        print("=" * 60)

        if turns:
            print("\n--- Conversation Turns ---")
            for t in turns:
                ts = t.get("timestamp", "?")[:19]
                role = t.get("source_type", "?")
                print(f"[{ts}] ({role}) {t['text'][:200]}")
                if len(t["text"]) > 200:
                    print("  ...")
                print()

        if gems:
            print("\n--- Extracted Gems ---")
            for g in gems:
                ts = g.get("timestamp", "?")[:19]
                imp = g.get("importance", "?")
                print(f"[{ts}] [{imp}] {g['text'][:200]}")
                if g.get("categories"):
                    print(f"  Categories: {', '.join(g['categories'])}")
                print()


if __name__ == "__main__":
    main()
