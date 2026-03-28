# 🏗️ System Architecture

> **For setup:** You don't need to read this during initial installation. Follow [QUICKSTART.md](QUICKSTART.md) instead. This document is a technical reference for understanding the system after it's running.

**Comprehensive technical reference for developers and AI agents implementing the Evergreen Toolkit.** Covers all components, memory system architecture, file structure, data flow, and configuration.

See also: [`docs/OPERATIONAL-GUIDE.md`](docs/OPERATIONAL-GUIDE.md) for agent autonomy guidelines, dashboard maintenance rules, and operational testing procedures.

---

## System Overview

The Evergreen Toolkit is a **self-improving automation framework** for OpenClaw agents. It consists of four autonomous programs (evergreens) that run on a schedule, each focused on continuous improvement in a specific domain.

```
┌────────────────────────────────────────────────────────────────┐
│                        Crontab Scheduler                        │
│  (Runs each evergreen directly at its scheduled time)          │
└────────────────────┬───────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        │ 4:00 AM    │ 4:30 AM    │ 5:00 AM    │ 5:30 AM
        ▼            ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Upstream │ │ System  │ │ Prompt  │ │Household│
   │Arch.    │ │ Health  │ │Inj.     │ │ Memory  │
   │(~30min) │ │ (~5min) │ │(~10min) │ │(~30min) │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Dashboard HTML       │
                    │   (Auto-generated)     │
                    └────────────────────────┘
```

---

## Core Components

### 1. AI Runner (`scripts/evergreen-ai-runner.sh`) — Recommended

**Purpose:** Spawn an AI agent session via `openclaw agent` to run a full evergreen cycle

**Key Functions:**
- Acquires `flock` lock (prevents concurrent runs of same evergreen)
- Checks OpenClaw gateway health
- Backs up STATE.md, AGENDA.md, and timing.json before each run
- Constructs task prompt with evergreen name, workspace context, cross-evergreen briefing, and time management guidance
- Calls `openclaw agent --message "..." --session-id "..." --timeout 1500 --json`
- Validates output files after completion (timing.json, AGENDA.md, STATE.md)
- Rolls back to backup and sends failure notification on error
- Appends a stub entry to the daily briefing file on success
- Cleans up old backups (>7 days) and daily briefings (>14 days)

**Execution Flow:**
```
1. Cron calls evergreen-ai-runner.sh <name>
2. flock acquires lock ($WORKSPACE/.evergreen-<name>.lock)
3. openclaw health — pre-flight check
4. Backup STATE.md, AGENDA.md, timing.json to .backups/
5. Pre-session state maintenance (compact old learnings, detect stale items)
6. Archive and reset agent session history (clean context window)
7. openclaw agent runs 8-step cycle (see EVERGREENS.md)
8. Validate output (timing.json valid, AGENDA.md & STATE.md non-empty)
9. On failure: rollback from backup, send notification, exit 1
10. On success: append findings to daily-briefing-YYYYMMDD.md
11. Cleanup old backups and briefings
12. Log results to logs/evergreen-<name>-YYYYMMDD.log
```

**Usage:**
```bash
# Cron runs one evergreen per scheduled time slot
./scripts/evergreen-ai-runner.sh system-health

# With custom timeout (seconds)
EVERGREEN_TIMEOUT=900 ./scripts/evergreen-ai-runner.sh upstream-architecture
```

**Key advantage:** The AI agent performs cognitive tasks — research, analysis, planning, synthesis — producing substantive reports with real, current data.

---

### 2. Direct Executor (`scripts/run-single-evergreen.py`) — Alternative

**Purpose:** Runs a single evergreen cycle via direct Python execution (no `openclaw agent` session, but still invokes AI orchestration via `evergreen_ai_executor.py`)

**Key Functions:**
- `run_evergreen(evergreen)` - Executes the full evergreen cycle
- `update_timing(evergreen, status)` - Updates timing.json with timestamps and status
- Calls `evergreen_ai_executor.py` for AI-orchestrated research

**Execution Flow:**
```python
1. Cron calls run-single-evergreen.py --evergreen <name>
2. update_timing(status="started")
3. Execute 8-step evergreen process (see EVERGREENS.md)
4. update_timing(status="completed")
5. Update dashboard
```

