# Memory System Integration Guide

**Bridging Evergreen Programs with Multi-User Memory Architecture**

> **Placeholder note:** Examples in this file use `alice`, `bob`, and `eve` as example personas. Replace with your actual household member IDs. See [NAME-CUSTOMIZATION.md](NAME-CUSTOMIZATION.md).

This document explains how the Evergreen Toolkit integrates with the Jarvis-inspired multi-user memory system, creating a cohesive "theory of mind" for the AI assistant.

> **Note:** This document focuses on the infrastructure capture pipeline (Redis → durable storage).
> For the full 7-layer memory architecture model, see [MEMORY-SYSTEM.md](../MEMORY-SYSTEM.md).

---

## 🧠 Why Memory Matters for Evergreens

Evergreen programs maintain long-running initiatives (security, health, architecture, memory itself). To execute these effectively, the AI assistant needs:

1. **Conversational Memory** - Remember what users said in past sessions
2. **Semantic Memory** - Search across conversations by meaning, not keywords
3. **Episodic Memory** - Recall specific events, dates, and contexts
4. **User Isolation** - Keep Alice's memories separate from Bob's
5. **System Memory** - Maintain Eve's own knowledge and evergreen state

The memory system provides the context needed for evergreens to make informed decisions.

---

## 📚 Capture Pipeline (Layers 2–4 of the 7-Layer Architecture)

> **Layer numbering:** This document covers the infrastructure capture pipeline — Layers 2 through 4 of the full [7-layer memory architecture](../MEMORY-SYSTEM.md). Layer 1 (Session) is handled by optional plugins. Layers 5–7 (PARA, AGENTS.md, MEMORY.md) are covered in [MEMORY-SYSTEM.md](../MEMORY-SYSTEM.md) and [ARCHITECTURE.md](../ARCHITECTURE.md).

### Layer 2: Redis Buffer (Fast Capture)

**Purpose:** Real-time session capture during conversations

**Structure:**
```
mem:<user_id> → List of recent turns
```

**Usage:**
```bash
# Save current session to Redis buffer
python3 memory/scripts/save_mem.py --user-id <user1>

# Search recent memories (semantic)
python3 memory/scripts/search_memories.py "What did <user2> say about backup?" --user-id <user2>
```

**Evergreen Integration:** Household-Memory evergreen monitors this layer daily, ensuring capture scripts run correctly and Redis is healthy.

---

### Layer 3: Raw Archive & Layer 4: AI Curation

Layer 3 (Raw Archive) stores full transcripts as human-readable daily markdown files and in Qdrant's `<agent>-memories` collection. Layer 4 (AI Curation) extracts high-salience gems into Qdrant's `true_recall` collection. Together they provide durable storage with both keyword and semantic search.

#### Daily Files (Human-Readable)

**Purpose:** Persistent, editable memory files organized by date and user

**Structure:**
```
memory/
├── <user2>/
│   ├── 2009-01-03.md
│   ├── 2009-01-04.md
│   └── ...
├── <user1>/
│   ├── 2009-01-03.md
│   ├── 2009-01-04.md
│   └── ...
└── <agent>/                        # Agent system-level memories (optional)
    ├── 2009-01-03.md               # Daily entries (same format as user files)
    └── ...                         # Created by memory pipeline when agent user_id is used
```

**Daily File Format:**
```markdown
# 2009-01-03 - <user1>

## Conversations
- Discussed Acme Bookkeeping business
- Mentioned dentist appointment on Tuesday

## Decisions
- Agreed to try AI assistant for scheduling

## Action Items
- [ ] Send invoice template to <user1>
- [ ] Set up calendar reminders
```

**Evergreen Integration:** Household-Memory evergreen reviews recent daily files, extracts gems for long-term storage.

#### Qdrant (Semantic Search)

**Purpose:** Vector-based semantic search across all user memories

**Collections** (two separate collections serve different purposes — curated gems vs. raw backups):
- `true_recall` — AI-curated gems (decisions, insights, preferences) via True Recall Curator at 2:30 AM
- `<agent>-memories` — Raw conversation backup via Jarvis Memory at 3:00 AM

> **Naming note:** "Jarvis Memory" is the upstream system name (SpeedyFoxAI). `<agent>-memories` is the default Qdrant collection it writes to — replace `<agent>` with your agent's name. There are **two** Qdrant collections: `QDRANT_COLLECTION` (raw backups, default `<agent>-memories`) and `TRUE_RECALL_COLLECTION` (curated gems, default `true_recall`). Both are configurable via environment variables — see `config/memory_env.example`.

**Usage:**
```bash
# Semantic search (finds similar concepts, not just keyword matches)
python3 memory/scripts/search_memories.py "backup strategy" --user-id <user2> --limit 5

# Hybrid search (combines keyword + semantic — preferred for best results)
python3 memory/scripts/hybrid_search.py "backup strategy" --user-id <user2> --limit 5
```

**Evergreen Integration:** Household-Memory evergreen monitors Qdrant health, collection sizes, and curation pipeline.

