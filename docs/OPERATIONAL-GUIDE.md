# 🏗️ Evergreen Operational Guide

**Agent autonomy guidelines, dashboard maintenance rules, and operational patterns.** This is the companion to [`ARCHITECTURE.md`](../ARCHITECTURE.md) (the comprehensive technical reference).

See also: [`ARCHITECTURE.md`](../ARCHITECTURE.md) for the full technical reference (components, memory system, file structure, configuration).

---

## How It Works

Each evergreen runs as a standalone cron job at its own scheduled time. The AI runner spawns a full agent session via `openclaw agent`, which performs cognitive work (research, analysis, planning) that scripted executors cannot do.

```
Cron (4:00 AM) → evergreen-ai-runner.sh upstream-architecture
                    ↓
                 openclaw agent [--agent <name>] --message "..." --session-id "..." --timeout 1500 --json
                    ↓
                 AI agent executes 8-step cycle:
                   1. Level-Set - Read STATE.md, AGENDA.md
                   2. Complete - Finish old tasks
                   3. Research - Run real commands, gather data
                   4. Analyze - Interpret findings, identify risks
                   5. Housekeep - Archive, compact
                   6. Plan - Define actionable tasks
                   7. Test - Run smoke/regression tests
                   8. Finalize - Write findings, update STATE.md
                    ↓
                 Agent writes: AGENDA.md, STATE.md, timing.json
                    ↓
                 Done - meaningful data in agendas and dashboard
```

> **Full 8-step cycle details:** See [`evergreens/EVERGREENS.md`](../evergreens/EVERGREENS.md) for the canonical description of each step.

Each evergreen runs independently at its own time slot (see [`config/crontab.sample`](../config/crontab.sample) for canonical times):
- **4:00 AM** — upstream-architecture
- **4:30 AM** — system-health
- **5:00 AM** — prompt-injection
- **5:30 AM** — household-memory
- **6:00 AM** — `evergreen-final-check.py` verifies all ran, generates alerts

---

## Component Responsibilities

### `evergreen-ai-runner.sh` (Cron-Facing — Recommended)

**Purpose:** Spawn an AI agent session to run a full evergreen cycle

**Called by:** Cron at the evergreen's scheduled time

