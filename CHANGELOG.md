# Changelog

All notable changes to the Evergreen Toolkit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

**For implementation guidance:** See [QUICKSTART.md](QUICKSTART.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

**For questions:** Open an issue on the project repository

---

## 1.1.0 — 2026-04-01

### Fixed
- **Exec config must be per-agent, not top-level** — The embedded agent runtime (used
  by the AI runner for scheduled cycles) resolves exec policy from the per-agent config
  (`agents.list[].tools.exec`), not from the top-level `tools.exec`. A top-level
  setting only applies to interactive CLI sessions. All documentation and the
  preflight check now correctly instruct users to set `tools.exec.security: "full"`
  and `tools.exec.ask: "off"` on each agent entry in `agents.list`, not at the top
  level. Without this, the interactive agent works but scheduled evergreen cycles hang
  waiting for approval that never arrives.

### Added
- **OpenClaw exec tool configuration requirement documented** — OpenClaw v2026.3.31+
  enables exec approvals by default, which blocks autonomous shell command execution.
  Documented the required per-agent `agents.list[].tools.exec` configuration in
  QUICKSTART.md (Step 7), SETUP-GUIDE.md, and AGENT-ONBOARDING.md with justification
  and security alternatives.
- **Pre-flight check: per-agent exec config validation** — `preflight-check.py` now
  reads `~/.openclaw/openclaw.json` and verifies that each agent in `agents.list` has
  `tools.exec.security` set to `"full"` and `tools.exec.ask` set to `"off"`, catching
  misconfiguration before first run.
- **Troubleshooting: "Commands Require Approval" entry** — New troubleshooting section
  covering symptoms, root cause (per-agent vs top-level config), and fix for the exec
  approval gate introduced in OpenClaw v2026.3.31.

---

## 1.0.1 — 2026-03-31

### Fixed
- **AI runner: JSON parsing failure when OpenClaw emits config warnings** — The agent
  invocation merged stderr into stdout (`2>&1`), causing `json.load()` to fail when
  OpenClaw wrote config warnings (e.g. duplicate plugin, version mismatch) before the
  JSON result. Separated stderr into a temp file and log it independently. This
  affected all evergreen runs, silently losing model/duration/stopReason diagnostics.
- **AI runner: robust fallback parser for mixed text+JSON output** — If stderr
  separation is insufficient (e.g. future OpenClaw versions change stream behavior),
  the inline Python parser now falls back to `json.JSONDecoder.raw_decode()` to
  extract JSON from mixed output, instead of failing silently.

### Added
- **AI runner: stopReason detection and logging** — After parsing agent output, the
  runner now checks `stopReason` and logs a warning when the agent session ended
  mid-tool-call (`toolUse`) or with a model error (`error`). Previously these
  conditions were masked by the JSON parse failure and reported generically as
  "Post-run validation failed".

---

## 1.0.0 — 2026-03-27 [Initial Release]

First public release of the Evergreen Toolkit.

### Core Framework
- Four evergreen programs: upstream-architecture, system-health, prompt-injection, household-memory
- AI runner (`evergreen-ai-runner.sh`) with flock locking, pre-run backup, post-run validation, automatic rollback, and session reset before each run
- Direct executor (`run-single-evergreen.py`) as alternative to AI runner
- Cross-evergreen daily briefing for context sharing between runs
- Pre-session state maintenance: automatic Key Learnings compaction and stale Next Steps detection
- Weekly deep-analysis cycle with cross-evergreen synthesis and trend projection
- Final check script (`evergreen-final-check.py`) with notification integration
- Dashboard generator (`update_evergreen_dashboard.py`)
- Seed script (`seed-evergreens.py`) for upstream monitoring initialization
- Deploy script (`deploy.sh`) with workspace setup, crontab generation, and post-deploy verification
- Customization validator (`validate-customization.py`) to verify placeholder replacement

### Memory System
- 7-layer memory architecture: Redis buffer → True Recall curation + Jarvis backup → Qdrant storage → PARA durable knowledge → AGENTS.md rules → MEMORY.md routing (see MEMORY-SYSTEM.md)
- Multi-user household support with theory of mind and per-user memory isolation
- Heartbeat-driven memory capture (`save_current_session_memory.py`)
- Hybrid search combining keyword + vector search (`hybrid_search.py`)
- Per-user curator prompts for personalized memory curation

### Tools & Documentation
- Markdown viewer (`tools/markdown-viewer.js`) for serving formatted docs
- Comprehensive documentation: QUICKSTART, SETUP-GUIDE, AGENT-ONBOARDING, ARCHITECTURE, SCHEDULING, TROUBLESHOOTING
- Sample configs: crontab, memory_env, openclaw-plugins, heartbeat template