**Usage:**
```bash
# Manual test run (direct executor)
python3 scripts/run-single-evergreen.py --evergreen system-health
```

**Note:** For cron use, prefer `evergreen-ai-runner.sh` which spawns its own agent session and handles locking, health checks, and logging automatically.

### Quick Reference: Which Runner?

| Use Case | Script | Notes |
|----------|--------|-------|
| Cron automation | `evergreen-ai-runner.sh` | Spawns agent session, handles locking/rollback |
| Manual testing | `run-single-evergreen.py` | Direct Python execution |
| Called internally | `evergreen_ai_executor.py` | AI orchestration helper — called by runner scripts, not by users directly |
| Fallback | `evergreen-scripted-executor.py` | Mechanical checks only, no AI (see note below) |

**Notes:**
- **Scripted executor limitations:** `evergreen-scripted-executor.py` only implements checks for `system-health` and `prompt-injection`. For `upstream-architecture` and `household-memory`, it logs a skip warning. Use the AI runner for full coverage.
- **Timeout differences:** The AI runner defaults to 1500s (25 min) timeout (overridable via `EVERGREEN_TIMEOUT`), while `run-single-evergreen.py` uses per-evergreen expected runtimes doubled (e.g., system-health: 600s, upstream-architecture: 3600s).

---

### 3. Dashboard Generator (`scripts/update_evergreen_dashboard.py`)

**Purpose:** Generates `evergreens/DASHBOARD.html` with real-time status

**Inputs:**
- `timing.json` from each evergreen (cycle timing, status)
- `STATE.md` from each evergreen (health status, recent activity)
- System metrics (disk, RAM, uptime via `system-health` evergreen)

**Outputs:**
- Single HTML file with:
  - System status summary
  - Four evergreen health cards
  - Recent activity log
  - Investment suggestions (optional)

**Regeneration:** Called automatically at end of each evergreen cycle

---

### 4. Weekly Deep-Analysis Cycle (Optional)

**Script:** [`scripts/evergreen-weekly-cycle.sh`](scripts/evergreen-weekly-cycle.sh)

An opt-in weekly cycle that performs heavier, LLM-powered analysis too expensive for daily runs:

- **Semantic learning compaction** — merge redundant Key Learnings entries in STATE.md
- **Agenda-history pattern mining** — surface emerging themes from the past week
- **Cross-evergreen synthesis** — identify issues that span multiple evergreen domains
- **PARA candidate extraction** — propose durable facts for promotion to the knowledge base
- **Next Steps triage** — recommend keep/escalate/merge/drop for each item
- **Metrics trend projection** — compute forward projections from `metrics.json`

**Schedule:** Once per week (e.g., Sunday 6:30 AM, after daily cycles complete). Add to crontab only if you want the deeper analysis. The daily cycles continue to work without this.

**Outputs:** `evergreens/weekly-synthesis-YYYYMMDD.md` — read by daily cycles if available.

**Fallback:** If the LLM step fails, `scripts/weekly-synthesis.py` provides a keyword-based shell-side synthesis.

---

### 5. Memory System (7-Layer Architecture + Multi-User Support)

**Key Differentiator:** This memory system is designed for **households with multiple users**, not just single-user setups.

See also: [`MEMORY-SYSTEM.md`](MEMORY-SYSTEM.md) for a standalone overview.

#### 7-Layer Architecture

| # | Layer | Purpose | Technology |
|---|-------|---------|------------|
| 1 | **Session** | In-session coherence + automatic recall | LCM (optional) + Gigabrain (optional) |
| 2 | **Fast Capture** | Real-time conversation capture | Redis buffer (`mem:<user_id>`) |
| 3 | **Raw Archive** | Full transcript backup + daily files | Qdrant `<agent>-memories` + `memory/<user>/YYYY-MM-DD.md` |
| 4 | **AI Curation** | High-salience gem extraction | True Recall → Qdrant `true_recall` |
| 5 | **Durable Knowledge** | Structured facts — canonical source of truth | PARA (`memory/para/<user>/`) |
| 6 | **Operational Rules** | Behavioral rules, autonomy guidelines | `AGENTS.md` (managed blocks) |
| 7 | **Routing** | Tells the agent where to look | `MEMORY.md` (tiny index) |

