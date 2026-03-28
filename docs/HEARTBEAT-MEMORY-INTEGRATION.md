# ❤️ Heartbeat-Driven Memory Capture

**Configure your agent to capture conversation memory during heartbeat polls.**

> **Your HEARTBEAT.md file location:** `~/.openclaw/workspace/HEARTBEAT.md` (OpenClaw reads this file during periodic heartbeat polls).

> **Path convention:** All paths in the heartbeat template are relative to the workspace root. The template starts with `cd $WORKSPACE` to establish this context. Replace `$WORKSPACE` with your actual workspace path (e.g., `~/.openclaw/workspace`).

---

## Why Heartbeats Matter for Memory

OpenClaw agents receive periodic **heartbeat polls** to check system status, process notifications, and perform maintenance. Heartbeats are the ideal time to capture conversation memory because:

1. **Sessions are active** — The agent is mid-conversation with fresh context
2. **Low-latency** — Capture happens before session data ages or rotates
3. **Background operation** — No user interaction required
4. **Consistent timing** — Heartbeats run on a predictable schedule (e.g., every 30 minutes)

Without heartbeat-driven capture, memory relies solely on:
- End-of-day cron jobs (which may miss active sessions)
- Manual triggers (which are easily forgotten)
- Session-end hooks (which may not fire if agent crashes)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   OpenClaw Main Session                      │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  User    │ →  │ Assistant│ →  │  Tool    │              │
│  │ Message  │    │ Response │    │ Results  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                                              │
│         ↓ Session JSONL file updated continuously            │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Heartbeat Poll (every 30 min)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    HEARTBEAT.md Execution                    │
│                                                              │
│  1. Check for new notifications                              │
│  2. CAPTURE SESSION MEMORY ← This is where memory happens!   │
│  3. Process any pending tasks                                │
│  4. Reply HEARTBEAT_OK if nothing needs attention            │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ save_mem.py or hb_append.py
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Redis Buffer                             │
│                                                              │
│  mem:<user1> → [recent turns]                              │
│  mem:<user2> → [recent turns]                              │
│                                                              │
│  ← Later: Cron jobs move this to Qdrant + daily files       │
└─────────────────────────────────────────────────────────────┘
```

---

## Two Capture Strategies

### Strategy 1: Full Save (Recommended for Heartbeats)

**Script:** `save_current_session_memory.py` (wraps `save_mem.py` with auto-user-detection)

**Behavior:** Saves ALL conversation turns from the current session to Redis, appending to the existing buffer. Auto-detects the current user from session metadata. Use `save_mem.py --reset` to clear and replace instead.

**When to use:**
- ✅ **Heartbeat polls** (most common)
- ✅ Session start (if you want fresh capture)
- ✅ After long gaps in conversation

**Pros:**
- Simple and reliable
- Always captures complete context
- No state file to manage

**Cons:**
- Duplicates data if run multiple times in same session

**Usage:**

> **Path note:** Heartbeat commands assume you are in the workspace directory. After deployment, all scripts live directly in the workspace, so paths are workspace-relative (e.g., `memory/scripts/...`). The `HEARTBEAT.md` snippets below use `cd $WORKSPACE` at the top to ensure the correct directory.

```bash
# In HEARTBEAT.md
cd $WORKSPACE
source .venv/bin/activate
source .memory_env

# Auto-detect user from current session
python3 memory/scripts/save_current_session_memory.py

# Or specify user explicitly
python3 memory/scripts/save_mem.py --user-id <user1>
```

---

### Strategy 2: Incremental Append (Advanced)

**Script:** `hb_append.py`

**Behavior:** Only saves NEW conversation turns since last run, using a state file to track position.

**When to use:**
- ✅ High-frequency heartbeats (every 5-10 minutes)
- ✅ Very long sessions (100+ turns)
- ✅ Resource-constrained environments

**Pros:**
- No duplicate data
- Efficient for frequent captures
- Maintains turn order

**Cons:**
- Requires state file management (`.mem_last_turn`)
- More complex error handling
- Can lose track if state file corrupted

**Usage:**
```bash
# Append new turns only
python3 memory/scripts/hb_append.py --user-id <user1>
```

**State file:** `.mem_last_turn` (tracks last turn number)

---

## HEARTBEAT.md Integration Template

> **Starting template:** Copy [`config/HEARTBEAT-TEMPLATE.md`](../config/HEARTBEAT-TEMPLATE.md) to your workspace root and customize, or use the minimal example below.

Copy this into your production `HEARTBEAT.md`:

````markdown
## Memory Capture (Every Heartbeat)

**CRITICAL:** This step MUST run every heartbeat to capture conversation context.

```bash
cd $WORKSPACE
source .venv/bin/activate
source .memory_env

