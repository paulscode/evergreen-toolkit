# Changelog

All notable changes to the Evergreen Toolkit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

**For implementation guidance:** See [QUICKSTART.md](QUICKSTART.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

**For questions:** Open an issue on the project repository

---

## 1.2.1

### Fixed
- **Lean workspace: use hard copies instead of symlinks for bootstrap files** —
  OpenClaw's bootstrap loader does not follow symlinks when reading workspace `.md`
  files for system prompt injection. Symlinked bootstrap files (SOUL.md, TOOLS.md,
  IDENTITY.md, USER.md, BOOTSTRAP.md, MEMORY.md) are treated as `missing` with zero
  content, causing the agent to run without critical context. Updated documentation to
  use hard copies for bootstrap `.md` files and symlinks only for directories (which
  work correctly for exec/read/write tool operations). Replaced the "Lean Workspace
  Requires Manual Symlink Maintenance" section with a sync script and crontab entry
  for keeping hard copies up to date.

- **Exec tool blocks long heredoc scripts despite `ask: "off"`** — OpenClaw's exec
  tool flags long inline heredoc scripts (e.g. multi-hundred-line Python blocks) as
  "potentially obfuscated" and requires manual approval, even with `security: "full"`
  and `ask: "off"`. During unattended cron runs this causes a silent failure: the
  agent completes its session but the blocked write never executes, so validation
  fails and the run is rolled back. Added a "File-writing strategy" section to the
  runner's task prompt instructing agents to write files individually rather than
  combining them into a single large script. Documented this gotcha in the exec
  approval troubleshooting section.

### Added
- **Fallback model server pre-flight check** — The AI runner now checks reachability
  of the fallback model server (defaults to `http://127.0.0.1:11434`, configurable via
  `OLLAMA_URL`) before each run. Logs a warning if unreachable so operators have
  visibility into degraded fallback coverage without blocking the run.

---

## 1.2.0

### Added
- **`AGENT_WORKSPACE` env var support in AI runner** — The runner now supports an
  `AGENT_WORKSPACE` environment variable (via `OPENCLAW_AGENT_WORKSPACE`) for
  pre-flight context estimation. When using a lean workspace for the evergreen agent
  (a directory with symlinks to essential files only), set this variable so the
  runner estimates token usage against the actual bootstrap files the agent sees,
  not the full workspace. Falls back to `OPENCLAW_WORKSPACE` if unset.

- **Context Overflow troubleshooting section** — New section in TROUBLESHOOTING.md
  covering: symptoms, diagnosis, contributing factors (large bootstrap, verbose tool
  output, retry mechanism, compaction limitations), and solutions (lean workspace
  pattern, output budgeting, pre-flight estimation).

- **OpenClaw Configuration Gotchas section** — New section in TROUBLESHOOTING.md
  documenting known OpenClaw behaviors that can cause subtle failures:
  - `models.json` silent re-corruption after gateway restarts or version mismatches
  - `agents.list` requiring array index notation (not name-based)
  - Per-agent bootstrap overrides not supported by the schema
  - Compaction structurally blocked for single-turn, tool-heavy sessions

- **Lean workspace maintenance guidance** — Documents the symlink maintenance
  requirement when using a separate lean workspace for evergreen agents.

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

