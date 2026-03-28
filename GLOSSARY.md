# Glossary

Key terms used throughout this project:

| Term | Definition |
|------|-----------|
| **OpenClaw** | The AI agent platform this toolkit extends. Provides the agent runtime, messaging, and tool infrastructure. |
| **Evergreen** | A self-improving automation program that runs on a schedule, focused on continuous improvement in a specific domain. |
| **Jarvis Memory** | The raw conversation backup system (upstream name from SpeedyFoxAI). Runs at 3:00 AM — dumps Redis → Qdrant, then clears Redis. |
| **True Recall** | The AI curation layer that extracts high-value "gems" from conversations. Runs at 2:30 AM — does NOT clear Redis. |
| **Gem** | A high-salience memory extracted by the True Recall curator (a key decision, preference, insight, or event). |
| **PARA** | Projects / Areas / Resources / Archives — a durable knowledge layer storing structured facts per user at `memory/para/<user>/`. Canonical source of truth. Originally from Tiago Forte's methodology; adapted here for multi-user AI agents. |
| **PARA Promotion** | The process of extracting durable facts from curated gems (True Recall) or daily notes and storing them in the PARA layer. Run by `promote_to_para.py`. |
| **MEMORY.md** | A tiny routing index that tells the agent where to look for different types of information. Not a memory store — a wayfinder. Template at `config/MEMORY-TEMPLATE.md`. |
| **Routing Layer** | Layer 7 of the memory system: `MEMORY.md` acts as a compact index pointing to all other memory sources. |
| **Durable Knowledge** | Layer 5 of the memory system: PARA directories holding canonical, structured facts about each user and the household. |
| **LCM (lossless-claw)** | Optional OpenClaw plugin for lossless session recovery — preserves full session context across reconnections. Session-scoped only, not durable truth. |
| **Gigabrain** | Optional OpenClaw plugin for automatic context recall — injects relevant past memories into active sessions. |
| **seed_para.py** | Script that initializes PARA directories for each household member from templates. Should be run during setup (after naming decisions). |
| **promote_to_para.py** | Script that promotes durable facts from True Recall gems or daily notes into PARA `items.json`. Handles tiered contradiction resolution. |
| **items.json** | Per-user structured fact store in PARA (`memory/para/<user>/items.json`). Rich schema: id, fact, category, source, confidence, supersedes, added, last_verified, tags. |
| **review-queue.md** | Per-user file for contradictions requiring conversational review (Tier 3). Located at `memory/para/<user>/review-queue.md`. |
| **SpeedyFoxAI** | Original author of the Jarvis Memory + True Recall system (GitLab username: mdkrush). See `memory/UPSTREAM-CREDITS.md`. |
| **Lucas Synnott** | Creator of the 5-Layer Memory Stack (appliedleverage.io). Layer separation concepts (PARA, routing, session recovery) adapted with attribution. See `memory/UPSTREAM-CREDITS.md`. |
| **The Curator** | The AI persona/system prompt used by `curate_memories.py` to decide what's worth preserving as a gem. |
| **Theory of Mind** | The AI's ability to track what each household member knows, believes, and prefers — separately per person. |
| **Heartbeat** | Periodic check-in during active sessions (~30 min intervals) that captures conversation context to Redis. |
| `QDRANT_COLLECTION` | Environment variable for the raw backup Qdrant collection (default: `<agent>-memories`). |
| `TRUE_RECALL_COLLECTION` | Environment variable for the curated gems Qdrant collection (default: `true_recall`). |
| **memory (disambiguation)** | "Memory system" = the Redis+Qdrant capture/storage pipeline. "Household-memory" = the evergreen program that maintains and improves the memory system. "User memories" = per-person conversation data in `memory/<user_id>/`. "Completed Recently" = evergreen activity logs in STATE.md (not part of the memory system). |
| **timing.json status values** | `"ready"` (initial state), `"in_progress"` (currently running), `"completed"` (finished successfully), `"partial"` (ran but incomplete — accepted by validator), `"requires_ai"` (scripted executor cannot run this evergreen — use AI runner instead), `"failed"` (cycle failed), `"timeout"` (cycle exceeded time limit), `"error"` (unexpected error during cycle). |
| **Daily briefing** | Cross-evergreen coordination file at `evergreens/daily-briefing-YYYYMMDD.md` (auto-generated, auto-cleaned after 14 days). Not to be confused with daily memory files at `memory/<user_id>/YYYY-MM-DD.md`. |
| **Weekly synthesis** | Cross-evergreen analysis file at `evergreens/weekly-synthesis-YYYYMMDD.md`. Generated weekly by `weekly-synthesis.py` (keyword-based, no LLM) and optionally enriched by `evergreen-weekly-cycle.sh` (LLM-powered). Read during Level-Set alongside the daily briefing. Auto-cleaned after 30 days. |
| **Weekly deep-analysis cycle** | Opt-in weekly meta-cycle (`scripts/evergreen-weekly-cycle.sh`) that performs LLM-powered cross-evergreen synthesis, learning compaction, PARA candidate extraction, Next Steps triage, and trend projection. Produces the weekly synthesis file. Daily cycles work without it. |
| **Pre-session state maintenance** | Shell-side script (`scripts/preflight-state-maintenance.py`) that runs before each agent session. Compacts old Key Learnings to monthly archive files and annotates stale Next Steps items. No LLM required. |
| **Learnings archive** | Monthly files (`LEARNINGS-ARCHIVE-YYYY-MM.md`) in each evergreen directory containing Key Learnings older than 14 days, moved there by pre-session state maintenance. |
| **Stale item** | A Next Steps entry that appears in 3+ consecutive agenda-history archives. Annotated with `⚠️ STALE (N cycles)` by the pre-session maintenance script. |
| **metrics.json** | Per-evergreen file tracking quantitative measurements over time (sizes, counts, rates). Rolling window of 90 data points per metric. Read by the weekly cycle for trend projections. |
| **Backup (disambiguation)** | Two distinct backup mechanisms: (1) **Evergreen pre-run backups** — `evergreen-ai-runner.sh` copies STATE.md, AGENDA.md, and timing.json to `evergreens/<name>/.backups/` before each cycle (auto-cleaned after 7 days). (2) **Full system backups** — the 3:30 AM cron job (`/path/to/your/backup-script.sh` in `config/crontab.sample`) — user-provided, backs up the entire workspace. |

