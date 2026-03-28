# Changelog

All notable changes to the Evergreen Toolkit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

**For implementation guidance:** See [QUICKSTART.md](QUICKSTART.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

**For questions:** Open an issue on the project repository

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

