# 🚀 Quick Start Guide

**Get Evergreen Toolkit running quickly.**

> **Note:** This is the **primary setup guide**. [`docs/SETUP-GUIDE.md`](docs/SETUP-GUIDE.md) covers the same steps in more detail — consult it if you need deeper context on any step. **Do not follow both guides sequentially** — they cover the same ground at different levels of detail. Pick one.

> **For AI agents:** This guide is the **step-by-step implementation path**. [AGENT-ONBOARDING.md](AGENT-ONBOARDING.md) provides the overview and checklist; this guide has the detailed instructions. Follow this guide's step ordering for setup.

---

## Prerequisites Check

```bash
# Verify Python 3.10+
python3 --version

# Verify Redis (should return PONG)
redis-cli ping
# If Redis is not installed: sudo apt install redis-server && sudo systemctl start redis

# Verify Qdrant (should return version info)
curl http://localhost:6333/
# If Qdrant is not installed:
#   Docker (recommended): docker run -d --name qdrant -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
#   Other options: https://qdrant.tech/documentation/guides/installation/

# Verify Ollama (required for memory embeddings + curation)
ollama --version
# Install from https://ollama.ai if not present

# Pull required models (embedding + curation)
ollama pull snowflake-arctic-embed2
ollama pull qwen3:4b   # recommended model for True Recall gem extraction

# Verify OpenClaw
openclaw --version

# Verify Node.js (for markdown viewer — optional)
node --version

# Verify system tools (used by health checks and AI runner)
which curl jq flock
```

> **Or skip ahead:** Clone first (Step 1), install (Step 2), deploy (Step 5), then run `python3 scripts/preflight-check.py` to verify everything at once. The prerequisites above are for manual verification if you prefer to check before installing.

> **What is OpenClaw?** OpenClaw is the AI agent platform this toolkit extends. If you don't have it installed, see [https://docs.openclaw.ai](https://docs.openclaw.ai) for installation instructions. The toolkit requires OpenClaw for the AI runner mode (recommended). The direct executor mode works without it.

> **No OpenClaw?** You can still use the toolkit with the direct executor (`run-single-evergreen.py`) for all evergreen cycles. Skip the AI runner steps and use the direct executor in your crontab instead. See [ARCHITECTURE.md](ARCHITECTURE.md) for the comparison.

