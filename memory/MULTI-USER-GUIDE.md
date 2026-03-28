# 👨‍👩‍👧‍👦 Multi-User Memory System

**Supporting theory of mind in household AI agents.**

> **Placeholder note:** Examples in this file use `alice`, `bob`, and `eve` as concrete user IDs to illustrate the system. Replace these with your actual household member IDs during setup. See [docs/NAME-CUSTOMIZATION.md](../docs/NAME-CUSTOMIZATION.md) for replacement guidance.

This guide explains how the Evergreen Toolkit's memory system supports multiple users in a household, maintaining separate memory spaces while enabling the AI to understand relationships and context across users.

---

## Why Multi-User Matters

In a household with multiple people (e.g., Alice, Bob, and other family members), the AI agent needs to:

1. **Remember who said what** - Attribute memories to the correct person
2. **Understand relationships** - "Bob is Alice's husband", "Alice is Bob's wife"
3. **Maintain privacy** - Personal memories stay personal unless explicitly shared
4. **Build theory of mind** - Understand that different people have different knowledge, preferences, and perspectives
5. **Context-switch seamlessly** - Talk to Alice about her grandkids, then switch to Bob about Bitcoin

Without user separation, the AI would confuse memories, attribute statements to the wrong person, and fail to build accurate mental models of each individual.

---

## Architecture Overview

### User-Specific Memory Keys

Each user has isolated memory storage at every layer:

```
┌──────────────────────────────────────────────────────────────┐
│ Redis Buffer (Fast Capture)                                  │
├──────────────────────────────────────────────────────────────┤
│ mem:<user1>  → User 1's conversation buffer                  │
│ mem:<user2>  → User 2's conversation buffer                  │
│ mem:<agent>  → System-level memories                         │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Daily Files (Human-Readable)                                 │
├──────────────────────────────────────────────────────────────┤
│ memory/<user1>/2009-01-02.md  → User 1's daily log           │
│ memory/<user2>/2009-01-02.md  → User 2's daily log           │
│ memory/<agent>/2009-01-02.md  → System logs                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Qdrant Collections (Semantic Search)                         │
├──────────────────────────────────────────────────────────────┤
│ Collection: <agent>-memories       → All users' embeddings    │
│   (isolated by user_id filter per query)                     │
│ Collection: true_recall           → Curated gems (all users) │
└──────────────────────────────────────────────────────────────┘
```

### Metadata Isolation

Every memory item includes `user_id` metadata:

```json
{
  "gem": "User decided to use Redis over Postgres for caching",
  "user_id": "user1",
  "categories": ["decision", "technical"],
  "timestamp": "2009-01-02T14:30:00Z",
  // ... other fields
}
```

This enables:
- **User-specific search** - `search_memories.py "Redis" --user-id user1`
- **Cross-user relationship tracking** - "Bob mentioned his wife Alice"
- **Privacy boundaries** - Personal memories not leaked between users

---

## Configuration

### Step 1: Define Your Users

Review and customize `memory/settings.md` with your household members:

```markdown
## Household Members

| User ID | Name | Channel | Phone | Notes |
|---------|------|---------|-------|-------|
| `alice` | Alice Smith | WhatsApp | +11234567890 | Primary user, non-technical |
| `bob` | Bob Smith | WhatsApp, Webchat | +12345678901 | Technical support, Bitcoin expert |
| `eve` | System | All | N/A | AI agent system memories |
```

### Step 2: Configure Default User

In `.memory_env`:

```bash
# Default user (fallback if not specified)
DEFAULT_USER_ID=alice
```

> **Note:** The Redis key pattern `mem:{user_id}` is hardcoded in memory scripts (not configurable via env var). All scripts use `mem:<user_id>` automatically — see `memory/settings.md` for details.

### Step 3: Configure Qdrant Collection

All users share a single Qdrant collection per storage type, isolated by `user_id` metadata filter.
There are **two** collections total: `QDRANT_COLLECTION` (raw backups via Jarvis) and `TRUE_RECALL_COLLECTION` (curated gems via True Recall). Both use `user_id` for multi-user isolation:

