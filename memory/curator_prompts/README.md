# Curator Prompts

This directory contains the prompts loaded by `curate_memories.py`.

- **`base.md`** — The base curator system prompt (loaded for all users). This is the canonical source.
- **`<user_id>.md`** — Per-user curator instructions (optional, appended after `base.md`)

The Curator extracts "gems" (valuable moments) from daily conversations and stores them as long-term memories in Qdrant.

## Per-User Prompts

Create `<user_id>.md` files in this directory to add user-specific curator instructions. The `curate_memories.py` script automatically loads `curator_prompts/<user_id>.md` (if it exists) and appends it to `curator_prompts/base.md` before running curation for that user.

Example: `alice.md` might contain speaker label mappings or user-specific extraction rules.
