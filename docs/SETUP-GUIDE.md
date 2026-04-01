# Evergreen Toolkit — Detailed Setup Guide

<!-- AI AGENT NOTE: If you've already followed QUICKSTART.md, skip this file.
     This covers the same steps in more detail. Use only as reference for
     deeper context on any step. Do NOT follow both guides sequentially. -->

> ⚠️ **This is the detailed reference version of [QUICKSTART.md](../QUICKSTART.md).** Follow ONE guide, not both. QUICKSTART is recommended for first-time setup.

> **Status: Reference Document.** The canonical setup path is [QUICKSTART.md](../QUICKSTART.md). This document provides deeper context on the same steps — use it as a reference, not a primary guide.

**For OpenClaw agents serving households.**

This guide walks you through installing and configuring the Evergreen Toolkit for your household AI agent. It follows the same step sequence as [../QUICKSTART.md](../QUICKSTART.md) but with deeper explanations. **Do not follow both guides sequentially** — they cover the same ground at different levels of detail. Pick one.

> **For a condensed quickstart:** See [../QUICKSTART.md](../QUICKSTART.md).
> **For a condensed checklist:** See the [Quick Reference Checklist](#quick-reference-checklist) at the bottom of this document.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone the Toolkit](#1-clone-the-toolkit)
3. [Install Dependencies](#2-install-dependencies)
4. [Decide on Your Names and IDs](#3-decide-on-your-names-and-ids)
5. [Configure .memory_env](#4-configure-memory_env)
6. [Deploy to Workspace](#5-deploy-to-workspace)
7. [Configure Memory](#6-configure-memory)
8. [Test One Evergreen](#7-test-one-evergreen)
9. [Seed Upstream Monitoring](#8-seed-upstream-monitoring)
10. [Customize Example Names](#9-customize-example-names)
11. [Set Up Scheduling](#10-set-up-scheduling)
12. [Verify Everything Works](#11-verify-everything-works)
13. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **OpenClaw** latest stable version
- **Python 3.10+**
- **Redis** (for memory system)
- **Qdrant** (for vector memory storage — install via Docker: `docker run -d --name qdrant -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant`, or see [qdrant.tech](https://qdrant.tech/documentation/guides/installation/))
- **Ollama** (required for memory embeddings and curation — install from [ollama.ai](https://ollama.ai), then pull both models below)
  - Embedding model: `ollama pull snowflake-arctic-embed2`
  - Curation model: `ollama pull qwen3:4b` (or any small instruct model for True Recall gem extraction)

### Optional (Recommended)

- **Node.js 18+** (for the local Markdown Viewer — see `tools/MARKDOWN-VIEWER.md`)
- **OpenClaw Gateway** connected to WhatsApp/Telegram for notifications
- **System tools:** `curl`, `jq` (health checks), `flock` (AI runner locking — pre-installed on most Linux)

### Verify Prerequisites

```bash
# Check Python version (3.10+)
python3 --version

# Check Redis (should return PONG)
redis-cli ping
# If Redis is not installed: sudo apt install redis-server && sudo systemctl start redis

# Check Qdrant (should return version info)
curl http://localhost:6333/

# Check Ollama
ollama --version

# Pull required models
ollama pull snowflake-arctic-embed2
ollama pull qwen3:4b

# Check OpenClaw
openclaw --version

# Check system tools
which curl jq flock
```

> **Or skip ahead:** Clone first (Step 1), install (Step 2), deploy (Step 5), then run `python3 scripts/preflight-check.py` to verify everything at once.

> **No OpenClaw?** You can still use the toolkit with the direct executor (`run-single-evergreen.py`) for all evergreen cycles. Skip the AI runner steps and use the direct executor in your crontab instead. See [../ARCHITECTURE.md](../ARCHITECTURE.md) for the comparison.

---

## 1. Clone the Toolkit

```bash
git clone https://github.com/paulscode/evergreen-toolkit.git ~/evergreen-toolkit
cd ~/evergreen-toolkit
```

> **This is the repo clone, not your workspace.** After setup, you will run `deploy.sh` (Step 5) to copy operational files into your OpenClaw workspace. The cloned repo can be kept for pulling updates or deleted after deployment.

---

## 2. Install Dependencies

```bash
# Option A: Automated setup (recommended)
bash scripts/setup.sh

# Option B: Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p logs
```

### What `setup.sh` Does

1. Creates a Python virtual environment (`.venv`) if it doesn't exist
2. Installs all Python dependencies from `requirements.txt`
3. Copies `config/memory_env.example` to `.memory_env` (with `chmod 600`) if it doesn't exist
4. Makes all shell scripts in `scripts/` executable
5. Creates the `logs/` directory

If you use Option B (manual), you need to handle steps 3-5 yourself.

---

## 3. Decide on Your Names and IDs

Before configuring memory or running evergreens, decide on these values — you'll use them in the next steps:

| Decision | Example | Used In |
|----------|---------|--------|
| **Agent name** | `jarvis`, `friday` | Qdrant collection name, logs, display |
| **Agent system user_id** | `eve`, `jarvis` | Redis key (`mem:<agent>`), system memory dir |
| **Household member IDs** | `alice`, `bob` | Redis keys, memory directories, cron jobs |
| **Timezone** | `America/Chicago` | Cron scheduling |
| **Notification target** (optional) | WhatsApp number, channel ID | Failure alerts |

### Placeholder Mapping

These example personas appear throughout the toolkit documentation. Map them to your household:

| Placeholder | Example in Docs | Your Value |
|-------------|----------------|------------|
| `<agent>` | Eve / eve | __________ |
| `<user1>` | Alice / alice | __________ |
| `<user2>` | Bob / bob | __________ |
| Mom / Dad | Family role labels | __________ |
| Smith | Example surname | __________ |
| Acme Bookkeeping | Example business | (remove or replace) |

> **Placeholder convention:** Throughout this toolkit, `<agent>` means your agent's name, `<user1>`/`<user2>` mean your household member IDs. `Alice`, `Bob`, and `Eve` are example personas — see [NAME-CUSTOMIZATION.md](NAME-CUSTOMIZATION.md) for replacement guidance.

> **When to replace what:** Replace `<angle-bracket>` placeholders during Steps 4-6 (config files, memory init commands). Replace named personas (Alice, Bob, Eve, etc.) later during Step 9 using the NAME-CUSTOMIZATION guide. The angle-bracket values are functional — scripts and configs break without them. The named personas are cosmetic until production use.

---

## 4. Configure .memory_env

The `.memory_env` file was created from the template by `setup.sh` in Step 2. Edit it now with the values you decided in Step 3 — `deploy.sh` will copy it to the workspace in the next step:

```bash
nano .memory_env
# - Set QDRANT_COLLECTION to <agent>-memories (using your agent name from Step 3)
# - Set DEFAULT_USER_ID to your primary user's ID (from Step 3)
# - Set CURATION_MODEL to your Ollama curation model (e.g. qwen3:4b)
```

> **` chmod 600`:** If you used `setup.sh`, permissions are already restricted. If you created `.memory_env` manually, run `chmod 600 .memory_env` — this file may contain API keys.

> **Why now?** `deploy.sh` checks `.memory_env` and warns if it still contains the `<agent>` placeholder. Configuring it here avoids that warning and ensures the workspace gets a fully configured file.

See `config/memory_env.example` for a commented reference of all available options.

---

## 5. Deploy to Workspace

Deploy the toolkit into your OpenClaw workspace. This copies scripts, evergreens, memory, and config templates (including the `.memory_env` you just configured) so the repo stays decoupled from the live instance:

```bash
bash scripts/deploy.sh --workspace ~/.openclaw/workspace
```

### What `deploy.sh` Does

- Copies `scripts/`, `evergreens/`, `memory/`, `tools/`, `templates/` into the workspace
- Deploys config templates as live files: `AGENTS.md` (from `config/AGENTS-TEMPLATE.md`), `MEMORY.md` (from `config/MEMORY-TEMPLATE.md`), `HEARTBEAT.md` (from `config/HEARTBEAT-TEMPLATE.md`) — only if they don't already exist
- Copies `ARCHITECTURE.md` to the workspace root (technical reference)
- Creates a `.venv` in the workspace with all dependencies
- Copies `.memory_env` to the workspace (if not already present)
- Generates a pre-filled `config/crontab.generated` ready for installation
- Runs `verify-deploy.py` to confirm everything is in place

### Options

| Flag | Effect |
|------|--------|
| `--workspace <path>` | Target directory (default: `~/.openclaw/workspace`) |
| `--force` | Overwrite existing scripts and tools (preserves user data like STATE.md, AGENDA.md, timing.json) |

### Safety

- `deploy.sh` refuses to deploy if the workspace is inside the repo directory
- It requires `.venv` to exist (run `setup.sh` first)
- It requires `.memory_env` to exist (warns if still contains `<agent>` placeholder)
- User data files (STATE.md, AGENDA.md, timing.json, APPROVED-CONTACTS.json, settings.md) are never overwritten

> **After deployment, all remaining steps happen in the workspace — not the cloned repo.**

```bash
cd ~/.openclaw/workspace
```

> **Path convention:** Documentation uses `~/.openclaw/workspace` as the default workspace path. Crontab examples use `$WORKSPACE` (set at the top of the crontab). Adjust for your actual workspace location.

---

## 6. Configure Memory

### Initialize Memory Collections

```bash
source .venv/bin/activate
source .memory_env
python3 memory/scripts/init_memory_collections.py
```

This creates both the `QDRANT_COLLECTION` (vector search) and `TRUE_RECALL_COLLECTION` (gem storage) in Qdrant.

> **Curation model:** The True Recall curator (`curate_memories.py`) uses a local LLM via Ollama to extract gems from raw memories. Verify `CURATION_MODEL` is set in `.memory_env` (you configured this in Step 4). Without it, automated curation will fail silently.

### Customize Workspace Config Files

`deploy.sh` copied template files as `AGENTS.md`, `MEMORY.md`, and `HEARTBEAT.md` in the workspace root. Review and customize them now:

```bash
# Replace <user1>, <user2>, <agent> placeholders with your actual values from Step 3
nano AGENTS.md
nano MEMORY.md
nano HEARTBEAT.md
```

| File | Purpose | Template Source |
|------|---------|----------------|
| `AGENTS.md` | Agent behavior rules and household context | `config/AGENTS-TEMPLATE.md` |
| `MEMORY.md` | Memory routing index (paths to all memory sources) | `config/MEMORY-TEMPLATE.md` |
| `HEARTBEAT.md` | Heartbeat poll actions (active session memory capture) | `config/HEARTBEAT-TEMPLATE.md` |

### Heartbeat Integration (CRITICAL for Active Session Capture)

Memory capture works best when integrated with your agent's **heartbeat polls**. A heartbeat is OpenClaw's periodic check-in during active sessions (every ~30 minutes) — it's defined in your workspace `HEARTBEAT.md` file (`deploy.sh` already placed the template there).

**Your `HEARTBEAT.md` should include:**
```bash
# cd to workspace root (all paths are relative to workspace)
cd $WORKSPACE
source .venv/bin/activate
source .memory_env

# Auto-detect current session user and save to Redis
python3 memory/scripts/save_current_session_memory.py
```

**Why this matters:** Heartbeats run every ~30 minutes during active sessions, capturing fresh conversation context before it's lost. Without this, memory relies solely on cron jobs (which may miss active sessions).

**Full documentation:** See [HEARTBEAT-MEMORY-INTEGRATION.md](HEARTBEAT-MEMORY-INTEGRATION.md)

### Initialize PARA (Durable Knowledge Layer)

PARA stores structured, canonical facts about each household member:

```bash
# Seed PARA directories for each household member
python3 memory/scripts/seed_para.py --users <user1> <user2>
# Creates: memory/para/<user1>/, memory/para/<user2>/, memory/para/shared/
# Each with: summary.md, items.json, review-queue.md (from templates)

# If seed_para.py is not yet available, create manually:
for user in <user1> <user2> shared; do
  mkdir -p memory/para/$user
  cp memory/para/templates/summary-template.md memory/para/$user/summary.md
  cp memory/para/templates/items-template.json memory/para/$user/items.json
  cp memory/para/templates/review-queue-template.md memory/para/$user/review-queue.md
done
```

**Why this matters:** Without PARA initialization, the agent has no durable knowledge store. Facts learned in conversation would only exist in Qdrant vectors (hard to browse) and daily markdown files (which accumulate without structure). PARA provides the canonical, structured truth layer.

### Configure Household Members

Edit `memory/settings.md` to define your household members, communication preferences, timezones, and relationships. This file was deployed from the template — update it with your actual household details.

### Configure User-Specific Prompts (Optional)

Create custom memory curation prompts for each user:

```bash
cp memory/curator_prompts/example-user.md memory/curator_prompts/<user1>.md
cp memory/curator_prompts/example-user.md memory/curator_prompts/<user2>.md
nano memory/curator_prompts/<user1>.md
nano memory/curator_prompts/<user2>.md
```

Each curator prompt tells the True Recall LLM what kinds of memories are worth preserving for that person. See `memory/curator_prompts/README.md` for guidance.

### Create User Categories (Optional but Recommended)

```bash
cp config/categories.example.yaml memory/<user1>/categories.yaml
cp config/categories.example.yaml memory/<user2>/categories.yaml
```

Categories define interest areas for memory gem classification by the True Recall curator. Edit each user's file to match their interests.

---

## 7. Test One Evergreen

### What to Expect on First Run

Before running, the evergreen directories contain stub/example data:
- **STATE.md** has 2008-2009 era dates (obviously fake placeholders)
- **AGENDA.md** says "No agenda generated yet"
- **timing.json** shows `"status": "ready"`

After a successful first run:
- **STATE.md** will show today's date and real system findings
- **AGENDA.md** will contain a populated agenda with actual research
- **timing.json** will show `"status": "completed"` with real timestamps
- **DASHBOARD.html** will regenerate with real data
- **agenda-history/** will get its first archived agenda

### Option A: AI Runner (Recommended)

> **⚠️ CRITICAL — Configure exec tool permissions (OpenClaw v2026.3.31+):**
> OpenClaw v2026.3.31 introduced **exec approvals** — enabled by default — which requires manual approval for every shell command the agent tries to run. Since evergreen cycles run autonomously via cron and need to execute shell commands (health checks, system probes, file operations), this approval gate must be disabled for autonomous operation.
>
> Add the following to your `~/.openclaw/openclaw.json`:
>
> ```json
> {
>   "tools": {
>     "exec": {
>       "security": "full",
>       "ask": "off"
>     }
>   }
> }
> ```
>
> - **`security: "full"`** — allows all shell commands (alternative: `"allowlist"` to restrict to pre-approved commands, or `"deny"` to block all exec)
> - **`ask: "off"`** — disables the interactive approval prompt (alternative: `"on-miss"` to prompt only for non-allowlisted commands, or `"always"` to prompt for every command)
>
> Without this, the AI runner will hang waiting for approval that never comes during unattended cron execution. The `preflight-check.py` script verifies this setting.
>
> **Security note:** This grants the agent unrestricted shell access. If you prefer a more restrictive setup, use `"security": "allowlist"` with `"ask": "on-miss"` — but you will need to pre-populate the exec allowlist (`~/.openclaw/exec-approvals.json`) with every command the evergreens need. See the [OpenClaw documentation](https://docs.openclaw.ai) for allowlist management.

```bash
# Run a single evergreen with full AI agent session
./scripts/evergreen-ai-runner.sh system-health

# The AI runner will:
# - Acquire a flock lock (prevents concurrent runs)
# - Check OpenClaw gateway health
# - Back up STATE.md, AGENDA.md, and timing.json
# - Spawn an AI agent session via openclaw agent
# - Agent reads daily briefing (if earlier evergreens ran today)
# - Agent executes real research (system checks, analysis)
# - Agent writes findings to AGENDA.md and STATE.md
# - Validate output (timing.json, AGENDA.md, STATE.md)
# - On failure: rollback from backup + send notification (if configured)
# - On success: append stub to daily briefing for later evergreens
# - Log everything to logs/evergreen-system-health-YYYYMMDD.log

# Check results (should show today's date)
cat evergreens/system-health/STATE.md | grep "Last Cycle"
cat evergreens/system-health/AGENDA.md | head -20
```

> **Timeout:** The AI runner defaults to 1500 seconds (25 minutes) via `EVERGREEN_TIMEOUT`. Research-heavy evergreens like `upstream-architecture` may need more time — set `EVERGREEN_TIMEOUT=2400` (40 min) in the crontab line or environment if you see timeout failures.

### Option B: Direct Executor (Manual Testing)

```bash
# Run without openclaw agent session (direct Python execution)
python3 scripts/run-single-evergreen.py --evergreen system-health

# Check results
cat evergreens/system-health/STATE.md | grep "Last Cycle"
cat evergreens/system-health/AGENDA.md | head -20
```

### Verify Results

```bash
# Check that timing was recorded
cat evergreens/system-health/timing.json | jq

# Check the agenda (should have today's date and findings)
cat evergreens/system-health/AGENDA.md | head -30

# Check the state (should show last cycle completed)
cat evergreens/system-health/STATE.md | grep "Last Cycle"
```

---

## 8. Seed Upstream Monitoring

After the initial test run, seed the evergreens with upstream monitoring tasks:

```bash
# Preview what will be added (optional)
python3 scripts/seed-evergreens.py --dry-run

# Seed upstream-architecture and household-memory with monitoring tasks
python3 scripts/seed-evergreens.py

# Review what was added
cat evergreens/upstream-architecture/AGENDA.md | head -40
cat evergreens/household-memory/AGENDA.md | head -40
```

**What this does:**
- Adds upstream monitoring tasks to `upstream-architecture` and `household-memory` evergreens
- Seeds STATE.md with upstream watchlist tables
- Establishes monitoring cadence (weekly/bi-weekly checks)
- Safe to run multiple times (won't overwrite existing content)
- `system-health` and `prompt-injection` are self-bootstrapping from their STATE.md stubs and don't need seeding

**Why this matters:** New installations start with zero context about upstream repositories. This ensures your agent immediately knows to watch for OpenClaw releases, True Recall improvements, and security advisories.

See [UPSTREAM-MONITORING-GUIDE.md](UPSTREAM-MONITORING-GUIDE.md) for details.

### Regenerate Dashboard

Regenerate the dashboard after initial setup so it reflects your current data instead of the shipped example:

```bash
python3 scripts/update_evergreen_dashboard.py
```

---

## 9. Customize Example Names

This toolkit uses example names (**Alice**, **Bob**, **Eve**) throughout. Replace these with your actual household names (from Step 3) before production use.

See **[NAME-CUSTOMIZATION.md](NAME-CUSTOMIZATION.md)** for the full step-by-step replacement workflow — it covers all file types (`.md`, `.py`, `.json`, `.yaml`, `.sh`) and includes dry-run previews.

> ⚠️ **Don't blindly find-and-replace!** Some examples contain relationship claims or preferences that may not apply to your household. The NAME-CUSTOMIZATION guide walks through each replacement in context.

```bash
# Quick preview of what needs replacing
grep -rn "Alice\|Bob\|Eve\|Smith\|Acme Bookkeeping" memory/ config/ docs/ evergreens/

# After replacement, verify nothing was missed
python3 scripts/validate-customization.py
```

---

## 10. Set Up Scheduling

If you used `deploy.sh`, a pre-filled `crontab.generated` was created in your workspace:

```bash
# 1. Review the generated crontab
cat config/crontab.generated

# 2. Edit user IDs and times for your setup
nano config/crontab.generated
# - Replace user IDs with your household members (from Step 3)
# - Adjust times for your timezone (see SCHEDULING.md)

# 3. Install the crontab
crontab config/crontab.generated

# 4. Verify installation
crontab -l | grep evergreen
```

> **Manual setup?** If you didn't use `deploy.sh`, copy `config/crontab.sample` to `/tmp/evergreen-cron`, set the `WORKSPACE` variable to your workspace path, replace user IDs, and install with `crontab /tmp/evergreen-cron`.

### Memory Cron Order (Critical)

The crontab includes memory system jobs that MUST run before evergreens:

| Time | Task | Why This Order |
|------|------|----------------|
| 2:30 AM | True Recall curation (per user) | Reads Redis buffer, extracts gems, does NOT clear |
| 3:00 AM | Jarvis backup (per user) | Reads Redis buffer, backs up to Qdrant, THEN clears Redis |
| 4:00-6:00 AM | Evergreens run | Household-memory evergreen analyzes fresh memory state |

**Critical:** True Recall must run BEFORE Jarvis backup because:
- True Recall extracts high-salience "gems" from the Redis buffer
- Jarvis backup clears the Redis buffer after backing up
- If Jarvis runs first, True Recall will have nothing to process

The sample crontab has this order correct. Don't change the relative ordering of memory tasks!

**Note:** Each user gets their own Redis key (`mem:<user1>`, `mem:<user2>`, etc.), so cron jobs are scheduled per-user with 5-minute spacing to avoid resource contention.

### Weekly Jobs

The crontab also includes a weekly PARA promotion job (Sunday ~2:00 AM) that promotes gems from True Recall into PARA summaries. See [SCHEDULING.md](SCHEDULING.md) for the full schedule breakdown.

### Notification Setup (Optional)

The AI runner and final check scripts can send failure notifications via `openclaw message send`. This requires a messaging channel configured in your OpenClaw installation.

```bash
# Set your notification target in the crontab environment section:
EVERGREEN_NOTIFY_TARGET=<your-messaging-target>
```

Notifications are optional — if `EVERGREEN_NOTIFY_TARGET` is not set, the system still runs normally. Errors are always logged to `logs/`.

### Final Check Alerts

The final check script (6:00 AM) creates two files:
- `.evergreen-final-check-status.json` — Machine-readable status
- `.evergreen-alert.md` — Human-readable alert (only if issues detected)

---

## 11. Verify Everything Works

Before considering setup complete, confirm:

```bash
# Run the pre-flight check (verifies dependencies, services, config)
python3 scripts/preflight-check.py

# Verify all placeholders have been replaced
python3 scripts/validate-customization.py

# Qdrant collections exist
curl -s http://localhost:6333/collections | python3 -m json.tool

# Redis is accepting writes
redis-cli ping

# Memory system keys exist
redis-cli KEYS "mem:*"

# One evergreen runs without errors
./scripts/evergreen-ai-runner.sh system-health

# Check logs after run
tail -20 logs/evergreen-*.log
```

For common issues (Redis connection refused, module not found, permission denied), see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting including cron issues, memory system errors, alert failures, and common setup problems.

---

## Next Steps

After setup is complete:

1. Monitor first automated run (check logs at 6:15 AM)
2. Verify dashboard shows all 4 evergreens completed
3. Confirm memory system is capturing conversations
4. Test one manual evergreen run per week for first month
5. Review and customize evergreen STATE.md templates for your needs

**Maintenance:**
- Review evergreen logs monthly
- Update crontab if you add/remove household members
- Back up your memory collections regularly
- Check for toolkit updates quarterly

Reference [../QUICKSTART.md](../QUICKSTART.md) for the condensed version of any step. Read [SCHEDULING.md](SCHEDULING.md) for timezone optimization.

---

## Quick Reference Checklist

Condensed installation steps for experienced users. If anything is unclear, refer to the detailed sections above.

### Prerequisites

```bash
python3 --version          # 3.10+
redis-cli ping             # PONG
curl http://localhost:6333/ # Qdrant JSON response
ollama --version           # Ollama installed
openclaw --version         # OpenClaw installed
which curl jq flock        # System tools
```

Optional: **Node.js 18+** (for markdown viewer)

### Install & Deploy

```bash
git clone https://github.com/paulscode/evergreen-toolkit.git ~/evergreen-toolkit
cd ~/evergreen-toolkit
bash scripts/setup.sh
nano .memory_env   # Set QDRANT_COLLECTION, DEFAULT_USER_ID, CURATION_MODEL
bash scripts/deploy.sh --workspace ~/.openclaw/workspace
cd ~/.openclaw/workspace
```

### Configure Memory

```bash
source .venv/bin/activate && source .memory_env
python3 memory/scripts/init_memory_collections.py
nano AGENTS.md MEMORY.md HEARTBEAT.md   # Replace placeholders
python3 memory/scripts/seed_para.py --users <user1> <user2>
```

### Test & Seed

```bash
./scripts/evergreen-ai-runner.sh system-health
python3 scripts/seed-evergreens.py
python3 scripts/update_evergreen_dashboard.py
```

### Customize & Automate

```bash
# Replace example names (see docs/NAME-CUSTOMIZATION.md)
python3 scripts/validate-customization.py

# Install crontab
nano config/crontab.generated   # Edit user IDs, timezone
crontab config/crontab.generated
```

### Verify

```bash
python3 scripts/preflight-check.py
python3 scripts/validate-customization.py
./scripts/evergreen-ai-runner.sh system-health
```

### Model Override (Optional)

```bash
# Create a named agent with the desired model
openclaw agents add evergreen --model "provider/model" --workspace ~/.openclaw/workspace

# Then set in your crontab environment:
EVERGREEN_AGENT=evergreen
```

The AI runner will use `--agent-name evergreen` when spawning sessions. See [SCHEDULING.md](SCHEDULING.md) for details.