```bash
# Shared collections (one per type, all users isolated by user_id filter)
QDRANT_COLLECTION=<agent>-memories

# All users' memories are stored here with user_id metadata
# Queries filter by user_id automatically:
#   search_memories.py "query" --user-id alice  → only alice's results
#   search_memories.py "query" --user-id bob    → only bob's results
```

### Step 4: Create Per-User Curator Prompts

Each user can have a customized True Recall curator prompt that reflects their interests and communication style:

```bash
# Copy the example template for each household member
cp memory/curator_prompts/example-user.md memory/curator_prompts/<user1>.md
cp memory/curator_prompts/example-user.md memory/curator_prompts/<user2>.md

# Customize each prompt for the user's context
nano memory/curator_prompts/<user1>.md
nano memory/curator_prompts/<user2>.md
```

Adjust the prompt to reflect each user's interests, technical level, and what types of memories matter most to them. See `memory/curator_prompts/README.md` for guidance.

### Step 5: Set Up User Detection

The AI agent must detect which user it's talking to. The toolkit ships with `save_current_session_memory.py` which handles auto-detection via phone number matching (configure `USER_PHONE_MAP` in that script). **Option A is recommended for most deployments** as it's the most reliable and requires no AI-side logic. The options below are for custom implementations if the default doesn't fit your setup:

**Option A: Channel-based detection (recommended)** (customize `USER_PHONE_MAP` in `save_current_session_memory.py`)
```python
# WhatsApp number → user_id mapping
USER_PHONE_MAP = {
    "+11234567890": "alice",
    "+12345678901": "bob",
}

def detect_user(channel_metadata):
    phone = channel_metadata.get('from')
    return USER_PHONE_MAP.get(phone, DEFAULT_USER_ID)
```

**Option B: Explicit user_id in session**
```python
# OpenClaw session metadata includes user_id
session = get_current_session()
user_id = session.metadata.get('user_id', DEFAULT_USER_ID)
```

**Option C: Conversation context**
```python
# Analyze conversation to infer user
# (e.g., if conversation mentions "my husband Bob", likely Alice)
def infer_user_from_context(conversation):
    if "husband Bob" in conversation:
        return "alice"
    if "wife Alice" in conversation:
        return "bob"
    return DEFAULT_USER_ID
```

---

## Usage Examples

### Saving Memories (User-Specific)

```bash
# Save Alice's conversation
python3 memory/scripts/save_mem.py --user-id alice

# Save Bob's conversation
python3 memory/scripts/save_mem.py --user-id bob

# System-level memory (agent's own knowledge)
python3 memory/scripts/save_mem.py --user-id eve
```

### Searching Memories (Isolated by User)

```bash
# Search Alice's memories only
python3 memory/scripts/search_memories.py "grandkids birthday" --user-id alice

# Search Bob's memories only
python3 memory/scripts/search_memories.py "Bitcoin OAuth setup" --user-id bob

# Hybrid search (keyword + vector) for specific user
python3 memory/scripts/hybrid_search.py "OpenAI configuration" --user-id bob
```

### Getting User Context

```bash
# Get last 24 hours of context for Alice
python3 memory/scripts/get_user_context.py --user-id alice --hours 24

# Get context formatted as markdown for prompt injection
python3 memory/scripts/get_user_context.py --user-id alice --hours 24 --format markdown
```

### Curation (Multi-User Aware)

The True Recall curator processes each user separately:

```bash
# Curate Alice's gems
python3 memory/scripts/curate_memories.py --user-id alice

# Curate Bob's gems
python3 memory/scripts/curate_memories.py --user-id bob
```

The curator prompt includes user context:
```markdown
You are curating memories for **Alice**. She is a non-technical Christian, pro-American, starting a bookkeeping business.

Focus on:
- Her grandkids (names, ages, important dates)
- Business decisions for AcmeBookkeeping
- Preferences (likes/dislikes)
- Decisions and commitments she's made

Ignore technical implementation details unless she explicitly decided something.
```