# Auto-detect current session user and save
python3 memory/scripts/save_current_session_memory.py
```

### Automatic User Detection

The `save_current_session_memory.py` script automatically:
1. Finds the most recent session JSONL file
2. Extracts USER_ID from session metadata or message context
3. Saves all turns to Redis buffer
4. Updates state file

### Fallback: Manual User ID

If auto-detect fails, specify user explicitly:
```bash
python3 memory/scripts/save_mem.py --user-id <user1>
```
````

---

## Multi-User Households

If your agent serves multiple users (Alice, Bob, etc.), the heartbeat should:

### Option 1: Auto-Detect (Recommended)

Let `save_current_session_memory.py` detect the active user:

```bash
# Works for whoever is chatting in the current session
python3 memory/scripts/save_current_session_memory.py
```

**Pros:** Simple, works automatically
**Cons:** Only captures the active session's user

### Option 2: Capture All Users

If you want to ensure all users are captured each heartbeat:

```bash
# Capture each user's most recent session
for user in <user1> <user2>; do
  python3 memory/scripts/save_mem.py --user-id $user
done
```

**Pros:** Comprehensive capture
**Cons:** Slower, may capture stale sessions

---

## Verification Commands

After heartbeat runs, verify memory was captured:

```bash
# Check Redis buffer exists
redis-cli KEYS "mem:*"

# Check buffer size (should show turn count)
redis-cli LLEN mem:<user1>
redis-cli LLEN mem:<user2>

# Sample recent memory
redis-cli LRANGE mem:<user1> 0 2 | python3 -m json.tool
```

Expected output:
```
mem:<user1>
mem:<user2>

(integer) 42
(integer) 38

[
  "{\\\"turn\\\": 42, \\\"role\\\": \\\"assistant\\\", \\\"content\\\": \\\"I'll help you with...\\\"}",
  "{\\\"turn\\\": 41, \\\"role\\\": \\\"user\\\", \\\"content\\\": \\\"Can you check...\\\"}"
]
```

---

## Troubleshooting

### No Memory Captured

**Check:** Session file exists
```bash
ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -3
```

**Check:** User ID detected correctly
```bash
python3 memory/scripts/save_current_session_memory.py --verbose
```

### Redis Connection Failed

**Check:** Redis is running
```bash
redis-cli ping
# Should return: PONG
```

**Fix:** Start Redis if needed
```bash
redis-server --daemonize yes
```

### Wrong User Captured

**Problem:** Auto-detect picked the wrong user ID

**Solution:** Use explicit user ID in HEARTBEAT.md:
```bash
python3 memory/scripts/save_mem.py --user-id <user1>
```

### Heartbeat Running Too Slow

**Problem:** Memory capture adding significant time to heartbeat

**Solutions:**
1. Use `hb_append.py` instead of `save_mem.py` (faster for incremental)
2. Reduce capture frequency (every other heartbeat)
3. Add timeout wrapper:
```bash
timeout 30 python3 memory/scripts/save_current_session_memory.py || echo "⚠️ Memory capture timed out"
```

---

## Relationship to Cron Jobs

Heartbeat capture works WITH cron jobs, not instead of them:

| Component | Timing | Purpose |
|-----------|--------|---------|
| **Heartbeat** | Every 30 min | Real-time session capture to Redis |
| **True Recall Cron** | 2:30 AM daily | Extract gems from Redis → Qdrant |
| **Backup Cron** | 3:00 AM daily | Redis → Qdrant + daily files, then clear Redis |

**Flow:**
```
Heartbeat (capture) → Redis buffer → [True Recall] → Qdrant gems
                                          ↓
                                 [Backup Cron] → Daily files + clear Redis
```

---

## Advanced: Email-Triggered Memory Capture

For urgent memory operations outside heartbeat schedule:

**Script:** `hb_check_email.py`

**Purpose:** Check for new emails and optionally trigger memory capture based on email content.

**Usage:**
```bash
python3 memory/scripts/hb_check_email.py --user-id <user1>
```

**Example scenario:** User emails "Remember to add this to memory: [important fact]"

---

## Key Takeaways

1. **Heartbeats are the primary capture mechanism** — Don't rely solely on cron jobs
2. **Use `save_mem.py` for simplicity** — Full save is fine for 30-minute heartbeats
3. **Auto-detect user when possible** — Reduces configuration complexity
4. **Verify with Redis commands** — `redis-cli LLEN mem:<user>` shows turn count
5. **Works with cron, not instead of** — Heartbeat captures, cron processes

---

**Memory that captures conversations in real-time, not just at end-of-day. ❤️**