```
Conversation → Redis capture → True Recall (gems) → PARA promotion (facts)
                             → Jarvis (raw backup) → Daily files
```

- **Layers 1-4** handle capture + retrieval (session → buffer → archive → curation).
- **Layer 5 (PARA)** is durable truth — structured facts that survive indefinitely.
- **Layer 6 (AGENTS.md)** holds behavioral rules, not memory.
- **Layer 7 (MEMORY.md)** is a routing index, not a memory store.

#### Multi-User Architecture

Each user has isolated memory within a shared collection (filtered by `user_id`):

```
User: Alice                          User: Bob
├─ Redis: mem:alice                 ├─ Redis: mem:bob
├─ Files: memory/alice/             ├─ Files: memory/bob/
├─ PARA: memory/para/alice/         ├─ PARA: memory/para/bob/
├─ Qdrant: <agent>-memories             ├─ Qdrant: <agent>-memories
│   (filter: user_id=alice)         │   (filter: user_id=bob)
└─ Curator: curator_prompts/alice.md └─ Curator: curator_prompts/bob.md
```

**Benefits:**
- **Theory of Mind** - AI understands Alice doesn't know what Bob knows
- **Privacy** - Personal memories stay private unless explicitly shared
- **Context** - AI remembers "Bob is Alice's husband" when talking to either
- **Personalization** - Different curator prompts per user (technical vs non-technical)
- **Durable Knowledge** - PARA directories hold canonical facts per user

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Session (Optional Plugins)                     │
│ - LCM (lossless-claw): session recovery                │
│ - Gigabrain: automatic context recall                   │
│ - See docs/PLUGIN-RECOMMENDATIONS.md                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Redis Buffer (Fast Capture)                    │
│ - Key: mem:<user_id>                                    │
│ - TTL: 24-48 hours                                      │
│ - Sub-second writes                                     │
│ - Scripts: save_mem.py, hb_append.py                   │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼ (2:30 AM)           ▼ (3:00 AM)
┌──────────────────────┐  ┌──────────────────────┐
│  True Recall Curator │  │  Jarvis Memory       │
│  AI-curated gems     │  │  Raw conversation    │
│  → Qdrant true_recall│  │  backup → Qdrant     │
│  (does NOT clear     │  │  <agent>-memories    │
│   Redis)             │  │  (clears Redis after)│
└──────────┬───────────┘  └──────────┬───────────┘
           │                         │
           ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Raw Archive                                    │
│ - Qdrant <agent>-memories (full transcripts)            │
│ - Markdown files: memory/<user_id>/2009-01-02.md       │
│ - Human-readable + machine-searchable                   │
│ - Scripts: cron_backup.py, cron_capture.py             │
├─────────────────────────────────────────────────────────┤
│ Layer 4: AI Curation                                    │
│ - Qdrant true_recall (high-salience gems)              │
│ - Permanent retention                                   │
│ - Scripts: curate_memories.py, extract_facts.py        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼ (weekly promotion)
┌─────────────────────────────────────────────────────────┐
│ Layer 5: PARA — Durable Knowledge                       │
│ - memory/para/<user>/summary.md (key facts)            │
│ - memory/para/<user>/items.json (structured facts)     │
│ - memory/para/<user>/review-queue.md (contradictions)  │
│ - Canonical source of truth per user                    │
│ - Scripts: promote_to_para.py, seed_para.py            │
└─────────────────────────────────────────────────────────┘
```

The system has seven layers organized in two groups: capture/retrieval (layers 1-4) and durable knowledge/rules (layers 5-7). True Recall runs first and does NOT clear Redis; Jarvis runs second and clears Redis after backing up. PARA promotion extracts durable facts from curated gems on a weekly cycle.

**PARA layer details:** See [`memory/para/README.md`](memory/para/README.md) for the full PARA schema, directory structure, and privacy model.

**Configuration:**
```bash
# .memory_env file
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=<agent>-memories
DEFAULT_USER_ID=<user-id>
```

---

### 6. Markdown Viewer (`tools/markdown-viewer.js`)

**Purpose:** Serve formatted .md files as web pages

**Features:**
- Node.js HTTP server with markdown rendering
- Syntax highlighting for code blocks
- Localhost-only access (security)
- Port 3000 by default

**Usage:**
```bash
cd tools
node markdown-viewer.js

