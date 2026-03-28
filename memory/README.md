# 🧠 Jarvis Memory + True Recall

**Enterprise-grade memory architecture for OpenClaw agents.**

This implementation provides a multi-layer memory system (capture → curation → durable knowledge) with two parallel processing paths, optimized for speed, durability, and semantic retrieval.

> **Full system overview:** See [`MEMORY-SYSTEM.md`](../MEMORY-SYSTEM.md) for the complete 7-layer architecture.

> **Convention:** All command examples assume you've `cd`'d into the workspace root
> (e.g., `~/.openclaw/workspace/`). Memory scripts are at `memory/scripts/` relative to
> that root.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Session                      │
│  (Optional: LCM for session recovery, Gigabrain for recall) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Redis Buffer (Fast Capture)                        │
│  - In-memory key-value store                                 │
│  - Sub-second writes                                         │
│  - Temporary holding (24-48 hours)                           │
│  - Key: mem:<user_id>                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼ (2:30 AM)           ▼ (3:00 AM)
┌──────────────────────┐  ┌──────────────────────┐
│  True Recall Curator │  │  Jarvis Memory       │
│  AI-curated gems     │  │  Raw conversation    │
│  → Qdrant true_recall│  │  backup → Qdrant     │
│  (does NOT clear     │  │  <agent>-memories         │
│   Redis)             │  │  (clears Redis after) │
└──────────────────────┘  └──────────────────────┘
          │                     │
          ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Raw Archive                                        │