---

## 🌲 Evergreen-Memory Integration Points

### Household-Memory Evergreen Responsibilities

The household-memory evergreen maintains the entire memory system:

| Task | Frequency | Script/Check |
|------|-----------|--------------|
| **Redis Health** | Daily | `redis-cli ping` |
| **Memory Capture** | Every session | `save_current_session_memory.py` |
| **Backup to Files** | Every session | Redis → daily file cron job |
| **Gem Curation** | Daily at 2:30 AM | `curate_memories.py --user-id <user>` |
| **Semantic Search** | On-demand | `search_memories.py` |
| **Qdrant Health** | Daily | Check collection status |

**Example Research:**
```bash
# Household-Memory research commands
redis-cli ping
ls -lt memory/<user2>/*.md | head -5
python3 memory/scripts/search_memories.py "recent decisions" --user-id <user1> --limit 3
```

---

### Other Evergreens Using Memory

All evergreens benefit from memory context:

#### Upstream Architecture
- **Memory Query:** "What models did Bob mention for async workloads?"
- **Context:** Remote GPU discussions, model strategy decisions

#### System Health
- **Memory Query:** "What backup concerns did Bob express?"
- **Context:** Past incidents, recovery tests, performance issues

#### Prompt Injection Defence
- **Memory Query:** "Did Alice approve any new skills recently?"
- **Context:** Skill vetting decisions, security discussions

**Example Usage in AGENDA.md:**
```markdown
## Research Findings
- **Memory Search:** Found Bob discussing backup concerns on 2008-12-28
  - Quote: "Make sure backups are tested, not just scheduled"
  - Action taken: Verified `/backup/openclaw/` integrity
  - Recommendation: Add backup restore test to monthly cycle
```

---

## 🔐 User Isolation & Security

### User ID Mapping

<!-- EXAMPLE: Replace with your household members. See AGENT-ONBOARDING.md for the full persona mapping. -->

| User | User ID | Channels | Memory Scope |
|------|---------|----------|--------------|
| Bob Smith | `bob` | Webchat, WhatsApp +12345678901 | `memory/bob/` |
| Alice Smith | `alice` | WhatsApp +11234567890 | `memory/alice/` |
| Eve (System) | `<agent>` | Internal | `memory/<agent>/` |

### Isolation Rules

**NEVER access another user's memory without explicit permission:**
- Bob's evergreen cycle → Only `memory/bob/` searches
- Alice's evergreen cycle → Only `memory/alice/` searches
- Cross-user insights → Aggregate anonymized, don't quote directly

**Exception:** System-level memories (`memory/<agent>/`) contain evergreen state and can be referenced by all cycles. This directory is created automatically by the memory pipeline if the agent stores system-level notes.

### Memory Access Security Rules

When working with multi-user memories:
```markdown
### Memory Access Rules

**Always:**
- Pass correct `--user-id` to memory scripts
- Log memory searches in AGENDA.md (for audit)
- Respect user: alice ≠ bob ≠ eve

**Never:**
- Search other users' memories without permission
- Quote private conversations in cross-user contexts
- Store credentials in memory (use credential files with 600 permissions)
```

---

## 📖 Implementation Checklist

### Required Files (Copy to Your Workspace)

| File | Purpose | Location |
|------|---------|----------|
| `save_mem.py` | Session capture | `memory/scripts/` |
| `search_memories.py` | Semantic search | `memory/scripts/` |
| `curate_memories.py` | Gem extraction | `memory/scripts/` |

### Configuration

**Redis:**
```bash
redis-cli ping  # Should return PONG
```

**Qdrant (Docker):**
```bash
docker ps | grep qdrant  # Should be running
```

**Embedding Model:**
```bash
ollama list | grep snowflake  # Should have snowflake-arctic-embed2
```

### Cron Jobs (Automatic)

> **Note:** The examples below are simplified for illustration. See [`config/crontab.sample`](../config/crontab.sample) for the full cron entries with `.memory_env` sourcing and absolute paths.

```bash
# True Recall curation (2:30 AM daily)
# Use full paths — 'source .venv/bin/activate' does NOT work in cron
30 2 * * * cd $WORKSPACE && .venv/bin/python3 memory/scripts/curate_memories.py --user-id <user1> >> logs/true-recall.log 2>&1
35 2 * * * cd $WORKSPACE && .venv/bin/python3 memory/scripts/curate_memories.py --user-id <user2> >> logs/true-recall.log 2>&1

# Jarvis Memory backup: Redis → Qdrant (3:00 AM daily)
0 3 * * * cd $WORKSPACE && .venv/bin/python3 memory/scripts/cron_backup.py --user-id <user1> >> logs/memory-backup.log 2>&1
5 3 * * * cd $WORKSPACE && .venv/bin/python3 memory/scripts/cron_backup.py --user-id <user2> >> logs/memory-backup.log 2>&1
```

---

## ❤️ Heartbeat-Driven Capture (Primary Method)