| **Deploy / Deployment** | The process of copying operational files from the cloned repo into the OpenClaw workspace using `scripts/deploy.sh`. After deployment, the repo is no longer needed at runtime. |
| **Workspace** | The OpenClaw workspace directory (default: `~/.openclaw/workspace/`) where deployed toolkit files, user data, and runtime state live. All cron jobs and operational paths point here, not the cloned repo. |
| **deploy.sh** | Script that copies scripts, evergreens, memory, tools, templates, and config from the repo to the workspace. Creates a `.venv`, generates `crontab.generated`, and runs `verify-deploy.py`. Safe to re-run with `--force` for upgrades. |
| **verify-deploy.py** | Post-deploy verification script that checks workspace structure, detects symlinks back to the repo, scans for leaked repo paths in config files, and validates runtime dependencies. |
| **crontab.generated** | Pre-filled crontab file created by `deploy.sh` with workspace paths already substituted. Review and install with `crontab crontab.generated`. |

For the memory system naming glossary (Jarvis Memory vs True Recall collections), see `memory/README.md`.

---

## Additional Terms

| Term | Definition |
|------|------------|
| **ClawHub** | OpenClaw’s skills marketplace / community hub. Referenced in prompt-injection security constraints. |
| **SOUL.md** | OpenClaw’s agent personality configuration file. Defines the agent’s identity, tone, and behavioral guidelines. |
| **Serper Clone** | An example self-hosted search API, referenced in `evergreens/upstream-architecture/TESTS.md` as an optional component. Not part of the core toolkit — if you don't self-host a search API, remove or ignore references to it in that file. |
| **Session (disambiguation)** | Two distinct meanings: (1) **OpenClaw session** — a running agent instance spawned by `openclaw agent` (e.g., evergreen AI runner sessions). (2) **Memory session** — a conversation transcript captured by `cron_capture.py` and stored in Redis for later backup/curation. |
