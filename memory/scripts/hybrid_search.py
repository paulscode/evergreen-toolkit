#!/usr/bin/env python3
"""
Hybrid search: Search both file-based memory and Qdrant vectors
Usage: hybrid_search.py "Query text" [--file-limit 3] [--vector-limit 3]
"""

import argparse
import json
import os
import subprocess
import sys
import re
from datetime import datetime, timedelta

WORKSPACE = os.environ.get("OPENCLAW_WORKSPACE", os.path.join(os.path.expanduser("~"), ".openclaw/workspace"))
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TOOLKIT_DIR = os.environ.get("EVERGREEN_TOOLKIT", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PARA_DIR = os.path.join(TOOLKIT_DIR, "memory", "para")

def search_para(query, user_id=None, limit=3):
    """Search PARA summary.md and items.json for keyword matches."""
    results = []
    query_lower = query.lower()
    keywords = set(query_lower.split())

    # Determine which PARA dirs to search
    dirs_to_search = []
    if user_id:
        dirs_to_search.append(os.path.join(PARA_DIR, user_id))
    dirs_to_search.append(os.path.join(PARA_DIR, "shared"))

    for para_path in dirs_to_search:
        # Search summary.md
        summary_path = os.path.join(para_path, "summary.md")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r') as f:
                    content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if any(kw in line.lower() for kw in keywords):
                        start = max(0, i - 1)
                        end = min(len(lines), i + 3)
                        context = '\n'.join(lines[start:end])
                        score = sum(1 for kw in keywords if kw in line.lower()) / len(keywords)
                        results.append({
                            "source": f"para:{summary_path}",
                            "date": "durable",
                            "score": score + 0.1,  # Slight boost for PARA (canonical)
                            "text": context.strip(),
                            "type": "para"
                        })
            except OSError:
                pass

        # Search items.json
        items_path = os.path.join(para_path, "items.json")
        if os.path.exists(items_path):
            try:
                with open(items_path, 'r') as f:
                    items = json.load(f)
                if isinstance(items, list):
                    for item in items:
                        fact = item.get("fact", "")
                        tags = " ".join(item.get("tags", []))
                        searchable = f"{fact} {tags}".lower()
                        if any(kw in searchable for kw in keywords):
                            score = sum(1 for kw in keywords if kw in searchable) / len(keywords)
                            results.append({
                                "source": f"para:{items_path}",
                                "date": item.get("last_verified", "durable"),
                                "score": score + 0.15,  # PARA facts are canonical
                                "text": f"[{item.get('category', 'other')}] {fact}",
                                "type": "para",
                                "confidence": item.get("confidence", 0.5)
                            })
            except (OSError, json.JSONDecodeError):
                pass

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def search_files(query, limit=3, user_id=None, days_back=1):
    """Search recent memory files for keyword matches"""
    results = []
    
    # Get recent memory files (last 30 days)
    files = []
    today = datetime.now()
    for i in range(30):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        # Check per-user directory first, then global
        if user_id:
            user_filepath = f"{MEMORY_DIR}/{user_id}/{date_str}.md"
            if os.path.exists(user_filepath):
                files.append((date_str, user_filepath))
                continue
        filepath = f"{MEMORY_DIR}/{date_str}.md"
        if os.path.exists(filepath):
            files.append((date_str, filepath))
    
    # Simple keyword search
    query_lower = query.lower()
    keywords = set(query_lower.split())
    
    for date_str, filepath in files[:days_back]:  # Check recent days
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Find sections that match
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(kw in line_lower for kw in keywords):
                    # Get context (3 lines before and after)
                    start = max(0, i - 3)
                    end = min(len(lines), i + 4)
                    context = '\n'.join(lines[start:end])
                    
                    # Simple relevance score based on keyword matches
                    score = sum(1 for kw in keywords if kw in line_lower) / len(keywords)
                    
                    results.append({
                        "source": f"file:{filepath}",
                        "date": date_str,
                        "score": score,
                        "text": context.strip(),
                        "type": "file"
                    })
                    
                    if len(results) >= limit * 2:  # Get more then dedupe
                        break
                        
        except Exception as e:
            continue
    
    # Sort by score and return top N
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def search_qdrant(query, limit=3, user_id=None):
    """Search Qdrant using the search_memories script"""
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_memories.py")
        cmd = ["python3", script_path, query, "--limit", str(limit), "--json"]
        if user_id:
            cmd.extend(["--user-id", user_id])
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            memories = json.loads(result.stdout)
            for m in memories:
                m["type"] = "vector"
                m["source"] = "qdrant"
            return memories
    except Exception as e:
        print(f"Qdrant search failed (falling back to files only): {e}", file=sys.stderr)
    
    return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hybrid memory search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--file-limit", type=int, default=3, help="Max file results")
    parser.add_argument("--vector-limit", type=int, default=3, help="Max vector results")
    parser.add_argument("--user-id", help="Filter results to this user")
    parser.add_argument("--days-back", type=int, default=1, help="Max number of recent daily files to search (default: 1, older days are in Qdrant)")
    parser.add_argument("--para-limit", type=int, default=3, help="Max PARA results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    print(f"Searching for: '{args.query}'" + (f" (user: {args.user_id})" if args.user_id else "") + "\n", file=sys.stderr)
    
    # Search all sources
    para_results = search_para(args.query, user_id=args.user_id, limit=args.para_limit)
    file_results = search_files(args.query, args.file_limit, user_id=args.user_id, days_back=args.days_back)
    vector_results = search_qdrant(args.query, args.vector_limit, user_id=args.user_id)
    
    # Combine results
    all_results = para_results + file_results + vector_results
    
    if not all_results:
        print("No memories found matching your query.")
        sys.exit(0)
    
    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        if para_results:
            print(f"📌 PARA (durable knowledge) results ({len(para_results)}):")
            print("-" * 50)
            for r in para_results:
                print(f"[{r.get('date', 'durable')}] Score: {r['score']:.2f}")
                print(r['text'][:300])
                if len(r['text']) > 300:
                    print("...")
                print()

        print(f"📁 File-based results ({len(file_results)}):")
        print("-" * 50)
        for r in file_results:
            print(f"[{r['date']}] Score: {r['score']:.2f}")
            print(r['text'][:300])
            if len(r['text']) > 300:
                print("...")
            print()
        
        print(f"\n🔍 Vector (Qdrant) results ({len(vector_results)}):")
        print("-" * 50)
        for r in vector_results:
            print(f"[{r.get('date', 'unknown')}] Score: {r.get('score', 0):.3f} [{r.get('importance', 'medium')}]")
            text = r.get('text', '')
            print(text[:300])
            if len(text) > 300:
                print("...")
            if r.get('tags'):
                print(f"Tags: {', '.join(r['tags'])}")
            print()