# Access: http://localhost:3000/view?file=/path/to/file.md
```

---

## File Structure

```
evergreen-toolkit/                 # Repo (source template)
├── config/                    # Configuration templates
│   ├── AGENTS-TEMPLATE.md     # AGENTS.md behavioral rules template
│   ├── HEARTBEAT-TEMPLATE.md  # Heartbeat check-in template
│   ├── MEMORY-TEMPLATE.md     # MEMORY.md routing index template
│   ├── README.md              # Configuration guide
│   ├── agenda-template.md     # Template for evergreen agendas
│   ├── categories.example.yaml # Memory curation category template
│   ├── crontab.sample         # Sample crontab with timezone comments
│   ├── memory_env.example     # .memory_env configuration template
│   └── openclaw-plugins.example.json  # OpenClaw config snippet
├── docs/                      # Detailed documentation
│   ├── AUTONOMY-GUIDELINES.md # Agent autonomy rules
│   ├── HEARTBEAT-MEMORY-INTEGRATION.md
│   ├── MEMORY-FIRST-STRATEGY.md # Memory-first design philosophy
│   ├── MEMORY-INTEGRATION.md  # Memory system integration
│   ├── NAME-CUSTOMIZATION.md  # Name replacement guidance
│   ├── OPERATIONAL-GUIDE.md   # Agent autonomy, operational patterns
│   ├── PLUGIN-RECOMMENDATIONS.md # Optional session-layer plugins
│   ├── README.md              # Documentation index
│   ├── SCHEDULING.md          # Timezone-aware scheduling
│   ├── SETUP-GUIDE.md         # Step-by-step setup
│   ├── TROUBLESHOOTING.md     # Common issues + solutions
│   └── UPSTREAM-MONITORING-GUIDE.md
├── evergreens/                # Evergreen program directories
│   ├── DASHBOARD.html         # Auto-generated status dashboard
│   ├── EVERGREENS.md          # Framework documentation
│   ├── upstream-architecture/ # Each evergreen has STATE.md, TESTS.md,
│   │   ├── STATE.md           #   timing.json, agenda-history/, plus
│   │   ├── TESTS.md           #   topic-specific files (AGENDA.md,
│   │   ├── REFERENCES.md      #   REFERENCES.md, CONSTRAINTS.md, etc.)
│   │   ├── timing.json
│   │   └── agenda-history/
│   ├── system-health/         # + RECOVERY-RUNBOOK.md, INFRASTRUCTURE-OPTIMIZATION.md
│   ├── prompt-injection/      # + CONSTRAINTS.md, CREDENTIAL-AUDIT.md, TOOL-AUDIT.md, etc.
│   ├── household-memory/      # + AGENDA.md, CAPTURE-PATTERNS.md, EXPERIMENTS.md
│   └── daily-briefing-*.md    # Cross-evergreen daily briefing (auto-generated, auto-cleaned)
│                              # NOTE: These are operational coordination files, NOT user memory.
│                              # User memory daily files are at memory/<user_id>/YYYY-MM-DD.md
├── memory/                    # Memory system implementation
│   ├── README.md              # Architecture overview
│   ├── MULTI-USER-GUIDE.md    # Multi-user setup
│   ├── UPSTREAM-CREDITS.md    # Attribution for upstream projects
│   ├── OPENCLAW-FORK-CHANGES.md # Fork-specific changes from upstream
│   ├── settings.md            # Configuration options
│   ├── SKILL.md               # OpenClaw skill definition
│   ├── para/                  # PARA durable knowledge layer
│   │   ├── README.md          # PARA schema, structure, privacy model
│   │   └── templates/         # Per-user directory templates
│   ├── curator_prompts/       # Curator prompts (base.md + per-user overrides)
│   ├── docs/                  # Memory system documentation
│   └── scripts/               # Memory scripts (~37 Python files)
├── scripts/                   # Core orchestration scripts
│   ├── evergreen-ai-runner.sh  # AI runner (cron-facing, recommended)
│   ├── evergreen-weekly-cycle.sh # Weekly deep-analysis cycle (opt-in)
│   ├── run-single-evergreen.py # Direct executor (alternative to AI runner)
│   ├── evergreen_ai_executor.py # AI orchestration helper
│   ├── evergreen-scripted-executor.py # Scripted cycle executor
│   ├── evergreen-final-check.py # Post-run verification
│   ├── final-check-wrapper.sh  # Shell wrapper for final check
│   ├── seed-evergreens.py     # Initialize evergreen structure
│   ├── update_evergreen_dashboard.py  # Dashboard generator
│   ├── preflight-check.py     # Pre-run environment validation
│   ├── preflight-state-maintenance.py # Pre-session state compaction and stale detection
│   ├── weekly-synthesis.py    # Shell-side cross-evergreen weekly synthesis
│   ├── validate-customization.py # Validate placeholder replacements
│   ├── health_check.sh        # System health checker
│   ├── fix-markdown-links.js  # Convert file:// links to viewer URLs
│   └── setup-markdown-viewer.sh # Install markdown viewer service
│   # Naming convention: shell scripts and Python entry points use hyphens;
│   #   importable Python modules use underscores (Python import convention).
├── templates/                 # Templates and examples
│   ├── EXAMPLE-COMPLETED-CYCLE.md  # Example completed cycle archive
│   └── STATE-TEMPLATE.md      # Blank state template
├── tools/                     # Utility tools
│   ├── markdown-viewer.js     # Markdown web viewer
│   ├── MARKDOWN-VIEWER.md     # Viewer documentation
│   └── README.md              # Tools overview
├── ARCHITECTURE.md            # This file
│                              # NOTE: MEMORY.md, AGENTS.md, and HEARTBEAT.md are workspace
│                              #   files created by deploy.sh from templates in config/.
│                              #   They do not exist in the repo itself — see QUICKSTART Step 5.
├── AGENT-ONBOARDING.md        # Quick reference for implementing agents
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
├── PUBLISHING.md              # Publishing / sharing your fork
├── GLOSSARY.md                # Key terminology definitions
├── QUICKSTART.md              # Condensed setup
├── README.md                  # Project overview
├── SECURITY.md                # Security policy and contacts
├── MEMORY-SYSTEM.md              # 7-layer memory system overview
├── LICENSE                    # MIT license
├── requirements.txt           # Python dependencies
└── .gitignore                 # Git ignore rules
```

---

## Data Flow

### Evergreen Execution Flow

```
1. Cron calls evergreen-ai-runner.sh <name>
   └─> Runs at scheduled time (e.g. 4:00 AM)
   └─> Acquires flock lock, checks gateway health

