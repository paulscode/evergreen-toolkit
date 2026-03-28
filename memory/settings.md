<!-- REFERENCE DOCUMENT: This file documents configuration variables and their
     defaults. It is NOT a config file — no script reads this file.
     Actual settings are in .memory_env, --user-id arguments in cron jobs,
     and curator prompt files. The “Household Members” section below shows
     the EXAMPLE format; customize it during setup per AGENT-ONBOARDING.md. -->

# True Recall Settings

> **⚠️ Reference document only** — to change configuration, edit `.memory_env` (see `config/memory_env.example` for the template). No script reads this file.

Configuration reference for the True Recall memory system. Actual values are set in your `.memory_env` file.

> **Note:** The actual user ID configuration happens through `.memory_env` (`DEFAULT_USER_ID`), `--user-id` arguments in cron jobs, and curator prompt files.

---

## General Settings

### Agent Name
- **Variable:** `AGENT_NAME`
- **Default:** *(none — must be set)*
- **Description:** Name of your OpenClaw agent instance. Used to construct collection names (e.g., `<agent>-memories`) and identify the agent in logs.
- **Format:** String (lowercase, alphanumeric, hyphens allowed)
- **Example:** `myagent`

### Workspace Path
- **Variable:** `OPENCLAW_WORKSPACE`
- **Default:** `~/.openclaw/workspace`
- **Description:** Root directory of your OpenClaw workspace. Memory scripts use this to locate memory files. Optional — defaults to `~/.openclaw/workspace` if not set.
- **Format:** Absolute directory path
- **Example:** `/home/alice/.openclaw/workspace`

### Default User ID
- **Variable:** `DEFAULT_USER_ID`
- **Default:** *(none — must be set)*
- **Description:** Primary user ID for memory capture scripts. Used as the default `--user-id` when no explicit user is specified. Set this to your primary household member's ID.
- **Format:** String (lowercase, alphanumeric, hyphens allowed)
- **Example:** `alice`

---

## Redis Settings

### Redis Host
- **Variable:** `REDIS_HOST`
- **Default:** `localhost`
- **Description:** Hostname or IP address of the Redis server
- **Format:** IP address or hostname string

### Redis Port
- **Variable:** `REDIS_PORT`
- **Default:** `6379`
- **Description:** Port number Redis is listening on
- **Format:** Integer (1-65535)
- **Range:** Well-known ports: 6379, 6380

### Redis Key Pattern
- **Convention:** `REDIS_KEY_PATTERN`
- **Default:** `mem:{user_id}`
- **Description:** Pattern for Redis keys storing conversation turns. This pattern is hardcoded in memory scripts (not a configurable env var) — documented here for reference.
- **Format:** String with `{user_id}` placeholder
- **Example:** `mem:alice`, `mem:bob`

### Redis TTL (Time-To-Live)
- **Variable:** `REDIS_TTL_HOURS`
- **Default:** `24` (hours)
- **Description:** How long conversation data stays in Redis before curation
- **Format:** Integer
- **Range:** 1-168 hours (1 hour to 1 week)
- **Note:** 24 hours recommended for daily curation

---

## Qdrant Settings

### Qdrant URL
- **Variable:** `QDRANT_URL`
- **Default:** `http://localhost:6333`
- **Description:** HTTP endpoint of Qdrant vector database
- **Format:** `http://hostname:port`

### Qdrant Collection Names

The default architecture uses **two Qdrant collections**:

| Collection | Purpose | Populated By | Schedule |
|------------|---------|-------------|----------|
| `true_recall` | AI-curated gems (decisions, insights, preferences) | `curate_memories.py` | 2:30 AM |
| `<agent>-memories` | Raw conversation backup (all turns) | `cron_backup.py` | 3:00 AM |

**Important:** True Recall (2:30 AM) MUST run before Jarvis backup (3:00 AM). Jarvis clears Redis after backup; True Recall does NOT.

