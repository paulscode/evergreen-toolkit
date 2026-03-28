# Agent Onboarding Guide

**Quick-reference for the OpenClaw agent implementing Evergreen Toolkit.**

This document is for you, the AI agent. Your human has deployed this toolkit and you need to understand the key concepts to operate it correctly.

---

## Decisions to Make Before Setup

Gather these from your user before starting installation:

1. **Agent name** (used in collection names, logs, display): e.g., `jarvis`, `friday`
2. **Household members** (name, user_id, primary communication channel per person)
3. **Timezone** (for cron scheduling): e.g., `America/Chicago`
4. **Notification target** (optional — phone/channel for failure alerts)
5. **Workspace path** (default: `~/.openclaw/workspace`)

Having these ready avoids backtracking during the setup steps in [QUICKSTART.md](QUICKSTART.md).

> **Recommended path:** Follow [QUICKSTART.md](QUICKSTART.md) step-by-step for initial setup — it is the **canonical implementation guide** with detailed instructions for each step. This document (AGENT-ONBOARDING) provides the overview, key concepts, and a summary checklist. Use [docs/SETUP-GUIDE.md](docs/SETUP-GUIDE.md) only as a reference for deeper context or troubleshooting — it covers the same ground in more detail but is not required for a successful deployment.

> **Path note:** After running `deploy.sh`, all operational files live in the OpenClaw workspace (e.g., `~/.openclaw/workspace/`). All path references in this project are relative to the workspace root. The cloned repo is only needed for initial setup and future upgrades.

---

## What This Is

The Evergreen Toolkit is a self-improving automation framework. You run 4 programs ("evergreens") on a schedule, each focused on a different domain:

| Evergreen | Purpose | Typical Duration |
|-----------|---------|-----------------|
| upstream-architecture | Monitor upstream repos for updates | ~30 min |
| system-health | Check infrastructure, optimize | ~5 min |
| prompt-injection | Security hardening, vulnerability scanning | ~10 min |
| household-memory | Analyze and improve memory system | ~30 min |

> **Model selection:** Research-heavy evergreens (`upstream-architecture`, `household-memory`) benefit from a capable reasoning model. Lighter evergreens (`system-health`) work well with faster models. If your agent framework supports per-session model selection, consider matching model capability to evergreen complexity.

Each evergreen follows an 8-step cycle documented in [evergreens/EVERGREENS.md](evergreens/EVERGREENS.md).
---

## How to Adapt This Toolkit

This toolkit is a template. Your job is to transform it from a generic example into a system that serves your specific household. The transformation has three phases:

1. **Infrastructure** — Install dependencies, configure services (Redis, Qdrant, Ollama, OpenClaw). These are mechanical steps in QUICKSTART.md.

2. **Personalization** — Replace example personas (Alice, Bob, Eve) with real household members. Create per-user curator prompts reflecting each person's interests and communication style. Configure scheduling for your timezone.

3. **Activation** — Run evergreens, install crontab, set up notifications. The system becomes self-improving from its first cycle forward.

After activation, the four evergreens handle continuous improvement autonomously. Your main ongoing task is responding to notifications and reviewing findings in AGENDA.md files.

---

## What You'll See After Cloning

The repository ships with **example data** to demonstrate the expected format:
- **STATE.md files** contain 2008-2009 era dates (obviously fake — these will be overwritten on first run)
- **AGENDA.md files** contain stubs ("No agenda generated yet")
- **timing.json** shows `"status": "ready"` (will update to `"completed"` after first run)
- **DASHBOARD.html** shows example cards (regenerated after each cycle)

This scaffolding ensures the file structure is in place and agents can see the expected format before any real data exists.
---

## Files to Configure During Setup

| File | Purpose | When |
|------|---------|------|
| `.memory_env` | Redis, Qdrant, Ollama connection details | Checklist item 4 (copy from `config/memory_env.example`) |
| `memory/settings.md` | Household member definitions (reference doc) | QUICKSTART Step 9 (name customization) |
| `memory/curator_prompts/<user_id>.md` | Per-user curation instructions | QUICKSTART Step 9 |
| `config/crontab.sample` | Scheduling template | QUICKSTART Step 10 (customize, then install) |