│  - Qdrant <agent>-memories (full transcripts)                │
│  - Markdown files: memory/<user_id>/2009-01-02.md           │
│  - Human-readable + machine-searchable                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: AI Curation                                        │
│  - Qdrant true_recall (high-salience gems)                   │
│  - Permanent retention                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (weekly promotion)
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: PARA — Durable Knowledge                           │
│  - memory/para/<user>/summary.md (key facts, narrative)      │
│  - memory/para/<user>/items.json (structured facts)          │
│  - memory/para/<user>/review-queue.md (contradictions)       │
│  - Canonical source of truth per user                        │
│  - See memory/para/README.md for schema + rules              │
└─────────────────────────────────────────────────────────────┘
```

### Naming Glossary

| Term | What it means |
|------|--------------|
| **Jarvis Memory** | The upstream system name (built by SpeedyFoxAI). Runs at 3:00 AM — dumps all raw conversation turns from Redis → Qdrant, then clears Redis. |
| **True Recall** | The AI curation layer. Runs at 2:30 AM — reads Redis, uses an LLM to extract high-value "gems" (decisions, insights, preferences), stores to Qdrant. Does NOT clear Redis. |
| `<agent>-memories` | Default Qdrant collection for Jarvis Memory. Replace `<agent>` with your agent's name. Configurable via `QDRANT_COLLECTION` env var. |
| `true_recall` | Default Qdrant collection for True Recall curated gems. `curate_memories.py` writes here by default, keeping curated gems separate from raw backups. |
| **The Curator** | The AI persona/system prompt used by `curate_memories.py` to decide what's worth preserving. See `memory/curator_prompts/base.md`. |

### Two Qdrant Collections (Quick Reference)

The system uses **two separate Qdrant collections** — don't mix them up:

| Collection | Env Var | Default Name | Written By | When | Clears Redis? |
|---|---|---|---|---|---|
| Raw backups | `QDRANT_COLLECTION` | `<agent>-memories` | `cron_backup.py` | 3:00 AM | **Yes** |
| Curated gems | `TRUE_RECALL_COLLECTION` | `true_recall` | `curate_memories.py` | 2:30 AM | No |

Both are created by `init_memory_collections.py` during setup. Configure names in `.memory_env`.

---

## Which Script Should I Use?

| Task | Script | Notes |
|------|--------|-------|
| **Heartbeat capture** (recommended) | `save_current_session_memory.py` | Auto-detects user |
| **Manual memory save** | `save_mem.py --user-id <id>` | Explicit user ID |
| **Search memories** | `search_memories.py "query" --user-id <id>` | Semantic vector search |
| **Hybrid search** (keyword + vector) | `hybrid_search.py "query" --user-id <id>` | Best recall |
| **Initialize Qdrant collections** | `init_memory_collections.py` | Run once during setup |
| **Daily curation** (cron) | `curate_memories.py --user-id <id>` | Extracts gems via LLM |
| **Daily backup** (cron) | `cron_backup.py --user-id <id>` | Redis → Qdrant, clears Redis |
| **Session transcript → Redis** (cron) | `cron_capture.py --user-id <id>` | Feeds new messages into Redis |

For the full categorized list, see [Components](#components) below.

---

## Components

### Redis Buffer (`scripts/`)

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `save_mem.py` | Capture **ALL** session turns to Redis | **Heartbeat polls** (every ~30 min) |
| `save_current_session_memory.py` | Full session save with auto-user-detection | **Heartbeat (recommended)** — wraps `save_mem.py` with user auto-detection |
| `hb_append.py` | Append **NEW** turns only (incremental) | High-frequency heartbeats (5-10 min) |
| `mem_retrieve.py` | Retrieve memories from Redis | On-demand context retrieval |
| `cron_backup.py` | Daily backup: Redis → Qdrant | Cron job (3:00 AM) |
| `cron_capture.py` | Append new session transcript messages to Redis | Cron job (every 5 min) |

**Which script for heartbeats?** For the default 30-minute heartbeat interval, use `save_current_session_memory.py` (auto-detects the current user) or `save_mem.py --user-id <id>` (explicit user). Only use `hb_append.py` if heartbeats are more frequent than every 10 minutes (it appends incrementally rather than re-saving the full session).

**Heartbeat vs. Cron capture — complementary, not redundant:**
- **Heartbeat** (`save_current_session_memory.py`) captures the *active session* in real time during conversations. It runs every ~30 minutes while the agent is engaged with a user.
- **Cron** (`cron_capture.py`) reads *transcript files* on disk and feeds new messages into Redis. It runs every 5 minutes regardless of session state, catching messages that heartbeat might miss (e.g., if the agent wasn't active when a message arrived).
- Both feed into the same Redis buffer. The nightly Jarvis backup (3:00 AM) and True Recall curation (2:30 AM) process whatever is in Redis, regardless of how it got there.
- **Recommendation:** Use both. Heartbeat provides low-latency capture during active sessions; cron provides reliable background coverage.

### Curation Scripts

| Script | Purpose |
|--------|---------|
| `curate_memories.py` | Main True Recall curation engine — extracts gems from conversations |
| `extract_facts.py` | Pull high-salience facts from conversations |
| `hybrid_search.py` | Combined keyword (daily files) + vector (Qdrant) search |

### Search & Retrieval

| Script | Purpose |
|--------|---------|
| `search_memories.py` | Semantic search in Qdrant via embeddings |
| `search_mem.py` | Redis (exact) then Qdrant (semantic) fallback search |
| `smart_search.py` | Hybrid search: knowledge base first, then web search |
| `get_conversation_context.py` | Retrieve user memories across all conversations |
| `get_session_context.py` | Retrieve all turns from a specific session, ordered chronologically |
| `get_user_context.py` | Quick user context summary from recent memories |

### Storage & Backup

| Script | Purpose |
|--------|---------|
| `store_memory.py` | Enhanced memory storage with metadata, tags, and batch upload |
| `store_conversation.py` | Store conversational turns to Qdrant with context |
| `auto_store.py` | Auto Mem0-style full context conversation storage |
| `background_store.py` | Fire-and-forget background wrapper for memory storage |
| `q_save.py` | Trigger immediate conversation storage to Qdrant |
| `daily_backup.py` | Daily memory backup to Qdrant with batch upload |
| `daily_conversation_backup.py` | Daily backup of day's conversations to Qdrant |
| `create_daily_memory.py` | Create today's memory markdown file if it doesn't exist |
| `harvest_sessions.py` | Harvest all session JSONL files and store to Qdrant |

> **Which storage script?** Most users only need the Redis buffer scripts above (capture to Redis, then cron processes to Qdrant). The storage scripts here are for direct Qdrant writes: `store_memory.py` for structured data with tags, `store_conversation.py` for raw turns, `q_save.py` for quick one-off saves, `auto_store.py` for full-context archival, and `background_store.py` as a non-blocking wrapper around any of them.

### Validation

| Script | Purpose |
|--------|---------|
| `validate_memory.py` | Validate content for injection patterns before storing in memory. Provides `validate_content()` and `wrap_external_content()` functions used by `save_mem.py` and other capture scripts |

### Utility & Integration

| Script | Purpose |
|--------|---------|
| `hb_check_email.py` | Email-triggered memory operations |
| `send_email.py` | Send email via Gmail SMTP with attachment support |
| `backfill_emails.py` | One-time backfill of existing emails to Qdrant |
| `activity_log.py` | Shared activity log for agent and evergreen coordination |
| `log_activity.py` | Convenience wrapper for activity logging |
| `init_memory_collections.py` | Create/recreate Qdrant collections with proper vector config |

### PARA Layer

| Script | Purpose |
|--------|---------|
| `seed_para.py` | Initialize PARA directories for users from templates |
| `promote_to_para.py` | Promote durable facts from True Recall gems → PARA items.json |
| `detect_stale_para.py` | Detect stale and contradictory facts in PARA items.json |
| `migrate_memory_to_para.py` | One-time migration: extract facts from existing memory into PARA (draft output for review) |
| `archive_daily_notes.py` | Archive old daily memory files after processing (move to archive directory) |

---

## Daily Note Lifecycle

Daily notes (`memory/<user>/YYYY-MM-DD.md`) are ephemeral working files, not durable truth. They follow this lifecycle:

```
1. Capture     → cron_capture.py writes new messages to Redis
2. Curation    → curate_memories.py extracts gems (2:30 AM)
3. Backup      → cron_backup.py dumps Redis → Qdrant + daily file (3:00 AM)
4. Promotion   → promote_to_para.py extracts durable facts → PARA (weekly)
5. Archive     → Files older than 30 days can be compressed or removed
```

**Key rules:**
- Daily notes are a **byproduct** of the backup process, not a primary store
- Important facts should be **promoted to PARA** — don't rely on finding them in daily files
- Search uses **Qdrant vectors** (semantic search), not daily file scanning
- The household-memory evergreen reviews daily notes for promotion candidates
- Old daily files can be archived (gzip) or removed after promotion — Qdrant retains the data

---

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install qdrant-client redis

# Start Redis (local)
redis-server --daemonize yes

# Start Qdrant (local or Docker)
docker run -d -p 6333:6333 qdrant/qdrant
```