- **Variable:** `QDRANT_COLLECTION`
- **Default:** `<agent>-memories` (replace `<agent>` with your agent name, e.g., `myagent-memories`)
- **Description:** Name of the Qdrant collection for raw conversation backups (Jarvis Memory)
- **Format:** String (alphanumeric, hyphens, underscores allowed)

### True Recall Collection
- **Variable:** `TRUE_RECALL_COLLECTION`
- **Default:** `true_recall`
- **Description:** Name of the Qdrant collection for AI-curated gems (True Recall)
- **Format:** String (alphanumeric, hyphens, underscores allowed)
- **Note:** Both collections are created by `init_memory_collections.py`. The `QDRANT_COLLECTION` variable controls the raw backup collection; `TRUE_RECALL_COLLECTION` controls the curated gems collection.

### Qdrant Vector Size
- **Variable:** `EMBEDDING_DIMENSIONS`
- **Default:** `1024`
- **Description:** Dimension of embedding vectors — must match your embedding model
- **Format:** Integer
- **Note:** Must match the embedding model output size (e.g., `snowflake-arctic-embed2` = 1024)

---

## Ollama / Embedding Settings

### Ollama URL
- **Variable:** `OLLAMA_URL`
- **Default:** `http://localhost:11434`
- **Description:** HTTP endpoint of Ollama server (used by the toolkit's Python scripts). Note: Ollama's own CLI uses the `OLLAMA_HOST` env var — both should point to the same Ollama instance.
- **Format:** `http://hostname:port`

### Embedding Model
- **Variable:** `EMBEDDING_MODEL`
- **Default:** `snowflake-arctic-embed2`
- **Description:** Model used for generating embeddings
- **Format:** String (Ollama model name)
- **Options:** 
  - `snowflake-arctic-embed2` (default, 1024 dims)
  - `mxbai-embed-large` (1024 dims, 66.5 MTEB)
  - `nomic-embed-text` (768 dims)
- **Note:** Must match the model used during curation; affects vector size

---

## Curation Settings (curate_memories.py)

### Hours to Process
- **Variable:** `HOURS_TO_PROCESS`
- **Default:** `24`
- **Description:** How many hours of conversation to process per curation run
- **Format:** Integer
- **Range:** 1-168 hours

### Confidence Threshold
- **Variable:** `MIN_CONFIDENCE`
- **Default:** `0.7`
- **Description:** Minimum confidence score for a gem to be stored. The curator prompt (see `curator_prompts/base.md`) allows gems with confidence ≥0.6 as a floor; this setting acts as a post-processing filter. Gems scoring between 0.6 and this value are extracted by the curator but not stored.
- **Format:** Float
- **Range:** 0.0-1.0
- **Recommendation:** 0.6-0.8; higher = stricter filtering

### Curator LLM Model
- **Variable:** `CURATION_MODEL`
- **Default:** `qwen3:4b`
- **Description:** Ollama model used for curation (extracting gems)
- **Format:** String (Ollama model name)
- **Options:**
  - `qwen3:4b` (recommended, fast, capable)
  - `qwen3:8b` (more capable, slower)
  - `llama3:8b` (alternative)

### Curator System Prompt
- **Variable:** `CURATOR_PROMPT_FILE`
- **Default:** `curator_prompts/base.md`
- **Description:** Path to the system prompt file for the curator LLM
- **Format:** File path string

---

## Search Settings (search_memories.py)

### Default Search Limit
- **Variable:** `DEFAULT_LIMIT`
- **Default:** `5`
- **Description:** Maximum number of results to return
- **Format:** Integer
- **Range:** 1-100

### Minimum Similarity Score
- **Variable:** `MIN_SCORE` / `--min-score`
- **Default:** `0.5`
- **Description:** Minimum similarity threshold for search results
- **Format:** Float
- **Range:** 0.0-1.0
- **Recommendation:** 0.5-0.7; higher = more precise but may miss relevant results

---

## OpenClaw Plugin Settings (memory-qdrant)

These settings are in your OpenClaw configuration at `~/.openclaw/openclaw.json` under `plugins.entries.memory-qdrant.config`. See `config/openclaw-plugins.example.json` in this toolkit for a template to copy from:

### autoCapture
- **Default:** `false`
- **Description:** Whether to automatically capture conversations to memory
- **Format:** Boolean
- **Note:** Keep false; use mem-redis for capture instead

### autoRecall
- **Default:** `true`
- **Description:** Whether to automatically inject relevant memories before AI responses
- **Format:** Boolean
- **Recommendation:** `true` for auto-injection

### collectionName
- **Default:** `<agent>-memories`
- **Description:** Qdrant collection to use for recall
- **Format:** String

### embeddingModel
- **Default:** `snowflake-arctic-embed2`
- **Description:** Embedding model for query encoding
- **Format:** String (must match curation model)
- **Must match:** The collection's embedding model

### maxRecallResults
- **Default:** `2`
- **Description:** Maximum number of memories to inject per response
- **Format:** Integer
- **Range:** 1-10
- **Note:** Higher = more context but more token usage

### minRecallScore
- **Default:** `0.7`
- **Description:** Minimum similarity score for memories to be injected
- **Format:** Float
- **Range:** 0.0-1.0
- **Important:** This is the MAIN setting affecting auto-injection
- **Recommendation:** Lower to `0.5` if memories aren't being injected

---

## Cron Schedule

### Curation Time
- **Default:** `30 2 * * *` (2:30 AM daily)
- **Description:** When the curator runs automatically
- **Format:** Standard cron format (minute hour day month weekday)
- **Example:** `30 2 * * *` = 2:30 AM every day
- **Important:** Must run before Jarvis backup (which clears Redis). See `config/crontab.sample`.

---

## File Locations

| Component | Script Location |
|-----------|-----------------|
| Curation | `memory/scripts/curate_memories.py` |
| Search | `memory/scripts/search_memories.py` |
| System Prompt | `memory/curator_prompts/base.md` |
| Redis Buffer | `mem:{user_id}` |
| Qdrant Collection | Configured via `QDRANT_COLLECTION` env var |

---

## Household Members

<!-- EXAMPLE: Replace the entire section below with your household members.
     The relationship format is optional — use whatever structure fits your household. -->

> **Reference only.** This section documents your household for human/agent readability. No script reads this file. Functional configuration lives in `.memory_env` and per-user curator prompts in `memory/curator_prompts/`.

Define each household member the AI agent interacts with. This section is the canonical place for member definitions — referenced by the memory curation system and multi-user guides.

```markdown
# Example — replace with your actual household members:

- **<user1-display-name>** (User ID: <user1>)
  - Primary communication: <channel, e.g. WhatsApp, Email>
  - Notes: <relevant context for the AI, e.g. interests, technical level>

- **<user2-display-name>** (User ID: <user2>)
  - Primary communication: <channel>
  - Notes: <relevant context>

# Relationships (optional)
- <user1-display-name> is <user2-display-name>'s <relationship>
- They share a household AI agent
```

> **Shipped example (for reference):** Alice (non-technical, WhatsApp) and Bob (technical, Email) are the example personas used in documentation. Replace them with your actual household members.

**Instructions:**
- Replace example names/IDs with your actual household members
- Create a matching `memory/<user_id>/` directory for each member
- Create a `memory/curator_prompts/<user_id>.md` file for each member (optional but recommended)
- See [`MULTI-USER-GUIDE.md`](MULTI-USER-GUIDE.md) for full multi-user setup details

---

## Quick Reference

```bash
# Minimal environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export QDRANT_URL=http://localhost:6333
export OLLAMA_URL=http://localhost:11434
export EMBEDDING_MODEL=snowflake-arctic-embed2
export QDRANT_COLLECTION=<agent>-memories
```

---

*Last updated: 2009-01-02*