## Key Files You'll Touch (Runtime)

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `scripts/evergreen-ai-runner.sh` | AI runner (cron-facing, recommended) | Rarely |
| `evergreens/<name>/STATE.md` | Current status, health, next steps | Every cycle |
| `evergreens/<name>/AGENDA.md` | Today's cycle plan and findings | Every cycle |
| `evergreens/<name>/timing.json` | Cycle timing (auto-updated) | Every cycle |
| `evergreens/DASHBOARD.html` | Auto-generated status dashboard | After each cycle |
| `tools/markdown-viewer.js` | Markdown rendering server | Install once, runs continuously |
| `scripts/fix-markdown-links.js` | Auto-fix raw file:// links | Every cycle (auto) |
| `memory/settings.md` | Household member definitions (reference doc) | Setup, then rarely |
| `templates/EXAMPLE-COMPLETED-CYCLE.md` | Example of a completed cycle archive | Reference |

---

## Which Runner Script?

The repository includes multiple runner scripts. Here's when to use each:

| Script | When to Use |
|--------|-------------|
| `scripts/evergreen-ai-runner.sh` | **Cron/production** — the recommended runner for scheduled execution |
| `scripts/run-single-evergreen.py` | **Manual testing** — run one evergreen interactively to verify setup |
| `scripts/evergreen-scripted-executor.py` | **Fallback** — mechanical checks only, no AI orchestration |

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed comparison.

> **Log files:** The AI runner creates per-evergreen per-day logs at `logs/evergreen-{name}-YYYYMMDD.log`. The direct executor logs to `logs/evergreen-executor.log`. Check the appropriate log when debugging.

> **On-demand runs:** Besides cron scheduling, evergreens can be triggered on-demand by creating a `.run_requested` file (e.g., `touch evergreens/system-health/.run_requested`). The heartbeat checks for these triggers and runs the evergreen if found. See `config/HEARTBEAT-TEMPLATE.md` and `docs/OPERATIONAL-GUIDE.md` for details.

---

## Placeholder Convention

- `<angle-bracket>` values (e.g., `<user1>`, `<agent>`) **must** be replaced with your actual values
- `Alice`, `Bob`, `Mom`, `Dad`, `Smith`, `Acme Bookkeeping` are example personas — replace with your household's actual users and context
- In narrative examples: `Alice` = `<user1>`, `Bob` = `<user2>`, `Eve` = `<agent>`
- Example dates from 2008–2009 in STATE.md files are stubs — they will be overwritten on first run

---

## Critical Rules

1. **Memory order matters**: True Recall (2:30 AM) runs before Jarvis backup (3:00 AM). Jarvis clears Redis; True Recall does NOT.
2. **STATE.md "Completed Recently"**: Keep 3-5 items max. Older items go to agenda-history.
3. **Don't modify timing.json manually** — `run-single-evergreen.py` populates it automatically.
4. **Path convention**: All commands assume you've `cd`'d into the workspace directory first. For AI runner, paths are auto-resolved from the script location. For direct executor mode, activate venv and source `.memory_env` before running scripts.
5. **User isolation**: Each household member has their own Redis key (`mem:<user_id>`) and Qdrant filter. Never mix user memories.
6. **Keep the repo decoupled from the live workspace** — the cloned repo is a source template. The live OpenClaw workspace must NOT depend on files inside the repo at runtime:
   - **Deployment:** Run `deploy.sh` to copy operational files from the repo into the workspace. The repo can be kept for upgrades or deleted after deployment.
   - **Scripts:** The crontab and systemd services point to the workspace's own `scripts/` directory, never into the repo.
   - **Data:** User data (PARA facts, daily notes, logs) lives in the workspace's own directories (e.g. `memory/para/`), not inside the repo.
   - **Verification:** Run `python3 scripts/verify-deploy.py` to confirm no files are symlinked back to the repo and no repo paths leak into config files.
   - **Why this matters:** The repo may be updated, moved, or `git clean`'d without warning. If the live system reads from it, those operations break production.

---

## First-Time Setup Checklist

If you're implementing this for a new household, follow this checklist. It expands [QUICKSTART.md](QUICKSTART.md) steps into atomic sub-tasks — step references in parentheses map back to QUICKSTART.md for cross-reference.

1. [ ] Clone the repo: `git clone https://github.com/paulscode/evergreen-toolkit.git ~/evergreen-toolkit` — *QUICKSTART Step 1*
2. [ ] Run `bash scripts/setup.sh` in the repo (creates `.venv`, installs deps, copies `.memory_env`) — *QUICKSTART Step 2*
3. [ ] Decide on agent name, user IDs, timezone, and notification targets — *QUICKSTART Step 3*
4. [ ] Edit `.memory_env` with Redis/Qdrant/Ollama config (set `QDRANT_COLLECTION`, `TRUE_RECALL_COLLECTION`, `DEFAULT_USER_ID`, and connection details) — *QUICKSTART Step 4*
5. [ ] Deploy to workspace: `bash scripts/deploy.sh --workspace ~/.openclaw/workspace` — *QUICKSTART Step 5*
6. [ ] **From here on, work in the workspace:** `cd ~/.openclaw/workspace`