**What it does:**
1. Acquires a `flock` lock (prevents concurrent runs of same evergreen)
2. Checks OpenClaw gateway health (warns but doesn't abort if down)
3. Backs up STATE.md, AGENDA.md, and timing.json to `.backups/` (dated)
4. Constructs a task prompt with the evergreen name, workspace paths, and cross-evergreen context
5. Calls `openclaw agent [--agent <name>] --message "..." --session-id "..." --timeout 1500 --json`
6. The AI agent reads STATE.md (and the daily briefing if one exists), runs commands, writes findings to AGENDA.md and STATE.md
7. Validates output: timing.json is valid with recent timestamp, AGENDA.md and STATE.md exist and are non-empty
8. On failure or validation error: rolls back files from backup and sends a notification (if `EVERGREEN_NOTIFY_TARGET` is set)
9. On success: appends a stub entry to the daily briefing file (`evergreens/daily-briefing-YYYYMMDD.md`)
10. Cleans up old backups (>7 days) and old daily briefings (>14 days)
11. Logs everything to `logs/evergreen-{name}-{YYYYMMDD}.log`
12. Returns exit code 0 (success) or 1 (failure)

**Usage:**
```bash
# Cron runs one per time slot
./scripts/evergreen-ai-runner.sh upstream-architecture
./scripts/evergreen-ai-runner.sh system-health

# With custom timeout (seconds)
EVERGREEN_TIMEOUT=900 ./scripts/evergreen-ai-runner.sh system-health

# With a specific named agent (routes to that agent's model)
EVERGREEN_AGENT=evergreen ./scripts/evergreen-ai-runner.sh system-health

# With failure notifications (uses your configured messaging channel)
EVERGREEN_NOTIFY_TARGET=+11234567890 ./scripts/evergreen-ai-runner.sh system-health
```

**Key advantage:** The AI agent can perform cognitive tasks — research, analysis, planning, synthesis — that scripted executors cannot. Each run produces a substantive report with real, current data.

---

### `run-single-evergreen.py` (Manual / Alternative)

**Purpose:** Run a single evergreen cycle via direct Python execution

**Called by:** Manual invocation or alternative crontab entries

**What it does:**
1. Starts timing (`timing.json`)
2. Invokes `evergreen_ai_executor.py` for AI-orchestrated research
3. Executes the full 8-step cycle
4. Updates timing, dashboard
5. Logs results

**Note:** This requires an active AI agent session to coordinate. For cron use, prefer `evergreen-ai-runner.sh` which spawns its own agent session.

**Usage:**
```bash
# Manual test run
python3 scripts/run-single-evergreen.py --evergreen system-health --verbose
```

---

### `evergreen_ai_executor.py` (AI Orchestration)

**Purpose:** Provide context and prompts for the AI agent to execute meaningful research

**What it does:**
- Reads the evergreen's STATE.md, AGENDA.md, TESTS.md
- Provides structured prompts for each of the 8 steps
- Handles mechanical steps (timing, archiving, dashboard updates)
- Returns control to the AI for cognitive work (research, analysis, planning)

**Key advantage:** The AI executes real commands (git, curl, systemctl) and writes substantive findings, rather than generating placeholder content.

---

### `evergreen-final-check.py` (Post-Run Verification)

**Purpose:** Verify all evergreens ran successfully, generate alerts if issues detected

**Called by:** Cron at 6:00 AM (after all evergreens should be complete)

**Outputs:**
- `.evergreen-final-check-status.json` — machine-readable status
- `.evergreen-alert.md` — human-readable alert (only if issues found)

**Note:** The cron wrapper (`final-check-wrapper.sh`) passes `--force` to always send a status notification (success or failure). Without `--force`, notifications are only sent when issues are detected.

---

### `update_evergreen_dashboard.py` (Dashboard Generator)

**Purpose:** Generate `evergreens/DASHBOARD.html` from timing and state data

**Called:** Automatically at end of each evergreen cycle

---

## Agent Autonomy & Decision-Making

See [AUTONOMY-GUIDELINES.md](AUTONOMY-GUIDELINES.md) for the complete autonomy framework covering auto-apply vs. ask-first rules, escalation procedures, and the 30-second reversibility test.

**Quick summary:** If you can undo it in <30 seconds with one command, auto-apply. Otherwise, document in AGENDA.md and notify for review.

---

## Dashboard "Recent Activity" Maintenance

The dashboard's "Recent Activity" section pulls from each evergreen's `STATE.md` "Completed Recently" section.

**Each evergreen is responsible for maintaining its own activity log:**

### Rules for AI Agent (in Step 8)
1. **Add** today's accomplishment after each cycle:
   ```markdown
   - [2009-01-03] AI orchestration implemented for evergreen cycles
   ```
2. **Keep** only 3-5 most recent items
3. **Remove** oldest item(s) when list exceeds 5 items
4. **Examples by evergreen:**
   - `upstream-architecture`: Version updates, model strategy changes, tool additions
   - `system-health`: Security fixes, backup improvements, health monitoring
   - `prompt-injection`: Vulnerability remediations, security audits
   - `household-memory`: Pipeline improvements, curation wins, user-specific milestones

### Dashboard Aggregation
The `update_evergreen_dashboard.py` script:
1. Reads all 4 `STATE.md` files
2. Extracts "Completed Recently" sections
3. Sorts by date (newest first)
4. Shows top 5-10 items in dashboard

---

## Sequential Processing Order

Evergreens should run in this order (enforced by cron time slots):

1. **upstream-architecture** (4:00 AM) — Dependencies, OpenClaw version, model strategy
2. **system-health** (4:30 AM) — Resources, backups, cron jobs (may depend on upstream info)
3. **prompt-injection** (5:00 AM) — Security posture (may depend on upstream/tool info)
4. **household-memory** (5:30 AM) — Memory architecture (may depend on all of the above)

**Why sequential?**
- Prevents resource contention
- Later evergreens benefit from the **daily briefing file** — each successful run appends a summary to `evergreens/daily-briefing-YYYYMMDD.md`, and later evergreens read it for cross-cutting context
- Clear timing tracking per evergreen
- Easier debugging (one at a time)

---

## Integration Points

### Crontab Configuration

See [`docs/SCHEDULING.md`](SCHEDULING.md) for the full default schedule and timezone conversion guidance. See [`config/crontab.sample`](../config/crontab.sample) for a ready-to-use crontab template.

**Summary:** Evergreens run at 4:00, 4:30, 5:00, and 5:30 AM via `evergreen-ai-runner.sh`. Final check runs at 6:00 AM. Memory jobs (True Recall + Jarvis backup) run at 2:30–3:05 AM before the evergreens.

### Error Handling

Each evergreen runs independently, so failures are isolated:

- **Pre-run backup:** STATE.md, AGENDA.md, and timing.json are backed up before each run
- **Post-run validation:** Output files are checked for existence, non-emptiness, and valid content
- **Automatic rollback:** If the agent fails or validation fails, files are restored from the pre-run backup
- **Failure notification:** If `EVERGREEN_NOTIFY_TARGET` is set, a message is sent via your configured OpenClaw messaging channel (WhatsApp, Telegram, Slack, etc.)
- **Single evergreen failure:** Logged, other evergreens unaffected
- **Final check detects failures:** Generates alert file for notification
- **Dashboard update failure:** Logged, doesn't block completion

**Log locations:**
- `logs/evergreen-{name}-{YYYYMMDD}.log` — Per-evergreen daily log (AI runner)
- `logs/evergreen-executor.log` — Combined log (direct executor)
- `evergreens/<name>/timing.json` — Per-evergreen timing data
- `evergreens/<name>/AGENDA.md` — Cycle findings and blockers

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting, including cron issues, dashboard problems, slow evergreens, memory system errors, and more.

---

## Testing Your Setup

### Manual Test (Recommended Before Automation)

```bash
cd ~/.openclaw/workspace

# Run one evergreen manually with AI runner
./scripts/evergreen-ai-runner.sh system-health

# Verify completion
cat evergreens/system-health/timing.json
cat evergreens/system-health/AGENDA.md | head -20
```

### Automated Test (After Configuring Cron)

```bash
# Wait for next scheduled run, then check:

# 1. Agendas should show today's date
ls evergreens/*/AGENDA.md | xargs head -1 | grep $(date +%Y-%m-%d)

# 2. Dashboard should be updated
cat evergreens/DASHBOARD.html | grep "Data updated"

# 3. Final check should show all passed
cat .evergreen-final-check-status.json
```

---

**TL;DR:** Cron runs each evergreen directly at its scheduled time. No trigger files needed for cron scheduling. Heartbeats can optionally use `.run_requested` trigger files for on-demand runs (create with `touch evergreens/<name>/.run_requested`; the heartbeat checks for these and runs the evergreen if found) — see `config/HEARTBEAT-TEMPLATE.md`. 🌲
