# 🌲 Evergreen Framework

Evergreens are standing programs that receive daily attention through small, reversible experiments and continuous improvement. Each operates independently with its own living memory.

---

## Design Principles

1. **Non-blocking** — Run as sub-agents or during low-activity periods
2. **Reversible** — Small experiments with clear rollback paths
3. **Constraint-aware** — Work within system limits (RAM, CPU, disk)
4. **Self-documenting** — Living memory captures state, experiments, and learnings
5. **Upstream-informed** — The Upstream Architecture evergreen constrains all others

---

## The Evergreen Registry

Four core evergreens, rotating schedule (see [`config/crontab.sample`](../config/crontab.sample) for exact cron times):

| Evergreen | Purpose | Runtime |
|-----------|---------|---------|
| 🌱 **upstream-architecture** | Monitor upstream dependencies, releases, breaking changes | ~30 min |
| 🌱 **system-health** | Check system resources, backups, cron jobs, reliability | ~5 min |
| 🌱 **prompt-injection** | Security audits, credential checks, memory validation, vetting | ~10 min |
| 🌱 **household-memory** | Memory architecture, capture patterns, curation experiments | ~30 min |

---

## The Eight-Step Evergreen Cycle

Each cycle follows this pattern:

### Step 1: Level-Set (State Assessment)

- Read your evergreen's `STATE.md`
- Review open tasks/experiments
- Check for changes in constraints or context
- **Pull from upstream:** Read `upstream-architecture/STATE.md` for current constraints
- Assess system impact of any running experiments
- **Update agenda:** Add initial tasks from STATE.md Next Steps section

### Step 2: Complete (Finish What's Started)

- Check for incomplete work from last cycle
- Run experiments that are ready
- Document results (success/failure/learnings)
- Clean up abandoned experiments
- **Update agenda:** Mark completed tasks, add findings and reasoning

### Step 3: Research (External Knowledge)

- Web search for new developments in your domain
- Check upstream project releases/changes
- Review security advisories (for security-related evergreens)
- Note new tools, techniques, or best practices
- **Update agenda:** Add findings to "Research Findings" section with sources

### Step 4: Analyze (Deep Dive)

- Synthesize research findings
- Identify gaps in current implementation
- Evaluate potential improvements
- Consider constraint impacts
- **Update agenda:** Add analysis results, recommendations with reasoning

### Step 5: Housekeep (Memory Maintenance)

- Archive previous cycle's AGENDA.md to `agenda-history/` (handled by executor)
- Check document sizes against thresholds
- Archive old verbose entries to daily files
- Compact summaries in main documents
- Ensure key learnings are in searchable memory (Qdrant)
- Prune truly dead ends
- **Update agenda:** Note any archival decisions

### Step 6: Plan (Next Steps)

- Propose small, reversible experiments
- **Define tests first** — How will we know it works? What could break?
- Document hypotheses to test
- Set success criteria
- Estimate effort and impact
- **Update agenda:** Draft next cycle plan in agenda

### Step 7: Test (Run Tests)

- Run smoke tests (every cycle)
- Run regression tests (after changes)
- Record results in `EXPERIMENTS.md`
- Roll back if failures detected
- **Update agenda:** Record test results

### Step 8: Finalize & Close

**Mark the cycle complete:**

1. **Complete agenda summary:**
   - Mark all task statuses (completed/blocked/pending)
   - Document any blockers with what's blocking, impact, and resolution needed
   - Write "Next Cycle Plan" section
   - Record completion timestamp and duration

2. **Check for user input needed:**
   - If blockers require user decision/input, send notification (see protocol below)
   - Log in agenda's "Notifications Sent" section

3. **Update STATE.md:**
   - Move completed items to "Completed Recently"
   - Update "Next Steps" from agenda's next cycle plan
   - Update cycle timing

4. **Mark timing complete:** (handled automatically by the runner scripts)

5. **Regenerate dashboard:**
   ```bash
   python3 scripts/update_evergreen_dashboard.py
   ```

---

## User Notification Protocol

### When to Notify

- Blocker requiring user decision
- Missing information that can't be obtained autonomously
- Security concern requiring immediate attention
- Opportunity requiring approval

### Notification Format (WhatsApp)

```
Hi! I'm working on [evergreen name] and need your input:

**Issue:** [Brief description]

**What I need:** [Specific question or request]

**Why it matters:** [Impact of not having this]

[If sensitive: This may involve sensitive info - you can respond via:
- WhatsApp message (if not highly sensitive)
- A file in the workspace
- In person when convenient]

No rush - I'll continue with other tasks until you respond.
```

### After Sending

- Log in agenda's "Notifications Sent" section with timestamp
- Continue with other tasks that don't depend on this

---

## Dashboard Section Ownership

| Section | Owner |
|---------|-------|
| System Status | upstream-architecture |
| Evergreen Summary | All (counts are additive) |
| Services | system-health + upstream-architecture |
| Upstream Architecture card | upstream-architecture |
| Household Memory card | household-memory |
| Prompt-Injection card | prompt-injection |
| System Health card | system-health |
| Investment Suggestions | system-health |
| Recent Activity | All (append only) |

