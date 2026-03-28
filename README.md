# 🌲 Evergreen Toolkit

> **🤖 Implementing Agent?** Read [AGENT-ONBOARDING.md](AGENT-ONBOARDING.md) for the overview, then follow [QUICKSTART.md](QUICKSTART.md) step-by-step. That's it. Alice, Bob, and Eve are example personas — you'll replace them during setup.

**Your household AI agent should get better every day, not drift into obsolescence.**

The Evergreen Toolkit is a self-improving automation framework for [OpenClaw](https://docs.openclaw.ai) agents serving **multi-user households**. OpenClaw is an open-source AI agent platform (a programmable AI assistant runtime) — this toolkit extends it with continuous self-improvement capabilities. It provides four evergreen programs that run on a schedule, continuously improving your agent's architecture, security, memory, and system health.

### 🏠 Built for Households, Not Just Individuals

Unlike generic AI assistants, this toolkit is designed for **family environments** where the AI interacts with multiple people daily:

- **Eve** (AI agent — the assistant itself, example name — replace with your agent's name)
- **Alice** (non-technical, uses WhatsApp, loves her grandkids)
- **Bob** (technical, Bitcoin expert, provides IT support)
- **Other family members** (each with their own preferences, knowledge, relationships)

> *Alice, Bob, and Eve are example personas used throughout this documentation. See [QUICKSTART.md](QUICKSTART.md#9-customize-example-names) for how to replace them with your household's actual names.*

The AI maintains **separate memories for each person** while understanding relationships between them—enabling true **theory of mind** and personalized interactions.

---

> **Document map:**
> ```
> For Implementing Agents:
>   AGENT-ONBOARDING.md  (overview + checklist)
>        ↓
>   QUICKSTART.md        (step-by-step setup)
>        ↓
>   Done! (refer to docs/* as needed)
> ```
> [QUICKSTART.md](QUICKSTART.md) is the primary setup path. [ARCHITECTURE.md](ARCHITECTURE.md) covers the full technical design. See [GLOSSARY.md](GLOSSARY.md) for key terminology. [docs/SETUP-GUIDE.md](docs/SETUP-GUIDE.md) covers the same steps as QUICKSTART in more detail — reference it if you need deeper context on any step, but do not follow both guides sequentially. Everything else in `docs/` is reference material — consult as needed.

---

## 🚀 Quick Start

```bash
git clone https://github.com/paulscode/evergreen-toolkit.git ~/evergreen-toolkit
cd ~/evergreen-toolkit
bash scripts/setup.sh
bash scripts/deploy.sh --workspace ~/.openclaw/workspace
python3 scripts/preflight-check.py
```

This gets the infrastructure in place. **You still need to configure `.memory_env` and initialize memory collections** — see [QUICKSTART.md](QUICKSTART.md) for the full 11-step setup including memory configuration, scheduling, and name customization.

---

### What You'll Need to Customize

- **Credentials & environment:** `.memory_env` (copy from `config/memory_env.example` — Redis, Qdrant, Ollama connection details)
- **Personas & users:** Replace placeholder names/contacts in memory files, STATE.md files, and curator prompts
- **Cron schedule:** Set up `config/crontab.sample` with real paths and timing for your deployment
- **OpenClaw plugins:** Copy and edit `config/openclaw-plugins.example.json` with your agent's collection names

### Placeholder Convention

- `<angle-bracket>` values (e.g., `<user1>`, `<agent>`) **must** be replaced with your actual values
- `Alice`, `Bob`, `Mom`, `Dad`, `Smith`, `Acme Bookkeeping` are example personas — replace with your household's actual users and context
- `Eve` is the example AI agent name — replace with your agent's name (e.g., in collection names, script references)
- Example dates from 2008–2009 in STATE.md files are stubs — they will be overwritten on first run
- All path examples use workspace-relative paths (e.g., `scripts/`, `memory/`) — after running `deploy.sh`, files live in your OpenClaw workspace
- Run `python3 scripts/validate-customization.py` to verify all placeholders have been replaced

---

## 📋 What's Included

### Four Evergreen Programs

Each evergreen runs automatically, focusing on continuous improvement:

| Evergreen | Purpose | Runtime |
|-----------|---------|---------|
| 🌱 **upstream-architecture** | Monitor dependencies, releases, breaking changes | ~30 min |
| 🌱 **system-health** | System resources, backups, cron jobs, reliability | ~5 min |
| 🌱 **prompt-injection** | Security audits, credential checks, supply chain vetting | ~10 min |
| 🌱 **household-memory** | Memory architecture, capture patterns, curation experiments | ~30 min |

### 🧠 Memory System (Multi-User Household Support)

Complete **7-layer memory architecture** with **theory of mind** for households. See [`MEMORY-SYSTEM.md`](MEMORY-SYSTEM.md) for the full technical overview.

Built on Jarvis Memory (raw conversation backup, upstream from SpeedyFoxAI), True Recall (AI curation, upstream from SpeedyFoxAI), and the PARA durable knowledge layer (adapted from Lucas Synnott's 5-Layer Memory Stack). Data flows: Conversation → Redis → True Recall (gems) & Jarvis (raw backup) → weekly PARA promotion (durable facts). See [`memory/README.md`](memory/README.md) for the naming glossary and [GLOSSARY.md](GLOSSARY.md) for definitions.

- **Redis buffer** — fast capture, sub-second writes (24-48h TTL)
- **Qdrant vector store** — semantic search across raw archive and curated gems
- **Daily markdown files** — human-readable per-user logs
- **True Recall curation** — AI extracts high-salience gems from conversations
- **PARA durable knowledge** — structured facts per user, canonical source of truth (`memory/para/<user>/`)
- **👨‍👩‍👧‍👦 Multi-user isolation** — separate memories per person (Alice, Bob, etc.)
- **🧠 Theory of mind** — AI understands relationships, different knowledge per person
- **🔒 Privacy boundaries** — personal memories stay private unless explicitly shared

See [`memory/MULTI-USER-GUIDE.md`](memory/MULTI-USER-GUIDE.md) for complete multi-user setup.

### 🛠️ Tools & Scripts

#### Core Evergreen Scripts

- `evergreen-ai-runner.sh` - **AI runner** — spawns `openclaw agent` session with locking (cron-facing, recommended)
- `run-single-evergreen.py` - Run a single evergreen cycle (direct executor, alternative to AI runner)
- `evergreen_ai_executor.py` - **AI-orchestrated cycle executor** (executes real research)
- `evergreen-scripted-executor.py` - Fallback executor (mechanical checks only, no AI; only supports `system-health` and `prompt-injection`)
- `evergreen-final-check.py` - Post-cycle verification and alerting
- `update_evergreen_dashboard.py` - Generate status dashboard HTML

#### Memory Scripts

Complete memory system with ~37 scripts for capture, search, curation, and backup in `memory/scripts/`.

**Key daily scripts:** `save_mem.py`, `save_current_session_memory.py`, `cron_backup.py`, `curate_memories.py`, `search_memories.py`, `hybrid_search.py`

**PARA promotion pipeline:** `promote_to_para.py` (weekly gem → fact promotion), `seed_para.py` (bootstrap PARA), `detect_stale_para.py` (staleness & contradiction audit), `archive_daily_notes.py` (daily note lifecycle)

See [`memory/README.md`](memory/README.md) for the full categorized list and usage guide.

#### Other Tools

- `health_check.sh` - Quick system health diagnostic (Redis, Qdrant, disk, memory, backups)
- `markdown-viewer.js` - Serve formatted .md files as web pages (port 3000)
- `fix-markdown-links.js` - Auto-convert `file://` .md links to viewer URLs
- `setup-markdown-viewer.sh` - Install markdown viewer as systemd service

**Architecture (AI Runner — Recommended):**
```
Cron (4:00-5:30 AM) → evergreen-ai-runner.sh → openclaw agent (full research + analysis)
Cron (6:00 AM) → evergreen-final-check.py → Verify all ran, generate alerts if issues
```

- Each evergreen spawns its own AI agent session with `flock` locking
- Agent performs cognitive work (research, analysis, planning, synthesis)
- Immediate feedback if something fails
- Per-evergreen daily log files

**Alternative (Direct Executor):**
```
Cron (4:00-5:30 AM) → run-single-evergreen.py → AI executes real research (direct)
```

**Full Documentation:**
- `docs/OPERATIONAL-GUIDE.md` - Agent autonomy, operational patterns
- `docs/AUTONOMY-GUIDELINES.md` - Agent autonomy framework
- `docs/MEMORY-INTEGRATION.md` - Multi-user memory system integration

### 🎯 Agent Autonomy

**Auto-Apply (No Permission Needed):**
- File permission fixes (`chmod 600/700`)
- Adding missing directories
- Updating timestamps, versions
- Restarting configured services
- Documentation fixes
- Temp file cleanup

**Ask First:**
- Cron/config changes
- Network/firewall modifications
- Package installation
- Data deletion
- External communications

**Rule:** If undoable in <30 seconds, auto-apply. See `docs/OPERATIONAL-GUIDE.md` for details.

### Dashboard "Recent Activity"

The dashboard shows rolling "Recent Activity" pulled from each evergreen's `STATE.md`:

```markdown
## Completed Recently
- [2009-01-03] AI orchestration implemented for evergreen cycles
- [2008-12-31] Voice-call extension merged with upstream
- [2008-12-28] Security vulnerabilities V001-V005 addressed
```

*(Dates shown are example stubs — will reflect real dates after first run)*

**Each evergreen maintains its own section:**
- Add today's accomplishment after each cycle
- Keep 3-5 most recent items (remove oldest when full)
- Dashboard aggregates all 4 evergreens automatically

See `docs/OPERATIONAL-GUIDE.md` for details and `templates/STATE-TEMPLATE.md` for format.

---

## 📚 Documentation

### Getting Started

| Document | Purpose |
|----------|---------|
| [**QUICKSTART.md**](QUICKSTART.md) | Primary setup guide (step-by-step) |
| [**AGENT-ONBOARDING.md**](AGENT-ONBOARDING.md) | Quick-reference for the implementing AI agent |
| [**docs/README.md**](docs/README.md) | Documentation index and reading guide |
| [**docs/SETUP-GUIDE.md**](docs/SETUP-GUIDE.md) | Complete installation and configuration |
| [**docs/SCHEDULING.md**](docs/SCHEDULING.md) | Timezone-aware scheduling (with conversion tables) |
| [**docs/TROUBLESHOOTING.md**](docs/TROUBLESHOOTING.md) | Common issues and solutions |

### Multi-User Household Setup

| Document | Purpose |
|----------|---------|
| [**memory/MULTI-USER-GUIDE.md**](memory/MULTI-USER-GUIDE.md) | Complete guide to multi-user memory with theory of mind |
| [**memory/OPENCLAW-FORK-CHANGES.md**](memory/OPENCLAW-FORK-CHANGES.md) | TypeScript gateway changes for end-to-end user isolation |
| [**memory/settings.md**](memory/settings.md) | Configure household members and user detection |
| [**memory/curator_prompts/**](memory/curator_prompts/) | User-specific memory curation prompts |

### Technical Deep Dive

| Document | Purpose |
|----------|---------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | System architecture, data flow, component details |
| [**MEMORY-SYSTEM.md**](MEMORY-SYSTEM.md) | 7-layer memory architecture and data flow |
| [**CONTRIBUTING.md**](CONTRIBUTING.md) | How to contribute (for developers and AI agents) |
| [**memory/README.md**](memory/README.md) | Memory architecture deep dive |
| [**memory/para/README.md**](memory/para/README.md) | PARA layer schema, rules, contradiction resolution |
| [**evergreens/EVERGREENS.md**](evergreens/EVERGREENS.md) | Evergreen framework and 8-step cycle |

### Advanced Topics

| Document | Purpose |
|----------|---------|  
| [**docs/MEMORY-FIRST-STRATEGY.md**](docs/MEMORY-FIRST-STRATEGY.md) | Agent behavioral strategy: always search memory first |
| [**docs/PLUGIN-RECOMMENDATIONS.md**](docs/PLUGIN-RECOMMENDATIONS.md) | Optional session-layer plugins (Gigabrain, LCM, OpenStinger) |
## 📖 Glossary

See [GLOSSARY.md](GLOSSARY.md) for definitions of key terms (OpenClaw, Evergreen, Jarvis Memory, True Recall, Gem, Heartbeat, etc.).

---

## ⏰ Default Schedule

All times shown in local time (adjust for your timezone - see [SCHEDULING.md](docs/SCHEDULING.md)). For exact cron entries, see [`config/crontab.sample`](config/crontab.sample) (the canonical source).

### Recommended Schedule

| Time | Action | Notes |
|------|--------|-------|
| Every 5 min | **Session capture** (`cron_capture.py`, per user) | Feeds new transcript messages into Redis |
| Sunday 2:00 AM | **PARA promotion** (weekly, per user) | Promotes gems from prior days into durable knowledge |
| 2:30 AM | **True Recall curation** (per user) | Reads Redis buffer, extracts gems, does NOT clear |
| 3:00 AM | **Jarvis backup** (per user) | Reads Redis, backs up, THEN clears Redis |
| 3:30 AM | Full system backup | After memory backup completes |
| 4:00 AM | **upstream-architecture** runs via AI runner (~30 min) | Research-heavy |
| 4:30 AM | **system-health** runs via AI runner (~5 min) | |
| 5:00 AM | **prompt-injection** runs via AI runner (~10 min) | |
| 5:30 AM | **household-memory** runs via AI runner (~30 min) | Analyzes fresh memory state |
| 6:00 AM | **Final check** verifies all succeeded | Alerts if issues ✅ |
| Sunday 6:30 AM | **Weekly synthesis** (opt-in) | Cross-evergreen insights |

**Daily maintenance window:** ~3.5 hours (2:30 AM - 6:00 AM)  
**Actual daily work:** ~90 minutes (memory + 4 evergreens + final check)  
**Weekly:** PARA promotion runs Sundays at 2:00 AM (before True Recall)

**Critical:** Memory cron jobs (2:30-3:00 AM) MUST run before evergreens. True Recall must run before Jarvis backup (which clears Redis). PARA promotion must run before True Recall on its weekly schedule. See `config/crontab.sample` for correct ordering.

---

## 🔧 How It Works

### The 8-Step Evergreen Cycle

Each evergreen follows this process every cycle:

1. **Level-Set** - Review STATE.md, check constraints, assess system
2. **Complete** - Finish incomplete tasks from last cycle
3. **Research** - Web search for new developments, upstream releases
4. **Analyze** - Synthesize findings, identify gaps
5. **Housekeep** - Archive old data, compact documents, update Qdrant
6. **Plan** - Propose next experiments with success criteria
7. **Test** - Run smoke/regression tests, record results
8. **Finalize** - Mark complete, update STATE.md and dashboard

### Fault Tolerance

- **Pre-run backup** — STATE.md, AGENDA.md, and timing.json backed up before each run
- **Post-run validation** — Output files checked for existence, valid content, and recent timestamps
- **Automatic rollback** — Files restored from backup if agent fails or validation fails
- **Failure notification** — Alert sent via your configured messaging channel (set `EVERGREEN_NOTIFY_TARGET`)
- **Sequential execution** — One evergreen at a time, no resource contention
- **Cross-evergreen briefing** — Each run appends findings to a daily briefing file; later evergreens read it for context
- **Error isolation** — One failure doesn't block others
- **Automatic logging** — All errors captured with timestamps

---

## 🎯 Use Cases

### During System Stabilization (Recommended)

Run **all 4 evergreens nightly** for:
- Rapid security vulnerability discovery
- Fast memory architecture iteration
- Quick feedback on experiments
- Comprehensive monitoring

### After Stabilization

Switch to **rotation schedule** (one per night, 4-day cycle) for:
- Lower resource usage (~30 min/night)
- Still comprehensive weekly coverage
- Mature systems with fewer changes

---

## ⚙️ Configuration

### Crontab Setup

```bash
# Copy example
cp config/crontab.sample /tmp/my-crontab

# Edit for your timezone and user IDs
nano /tmp/my-crontab

# Install
crontab /tmp/my-crontab
```

See [config/crontab.sample](config/crontab.sample) for complete template.

> **Note:** If you used `deploy.sh`, a pre-filled `config/crontab.generated` was created in your workspace with paths already substituted. Review it and install with `crontab config/crontab.generated`. See [QUICKSTART.md](QUICKSTART.md) Step 10 for details.

### Memory Configuration

```bash
# Edit .memory_env in your workspace (deployed from config/memory_env.example)
nano ~/.openclaw/workspace/.memory_env

# Set these values:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# QDRANT_URL=http://localhost:6333
# QDRANT_COLLECTION=<agent>-memories
# DEFAULT_USER_ID=your-user-id
```

### OpenClaw Integration

The recommended AI runner mode requires **OpenClaw** installed and on PATH. The runner spawns a full agent session via `openclaw agent` for each evergreen cycle. The direct executor mode (`run-single-evergreen.py`) runs AI orchestration via Python directly — it still performs research and analysis but doesn't use an `openclaw agent` session.

See `config/crontab.sample` for the full schedule template and [`docs/SCHEDULING.md`](docs/SCHEDULING.md) for timezone adjustment.

---

## 📊 Example Output

### Dashboard View

```html
<!-- evergreens/DASHBOARD.html -->
<div class="evergreen-card">
  <h3>🌱 Upstream Architecture</h3>
  <p>Status: 🟢 Good</p>
  <p>Last Cycle: 2009-01-01 06:00 AM</p>
  <p>Duration: 31 min</p>
</div>
```

### STATE.md Update

```markdown
## Status
- Overall Health: 🟢 Good
- Last Cycle: 2009-01-01T06:00:00Z
- Duration: ~31 min

## Completed Recently
- [2009-01-01] Monitored Ollama releases, no breaking changes
- [2009-01-01] Checked OpenClaw upstream, v2009.1.2 available
- [2009-01-01] Verified remote GPU connectivity

## Next Steps
1. Investigate Ollama v0.6.0 new_features
2. Test OpenClaw beta channel
3. Benchmark new embedding models
```

---

## 🤝 Community & Credits

This toolkit is open-source and community-maintained.

- **License:** MIT (permissive, commercial use OK)
- **Repository:** https://github.com/paulscode/evergreen-toolkit
- **Discord:** https://discord.com/invite/clawd (#skills channel)
- **ClawHub:** Submit to https://clawhub.com for official listing

### 🙏 Special Thanks

**Jarvis Memory + True Recall System** designed and implemented by **SpeedyFoxAI**.

This toolkit builds upon SpeedyFoxAI's groundbreaking work on the OpenClaw True Recall base system. His memory architecture (Redis buffer → parallel processing via True Recall curation + Jarvis raw backup → Qdrant durable storage) forms the foundation of our household-memory evergreen.

**Upstream Repository:** Watch https://gitlab.com/mdkrush/openclaw-true-recall-base for active development and improvements to adopt.

**5-Layer Memory Architecture & PARA Concepts** by **Lucas Synnott** ([appliedleverage.io](https://appliedleverage.io)).

The PARA durable knowledge layer, MEMORY.md routing philosophy, and layer-separation principles are adapted from Lucas's 5-Layer Memory Stack for OpenClaw. His insights on keeping each memory layer focused on a single job and treating file-based facts as canonical truth shaped the 7-layer architecture used here. The PARA method itself originates from Tiago Forte.

See `memory/UPSTREAM-CREDITS.md` for full attribution details.

### Contributing

Contributions welcome! Areas for improvement:
- Additional evergreen types (performance, cost optimization)
- Memory layer enhancements (PARA contradiction resolution, semantic tagging)
- Better visualizations (dashboard improvements, memory state graphs)
- Internationalization
- Unit tests and CI/CD

---

## 📈 Metrics

After installation, track your agent's improvement:

- **Security:** Vulnerabilities found and fixed
- **Memory:** Facts captured, Qdrant items, retrieval speed
- **Reliability:** Uptime, backup success rate, cron job health
- **Architecture:** Experiments run, changes adopted, tech debt reduced

---

## 🔒 Security Notes

This toolkit has been **sanitized for public distribution**:

✅ No personal information  
✅ No credentials or API keys  
✅ Phone numbers and email addresses are example/placeholder values only  
✅ All paths are relative or generic  
✅ User IDs are placeholders (`<user1>`, `<user2>`)

**Before installing:**
- Review all config files
- Replace placeholders with your values
- Set appropriate file permissions
- Vet any additional skills before installing (malicious skills have been found on ClawHub)

See [evergreens/prompt-injection/CREDENTIAL-AUDIT.md](evergreens/prompt-injection/CREDENTIAL-AUDIT.md) for security best practices.

---

## 💡 Philosophy

> "Your agent should compound in capability, not technical debt."

The evergreen approach ensures:
- **Continuous improvement** - Small, reversible experiments daily
- **Constraint-aware** - Work within system limits
- **Evidence-based** - Test before adopting changes
- **Self-documenting** - Living memory captures all decisions
- **Community-driven** - Share findings, learn from others

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

**Short version:** Use it, modify it, share it. Just keep the copyright notice.

---

## 🎯 Success Criteria

Your implementation is successful when:

- ✅ Evergreens run automatically on schedule
- ✅ STATE.md files stay current with real work
- ✅ Dashboard shows accurate status
- ✅ Memory system captures conversation context
- ✅ User receives notifications when needed
- ✅ System handles errors gracefully
- ✅ You can explain the architecture to another agent
- ✅ You can add a new evergreen type independently

---

## Before Production: Replace Example Names

This toolkit uses example names (Alice, Bob, Eve) throughout. Before deploying, replace them with your household's actual names and user IDs.

**Important:** Review each instance before replacing — some contain specific claims (relationships, preferences) that may not apply to your household. Don't blindly search-and-replace.

**Full instructions with detailed examples:** See [docs/NAME-CUSTOMIZATION.md](docs/NAME-CUSTOMIZATION.md)

**Key files to customize:**
- `memory/MULTI-USER-GUIDE.md` - User profiles, phone numbers, user IDs
- `memory/OPENCLAW-FORK-CHANGES.md` - Gateway TypeScript changes for user isolation
- `memory/curator_prompts/base.md` - AI curator prompt (speaker labels, gem extraction rules)
- `docs/MEMORY-INTEGRATION.md` - User mapping table (names + IDs)
- `config/crontab.sample` - Paths, user IDs

> **Note:** If using voice calls, also configure `~/.openclaw/user-phone-mapping.json` (part of your OpenClaw installation, not this toolkit).

---

**Make your agent better every single night. 🌲**

*Developed for multi-user household AI assistants. Made available to the OpenClaw community.*
