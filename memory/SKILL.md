<!-- Placeholder convention: <user1>=Alice, <user2>=Bob, <agent>=Eve in examples.
     See AGENT-ONBOARDING.md for the full mapping. -->

<!-- This file is an OpenClaw skill definition. Place it where your agent's skill
     scanner can find it (typically the workspace root or a skills/ directory).
     It provides the agent with instructions on how to use the memory capture system.
     It is NOT general documentation — see README.md for that. -->

# Memory Capture System

Fast capture of conversation context via Redis buffers, with cron-driven archival to Qdrant and daily files.

## Purpose

Captures recent conversation turns in Redis for quick retrieval (Layer 2), then archives to Qdrant vector search and daily markdown files via scheduled cron jobs (Layers 3-4).

## Quick Start

### Heartbeat Integration (Recommended)

**Add to your `HEARTBEAT.md` file** for automatic capture every ~30 minutes:

```bash
source .venv/bin/activate
source .memory_env

# Auto-detect user from current session
python3 memory/scripts/save_current_session_memory.py
```

**Why heartbeats?** Active sessions are captured in real-time, not just at end-of-day cron jobs.

### Manual Commands

```bash
# Activate environment first
source .venv/bin/activate
source .memory_env

# Save current session to Redis (full capture)
python3 memory/scripts/save_mem.py --user-id <user_id>

# Retrieve recent turns
python3 memory/scripts/mem_retrieve.py --user-id <user_id> --limit 10

# Semantic search in Qdrant
python3 memory/scripts/search_memories.py "query" --user-id <user_id>

# Append only NEW turns (incremental, for high-frequency heartbeats)
python3 memory/scripts/hb_append.py --user-id <user_id>
```

## User IDs

- `<user1>` — Primary User
- `<user2>` — Secondary User
- `<agent>` — System-level

## Redis Keys

- `mem:<user1>` — <user1>'s conversation buffer
- `mem:<user2>` — <user2>'s conversation buffer
- `mem:<agent>` — System buffer

## Integration

### Heartbeat-Driven Capture (Primary)
- **When:** Every ~30 minutes during active sessions
- **Script:** `save_mem.py` or `save_current_session_memory.py` (auto-detect)
- **Purpose:** Real-time session capture

### Cron-Driven Processing (Secondary)
- **When:** 2:30 AM (True Recall), 3:00 AM (Backup)
- **Scripts:** `curate_memories.py`, `cron_backup.py`
- **Purpose:** Process Redis → Qdrant + daily files

---

**See also:**
- `memory/scripts/search_memories.py` for semantic search
- [`docs/HEARTBEAT-MEMORY-INTEGRATION.md`](../docs/HEARTBEAT-MEMORY-INTEGRATION.md) for heartbeat setup