2. Pre-run backup
   └─> STATE.md, AGENDA.md, timing.json → .backups/{file}.pre-YYYYMMDD

3. Pre-session state maintenance
   ├─> Compact Key Learnings older than 14 days → LEARNINGS-ARCHIVE-YYYY-MM.md
   └─> Annotate Next Steps items stuck for 3+ cycles with ⚠️ STALE marker

4. Archive and reset agent session history (clean context window)

5. AI runner spawns agent session
   └─> openclaw agent --message "..." --session-id "..." --timeout 1500 --json
   └─> Agent receives cross-evergreen briefing and weekly synthesis (if any)

6. Agent runs evergreen cycle
   ├── Step 1: Level-Set (read STATE.md, daily briefing, weekly synthesis, metrics)
   ├── Step 2: Complete (finish incomplete tasks)
   ├── Step 3: Research (web search, upstream checks)
   ├── Step 4: Analyze (synthesize findings)
   ├── Step 5: Housekeep (archive, compact)
   ├── Step 6: Plan (propose experiments)
   ├── Step 7: Test (run smoke/regression tests)
   └── Step 8: Finalize (update STATE.md, metrics.json, dashboard)

7. Post-run validation
   ├── timing.json: valid JSON, completed_at recent, status completed/partial
   ├── AGENDA.md: exists, non-empty
   └── STATE.md: exists, non-empty

8. On failure: rollback from backup, send notification
   On success: update dashboard, append findings to daily-briefing-YYYYMMDD.md

9. Cleanup old backups (>7 days) and briefings (>14 days)

10. Final check (6:00 AM)
   └─> evergreen-final-check.py verifies all ran

11. Weekly deep-analysis cycle (opt-in, Sunday 6:30 AM)
   ├─> Shell-side synthesis: keyword overlap across all evergreens
   └─> LLM-powered analysis: semantic cross-evergreen synthesis,
       learning compaction, PARA candidate extraction, Next Steps triage,
       trend projection → weekly-synthesis-YYYYMMDD.md