---

## Theory of Mind Implementation

### What is Theory of Mind?

Theory of mind is the ability to understand that others have:
- **Different knowledge** - Alice doesn't know what Bob knows about Bitcoin
- **Different beliefs** - Bob believes Bitcoin will be global reserve currency; Alice may not care
- **Different perspectives** - "My husband Bob" (Alice's view) vs "my wife Alice" (Bob's view)
- **Different preferences** - Alice prefers WhatsApp; Bob prefers Webchat for technical work

### How We Support It

#### 1. User-Specific Prompts

Each user gets a customized curator prompt in `memory/curator_prompts/{user_id}.md`:

```markdown
# Alice's Curator Prompt

You are curating memories for **Alice Smith**.

## About Alice
- Non-technical, prefers simple explanations
- Devout Christian, conservative-leaning, pro-American
- Starting AcmeBookkeeping business
- Loves her grandkids, very family-oriented
- Prefers WhatsApp for communication
- Doesn't tolerate obscenity or bad language

## What to Capture
- Decisions about her business
- Grandkids' names, ages, milestones
- Family events and commitments
- Preferences (likes/dislikes)
- Health-related decisions
- Financial/bookkeeping insights she shares

## What to Ignore
- Technical implementation details
- Cryptocurrency discussions (unless she's making a decision)
- Agent architecture conversations
```

#### 2. Relationship Tracking

The system captures relationships in memories:

```json
{
  "gem": "Bob is Alice's husband, provides technical support for Eve AI",
  "user_id": "alice",
  "categories": ["knowledge", "preference", "insight"],
  "confidence": 0.95
}
```

This enables the AI to understand:
- When Alice mentions "Bob", she means her husband
- When Bob mentions "Alice", she's his wife
- The AI can context-switch: talk to Alice about Bob differently than talking to Bob about Alice

#### 3. Knowledge Boundaries

The AI must respect knowledge boundaries:

```python
# When talking to Alice:
context = get_user_context("alice", hours=24)
# Should include: Alice's memories, general knowledge
# Should NOT include: Bob's private technical conversations

# When talking to Bob:
context = get_user_context("bob", hours=24)
# Should include: Bob's memories, technical details
# Can include: Alice's memories if relevant (she's his wife)
```

#### Verifying Theory of Mind

To confirm user isolation and theory of mind are working correctly:

1. **Save a memory for user A** with a distinctive preference (e.g., "Alice mentioned she prefers morning walks")
2. **Search as user B** — `python3 memory/scripts/search_memories.py "morning walks" --user-id bob` — the preference should **not** appear
3. **Search as user A** — `python3 memory/scripts/search_memories.py "morning walks" --user-id alice` — the preference **should** appear
4. **Cross-reference** — If Bob asks "does Alice like walking?", the AI should search Alice's memories (with appropriate privacy boundaries) to respond

#### 4. Cross-User References

When a user mentions another user, create a cross-reference:

```python
# Alice says: "Bob helped me set up WhatsApp"
# Memory created:
{
  "gem": "Bob helped Alice set up WhatsApp for Eve AI",
  "user_id": "alice",
  "mentioned_users": ["bob"],
  "categories": ["technical", "knowledge"],
  "timestamp": "2009-01-02T14:30:00Z"
}

# This memory is:
# - Stored in <agent>-memories collection (filtered by user_id=alice)
# - Tagged with mentioned_users: ["bob"]
# - Can be found when searching either user's context (if appropriate)
```

---

## Privacy & Security

### Memory Isolation

By default, users cannot access each other's memories:

```bash
# Alice's search only returns Alice's memories
python3 memory/scripts/search_memories.py "Bitcoin" --user-id alice
# Result: [] (Alice hasn't discussed Bitcoin)

# Bob's search returns Bob's memories
python3 memory/scripts/search_memories.py "Bitcoin" --user-id bob
# Result: [Bob's Bitcoin OAuth discussion]
```

