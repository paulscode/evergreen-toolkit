# 📋 Configuration Examples

Sample configuration files for Evergreen Toolkit.

---

## ❤️ Heartbeat Template (`HEARTBEAT-TEMPLATE.md`)

Copy this to your workspace root for heartbeat-driven memory capture (handled automatically by `deploy.sh`):

```bash
# Automatic (recommended):
bash scripts/deploy.sh --workspace ~/.openclaw/workspace

# Manual alternative:
cp config/HEARTBEAT-TEMPLATE.md ~/.openclaw/workspace/HEARTBEAT.md
```

**What it does:** Captures active conversation sessions to Redis every ~30 minutes during heartbeats. This is the **primary memory capture mechanism** — don't rely solely on end-of-day cron jobs.

**Includes:**
- Auto-detection of current session user
- Redis buffer storage
- Fallback manual user ID specification
- Evergreen trigger checking
- Notification processing

**Full documentation:** See [`docs/HEARTBEAT-MEMORY-INTEGRATION.md`](../docs/HEARTBEAT-MEMORY-INTEGRATION.md)

---

## Crontab Example (`crontab.sample`)

See [`crontab.sample`](crontab.sample) for the canonical crontab template with full comments.

**Key points:**
```bash
# Set PATH explicitly (cron has minimal PATH)
# Add your Node.js bin directory if using NVM
PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin
SHELL=/bin/bash

# Memory jobs — use absolute paths (source .venv/bin/activate does NOT work in cron)
# IMPORTANT: source .memory_env to set QDRANT_URL, REDIS_HOST, etc.
30 2 * * * cd $WORKSPACE && source $WORKSPACE/.memory_env && $WORKSPACE/.venv/bin/python3 $WORKSPACE/memory/scripts/curate_memories.py --user-id <user1> >> $WORKSPACE/logs/true-recall.log 2>&1

# Evergreen AI runner: Spawns agent session with locking (recommended)
0 4 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh upstream-architecture
```

**Timezone conversions (example assumes America/Chicago CST — adjust for your timezone):**
- CST (Central): As shown
- PST (Pacific): Subtract 2 hours (4:00 AM CST = 2:00 AM PST)
- EST (Eastern): Add 1 hour (4:00 AM CST = 5:00 AM EST)
- UTC: Add 6 hours (4:00 AM CST = 10:00 AM UTC)

---

## OpenClaw Plugins Example (`openclaw-plugins.example.json`)

See the actual [`openclaw-plugins.example.json`](openclaw-plugins.example.json) for the full configuration with all available plugins (memory-redis, memory-qdrant, voice-call, discord, telegram, whatsapp) and inline descriptions.

**Key plugins:**
- **memory-redis** — Redis buffer for fast memory capture (required)
- **memory-qdrant** — Qdrant vector store for semantic search (required)
- **voice-call** — Twilio/Telnyx telephony support (optional, disabled by default)
- **discord / telegram / whatsapp** — Messaging channel support (optional)

> **Note:** Copy relevant sections from this example to your `~/.openclaw/openclaw.json`. The `voice-call` plugin is optional — only include it if your deployment uses telephony features.

---

## Agenda Template (`agenda-template.md`)

Template used by the AI agent at the start of each evergreen cycle. See the actual [`agenda-template.md`](agenda-template.md) for the full template with all sections (Cycle Status, Tasks, Research Findings, Analysis, Blockers, Next Cycle Plan, Notifications, Cycle Summary).

---

## Categories Example (`categories.example.yaml`)

Per-user interest areas for memory gem classification. Copy to `memory/<user_id>/categories.yaml` for each household member:

```bash
cp config/categories.example.yaml memory/alice/categories.yaml
```

**What it does:** Adds a second layer of user-specific interest tags to curated gems, so memories can be filtered by topic (e.g., relationships, preferences, decisions). The curator prompt classifies gems by *type* (decision, insight, etc.); this file adds *topic* labels.

**Note:** Optional — curation works without this file, but gems won't have interest-area tags.

---

## Environment File (`.memory_env`)

See the actual [`memory_env.example`](memory_env.example) for the full configuration template with detailed comments. Copy it to your toolkit root and customize:

```bash
cp config/memory_env.example .memory_env
nano .memory_env
```

Key variables: `REDIS_HOST`, `REDIS_PORT`, `QDRANT_URL`, `QDRANT_COLLECTION`, `TRUE_RECALL_COLLECTION`, `DEFAULT_USER_ID`, `AGENT_NAME`. See the example file for all options and defaults.

---

## Python Virtual Environment Setup

```bash
# Create virtual environment
cd $WORKSPACE
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify
python3 scripts/run-single-evergreen.py --list
```

---

## Requirements File (`requirements.txt`)

See the actual [`requirements.txt`](../requirements.txt) in the repository root for the current dependency list. Key packages:

- `qdrant-client` — Qdrant vector database client
- `redis` — Redis client for memory buffer
- `requests` — HTTP client
- `pyyaml` — YAML parsing

---

## Backup Script (Example — Create Your Own)

The following is an example backup script you can customize and save as `backup.sh`:

```bash
#!/bin/bash
# Full system backup for OpenClaw

BACKUP_DIR="/backup/openclaw"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORKSPACE="/home/<your-user>/.openclaw/workspace"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup workspace
tar -czf "$BACKUP_DIR/workspace-$TIMESTAMP.tar.gz" \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='logs' \
  "$WORKSPACE"

# Backup Redis (if running locally)
# NOTE: Check your Redis dump location first:
#   redis-cli CONFIG GET dir
# Default on Debian/Ubuntu is /var/lib/redis/dump.rdb
redis-cli SAVE
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis-$TIMESTAMP.rdb" 2>/dev/null

# Backup Qdrant storage
cp -r ~/.openclaw/qdrant-storage "$BACKUP_DIR/qdrant-$TIMESTAMP" 2>/dev/null

# Rotate old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete
find "$BACKUP_DIR" -type d -name "qdrant-*" -mtime +7 -exec rm -rf {} \;

echo "Backup complete: $BACKUP_DIR"
```

---

**Copy and customize these files for your deployment.**