**This is the recommended way to capture conversation memory in production.**

Your agent's **heartbeat polls** (typically every ~30 minutes) are the ideal time to capture session memory. This ensures:
- ✅ Real-time capture during active sessions
- ✅ No reliance on end-of-day cron jobs
- ✅ Fresh context before session rotation

### Add to HEARTBEAT.md

```bash
source .venv/bin/activate
source .memory_env

# Auto-detect current session user and save to Redis
python3 memory/scripts/save_current_session_memory.py
```

**What happens:**
1. Finds the most recent session JSONL file
2. Extracts USER_ID from session metadata
3. Saves ALL conversation turns to Redis buffer (`mem:<user_id>`)
4. Updates state file for tracking

**For detailed heartbeat integration:** See [`HEARTBEAT-MEMORY-INTEGRATION.md`](./HEARTBEAT-MEMORY-INTEGRATION.md)

---

## 🧪 Testing Memory Integration

### Test 1: Manual Capture

```bash
cd ~/.openclaw/workspace
source .venv/bin/activate
source .memory_env

# Capture current session (auto-detects user)
python3 memory/scripts/save_current_session_memory.py

# Or specify user explicitly
python3 memory/scripts/save_mem.py --user-id alice
```

**Expected output:**
```
✅ Saved 42 turns to Redis (mem:alice)
   State updated to turn 42
```

### Test 2: Semantic Search

```bash
# Search Alice's memories
python3 memory/scripts/search_memories.py "backup concerns" --user-id alice --limit 3

# Search Bob's memories
python3 memory/scripts/search_memories.py "model strategy" --user-id bob --limit 5
```

### Test 3: Memory Health Check (for Evergreen)

```bash
# Check Redis
redis-cli ping

# Check Qdrant
curl -s http://localhost:6333/collections | jq .

# Check recent daily files
ls -lt memory/bob/*.md | head -3
ls -lt memory/alice/*.md | head -3
```

**Log in AGENDA.md:**
```markdown
## Research Findings
- **Redis:** ✅ PONG (healthy)
- **Qdrant:** ✅ 2 collections, 58 memories total
- **Daily Files:** ✅ 15 files for bob (March), 12 for alice
```

---

## 📊 Example: Household-Memory Cycle

### Full Cycle Walkthrough

**Step 1: Level-Set**
```bash
cat evergreens/household-memory/STATE.md
cat evergreens/household-memory/AGENDA.md
```

**Step 2: Research**
```bash
# Check memory health
redis-cli ping
curl -s http://localhost:6333/collections | jq '.result[] | {name: .name, points_count: .points_count}'

# Check recent captures
ls -lt memory/bob/*.md | head -5
ls -lt memory/alice/*.md | head -5

# Search for recent decisions
python3 memory/scripts/search_memories.py "decisions made this week" --user-id bob --limit 5
```

**Step 3: Analyze**
```markdown
## Analysis
- Redis healthy, latency <1ms
- Qdrant collections growing steadily (58 total memories)
- Recent captures show Bob discussing GPU model strategy
- Alice's Acme Bookkeeping business planning captured

## Patterns
- Both users actively using assistant
- Memory capture working consistently
- True Recall curation extracting quality gems
```

**Step 4: Plan**
```markdown
## Tasks for This Cycle

### 1. Verify True Recall curation ran this morning
- Status: ✅ completed
- Findings: Cron logs show successful run at 2:30 AM
- Actions taken: Checked `logs/true-recall.log`
- Reasoning: Ensures gem extraction pipeline working

### 2. Check Qdrant collection sizes
- Status: ✅ completed
- Findings: <agent>-memories (58), true_recall (8)
- Recommendations: Monitor growth, optimize if >10k
```

**Step 4b: Update STATE.md "Completed Recently"**
```markdown
## Completed Recently
- [2009-01-03] Memory system health verified - Redis, Qdrant, daily files all healthy
- [2008-12-28] True Recall curator operational - 8 gems stored
- [2008-12-28] Memory capture patterns documented
```

**Step 5-8: Mechanical**
```bash
python3 scripts/evergreen_ai_executor.py --evergreen household-memory --mode auto
```

---

## 🎯 Key Takeaways

1. **Memory enables context-aware evergreens** - AI can reference past conversations when making decisions

2. **User isolation is critical** - Always pass `--user-id` to memory scripts

3. **Household-Memory maintains the system** - Other evergreens consume memory, this one maintains it

4. **Two layers serve different purposes:**
   - Layer 2 (Redis): Fast session capture
   - Layers 3-4 (Qdrant + daily files): Durable storage and semantic search

5. **Cron jobs automate the pipeline** - Memory flows from Redis → Files → Qdrant automatically

6. **Evergreens use memory for research** - "What did Bob say about X?" becomes answerable

---

**Source:** Adapted from https://gitlab.com/mdkrush/openclaw-true-recall-base (see [memory/UPSTREAM-CREDITS.md](../memory/UPSTREAM-CREDITS.md) for full attribution)
