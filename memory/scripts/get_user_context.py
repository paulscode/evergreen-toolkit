#!/usr/bin/env python3
"""
Quick user context for email replies.
Returns recent memory summary, not full conversations.
"""

import json
import os
import sys
import urllib.request
from typing import Optional

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "agent-memories")
WORKSPACE = os.getenv("OPENCLAW_WORKSPACE", os.path.join(os.path.expanduser("~"), ".openclaw/workspace"))
TOOLKIT_DIR = os.getenv("EVERGREEN_TOOLKIT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PARA_DIR = os.path.join(TOOLKIT_DIR, "memory", "para")


def get_para_summary(user_id: str) -> str:
    """Read the user's PARA summary.md if it exists."""
    summary_path = os.path.join(PARA_DIR, user_id, "summary.md")
    if not os.path.exists(summary_path):
        return ""
    try:
        with open(summary_path, 'r') as f:
            content = f.read().strip()
        # Skip template-only content
        if not content or "Not yet known" in content and len(content) < 500:
            return ""
        # Return first ~500 chars of summary (enough for context injection)
        return content[:500]
    except OSError:
        return ""

def get_user_context(user_id: str, limit: int = 5) -> str:
    """Get recent context for user - returns formatted summary."""
    
    # Check PARA first (canonical source of truth)
    para_summary = get_para_summary(user_id)

    # Use scroll to get recent memories for user
    data = json.dumps({
        "limit": 10,  # Get more to find profile
        "with_payload": True,
        "filter": {
            "must": [
                {"key": "user_id", "match": {"value": user_id}}
            ]
        }
    }).encode()

    req = urllib.request.Request(
        f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            points = result.get("result", {}).get("points", [])

        if not points:
            return ""

        # Prioritize: 1) Profile info, 2) Recent user message, 3) Recent context
        profile = None
        recent_user = None
        recent_context = []

        for point in points:
            payload = point.get("payload", {})
            text = payload.get("text", "")
            source_type = payload.get("source_type", "")
            
            # Look for profile (contains "Profile" or key identifying info)
            if "profile" in text.lower() or "lives in" in text.lower():
                profile = text[:200]
            elif source_type == "user" and not recent_user:
                recent_user = text[:150]
            elif source_type in ["assistant", "system"]:
                clean = text.replace("\r\n", " ").replace("\n", " ")[:150]
                recent_context.append(clean)

        # Build output: PARA first (canonical), then profile, then recent context
        parts = []
        if para_summary:
            parts.append(f"[PARA] {para_summary[:300]}")
        if profile:
            parts.append(f"[PROFILE] {profile}")
        if recent_user:
            parts.append(f"[USER] {recent_user}")
        if recent_context:
            parts.append(f"[CONTEXT] {recent_context[0][:100]}")

        return " || ".join(parts) if parts else ""

    except Exception as e:
        return ""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Get quick user context")
    parser.add_argument("--user-id", required=True, help="User ID")
    parser.add_argument("--limit", type=int, default=5, help="Max memories")
    args = parser.parse_args()

    context = get_user_context(args.user_id, args.limit)
    if context:
        print(context)