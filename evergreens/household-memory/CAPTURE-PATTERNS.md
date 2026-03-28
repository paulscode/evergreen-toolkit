<!-- EXAMPLE: Capture patterns shown here illustrate the expected format.
     Adapt polling intervals and user IDs for your deployment.
     Placeholder convention: <user1>=Alice, <user2>=Bob, <agent>=Eve.
     See AGENT-ONBOARDING.md for the full mapping. -->

# Memory Capture Patterns

## When Memory is Captured

### 1. Session Saves
- **Script:** `memory/scripts/save_mem.py`
- **Trigger:** After meaningful conversations or via cron
- **What:** Session context is saved to Redis buffer

### 2. Manual Triggers
- **Command:** `python3 memory/scripts/save_mem.py --user-id <USER_ID>`
- **When:** After meaningful conversations
- **What:** All context from current session

### 3. Cron Jobs (Automated)

| Time | Job | Purpose |
|------|-----|---------|
| 2:30 AM | True Recall curator (<user1>) | Extract gems from last 24h |
| 2:35 AM | True Recall curator (<user2>) | Extract gems from last 24h |
| 3:00 AM | Jarvis Memory backup (<user1>) | Raw backup to Qdrant |
| 3:05 AM | Jarvis Memory backup (<user2>) | Raw backup to Qdrant |

## What is Captured

### Redis Buffer (Raw Turns)
- **Keys:** `mem:<user1>`, `mem:<user2>`, `mem:<agent>`
- **Format:** JSON list of turns with:
  - `turn`: Turn number
  - `role`: "user" or "assistant"
  - `content`: Text (truncated to 2000 chars)
  - `timestamp`: ISO timestamp
  - `user_id`: User identifier
  - `session`: Session identifier
  - `validation_warnings`: Injection pattern warnings (if any)

### True Recall (Curated Gems)
- **Collection:** `true_recall`
- **Format:** Structured gems with:
  - `gem`: Extracted insight/decision/preference
  - `categories`: Relevant categories
  - `importance`: high/medium/low
  - `confidence`: 0.0-1.0
  - `user_id`: User isolation
  - `timestamp`: When extracted
  - `embedding`: Vector for semantic search

### Daily Files (Human-Readable)
- **Location:** `memory/{<user1>,<user2>,<agent>}/2009-01-02.md`
- **Format:** Markdown notes
- **Purpose:** Human review and editing

### Qdrant Collections

| Collection | Purpose | Retention |
|------------|---------|-----------|
| `true_recall` | AI-curated gems | Permanent |
| `<agent>-memories` | Raw conversation backup | Permanent (implement retention policy via household-memory evergreen if needed) |

## How Memory Flows

```
┌─────────────────┐
│   Conversation  │
└────────┬────────┘
         │ save_mem.py
         ▼
┌─────────────────┐
│  Redis Buffer   │ ◄── Fast capture (mem:<user1>, mem:<user2>, mem:<agent>)
└────────┬────────┘
         │
         ├──────────────────────┐
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ True Recall     │    │ Jarvis Memory   │
│ (2:30 AM)       │    │ (3:00 AM)       │
│ Curated Gems    │    │ Raw Backup      │
└────────┬────────┘    └────────┬────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Qdrant          │    │ Qdrant          │
│ true_recall     │    │ <agent>-memories   │
└─────────────────┘    └─────────────────┘
```

## Current Coverage

> **Note:** Values below are illustrative examples. Your actual counts will differ after first run.

| Source | <user1> | <user2> | <agent> |
|--------|------|-------|------|
| Redis Buffer | 0 items (grows with usage) | 0 items (grows with usage) | 0 items (grows with usage) |
| True Recall | 0 gems (grows with curation) | 0 gems (grows with curation) | 0 gems (grows with curation) |
| Daily Files | ⏳ Manual | ⏳ Manual | ⏳ Manual |
| Qdrant (<agent>-memories) | ⏳ Not yet checked | ⏳ Not yet checked | ⏳ Not yet checked |

## Gaps Identified

1. **<user2> Memory Capture:** No Redis items yet (no conversations recorded via this system)
2. **Daily File Automation:** Currently manual
3. **Retention Policy:** No clear retention for Qdrant collections
4. **Memory Expiry:** No mechanism to forget outdated information

## Recommendations

1. **Automate Daily File Creation:** Add to heartbeat or cron
2. **Define Retention Policy:** 90 days for raw, permanent for gems?
3. **Add Memory Expiry:** Allow users to request forgetting
4. **Cross-Session Context:** Better handoff between sessions

---

*Created: 2009-01-02*
*Reference: evergreens/household-memory/STATE.md*