---

## Memory Structure

Each evergreen has a directory under `evergreens/`:

```
evergreens/<name>/
├── STATE.md           # Current state, active experiments, next steps (REQUIRED)
├── TESTS.md           # Smoke, regression, integration, safety tests (REQUIRED)
├── timing.json        # Cycle timing metadata (REQUIRED - auto-generated)
├── agenda-history/    # Archived agendas (REQUIRED - auto-created)
│   └── 2009-01-02.md
├── AGENDA.md          # Current cycle agenda (created at start, archived at end)
├── metrics.json       # Quantitative measurements over time (created as needed)
├── LEARNINGS-ARCHIVE-YYYY-MM.md  # Archived Key Learnings by month (auto-generated)
├── EXPERIMENTS.md     # Experiment backlog with status (created as needed)
├── CONSTRAINTS.md     # Relevant constraints and their sources (created as needed)
├── REFERENCES.md      # Links, docs, and resources (created as needed)
└── HISTORY.md         # Log of completed cycles with dates (created as needed; agenda-history/ is the primary cycle archive)
```

**Required files:** STATE.md, TESTS.md, and timing.json must exist for each evergreen. Other files are created automatically by the AI agent during 8-step cycles as needed.

**Auto-generated files:**
- `LEARNINGS-ARCHIVE-YYYY-MM.md` — Key Learnings older than 14 days are archived here by the pre-session maintenance script.
- `metrics.json` — Quantitative measurements (sizes, counts, rates) that persist across cycles. The agent appends data points; the runner and weekly cycle read them for trend analysis.

**Example completed cycles:** See [`templates/EXAMPLE-COMPLETED-CYCLE.md`](../templates/EXAMPLE-COMPLETED-CYCLE.md) for an example of a completed cycle archive.

> **Note:** Each evergreen's `agenda-history/` directory ships with an example cycle file (e.g., `cycle-2009-01-03.md`). These are reference-only and will be replaced by real archives after the first run. You can safely delete them once actual cycles begin.

### timing.json Schema

Each evergreen's `timing.json` tracks cycle execution. Auto-updated by the runner scripts.

```json
{
  "started_at": "2009-01-03T04:00:00Z",
  "completed_at": "2009-01-03T04:05:00Z",
  "duration_seconds": 300,
  "status": "completed",
  "_comment": "Optional description of this cycle"
}
```

**Valid `status` values:**
| Status | Meaning |
|--------|---------|
| `ready` | Initialized, no cycle run yet |
| `in_progress` | Cycle is currently running |
| `completed` | Full cycle finished successfully |
| `partial` | Cycle ran but ended early (e.g., timeout) |
| `requires_ai` | Scripted executor deferred to AI runner |
| `failed` | Cycle encountered an error |
| `timeout` | Cycle exceeded time limit |
| `error` | Unexpected error during execution |

The post-run validator accepts `completed` or `partial` as success. It also checks that `completed_at` is within the last 30 minutes.

### metrics.json Schema

Evergreens that track quantitative measurements store them in `metrics.json`.
The agent appends a data point each cycle; the runner reads the file for trend
detection. A rolling window of 90 data points per metric keeps the file small.

```json
{
  "backup_size_bytes": [
    {"date": "2009-01-01", "value": 260084182},
    {"date": "2009-01-02", "value": 260411944}
  ],
  "bootstrap_chars": [
    {"date": "2009-01-01", "value": 12500}
  ]
}
```

Metric names should be descriptive and use snake_case. Values are always
numeric (integers or floats). The weekly deep-analysis cycle reads these
files across all evergreens to compute trend projections.

### Daily Briefing Format

Each successful run appends a stub entry to `evergreens/daily-briefing-YYYYMMDD.md`. Later evergreens read this file for cross-cutting context from earlier runs that day.

```markdown
# Daily Briefing - 2009-01-03

## 4:00 AM: upstream-architecture
- Status: ✅ Completed (30 min)
- Key findings: [summary appended by agent]
- Files updated: STATE.md, AGENDA.md, timing.json

## 4:30 AM: system-health
- Status: ✅ Completed (5 min)
- Key findings: [summary appended by agent]
```

Daily briefing files are auto-cleaned after 14 days.

### Weekly Synthesis

Once per week (opt-in), a deeper cross-evergreen analysis runs after the daily
cycles complete. This produces `evergreens/weekly-synthesis-YYYYMMDD.md` with:

- **Cross-Cutting Issues** — findings from different evergreens that describe the same underlying problem
- **Patterns Detected** — recurring themes mined from agenda-history
- **PARA Candidates** — durable facts worth promoting to the PARA knowledge layer
- **Next Steps Triage** — recommendations to keep, escalate, merge, or drop stuck items
- **Trend Projections** — computed from metrics.json data across all evergreens

Daily cycles read the weekly synthesis file during Level-Set (if it exists and
is less than 7 days old), alongside the daily briefing.

A shell-side version (`scripts/weekly-synthesis.py`) uses keyword overlap and
runs without an LLM. The full weekly deep-analysis cycle
(`scripts/evergreen-weekly-cycle.sh`) spawns an AI agent for richer semantic
analysis. The shell-side version serves as a fallback if the LLM cycle is
skipped or fails.

