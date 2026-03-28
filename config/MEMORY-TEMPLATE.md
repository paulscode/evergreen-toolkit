# Memory System — Routing Index

Use retrieval, not preload. This file tells the agent where to look — it is NOT a memory store.

## Where to Look

| Need | Go To |
|------|-------|
| Durable facts about a user | `memory/para/<user>/summary.md` → `items.json` |
| Shared household facts | `memory/para/shared/summary.md` → `items.json` |
| Today's conversation log | `memory/<user>/YYYY-MM-DD.md` |
| Recent high-salience memories | Qdrant `true_recall` collection (filter by `user_id`) |
| Full conversation history | Qdrant `<agent>-memories` collection (filter by `user_id`) |
| User preferences / personality | `memory/para/<user>/areas/` or `memory/curator_prompts/<user>.md` |
| Active projects | `memory/para/<user>/projects/` |
| Contradictions to resolve | `memory/para/<user>/review-queue.md` |
| System architecture | `memory/para/<agent>/` |

## Memory Commands

```bash
# Activate environment (from workspace root)
source .venv/bin/activate
source .memory_env

# Save current session to Redis
python3 memory/scripts/save_mem.py --user-id <user_id>

# Search memories (hybrid: keyword + semantic)
python3 memory/scripts/hybrid_search.py "query" --user-id <user_id>

# Search with date range (dates below are illustrative — use your actual date range)
python3 memory/scripts/search_memories.py "query" --user-id <user_id> --after 2009-01-01 --before 2009-01-23

# Get user context (for session injection)
python3 memory/scripts/get_user_context.py --user-id <user_id> --hours 24
```

## Rules

- **PARA (`memory/para/`) is durable truth.** Nothing overrides it.
- **Daily notes are ephemeral.** Promote important findings to PARA, then archive.
- **Search memory before claiming ignorance.** Try 2+ rephrased queries before giving up.
- **LCM / lossless-claw is session memory**, not durable truth.
- **Keep this file tiny.** Put facts in PARA, not here.

## Common Searches

- `<user> preferences communication`
- `decisions about <topic>`
- `<user> active projects`
- `relationship between <user1> and <user2>`
- `<agent> system configuration`