> **Qdrant:** Qdrant is the vector database used for semantic memory search. Install via Docker: `docker run -d --name qdrant -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant`. See [qdrant.tech](https://qdrant.tech/documentation/guides/installation/) for other installation methods.

> **Ollama:** Ollama is **required** for memory embeddings (vector search) and True Recall curation (gem extraction). Without it, the memory system cannot generate embeddings or curate gems. Install from [https://ollama.ai](https://ollama.ai), then pull both models: `ollama pull snowflake-arctic-embed2` (embeddings) and `ollama pull qwen3:4b` (curation).

> **System tools:** `curl` and `jq` are used by health checks. `flock` is used by the AI runner for locking (pre-installed on most Linux distributions). Node.js is only needed for the optional markdown viewer. Install missing tools via your package manager (e.g., `sudo apt install curl jq nodejs`).

> **Pre-flight check:** After completing setup, run `python3 scripts/preflight-check.py` to verify all dependencies, services, and configuration are in place.

---

## 1. Clone the Toolkit

```bash
git clone https://github.com/paulscode/evergreen-toolkit.git ~/evergreen-toolkit
cd ~/evergreen-toolkit
```

> **This is the repo clone, not your workspace.** After setup, you will run `deploy.sh` (Step 5) to copy the operational files into your OpenClaw workspace. The cloned repo can be kept for upgrades or deleted after deployment.

---

## 2. Install Dependencies

```bash
# Option A: Automated setup (recommended)
bash scripts/setup.sh

# Option B: Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Note:** `setup.sh` creates the virtual environment, installs dependencies, copies `.memory_env` from the template, makes scripts executable, and creates the `logs/` directory. If you prefer manual setup, ensure the `logs/` directory exists: `mkdir -p logs`

---

## 3. Decide on Your Names and IDs

Before configuring memory or running evergreens, decide on these values — you'll need them in the next steps:

| Decision | Example | Used In |
|----------|---------|--------|
| **Agent name** | `jarvis`, `friday` | Qdrant collection name, logs, display |
| **Agent system user_id** | `eve`, `jarvis` | Redis key (`mem:<agent>`), system memory dir |
| **Household member IDs** | `alice`, `bob` | Redis keys, memory directories, cron jobs |
| **Timezone** | `America/Chicago` | Cron scheduling |
| **Notification target** (optional) | WhatsApp number, channel ID | Failure alerts |

### Placeholder Mapping

These example personas appear throughout the documentation. Map them to your household:

| Placeholder | Example in Docs | Your Value |
|-------------|----------------|------------|
| `<agent>` | Eve / eve | __________ |
| `<user1>` | Alice / alice | __________ |
| `<user2>` | Bob / bob | __________ |
| Mom / Dad | Family role labels | __________ |
| Smith | Example surname | __________ |
| Acme Bookkeeping | Example business | (remove or replace) |

> **Placeholder convention:** Throughout this toolkit, `<agent>` means your agent's name, `<user1>`/`<user2>` mean your household member IDs. `Alice`, `Bob`, and `Eve` are example personas — see [docs/NAME-CUSTOMIZATION.md](docs/NAME-CUSTOMIZATION.md) for replacement guidance.

> **When to replace what:** Replace `<angle-bracket>` placeholders during Steps 4-6 (config files, memory init commands). Replace named personas (Alice, Bob, Eve, etc.) later during Step 9 using the NAME-CUSTOMIZATION guide. The angle-bracket values are functional — scripts and configs break without them. The named personas are cosmetic until production use.

> **Name customization:** After completing setup, you'll replace the example personas throughout the codebase. See [Step 9: Customize Example Names](#9-customize-example-names) for the workflow.

---

## 4. Configure .memory_env

The `.memory_env` file was created from the template by `setup.sh` in Step 2. Edit it now with the values you decided in Step 3 — `deploy.sh` will copy it to the workspace in the next step:

```bash
nano .memory_env
# - Set QDRANT_COLLECTION to <agent>-memories (using your agent name from Step 3)
# - Set DEFAULT_USER_ID to your primary user's ID (from Step 3)
# - Set CURATION_MODEL to your Ollama curation model (e.g. qwen3:4b)
```

> **Note:** `.memory_env` is the functional configuration file sourced by scripts at runtime. `memory/settings.md` is a separate reference document for human/agent readability — it is not read by any script.

> **Two Qdrant collections:** The system uses separate collections for raw backups (`QDRANT_COLLECTION`, e.g., `myagent-memories`) and curated gems (`TRUE_RECALL_COLLECTION`, default: `true_recall`). Both are required. See [MEMORY-SYSTEM.md](MEMORY-SYSTEM.md) for why they're separate.

> **Why now?** `deploy.sh` checks `.memory_env` and warns if it still contains the `<agent>` placeholder. Configuring it here avoids that warning and ensures the workspace gets a fully configured file.

---

## 5. Deploy to Workspace

Deploy the toolkit into your OpenClaw workspace. This copies scripts, evergreens, memory, and config templates (including the `.memory_env` you just configured) so the repo stays decoupled from the live instance:

```bash
bash scripts/deploy.sh --workspace ~/.openclaw/workspace
```

**What `deploy.sh` does:**
- Copies `scripts/`, `evergreens/`, `memory/`, `tools/`, `templates/` into the workspace
- Deploys config templates as live files (`AGENTS.md`, `MEMORY.md`, `HEARTBEAT.md`)
- Copies `ARCHITECTURE.md` to the workspace root (technical reference)
- Creates a `.venv` in the workspace with all dependencies
- Generates a pre-filled `config/crontab.generated` ready for installation
- Runs `verify-deploy.py` to confirm everything is in place

> **After deployment, all remaining steps happen in the workspace — not the cloned repo.**

```bash
cd ~/.openclaw/workspace
```

> **Path convention:** Documentation uses `~/.openclaw/workspace` as the default workspace path. Crontab examples use `$WORKSPACE` (set at the top of the crontab). Adjust for your actual workspace location.

> **Quick sanity check:** After deploying, run `python3 scripts/preflight-check.py` to verify dependencies and services before continuing with memory configuration.

---

## 6. Configure Memory

```bash
# Initialize memory collections (creates both QDRANT_COLLECTION and TRUE_RECALL_COLLECTION)
source .venv/bin/activate
source .memory_env
python3 memory/scripts/init_memory_collections.py
```

> **Curation model:** The True Recall curator (`curate_memories.py`) uses a local LLM via Ollama to extract gems from raw memories. Verify `CURATION_MODEL` is set in `.memory_env` (you configured this in Step 4). Without it, automated curation will fail silently.

### Customize Workspace Config Files

`deploy.sh` copied template files as `AGENTS.md`, `MEMORY.md`, and `HEARTBEAT.md` in the workspace root. Review and customize them now:

```bash
# Replace <user1>, <user2>, <agent> placeholders with your actual values from Step 3
nano AGENTS.md
nano MEMORY.md
nano HEARTBEAT.md
```

> These files configure your agent's behavior (`AGENTS.md`), memory routing (`MEMORY.md`), and heartbeat actions (`HEARTBEAT.md`). See the templates in `config/` for reference.

### Heartbeat Integration (CRITICAL for Active Session Capture)

Memory capture works best when integrated with your agent's **heartbeat polls**. A heartbeat is OpenClaw's periodic check-in during active sessions (every ~30 minutes) — it's defined in your workspace `HEARTBEAT.md` file. If you used `deploy.sh`, the template was already copied to your workspace as `HEARTBEAT.md`.

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

**Full documentation:** See [`docs/HEARTBEAT-MEMORY-INTEGRATION.md`](docs/HEARTBEAT-MEMORY-INTEGRATION.md)

### Initialize PARA (Durable Knowledge Layer)

PARA (Projects, Areas, Resources, Archives) is a structured knowledge methodology adapted for multi-user AI agents. It stores canonical, durable facts about each household member. Initialize it for your users:

```bash
cd ~/.openclaw/workspace
source .venv/bin/activate

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

> **MEMORY.md routing:** After PARA is set up, verify that your workspace `MEMORY.md` has the correct paths (if you used `deploy.sh`, it was already deployed from the template). This gives your agent a compact routing index for all memory sources.

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

> **Requires OpenClaw.** This mode spawns an agent session via `openclaw agent`. If OpenClaw is not installed, use Option B (Direct Executor) below instead. See Prerequisites at the top of this guide.

> **⚠️ CRITICAL — Configure exec tool permissions (OpenClaw v2026.3.31+):**
> OpenClaw v2026.3.31 introduced **exec approvals** — enabled by default — which requires manual approval for every shell command the agent tries to run. Since evergreen cycles run autonomously via cron and need to execute shell commands (health checks, system probes, file operations), this approval gate must be disabled for autonomous operation.
>
> **Important:** This must be set **per-agent** in your `~/.openclaw/openclaw.json`, not at the top level. The AI runner spawns embedded agent sessions, and the embedded runtime resolves exec policy from the agent entry — it does not inherit the top-level `tools.exec` config. A top-level setting only applies when running `openclaw agent` interactively from a terminal.
>
> Add `tools.exec` to each agent that runs evergreens in your `agents.list`:
>
> ```json
> {
>   "agents": {
>     "list": [
>       {
>         "id": "evergreen",
>         "tools": {
>           "exec": {
>             "security": "full",
>             "ask": "off"
>           }
>         }
>       }
>     ]
>   }
> }
> ```
>
> - **`security: "full"`** — allows all shell commands (alternative: `"allowlist"` to restrict to pre-approved commands, or `"deny"` to block all exec)
> - **`ask: "off"`** — disables the interactive approval prompt (alternative: `"on-miss"` to prompt only for non-allowlisted commands, or `"always"` to prompt for every command)
>
> Without this, the AI runner will hang waiting for approval that never comes during unattended cron execution. The `preflight-check.py` script verifies this setting per-agent.
>
> **Scope:** This config is only required on agents that run evergreen cycles (typically the `evergreen` agent). If you also want unrestricted exec on other agents (e.g. `main` for interactive use over WhatsApp or other gateway channels), add the same `tools.exec` block to those agent entries as well — the embedded runtime resolves exec policy per-agent regardless of which agent is invoked.
>
> **Security note:** This grants the agent unrestricted shell access. If you prefer a more restrictive setup, use `"security": "allowlist"` with `"ask": "on-miss"` — but you will need to pre-populate the exec allowlist (`~/.openclaw/exec-approvals.json`) with every command the evergreens need. See the [OpenClaw documentation](https://docs.openclaw.ai) for allowlist management.

```bash
# Make AI runner executable
chmod +x scripts/evergreen-ai-runner.sh

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

> **First run expectation:** After a successful run, STATE.md will show today's date
> and real system findings. The AGENDA.md stub ("No agenda generated yet") will be
> replaced with a populated agenda. The timing.json will show `"status": "completed"`
> with real timestamps. Any example 2008-2009 dates will be overwritten.

> **Timeout:** The AI runner defaults to 1500 seconds (25 minutes) via `EVERGREEN_TIMEOUT`. Research-heavy evergreens like `upstream-architecture` may need more time — set `EVERGREEN_TIMEOUT=2400` (40 min) in the crontab line or environment if you see timeout failures.

### Option B: Direct Executor (Manual Testing)

```bash
# Run without openclaw agent session (direct Python execution)
python3 scripts/run-single-evergreen.py --evergreen system-health

# Check results
cat evergreens/system-health/STATE.md | grep "Last Cycle"
cat evergreens/system-health/AGENDA.md | head -20
```

---

> **Minimum viable setup complete.** Steps 1-7 give you a working system. Steps 8-11 below are production hardening — scheduling, monitoring seeds, name customization, and cron installation. You can return to them at any time.

---

## 8. Seed Upstream Monitoring Tasks (Recommended)

After installation, seed the evergreens with upstream monitoring tasks:

```bash
cd ~/.openclaw/workspace
source .venv/bin/activate

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

**Why this matters:** New installations start with zero context about upstream repositories. This ensures your agent immediately knows to watch for:
- OpenClaw releases and breaking changes
- True Recall memory system improvements
- Security advisories and bug fixes

### Regenerate Dashboard (Important)

Regenerate the dashboard after initial setup so it reflects your current data instead of the shipped example:

```bash
python3 scripts/update_evergreen_dashboard.py
```

---

## 9. Customize Example Names

This toolkit uses example names (**Alice**, **Bob**, **Eve**) throughout. Replace these with your actual household names (from Step 3) before production use.

See **[docs/NAME-CUSTOMIZATION.md](docs/NAME-CUSTOMIZATION.md)** for the full step-by-step replacement workflow — it covers all file types (`.md`, `.py`, `.json`, `.yaml`, `.sh`) and includes dry-run previews.

Also customize **`memory/settings.md`** with your household member definitions (names, user IDs, communication preferences). This file is a reference document — not read by scripts — but ensures you and your agent have a single source of truth for household membership.

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
cat ~/.openclaw/workspace/config/crontab.generated

# 2. Edit user IDs and times for your setup
nano ~/.openclaw/workspace/config/crontab.generated
# - Replace user IDs with your household members (from Step 3)
# - Adjust times for your timezone (see docs/SCHEDULING.md)

# 3. Install the crontab
crontab ~/.openclaw/workspace/config/crontab.generated

# 4. Verify installation
crontab -l | grep evergreen
```

> **Manual setup?** If you didn't use `deploy.sh`, copy `config/crontab.sample` to `/tmp/evergreen-cron`, set the `WORKSPACE` variable to your workspace path, replace user IDs, and install with `crontab /tmp/evergreen-cron`.

**Critical:** The crontab runs memory jobs (2:30-3:00 AM) before evergreens (4:00-6:00 AM). True Recall must run before Jarvis backup. Don't change this ordering — see `config/crontab.sample` for details.

> **Timeouts:** The generated crontab includes longer timeouts (2400s) for research-heavy evergreens (upstream-architecture, household-memory). Don't reduce these below the default 1500s without testing.

**Weekly jobs:** The crontab also includes a weekly PARA promotion job (Sunday ~2:00 AM) that promotes gems from True Recall into PARA summaries. This is a separate cron entry — see [docs/SCHEDULING.md](docs/SCHEDULING.md) for the full schedule breakdown.

### Notification Setup (Optional)

The AI runner and final check scripts can send failure notifications via `openclaw message send`. This requires a messaging channel (WhatsApp, Telegram, etc.) configured in your OpenClaw installation.

```bash
# Set your notification target (phone number or channel ID)
export EVERGREEN_NOTIFY_TARGET="+1234567890"

# Or add it to the crontab environment section
# EVERGREEN_NOTIFY_TARGET=+1234567890
```

Notifications are optional — if `EVERGREEN_NOTIFY_TARGET` is not set or `openclaw message send` is unavailable, the system still runs normally. Errors are always logged to `logs/`.

> **DST zones:** If your timezone observes Daylight Saving Time, avoid scheduling memory jobs in the 2:00–3:00 AM window — the spring-forward transition can cause True Recall and Jarvis to race. See [docs/SCHEDULING.md](docs/SCHEDULING.md#adjust-for-daylight-saving-time) for details.

---

## 11. Verify Everything Works


Before considering setup complete, confirm:

```bash
# Verify all placeholders have been replaced
python3 scripts/validate-customization.py

# Qdrant collections exist
curl -s http://localhost:6333/collections | python3 -m json.tool

# Check memory system
redis-cli KEYS "mem:*"

# Redis is accepting writes
redis-cli ping

# One evergreen runs without errors
./scripts/evergreen-ai-runner.sh system-health

# Check logs after first automated run
tail -20 logs/evergreen-*.log
```

For common issues (Redis connection refused, module not found, permission denied), see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## Next Steps

- Reference [docs/SETUP-GUIDE.md](docs/SETUP-GUIDE.md) if you need deeper context on any step above
- Read [docs/SCHEDULING.md](docs/SCHEDULING.md) for timezone optimization

---

## Quick Reference

```bash
# Run a specific evergreen (AI runner — recommended)
./scripts/evergreen-ai-runner.sh <name>

# Run a specific evergreen (direct executor)
python3 scripts/run-single-evergreen.py --evergreen <name>

# Run with custom timeout
EVERGREEN_TIMEOUT=900 ./scripts/evergreen-ai-runner.sh <name>

# Run with a specific named agent (routes to that agent's model)
EVERGREEN_AGENT=evergreen ./scripts/evergreen-ai-runner.sh <name>

# Run with verbose output (direct executor)
python3 scripts/run-single-evergreen.py --evergreen <name> --verbose

# Save memory
python3 memory/scripts/save_mem.py --user-id <your-user-id>

# Search memories
python3 memory/scripts/search_memories.py "your query" --user-id <your-user-id>

# Start markdown viewer (one-time setup recommended)
# Option 1: Run manually
node tools/markdown-viewer.js

# Option 2: Install as systemd service (auto-starts on boot)
./scripts/setup-markdown-viewer.sh --port 3000

# Verify it's running
curl http://localhost:3000/health
```

---

**That's it! Your agent is now on the path to continuous improvement. 🌲**

For detailed documentation, see the [docs/](docs/) directory.