```

---

## Scheduling

### Default Schedule (Example: CST — adjust for your timezone)

> **Canonical source:** [`config/crontab.sample`](config/crontab.sample) contains the actual cron entries with full comments. The table below is a summary.

| Time | Action | Component |
|------|--------|-----------|
| Every 5 min | Session capture from transcripts (per user) | Cron → `cron_capture.py` (per user) |
| 2:30 AM | True Recall curation | Cron → `curate_memories.py` |
| 3:00 AM | Jarvis Memory backup | Cron → `cron_backup.py` |
| 3:30 AM | Full system backup | Cron → system backup script |
| 4:00 AM | upstream-architecture | Cron → `evergreen-ai-runner.sh` |
| 4:30 AM | system-health | Cron → `evergreen-ai-runner.sh` |
| 5:00 AM | prompt-injection | Cron → `evergreen-ai-runner.sh` |
| 5:30 AM | household-memory | Cron → `evergreen-ai-runner.sh` |
| 6:00 AM | Final check | Cron → `evergreen-final-check.py` |
| Sunday 6:30 AM | Weekly deep-analysis (opt-in) | Cron → `evergreen-weekly-cycle.sh` |

### Timezone Conversion

Adjust all crontab times for your server's local timezone. See [`docs/SCHEDULING.md`](docs/SCHEDULING.md) for conversion tables and examples.

---

## Configuration Files

### 1. Crontab (`crontab -e`)

```bash
# Evergreen AI runner (recommended — spawns agent session with locking)
0 4 * * *  $WORKSPACE/scripts/evergreen-ai-runner.sh upstream-architecture
30 4 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh system-health
0 5 * * *  $WORKSPACE/scripts/evergreen-ai-runner.sh prompt-injection
30 5 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh household-memory

# Final check (6:00 AM)
0 6 * * * $WORKSPACE/scripts/final-check-wrapper.sh

# Weekly deep-analysis cycle (opt-in, Sunday 6:30 AM)
30 6 * * 0 $WORKSPACE/scripts/evergreen-weekly-cycle.sh

# See config/crontab.sample for complete template
```

### 2. Memory Environment (`.memory_env`)

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export QDRANT_URL=http://localhost:6333
export QDRANT_COLLECTION=<agent>-memories
export DEFAULT_USER_ID=<default-user-id>
```

---

## Path Convention

The toolkit uses a **deploy model**: the cloned repo is a source template, and `deploy.sh` copies operational files into the OpenClaw workspace.

- **Workspace root** — where the deployed toolkit lives (e.g., `~/.openclaw/workspace/`). Scripts in `scripts/` auto-detect this from their own location using `dirname`. This is where evergreen docs, config files, orchestration scripts, and user data live.
- **OpenClaw workspace** (`OPENCLAW_WORKSPACE`) — same as the workspace root in the deployed model. Memory scripts use this to find transcript files, session data, and other OpenClaw artifacts.
- **Repo clone** — where the toolkit was originally cloned (e.g., `~/evergreen-toolkit/`). Only needed for initial setup and future upgrades. Can be deleted after deployment.

Scripts handle path resolution automatically using `__file__`-relative paths — the same scripts work in both the repo and the deployed workspace.

---

## Security Considerations

### Credential Management

- **Never commit** `.memory_env`, API keys, or credentials
- Use environment variables or secret management
- All example configs use placeholders (`<user1>`, `yourdomain.com`)

### Network Security

- Redis: Bind to localhost only (`127.0.0.1`)
- Qdrant: Bind to localhost or use authentication
- Markdown viewer: Localhost only, no CORS to external domains

### Memory Validation

- External content (emails, web fetches) wrapped with security notices
- Input validation on all user-provided data
- Sanitization before storing in memory

See [`evergreens/prompt-injection/CREDENTIAL-AUDIT.md`](evergreens/prompt-injection/CREDENTIAL-AUDIT.md) for complete security guidelines.

---

## Extending the Toolkit

### Adding a New Evergreen

1. **Create directory:**
   ```bash
   mkdir evergreens/your-evergreen-name
   cd evergreens/your-evergreen-name
   ```

