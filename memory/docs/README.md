# Memory Documentation

This directory is reserved for generated or supplementary memory documentation (e.g., auto-generated reports from memory curation, analysis outputs from the household-memory evergreen). It starts empty — the household-memory evergreen may populate it over time.

## Memory Documentation Index

All primary memory documentation lives in the parent `memory/` directory:

| File | Purpose |
|------|---------|
| [README.md](../README.md) | Architecture overview, 7-layer memory system design, and script reference |
| [settings.md](../settings.md) | Configuration reference — all environment variables and defaults |
| [MULTI-USER-GUIDE.md](../MULTI-USER-GUIDE.md) | Multi-user household setup, per-user directories, and curator prompts |
| [SKILL.md](../SKILL.md) | Memory system skill definition for agent consumption |
| [USERS-README.md](../USERS-README.md) | Per-user directory structure and setup |
| [IDENTITY-VERIFICATION.md](../IDENTITY-VERIFICATION.md) | Identity verification procedures (stub — developed by evergreen cycles) |
| [APPROVED-CONTACTS.json](../APPROVED-CONTACTS.json) | Approved external contacts list |
| [curator_prompts/](../curator_prompts/) | Curator prompts — `base.md` (loaded for all users) + per-user overrides |
| [UPSTREAM-CREDITS.md](../UPSTREAM-CREDITS.md) | Attribution for upstream OpenClaw memory system |
| [OPENCLAW-FORK-CHANGES.md](../OPENCLAW-FORK-CHANGES.md) | Changes needed in an OpenClaw gateway fork for end-to-end multi-user memory isolation |

## Related Documentation

- [docs/MEMORY-INTEGRATION.md](../../docs/MEMORY-INTEGRATION.md) — How the memory system integrates with evergreen programs
- [docs/MEMORY-FIRST-STRATEGY.md](../../docs/MEMORY-FIRST-STRATEGY.md) — Memory-first operational strategy
- [docs/HEARTBEAT-MEMORY-INTEGRATION.md](../../docs/HEARTBEAT-MEMORY-INTEGRATION.md) — Heartbeat and memory integration patterns