### Shared Memories

Some memories are explicitly shared (system-level):

```bash
# System memories (accessible to all users)
python3 memory/scripts/save_mem.py --user-id eve
# Example: "Eve's voice is Nova (warm, slightly British)"
# Note: System-level memories are stored under the agent's user_id (e.g., eve)
# and can be queried by any user's search. There is no separate --shared flag.
```

### User Consent

Before storing sensitive memories:

```markdown
**Sensitive Topics** (require explicit consent):
- Health information
- Financial details (account numbers, passwords)
- Personal relationships
- Legal matters

**Implementation:**
If conversation touches on sensitive topics:
1. Ask user: "Should I remember this?"
2. If yes, store with appropriate category
3. If no, skip memory capture for that turn
```

---

## Testing Multi-User Setup

### Test 1: User Isolation

```bash
# Save different memories for each user
python3 memory/scripts/save_mem.py --user-id alice
# (Have conversation about grandkids)

python3 memory/scripts/save_mem.py --user-id bob
# (Have conversation about Bitcoin)

# Verify isolation
python3 memory/scripts/search_memories.py "grandkids" --user-id alice
# Should return: Alice's grandkids memories

python3 memory/scripts/search_memories.py "grandkids" --user-id bob
# Should return: [] (Bob hasn't discussed grandkids)
```

### Test 2: Relationship Tracking

```bash
# Alice mentions Bob
python3 memory/scripts/save_mem.py --user-id alice
# Conversation: "Bob helped me set up the AI"

# Check memory includes relationship
python3 memory/scripts/search_memories.py "Bob" --user-id alice
# Should mention: "husband Bob" or "Bob helped"
```

### Test 3: Context Switching

```bash
# Get Alice's context
python3 memory/scripts/get_user_context.py --user-id alice --hours 24
# Should include: Alice's conversations, preferences

# Get Bob's context
python3 memory/scripts/get_user_context.py --user-id bob --hours 24
# Should include: Bob's technical discussions

# Verify no leakage
# Alice's context should NOT include Bob's Bitcoin OAuth details
```

---

## Common Issues

### Issue: Memories Mixed Between Users

**Symptom:** Searching Alice's memories returns Bob's memories

**Cause:** `user_id` not being passed to save script

**Fix:**
```python
# Always pass user_id explicitly
python3 memory/scripts/save_mem.py --user-id alice  # ✅ Correct
python3 memory/scripts/save_mem.py  # ❌ Wrong (uses DEFAULT_USER_ID)
```

### Issue: Wrong Collection Name

**Symptom:** Qdrant search returns no results

**Cause:** Collection name mismatch between `.memory_env` and actual Qdrant collection

**Fix:**
```bash
# Verify collection exists
curl http://localhost:6333/collections

# Should see your configured collection name (e.g., <agent>-memories)

# If missing, initialize:
python3 memory/scripts/init_memory_collections.py
```

### Issue: User Detection Failing

**Symptom:** All memories saved to wrong user

**Cause:** User detection logic incorrect

**Fix:**
```python
# Log detected user_id
print(f"Detected user: {user_id}")

# Verify mapping
USER_PHONE_MAP = {
    "+11234567890": "alice",  # Verify this is correct
    "+12345678901": "bob",
}
```

---

## Best Practices

### 1. Consistent User IDs

Use the same `user_id` across all systems:
- Redis keys: `mem:alice`
- Qdrant filter: `user_id=alice` (within shared collection)
- File paths: `memory/alice/2009-01-02.md`
- Script arguments: `--user-id alice`

### 2. Clear User Definitions

Document each user in `memory/settings.md`:
- Name, communication channels, phone numbers
- Technical proficiency level
- Key relationships to other users
- Privacy preferences

### 3. Regular Audits

Monthly, audit memory isolation:
```bash
# Check for cross-user contamination
for user in alice bob eve; do
  echo "=== $user ==="
  python3 search_memories.py "" --user-id $user --limit 5
done
```