### Configuration

Create `.memory_env` in your workspace:

```bash
# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Qdrant
export QDRANT_URL=http://localhost:6333
export QDRANT_COLLECTION=<agent>-memories           # Raw conversation backups (Jarvis Memory)
export TRUE_RECALL_COLLECTION=true_recall           # AI-curated gems (True Recall)

# User IDs (customize for your agents)
export DEFAULT_USER_ID=user1
```

### Environment Activation

```bash
source .venv/bin/activate
source .memory_env
```

---

## Quick Start

### 1. Initialize Collections

```bash
python3 memory/scripts/init_memory_collections.py
```

> **Note:** Run this from the workspace root directory (e.g., `~/.openclaw/workspace/`). Creates **both** Qdrant collections — `QDRANT_COLLECTION` (raw backups) and `TRUE_RECALL_COLLECTION` (curated gems) — with proper vector config (1024 dims, cosine distance). It supports `--recreate` to rebuild from scratch. Do NOT confuse this with `auto_store.py`, which is a conversation-turn storage tool (no `--init` flag).

### 2. Test Memory Capture

```bash
# Save current session
python3 memory/scripts/save_mem.py --user-id <user1>

# Search memories
python3 memory/scripts/search_memories.py "What did we discuss about backups?" --user-id <user1>
```

### 3. Set Up Crons

Add to your crontab (see `config/crontab.sample`):

```bash
# True Recall curation (2:30 AM)
30 2 * * * cd $WORKSPACE && $WORKSPACE/.venv/bin/python3 memory/scripts/curate_memories.py --user-id <user1>

# Redis → Qdrant backup (3:00 AM)
0 3 * * * cd $WORKSPACE && $WORKSPACE/.venv/bin/python3 memory/scripts/cron_backup.py --user-id <user1>
```

---

## Memory Lifecycle