2. **Initialize STATE.md:**
   ```markdown
   # Your Evergreen Name - State

   ## Status
   - Overall Health: 🟢 Good
   - Last Cycle: 2009-01-02

   ## Next Steps
   - [ ] First task
   ```

3. **Create TESTS.md:**
   ```markdown
   ## Smoke Tests (Every Cycle)
   - [ ] Can read STATE.md
   - [ ] Can write to directory

   ## Regression Tests (After Changes)
   - [ ] Test description
   ```

4. **Add to schedule:**
   - Add crontab entry: `/path/to/scripts/evergreen-ai-runner.sh your-evergreen-name`
   - Document in README.md

### Adding Memory Scripts

1. **Create script in `memory/scripts/`:**
   ```python
   #!/usr/bin/env python3
   """
   Script purpose description.

   Usage: python3 script_name.py [args]
   """

   import os
   import sys
   from pathlib import Path

   # Use environment variables for config
   REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
   USER_ID = os.getenv('USER_ID', 'your-user-id')

   # Implementation...
   ```

2. **Add to memory/README.md table**
3. **Create tests in memory/scripts/TESTS.md**

---

## Performance Characteristics

### Resource Usage

| Component | RAM | CPU | Disk | Network |
|-----------|-----|-----|------|---------|
| Redis | ~50 MB | <1% | Minimal | Local only |
| Qdrant | ~200 MB | <5% | ~1 GB/year | Local only |
| Evergreen execution | ~100 MB | 10-20% | Minimal | Moderate (API calls) |
| Dashboard generation | ~50 MB | <5% | 50 KB output | None |

### Scaling

- **Single-agent:** Default deployment (one OpenClaw instance)
- **Multi-agent:** Each agent runs independent evergreens
- **Shared services:** Redis/Qdrant can be shared across agents

### Bottlenecks

1. **LLM API calls** - Rate limits, latency (most time spent)
2. **Web searches** - External API dependencies
3. **Memory curation** - CPU-intensive for large datasets

**Optimization tips:**
- Use caching for repeated queries
- Batch API calls when possible
- Run during low-activity periods

---

## Troubleshooting

### Common Issues

**"Cron job not running"**
- Check crontab: `crontab -l | grep evergreen`
- Verify cron is running: `systemctl status cron`
- Check permissions: User must own workspace directory

**"Redis connection refused"**
- Start Redis: `redis-server --daemonize yes`
- Verify: `redis-cli ping` should return `PONG`
- Check `.memory_env` has correct host/port

**"Qdrant collection not found"**
- Initialize collection: Run `memory/scripts/init_memory_collections.py`
- Verify Qdrant running: `curl http://localhost:6333/`
- Check collection: `curl http://localhost:6333/collections`

**"Evergreen stuck in progress"**
- Check `timing.json` for status
- Review logs: `tail logs/evergreen-*.log`
- Manually run: `./scripts/evergreen-ai-runner.sh <name>`

### Debug Mode

Enable verbose logging:
```bash
# AI runner (recommended)
./scripts/evergreen-ai-runner.sh system-health
# Output is logged to logs/evergreen-system-health-YYYYMMDD.log

# Direct executor (alternative)
export DEBUG=1
python3 scripts/run-single-evergreen.py --evergreen system-health --verbose
```

---

### 🙏 Attribution: Jarvis Memory + True Recall

The memory system was designed and implemented by **SpeedyFoxAI**:

- **Jarvis Memory** — the raw conversation backup process (Redis → Qdrant at 3:00 AM, then clears Redis)
- **True Recall** — the AI curation layer (reads Redis at 2:30 AM, extracts high-value "gems" via LLM, stores to Qdrant)

The Qdrant collection `<agent>-memories` uses your agent's name as a prefix (e.g., `eve-memories`, `jarvis-memories`). See `memory/README.md` for the full naming glossary.

- **Original Repository:** https://gitlab.com/mdkrush/openclaw-true-recall-base
- **Status:** Actively maintained

See `memory/UPSTREAM-CREDITS.md` for full attribution details and upstream monitoring instructions.

---

**For implementation help:** See [QUICKSTART.md](QUICKSTART.md) and [docs/SETUP-GUIDE.md](docs/SETUP-GUIDE.md)

**For questions:** Open an issue on GitHub or ask in Discord #skills channel