**Configure memory** (*QUICKSTART Step 6* — items 7-10 are sub-steps):  
7. [ ] Run `python3 scripts/preflight-check.py` to verify all dependencies and services
8. [ ] Source environment and create Qdrant collections: `source .venv/bin/activate && source .memory_env && python3 memory/scripts/init_memory_collections.py`
9. [ ] Initialize PARA for each user: `python3 memory/scripts/seed_para.py --users <user1> <user2>`
10. [ ] Customize `MEMORY.md`, `AGENTS.md`, and `HEARTBEAT.md` in the workspace root (deployed from templates by `deploy.sh`)

11. [ ] Test one evergreen manually: `./scripts/evergreen-ai-runner.sh system-health` — *QUICKSTART Step 7*
12. [ ] Run `python3 scripts/seed-evergreens.py` to populate upstream monitoring tasks — *QUICKSTART Step 8*

**Customize names and personas** (*QUICKSTART Step 9* — items 13-15):  
13. [ ] Customize example names — see [docs/NAME-CUSTOMIZATION.md](docs/NAME-CUSTOMIZATION.md) and [QUICKSTART.md](QUICKSTART.md#9-customize-example-names)
14. [ ] Customize `memory/settings.md` with household member details
15. [ ] Create per-user curator prompts in `memory/curator_prompts/<user_id>.md`

16. [ ] (Optional) Add memory-first strategy and household context to your agent's `SOUL.md` — see [docs/MEMORY-FIRST-STRATEGY.md](docs/MEMORY-FIRST-STRATEGY.md)
17. [ ] Install crontab: review and install `crontab.generated` (created by `deploy.sh`) — *QUICKSTART Step 10*
18. [ ] Verify everything works — `python3 scripts/validate-customization.py` — *QUICKSTART Step 11*
19. [ ] Run `python3 scripts/verify-deploy.py` to confirm no repo dependencies remain — *Critical Rule 6*

> **Skip during setup:** `memory/IDENTITY-VERIFICATION.md`, `memory/APPROVED-CONTACTS.json`, and `memory/OPENCLAW-FORK-CHANGES.md` are not needed during initial setup. The first two are stubs that will be auto-populated by the prompt-injection evergreen during its first cycles. The fork changes document is for advanced users who want to modify the OpenClaw gateway for end-to-end user isolation — skip it unless you're forking the gateway.

---

## Name Customization

This toolkit uses an **example household** throughout documentation to demonstrate multi-user features. Here is the full cast of example personas:

| Example | Role | Details | Replace With |
|---------|------|---------|-------------|
| Eve | AI agent | user_id: `eve`, system memory path: `memory/eve/` | Your agent's name, ID, and memory path |
| Alice Smith | Household member #1 (Mom) | user_id: `alice`, phone: `+11234567890`, non-technical, uses WhatsApp | Actual user |
| Bob Smith | Household member #2 (Dad) | user_id: `bob`, phone: `+12345678901`, technical, Bitcoin expert | Actual user |
| Acme Bookkeeping | Alice's business | Used in memory examples | Actual context or remove |
| `<agent>-memories` | Qdrant collection | Raw conversation backups | e.g., `myagent-memories` |

**Important:** Review each instance before replacing — some contain specific claims (relationships, preferences, technical expertise) that may not apply to your household. Don't blindly search-and-replace.

**Date convention:** All example dates in STATE.md and AGENDA.md files use 2008-2009 era timestamps to make them obviously distinguishable from real data.

See QUICKSTART.md for sed commands to do bulk replacement.

---

## After Setup

Once the crontab is active, the system is self-improving:
- Evergreens run nightly (4:00–6:00 AM by default)
- Daily briefings accumulate cross-evergreen context
- Weekly synthesis (if enabled) provides trend analysis
- PARA facts grow as gems are promoted weekly

Your ongoing responsibilities:
- Check `DASHBOARD.html` periodically for health status
- Review `review-queue.md` files when PARA promotion flags contradictions
- Respond to failure notifications (if configured)
- The system handles everything else autonomously

---

## Where to Find More

- **Full setup walkthrough**: [docs/SETUP-GUIDE.md](docs/SETUP-GUIDE.md)
- **Architecture deep-dive**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Scheduling & timezones**: [docs/SCHEDULING.md](docs/SCHEDULING.md)
- **Multi-user memory**: [memory/MULTI-USER-GUIDE.md](memory/MULTI-USER-GUIDE.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Upstream monitoring**: [docs/UPSTREAM-MONITORING-GUIDE.md](docs/UPSTREAM-MONITORING-GUIDE.md)