### Capture → Process → Retrieve

#### Capture (Real-time)

Every conversation turn is automatically staged to Redis:

```python
# Automatic via OpenClaw hook
mem: user1 → [conversation turns in Redis list]
```

#### Processing (Scheduled)

**True Recall (2:30 AM):**
1. Scans Redis for high-salience events
2. Extracts critical facts, decisions, action items
3. Writes immediately to Qdrant + today's daily file

**Backup (3:00 AM):**
1. Embeds remaining Redis content
2. Upserts to Qdrant vector store
3. Appends to daily markdown file
4. Flushes Redis buffer

#### Retrieval (On-demand)

```bash
# Semantic search
python3 memory/scripts/search_memories.py "OAuth configuration" --user-id <user1>

# Get recent context
python3 memory/scripts/get_user_context.py --user-id <user1> --hours 24
```

---

## Data Formats

### Redis Structure

```
mem:<user_id> (LIST)
  - Each element: JSON string representing one conversation turn
  - Written by: save_mem.py (LPUSH), cron_capture.py (RPUSH), hb_append.py (LPUSH)
  - Read by: cron_backup.py (LRANGE), curate_memories.py (LRANGE)
  - Cleared by: cron_backup.py (DEL) after successful Qdrant backup
```

### Daily File Format

```markdown
# Memory for 2009-01-02

## Session: [Channel] - [Time]

**USER:** What's the weather like?

**ASSISTANT:** Checking weather for your location...

---

## Session: [Channel] - [Time]

**USER:** Remember that <user1> prefers SSH key auth

**ASSISTANT:** Noted! Added to preferences.

### ✅ Extracted Facts
- <user1> prefers SSH key authentication over passwords
```

### Qdrant Payload

```json
{
  "user_id": "user1",
  "session_key": "agent:main:whatsapp:...",
  "timestamp": "2009-01-02T14:30:00Z",
  "content": "User discussed OAuth configuration...",
  "type": "conversation",
  "tags": ["technical", "configuration"]
}
```

---

## Advanced Features

### Hybrid Search

Combines keyword + vector search for best results:

```bash
python3 memory/scripts/hybrid_search.py "OpenAI OAuth setup" --user-id <user1>
```

### Session Context

Get last N hours of conversation context:

```bash
python3 memory/scripts/get_user_context.py --user-id <user1> --hours 24 --format markdown
```

### Activity Logging

Track memory operations:

```bash
python3 memory/scripts/activity_log.py --user-id <user1> --since 2009-01-02
```

---

## Performance Tips

### Optimization Strategies

1. **Batch embeddings** - Process 100 items at once, not individually
2. **Use Redis pipelines** - Reduce network round-trips
3. **Index Qdrant collections** - HNSW for fast ANN search
4. **Compact daily files** - Archive old entries weekly

### Resource Usage

| Operation | Memory | CPU | Time |
|-----------|--------|-----|------|
| Redis write | ~1 KB | Low | <10ms |
| Embedding (batch 100) | ~50 MB | Medium | ~2s |
| Qdrant upsert | ~5 MB | Low | ~100ms |
| Semantic search | ~10 MB | Low | ~50ms |

---

## Troubleshooting

### Redis Connection Failed

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### Qdrant Collection Missing

```bash
# Reinitialize
python3 memory/scripts/init_memory_collections.py
```

### High Memory Usage

```bash
# ⚠️ WARNING: This deletes ALL pending memory buffers for ALL users.
# Only use after confirming backups are complete (Jarvis backup runs at 3:00 AM).
# Flush old Redis entries
redis-cli KEYS "mem:*" | xargs redis-cli DEL

# Compact Qdrant
curl -X POST 'http://localhost:6333/collections/<agent>-memories/points/vacuum'
```

---

## External Dependencies

Some scripts reference modules that live in the broader OpenClaw workspace (not in this toolkit):

| Module | Used By | Purpose | If Missing |
|--------|---------|---------|------------|
| `memory_validation` | `save_mem.py` | Injection pattern detection | Gracefully skipped (warning printed) |

These are optional. The scripts handle their absence with try/except and continue working without them.

---

**Memory that works like human memory: fast recall, durable storage, smart prioritization. 🧠**
