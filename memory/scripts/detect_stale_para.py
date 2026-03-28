#!/usr/bin/env python3
"""
Detect stale and contradictory facts in PARA items.json.

Staleness: Facts not verified within a configurable threshold are flagged.
Contradictions: Facts within the same category with overlapping keywords
are flagged as potential conflicts for human review.

This is a standalone auditing tool — it reads items.json but does not
modify it. Output goes to stdout (or --json for machine-readable output).
Use promote_to_para.py for active contradiction resolution during promotion.

Usage:
    python3 detect_stale_para.py --user-id alice
    python3 detect_stale_para.py --user-id alice --stale-days 90
    python3 detect_stale_para.py --user-id alice --check contradictions
    python3 detect_stale_para.py --user-id alice --check all --json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Tuple

SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
PROJECT_DIR = SCRIPT_DIR.parent  # memory/
PARA_DIR = PROJECT_DIR / "para"


def load_items(user_id: str) -> List[Dict[str, Any]]:
    """Load items.json for a user."""
    items_path = PARA_DIR / user_id / "items.json"
    if not items_path.exists():
        return []
    try:
        with open(items_path) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def detect_stale(items: List[Dict[str, Any]], stale_days: int) -> List[Dict[str, Any]]:
    """Find items not verified within stale_days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
    cutoff_str = cutoff.isoformat()
    stale = []
    for item in items:
        last_verified = item.get("last_verified", item.get("added", ""))
        if not last_verified or last_verified < cutoff_str:
            days_old = "unknown"
            if last_verified:
                try:
                    dt = datetime.fromisoformat(last_verified.replace("Z", "+00:00"))
                    days_old = (datetime.now(timezone.utc) - dt).days
                except ValueError:
                    pass
            stale.append({
                "id": item.get("id", "?"),
                "fact": item.get("fact", ""),
                "category": item.get("category", "other"),
                "last_verified": last_verified,
                "days_since_verified": days_old,
            })
    return stale


def normalize_fact(text: str) -> set:
    """Extract keywords from a fact for overlap comparison."""
    text = re.sub(r"[^\w\s]", "", text.lower())
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "has", "have", "had",
                 "be", "been", "being", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "can", "shall", "to", "of", "in", "for",
                 "on", "with", "at", "by", "from", "as", "into", "about", "that",
                 "this", "it", "its", "and", "or", "but", "not", "no", "user"}
    words = set(text.split()) - stopwords
    return words


def detect_contradictions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find potential contradictions — facts in the same category with high keyword overlap."""
    conflicts = []
    # Group by category
    by_category = {}
    for item in items:
        cat = item.get("category", "other")
        by_category.setdefault(cat, []).append(item)

    for cat, cat_items in by_category.items():
        if len(cat_items) < 2:
            continue
        # Compare each pair
        for i in range(len(cat_items)):
            kw_i = normalize_fact(cat_items[i].get("fact", ""))
            for j in range(i + 1, len(cat_items)):
                kw_j = normalize_fact(cat_items[j].get("fact", ""))
                overlap = kw_i & kw_j
                union = kw_i | kw_j
                if not union:
                    continue
                similarity = len(overlap) / len(union)
                # Flag pairs with moderate overlap (potential contradiction)
                if similarity >= 0.4 and len(overlap) >= 2:
                    conflicts.append({
                        "category": cat,
                        "similarity": round(similarity, 2),
                        "shared_keywords": sorted(overlap),
                        "fact_a": {
                            "id": cat_items[i].get("id", "?"),
                            "fact": cat_items[i].get("fact", ""),
                            "confidence": cat_items[i].get("confidence", 0),
                            "added": cat_items[i].get("added", ""),
                        },
                        "fact_b": {
                            "id": cat_items[j].get("id", "?"),
                            "fact": cat_items[j].get("fact", ""),
                            "confidence": cat_items[j].get("confidence", 0),
                            "added": cat_items[j].get("added", ""),
                        },
                    })

    conflicts.sort(key=lambda c: c["similarity"], reverse=True)
    return conflicts


def main():
    parser = argparse.ArgumentParser(
        description="Detect stale facts and contradictions in PARA items.json"
    )
    parser.add_argument("--user-id", required=True, help="User ID to audit")
    parser.add_argument(
        "--stale-days", type=int, default=90,
        help="Flag facts not verified in this many days (default: 90)"
    )
    parser.add_argument(
        "--check", choices=["stale", "contradictions", "all"], default="all",
        help="What to check (default: all)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    items = load_items(args.user_id)
    if not items:
        print(f"No items found for user '{args.user_id}'")
        sys.exit(0)

    results = {"user_id": args.user_id, "total_items": len(items)}

    if args.check in ("stale", "all"):
        stale = detect_stale(items, args.stale_days)
        results["stale"] = stale
        results["stale_count"] = len(stale)

    if args.check in ("contradictions", "all"):
        conflicts = detect_contradictions(items)
        results["contradictions"] = conflicts
        results["contradiction_count"] = len(conflicts)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"PARA Audit: {args.user_id} ({len(items)} items)")
        print("=" * 60)

        if "stale" in results:
            stale = results["stale"]
            print(f"\n⏰ Stale facts (not verified in {args.stale_days}+ days): {len(stale)}")
            if stale:
                for s in stale[:20]:
                    days = s["days_since_verified"]
                    print(f"  [{s['id']}] ({days}d) [{s['category']}] {s['fact'][:80]}")
                if len(stale) > 20:
                    print(f"  ... and {len(stale) - 20} more")

        if "contradictions" in results:
            conflicts = results["contradictions"]
            print(f"\n⚠️  Potential contradictions: {len(conflicts)}")
            if conflicts:
                for c in conflicts[:10]:
                    print(f"\n  [{c['category']}] Similarity: {c['similarity']}")
                    print(f"    A: [{c['fact_a']['id']}] {c['fact_a']['fact'][:70]}")
                    print(f"    B: [{c['fact_b']['id']}] {c['fact_b']['fact'][:70]}")
                    print(f"    Shared: {', '.join(c['shared_keywords'][:5])}")
                if len(conflicts) > 10:
                    print(f"\n  ... and {len(conflicts) - 10} more")

        if not results.get("stale") and not results.get("contradictions"):
            print("\n✅ No issues found.")


if __name__ == "__main__":
    main()