### 4. Theory of Mind Testing

Regularly test the AI's understanding:
- Ask Alice: "What does Bob think about Bitcoin?" (should know she doesn't care)
- Ask Bob: "What did Alice say about her grandkids?" (should recall)
- Ask about relationships: "Who is Alice to you?" (should answer correctly)

---

## Per-User File Structure

When `--user-id` is provided, daily memory files and hybrid search use per-user directories:

```
memory/
├── alice/
│   ├── 2009-01-02.md      ← Alice's daily log
│   └── 2009-01-03.md
├── bob/
│   ├── 2009-01-02.md      ← Bob's daily log
│   └── 2009-01-03.md
├── eve/
│   └── 2009-01-03.md      ← System/agent logs
├── 2009-01-02.md           ← Flat directory (used when --user-id is omitted)
└── settings.md
```

The `hybrid_search.py` script checks per-user directories first, then falls back to the flat directory:

```bash
# Searches alice/ subdirectory for daily files, then Qdrant with user_id filter
python3 memory/scripts/hybrid_search.py "grandkids birthday" --user-id alice --days-back 7

# No --user-id: searches flat directory (default without --user-id)
python3 memory/scripts/hybrid_search.py "grandkids birthday"
```

### Organizing Existing Files into Per-User Directories

If you have existing daily files in the flat `memory/` directory, you can organize them:

```bash
# Create per-user directories (e.g., alice, bob)
mkdir -p memory/<user1> memory/<user2>

# Move files (if you can identify which user they belong to)
# Or leave them in place — hybrid_search.py falls back to the flat directory
```

---

## Phone-to-User Mapping (Voice/WhatsApp)

For voice calls and WhatsApp, user identity is resolved from the caller's phone number. Create a mapping file:

### Setup

Create `~/.openclaw/user-phone-mapping.json`:

```json
{
  "+11234567890": "alice",
  "+12345678901": "bob"
}
```

### How It Works

1. **Incoming call/message** → OpenClaw receives the sender's phone number (E.164 format)
2. **Lookup** → The gateway reads `user-phone-mapping.json` to resolve user_id
3. **Memory operations** → All `store_memory.py`, `search_memories.py`, and `hybrid_search.py` calls include `--user-id <resolved_user>`
4. **Isolation** → Qdrant queries filter by `user_id` in the payload

### Integration with OpenClaw Gateway

The gateway's `memory-tool.ts` resolves the caller identity. See [OPENCLAW-FORK-CHANGES.md](OPENCLAW-FORK-CHANGES.md) for the TypeScript changes needed in your OpenClaw fork.

---

## OpenClaw Fork Changes for Full Isolation

To wire multi-user isolation end-to-end through the OpenClaw gateway, several TypeScript files need modification. These changes ensure that:

1. **Voice calls** resolve user identity from the caller's phone number
2. **Chat/web sessions** can pass user_id through session metadata
3. **Memory tools** pass `--user-id` to all Python scripts
4. **System prompts** instruct the AI to maintain separate mental models per user

See [OPENCLAW-FORK-CHANGES.md](OPENCLAW-FORK-CHANGES.md) for a complete guide to the required gateway modifications.

---

## Script Changes Summary

The following scripts support `--user-id` for multi-user isolation:

| Script | `--user-id` | Payload `user_id` | Per-User Dirs | Notes |
|--------|:-----------:|:------------------:|:-------------:|-------|
| `search_memories.py` | ✅ | N/A (filter) | N/A | Filters Qdrant results by user_id |
| `hybrid_search.py` | ✅ | N/A (filter) | ✅ | Checks `memory/<user_id>/` first |
| `store_memory.py` | ✅ | ✅ | N/A | Stores user_id in Qdrant payload |
| `store_conversation.py` | ✅ | ✅ | N/A | Stores user_id in both turns |
| `daily_conversation_backup.py` | ✅ | ✅ | N/A | |
| `harvest_sessions.py` | ✅ | ✅ | N/A | |
| `auto_store.py` | ✅ | ✅ | N/A | |

### Usage Pattern

```bash
# All memory operations should include --user-id when known:
python3 memory/scripts/store_memory.py "Alice prefers morning calls" --user-id alice
python3 memory/scripts/store_conversation.py "What's the weather?" "It's sunny today" --user-id alice
python3 memory/scripts/hybrid_search.py "morning preference" --user-id alice
python3 memory/scripts/search_memories.py "morning preference" --user-id alice
python3 memory/scripts/daily_conversation_backup.py 2009-01-02 --user-id alice
```

---

## Setting Up Multi-User from Single-User

### Step 1: Create User Phone Mapping

```bash
# Create the mapping file
cat > ~/.openclaw/user-phone-mapping.json << 'EOF'
{
  "+11234567890": "alice",
  "+12345678901": "bob"
}
EOF
```

### Step 2: Create Per-User Memory Directories

```bash
mkdir -p memory/<user1>
mkdir -p memory/<user2>
```

### Step 3: Tag Existing Qdrant Entries

Existing memories in Qdrant won't have `user_id` fields. You can backfill them:

```python
#!/usr/bin/env python3
"""Backfill user_id on existing Qdrant entries"""
import json, urllib.request

QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION = "<agent>-memories"  # your collection name
DEFAULT_USER = "alice"       # assign existing entries to this user

# Scroll all points
scroll_data = json.dumps({"limit": 100, "with_payload": True}).encode()
req = urllib.request.Request(
    f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
    data=scroll_data, headers={"Content-Type": "application/json"}, method="POST"
)
with urllib.request.urlopen(req) as resp:
    points = json.loads(resp.read())["result"]["points"]

# Update points missing user_id
for p in points:
    if "user_id" not in p["payload"]:
        set_data = json.dumps({
            "points": [p["id"]],
            "payload": {"user_id": DEFAULT_USER}
        }).encode()
        req = urllib.request.Request(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/payload",
            data=set_data, headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req)
        print(f"Tagged {p['id'][:8]}... with user_id={DEFAULT_USER}")
```

### Step 4: Update Cron Jobs

```bash
# Before (single user):
30 3 * * * cd $WORKSPACE && source $WORKSPACE/.memory_env && $WORKSPACE/.venv/bin/python3 $WORKSPACE/memory/scripts/daily_conversation_backup.py

# After (multi-user):
30 3 * * * cd $WORKSPACE && source $WORKSPACE/.memory_env && $WORKSPACE/.venv/bin/python3 $WORKSPACE/memory/scripts/daily_conversation_backup.py --user-id <user1>
35 3 * * * cd $WORKSPACE && source $WORKSPACE/.memory_env && $WORKSPACE/.venv/bin/python3 $WORKSPACE/memory/scripts/daily_conversation_backup.py --user-id <user2>
```

### Step 5: Apply OpenClaw Fork Changes

Follow the guide in [OPENCLAW-FORK-CHANGES.md](OPENCLAW-FORK-CHANGES.md) to wire user identity through the gateway.

---

## Future Enhancements

### Planned Features

1. **Shared Memory Spaces** - Explicitly shared memories between specific users
2. **Relationship Graph** - Visual map of household relationships
3. **Permission System** - Fine-grained control over memory access
4. **Cross-User Search** - "Find all mentions of Alice" across all users
5. **Memory Sharing API** - Programmatically share specific memories

### Experimental Features

1. **Group Conversations** - Multiple users in same conversation (e.g., family group chat)
2. **Memory Reconciliation** - Detect conflicting memories between users
3. **Perspective Taking** - "What would Alice think about this?"

---

**Multi-user memory is what transforms an AI assistant from a generic chatbot into a true household companion with theory of mind.** 🌲

For implementation help, see:
- `memory/settings.md` - User configuration
- `memory/curator_prompts/` - User-specific curator prompts
- `evergreens/household-memory/STATE.md` - Active memory experiments
