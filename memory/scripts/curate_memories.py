#!/usr/bin/env python3
"""
True Recall Curator: User-Aware Gem Extraction

Reads 24 hours of conversation from Redis, processes as narrative,
extracts contextual gems using a local LLM, stores to Qdrant with Ollama embeddings.

KEY CHANGES FROM ORIGINAL:
- Does NOT clear Redis buffer (Jarvis Memory handles that)
- Loads user-specific curator prompts
- Includes user context in gems
- Outputs suggested categories for approval flow

Usage:
    python curate_memories.py --user-id USER_ID
    python curate_memories.py --user-id USER_ID --hours 48
    python curate_memories.py --user-id USER_ID --dry-run
"""

import json
import argparse
import redis
import requests
import yaml
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("TRUE_RECALL_COLLECTION", "true_recall")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "snowflake-arctic-embed2")
CURATION_MODEL = os.getenv("CURATION_MODEL", "qwen3:4b")

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)  # memory/
TOOLKIT_DIR = os.path.dirname(PROJECT_DIR)  # evergreen-toolkit/
WORKSPACE_DIR = os.getenv("OPENCLAW_WORKSPACE", os.path.dirname(TOOLKIT_DIR))
CURATOR_PROMPTS_DIR = os.path.join(PROJECT_DIR, "curator_prompts")
MEMORY_DIR = os.path.join(WORKSPACE_DIR, "memory")


def load_user_categories(user_id: str) -> Dict[str, Any]:
    """Load user's categories.yaml."""
    categories_path = os.path.join(MEMORY_DIR, user_id, "categories.yaml")
    if os.path.exists(categories_path):
        with open(categories_path, 'r') as f:
            return yaml.safe_load(f)
    return {"categories": {}, "suggestions": {}}


def load_user_context(user_id: str) -> Dict[str, Any]:
    """Load user context from categories.yaml."""
    categories = load_user_categories(user_id)
    return categories.get("user_context", {})


def load_curator_prompt(user_id: str) -> str:
    """Load the combined curator prompt (base + user-specific)."""
    # Load base prompt
    base_path = os.path.join(CURATOR_PROMPTS_DIR, "base.md")
    with open(base_path, 'r') as f:
        base_prompt = f.read()
    
    # Load user-specific prompt
    user_prompt_path = os.path.join(CURATOR_PROMPTS_DIR, f"{user_id}.md")
    if os.path.exists(user_prompt_path):
        with open(user_prompt_path, 'r') as f:
            user_prompt = f.read()
    else:
        user_prompt = ""
    
    # Load categories for this user
    categories = load_user_categories(user_id)
    category_list = []
    for cat_name, cat_data in categories.get("categories", {}).items():
        desc = cat_data.get("description", "")
        subs = cat_data.get("subcategories", [])
        if subs:
            category_list.append(f"- `{cat_name}`: {desc} (subcategories: {', '.join(subs)})")
        else:
            category_list.append(f"- `{cat_name}`: {desc}")
    
    categories_text = "\n".join(category_list) if category_list else "No categories defined."
    
    # Combine all parts
    combined = f"""{base_prompt}

---

{user_prompt}

---

## Available Categories for {user_id}

{categories_text}
"""
    return combined


def get_redis_client() -> redis.Redis:
    """Get Redis connection."""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )


def get_staged_turns(user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Get all staged turns from Redis for a user."""
    r = get_redis_client()
    key = f"mem:{user_id}"
    
    # Get all items from the list
    items = r.lrange(key, 0, -1)
    
    turns = []
    for item in items:
        try:
            turn = json.loads(item)
            # Filter by timestamp if needed
            if hours:
                ts = turn.get('timestamp', '')
                if ts:
                    # Handle various timestamp formats
                    if ts.endswith('Z'):
                        ts = ts[:-1] + '+00:00'
                    turn_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    cutoff = datetime.now(turn_time.tzinfo) - timedelta(hours=hours)
                    if turn_time >= cutoff:
                        turns.append(turn)
                else:
                    turns.append(turn)
            else:
                turns.append(turn)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Skipping invalid turn: {e}")
            continue
    
    # Sort by turn number
    turns.sort(key=lambda x: x.get('turn', 0))
    return turns


def extract_gems_with_curator(turns: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
    """Use qwen3 to extract gems from conversation turns."""
    if not turns:
        return {"gems": [], "suggested_categories": [], "suggested_subcategories": []}
    
    prompt = load_curator_prompt(user_id)
    
    # Build the conversation input
    conversation_json = json.dumps(turns, indent=2)
    
    # Call Ollama with native system prompt
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": CURATION_MODEL,
            "system": prompt,
            "prompt": f"## Input Conversation\n\n```json\n{conversation_json}\n```\n\n## Output\n",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 6000  # Increased for category suggestions
            }
        },
        timeout=300  # 5 minute timeout
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Curation failed: {response.text}")
    
    result = response.json()
    output = result.get('response', '').strip()
    
    # Extract JSON from output (handle markdown code blocks)
    if '```json' in output:
        output = output.split('```json')[1].split('```')[0].strip()
    elif '```' in output:
        output = output.split('```')[1].split('```')[0].strip()
    
    try:
        parsed = json.loads(output)
        
        # Handle both old format (list) and new format (object with gems)
        if isinstance(parsed, list):
            return {"gems": parsed, "suggested_categories": [], "suggested_subcategories": []}
        elif isinstance(parsed, dict):
            return {
                "gems": parsed.get("gems", []),
                "suggested_categories": parsed.get("suggested_categories", []),
                "suggested_subcategories": parsed.get("suggested_subcategories", [])
            }
        else:
            return {"gems": [], "suggested_categories": [], "suggested_subcategories": []}
            
    except json.JSONDecodeError as e:
        print(f"Error parsing curator output: {e}")
        print(f"Raw output: {output[:500]}...")
        return {"gems": [], "suggested_categories": [], "suggested_subcategories": []}


def get_embedding(text: str) -> List[float]:
    """Get embedding vector from Ollama using EMBEDDING_MODEL env var (default: snowflake-arctic-embed2)."""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text
        },
        timeout=60
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Embedding failed: {response.text}")
    
    return response.json()['embedding']


def ensure_collection_exists():
    """Ensure the true_recall collection exists in Qdrant."""
    response = requests.get(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}")
    if response.status_code == 404:
        print(f"📦 Creating collection: {QDRANT_COLLECTION}")
        create_response = requests.put(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}",
            json={
                "vectors": {
                    "size": int(os.getenv('EMBEDDING_DIMENSIONS', '1024')),
                    "distance": "Cosine"
                }
            }
        )
        if create_response.status_code != 200:
            raise RuntimeError(f"Failed to create collection: {create_response.text}")
        print("✅ Collection created")


def extract_mentioned_entities(gem: Dict[str, Any]) -> List[str]:
    """Extract mentioned entity names from a gem's text fields.

    Uses simple heuristics: capitalized multi-word names, single capitalized
    words that aren't sentence-starters, and known patterns like @mentions.
    """
    import re
    text = f"{gem.get('gem', '')} {gem.get('context', '')} {gem.get('snippet', '')}"
    entities = set()

    # Find capitalized names (2+ words, e.g. "John Smith", "Acme Corp")
    for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text):
        entities.add(match.group(1))

    # Find single capitalized words that look like proper nouns (not at sentence start)
    for match in re.finditer(r'(?<=[.!?]\s\w+\s|,\s|;\s|\band\s|\bor\s|\bwith\s)([A-Z][a-z]{2,})\b', text):
        entities.add(match.group(1))

    # Strip common false positives
    stop_entities = {"The", "This", "That", "These", "Those", "What", "When",
                     "Where", "Which", "True", "False", "None", "Yes", "Redis",
                     "Qdrant", "Ollama", "Python"}
    entities -= stop_entities

    return sorted(entities)


def store_gem_to_qdrant(gem: Dict[str, Any], user_id: str) -> bool:
    """Store a gem to Qdrant with embedding."""
    ensure_collection_exists()
    
    # Create embedding from gem text
    embedding_text = f"{gem['gem']} {gem['context']} {gem['snippet']}"
    vector = get_embedding(embedding_text)
    
    # Load user context to include in payload
    user_context = load_user_context(user_id)
    
    # Prepare payload
    payload = {
        "user_id": user_id,
        "user_context": user_context,
        "mentioned_entities": extract_mentioned_entities(gem),
        **gem
    }
    
    # Generate deterministic integer ID (Qdrant requires integer or UUID)
    import hashlib
    hash_bytes = hashlib.sha256(
        f"{user_id}:{gem['conversation_id']}:{gem['turn_range']}".encode()
    ).digest()[:8]
    gem_id = int.from_bytes(hash_bytes, byteorder='big') % (2**63)  # Ensure positive int64
    
    # Store to Qdrant
    response = requests.put(
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points",
        json={
            "points": [{
                "id": gem_id,
                "vector": vector,
                "payload": payload
            }]
        }
    )
    
    return response.status_code == 200


def save_suggested_categories(user_id: str, suggestions: Dict[str, Any]) -> bool:
    """Save suggested categories to pending review file."""
    suggestions_path = os.path.join(MEMORY_DIR, user_id, "suggested_categories.json")
    
    # Load existing
    if os.path.exists(suggestions_path):
        with open(suggestions_path, 'r') as f:
            existing = json.load(f)
    else:
        existing = {
            "suggested_categories": [],
            "suggested_subcategories": [],
            "pending_review": [],
            "last_reviewed": None,
            "review_history": []
        }
    
    # Add new suggestions to pending review
    new_categories = suggestions.get("suggested_categories", [])
    new_subcategories = suggestions.get("suggested_subcategories", [])
    
    for cat in new_categories:
        # Handle both string (simple name) and dict (detailed) formats
        cat_entry = cat if isinstance(cat, dict) else {"name": cat}
        if cat_entry not in existing["pending_review"]:
            existing["pending_review"].append({
                "type": "category",
                "timestamp": datetime.now().isoformat(),
                **cat_entry
            })
    
    for sub in new_subcategories:
        # Handle both string (simple name) and dict (detailed) formats
        sub_entry = sub if isinstance(sub, dict) else {"name": sub}
        if sub_entry not in existing["pending_review"]:
            existing["pending_review"].append({
                "type": "subcategory",
                "timestamp": datetime.now().isoformat(),
                **sub_entry
            })
    
    # Save
    with open(suggestions_path, 'w') as f:
        json.dump(existing, f, indent=2)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="True Recall Curator (User-Aware)")
    parser.add_argument("--user-id", required=True, help="User ID to process")
    parser.add_argument("--hours", type=int, default=24, help="Hours of history to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't store, just preview")
    args = parser.parse_args()
    
    print(f"🔍 True Recall Curator for {args.user_id}")
    print(f"⏰ Processing last {args.hours} hours")
    print(f"🧠 Embedding model: {EMBEDDING_MODEL}")
    print(f"🧠 Curation model: {CURATION_MODEL}")
    print(f"💎 Target collection: {QDRANT_COLLECTION}")
    print(f"🚫 Redis clear: DISABLED (Jarvis handles this)")
    print()
    
    # Get staged turns
    print("📥 Fetching conversation turns from Redis...")
    turns = get_staged_turns(args.user_id, args.hours)
    print(f"✅ Found {len(turns)} turns")
    
    if not turns:
        print("⚠️ No turns to process. Exiting.")
        return
    
    # Extract gems
    print(f"\n🧠 Extracting gems with The Curator ({CURATION_MODEL})...")
    result = extract_gems_with_curator(turns, args.user_id)
    gems = result.get("gems", [])
    suggested_categories = result.get("suggested_categories", [])
    suggested_subcategories = result.get("suggested_subcategories", [])
    
    print(f"✅ Extracted {len(gems)} gems")
    if suggested_categories:
        print(f"💡 Suggested new categories: {len(suggested_categories)}")
    if suggested_subcategories:
        print(f"💡 Suggested new subcategories: {len(suggested_subcategories)}")
    
    if not gems:
        print("⚠️ No gems extracted. Exiting.")
        return
    
    # Preview gems
    print("\n💎 Preview of extracted gems:")
    for i, gem in enumerate(gems[:3], 1):
        print(f"\n--- Gem {i} ---")
        print(f"Gem: {gem.get('gem', 'N/A')[:100]}...")
        print(f"Categories: {gem.get('categories', [])}")
        print(f"Importance: {gem.get('importance', 'N/A')}")
        print(f"Confidence: {gem.get('confidence', 'N/A')}")
    
    if len(gems) > 3:
        print(f"\n... and {len(gems) - 3} more gems")
    
    # Show suggestions
    if suggested_categories or suggested_subcategories:
        print("\n💡 Category suggestions:")
        for cat in suggested_categories[:3]:
            print(f"  📁 {cat.get('category', 'unknown')}: {cat.get('reason', 'no reason')[:50]}...")
        for sub in suggested_subcategories[:3]:
            print(f"  📂 {sub.get('parent', '?')}/{sub.get('subcategory', '?')}: {sub.get('reason', 'no reason')[:50]}...")
    
    if args.dry_run:
        print("\n🏃 DRY RUN: Not storing anything.")
        return
    
    # Store gems
    print("\n💾 Storing gems to Qdrant...")
    stored = 0
    for gem in gems:
        if store_gem_to_qdrant(gem, args.user_id):
            stored += 1
        else:
            print(f"⚠️ Failed to store gem: {gem.get('gem', 'N/A')[:50]}...")
    
    print(f"✅ Stored {stored}/{len(gems)} gems")
    
    # Save suggestions
    if suggested_categories or suggested_subcategories:
        print("\n📝 Saving category suggestions for review...")
        save_suggested_categories(args.user_id, result)
        print("✅ Suggestions saved to memory/{user_id}/suggested_categories.json")
    
    # Note: We do NOT clear Redis - Jarvis Memory handles that at 3:00 AM
    print("\n📌 Redis buffer left intact (Jarvis Memory will clear at 3:00 AM)")
    
    print("\n🎉 Curation complete!")


if __name__ == "__main__":
    main()