Weekly synthesis files are auto-cleaned after 30 days.

---

## STATE.md Template

The canonical STATE.md template is at [`templates/STATE-TEMPLATE.md`](../templates/STATE-TEMPLATE.md). Copy it when creating a new evergreen:

```bash
cp templates/STATE-TEMPLATE.md evergreens/your-evergreen-name/STATE.md
```

**Required sections:** Status, Cycle Timing, Current Focus, Key Learnings, Blocking Issues, Completed Recently, Next Steps.

**Optional sections (add as needed):** Active Experiments, System Information, Research Topics.

**Important:** The "Completed Recently" section feeds the dashboard's "Recent Activity" display. Keep 3–5 items and remove older ones.

---

## Memory Maintenance

Evergreen documents must be kept lean to remain useful. Apply **progressive summarization**:

### Automatic State Maintenance

Before each daily cycle, the runner calls `preflight-state-maintenance.py` which:

1. **Key Learnings compaction** — Entries older than 14 days are moved to monthly
   archive files (`LEARNINGS-ARCHIVE-YYYY-MM.md`). Only recent learnings stay in
   STATE.md, keeping context lean for the agent.

2. **Stale item detection** — Next Steps items that appear in 3+ consecutive
   agenda-history archives are annotated with `⚠️ STALE (N cycles)`. This
   surfaces stuck work so the agent can escalate or drop it.

These operations are shell-side (no LLM required) and run before the agent
session starts.

### Compaction Rules

| Document | Trigger | Action |
|----------|---------|--------|
| STATE.md | > 15 active items or > 5 completed items | Archive completed items |
| HISTORY.md | > 30 days of entries | Compact older entries |
| EXPERIMENTS.md | > 20 experiments | Archive completed/abandoned |

### Compaction Process

1. **Identify candidates** — Items older than 7 days or beyond thresholds
2. **Extract details** — Full verbose entry with all context
3. **Archive to searchable storage:**
   - Daily file: `evergreens/<evergreen-name>/agenda-history/2009-01-02.md`
   - Or Qdrant: Use semantic memory for key learnings
4. **Replace with summary** — Single bullet point with key outcome and link to archive
5. **Prune dead ends** — Failed experiments with no learnings can be deleted

### Summary Format

After archiving, replace verbose entries with:

```markdown
- [2009-01-02] Completed X, result Y → [details](agenda-history/2009-01-02.md)
```

---

## Dashboard Implementation

Dashboard is a single HTML file regenerated each cycle:

**Location:** `evergreens/DASHBOARD.html`

**Features:**
- System status summary
- Evergreen health cards
- Recent activity log
- Investment suggestions (optional)

**Regeneration:** Called at end of each evergreen cycle via:
```bash
python3 scripts/update_evergreen_dashboard.py
```

---

## Agenda Pattern

**Why agendas?** Each cycle should have a clear plan, tracked in real-time.

**Implementation:**

1. **Start of cycle:** Create `AGENDA.md` from template
2. **During cycle:** Update sections as you work
3. **End of cycle:** Finalize with results, archive, delete current `AGENDA.md`

**Template:** See `config/agenda-template.md`

---

## Fault Tolerance

Evergreens should be robust:

- **Sequential execution:** One at a time, no resource contention
- **Error isolation:** One failure doesn't block others
- **Logging:** All errors captured with timestamps
- **Notifications:** User alerted if failures occur
- **Self-healing:** Partial runs recoverable on next cycle

---

## Best Practices

### What Works

- **Small experiments** — Easy to roll back, fast to learn
- **Clear tests** — Define success criteria before running
- **Daily cadence** — Fresh data, consistent improvement
- **Living documents** — Archive aggressively, keep STATE.md lean
- **Constraint-aware** — Know your system limits

### Common Pitfalls

- ❌ **Too many active experiments** — Focus on 1-3 at a time
- ❌ **Vague success criteria** — Be specific about what "done" looks like
- ❌ **Skipping tests** — Always run smoke tests, even if nothing changed
- ❌ **Hoarding memory** — Archive aggressively, summarize ruthlessly
- ❌ **Ignoring constraints** — Respect upstream architecture decisions

---

## Getting Started

1. **Pick one evergreen** to start (recommend: `system-health` - simplest)
2. **Run your first cycle** manually: `./scripts/evergreen-ai-runner.sh system-health`
3. **Follow the 8 steps** as documented above
4. **Schedule it** once manual runs work (see `docs/SCHEDULING.md`)
5. **Add more evergreens** one at a time

**First cycle checklist:**
- [ ] Create directory structure
- [ ] Initialize STATE.md with template
- [ ] Run cycle manually
- [ ] Verify dashboard updates
- [ ] Schedule in crontab

---

## Upstream References

This framework builds on concepts from:
- Andy Matuschak's [evergreen notes](https://notes.andymatuschak.org/Evergreen_notes)
- OpenClaw's sub-agent architecture
- Various DevOps continuous improvement frameworks

---

**Continuous improvement, automated. 🌲**
