#!/usr/bin/env python3
"""
Initialize Qdrant collections for the memory system.

Creates two collections:
  1. <agent>-memories (raw conversation backups, via QDRANT_COLLECTION env var)
  2. true_recall (AI-curated gems)

Both use the same vector size (default: 1024 for snowflake-arctic-embed2).

Usage: init_memory_collections.py [--recreate]
"""

import argparse
import sys
import urllib.request
import json

import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "agent-memories")
TRUE_RECALL_COLLECTION = os.getenv("TRUE_RECALL_COLLECTION", "true_recall")
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

if not os.getenv("QDRANT_COLLECTION"):
    print(f"⚠️  QDRANT_COLLECTION not set — using default '{COLLECTION_NAME}'.")
    print(f"   Set QDRANT_COLLECTION in .memory_env (e.g., 'source .memory_env') for your agent's collection name.")

def make_request(url, data=None, method="GET"):
    req = urllib.request.Request(url, method=method)
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    return req

def collection_exists(name):
    try:
        req = make_request(f"{QDRANT_URL}/collections/{name}")
        with urllib.request.urlopen(req, timeout=5) as response:
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise
    except Exception:
        return False

def get_info(name):
    try:
        req = make_request(f"{QDRANT_URL}/collections/{name}")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None

def create_collection(name):
    config = {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine"
        }
    }
    req = make_request(
        f"{QDRANT_URL}/collections/{name}",
        data=config,
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get("result") == True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def delete_collection(name):
    req = make_request(f"{QDRANT_URL}/collections/{name}", method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode()).get("status") == "ok"
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def init_collection(name, recreate=False):
    """Initialize a single collection. Returns True on success."""
    exists = collection_exists(name)

    if exists:
        if recreate:
            print(f"  Deleting existing {name}...")
            delete_collection(name)
            exists = False
        else:
            info = get_info(name)
            if info:
                size = info.get("result", {}).get("vectors_config", {}).get("params", {}).get("vectors", {}).get("size", "?")
                points = info.get("result", {}).get("points_count", 0)
                print(f"  ⚠️  {name} already exists (vector size: {size}, points: {points})")
                return True

    if not exists:
        if create_collection(name):
            print(f"  ✅ Created {name} (vector size: {VECTOR_SIZE}, distance: Cosine)")
            return True
        else:
            print(f"  ❌ Failed to create {name}", file=sys.stderr)
            return False

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Qdrant memory collections")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate")
    args = parser.parse_args()
    
    try:
        req = make_request(f"{QDRANT_URL}/")
        with urllib.request.urlopen(req, timeout=3) as response:
            pass
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Qdrant: {QDRANT_URL}")
    print(f"Vector size: {VECTOR_SIZE} (snowflake-arctic-embed2)\n")

    ok = True

    print(f"Raw backups collection (QDRANT_COLLECTION):")
    if not init_collection(COLLECTION_NAME, args.recreate):
        ok = False

    print(f"\nCurated gems collection (TRUE_RECALL_COLLECTION):")
    if not init_collection(TRUE_RECALL_COLLECTION, args.recreate):
        ok = False

    if not ok:
        sys.exit(1)
