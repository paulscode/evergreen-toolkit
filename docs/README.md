# Documentation Index

Prioritized reading guide for the `docs/` directory.

> **Which doc should I read?**
> - Setting up for the first time? → [SETUP-GUIDE.md](SETUP-GUIDE.md)
> - Configuring scheduling? → [SCHEDULING.md](SCHEDULING.md)
> - Memory system not working? → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
> - Understanding the architecture? → [../ARCHITECTURE.md](../ARCHITECTURE.md)

## Recommended Reading Order (for implementing agents)

> You should have already read [../AGENT-ONBOARDING.md](../AGENT-ONBOARDING.md) before arriving here.

1. [SETUP-GUIDE.md](SETUP-GUIDE.md) — Detailed setup reference (or use [../QUICKSTART.md](../QUICKSTART.md) for the condensed version)
2. [SCHEDULING.md](SCHEDULING.md) — Before installing crontab
3. [NAME-CUSTOMIZATION.md](NAME-CUSTOMIZATION.md) — Before production use
4. Everything else: consult as needed

## Essential (Read First)

| File | Purpose |
|---|---|
| [SETUP-GUIDE.md](SETUP-GUIDE.md) | **Detailed setup reference** — full installation, configuration, and a condensed quick-reference checklist. See [../QUICKSTART.md](../QUICKSTART.md) for the primary condensed guide. |
| [SCHEDULING.md](SCHEDULING.md) | Cron schedule configuration and timezone handling |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and fixes |
| [../MEMORY-SYSTEM.md](../MEMORY-SYSTEM.md) | Standalone 7-layer memory architecture overview |

## Memory System

| File | Purpose |
|---|---|
| [MEMORY-INTEGRATION.md](MEMORY-INTEGRATION.md) | How the memory capture pipeline (Layers 2–4) integrates with evergreens |
| [HEARTBEAT-MEMORY-INTEGRATION.md](HEARTBEAT-MEMORY-INTEGRATION.md) | Heartbeat-driven memory capture and session persistence |
| [MEMORY-FIRST-STRATEGY.md](MEMORY-FIRST-STRATEGY.md) | Agent behavioral strategy: always search memory before claiming ignorance |

## Reference

| File | Purpose |
|---|---|
| [OPERATIONAL-GUIDE.md](OPERATIONAL-GUIDE.md) | Agent autonomy, dashboard maintenance, operational patterns |
| [AUTONOMY-GUIDELINES.md](AUTONOMY-GUIDELINES.md) | Rules for autonomous agent operation |
| [UPSTREAM-MONITORING-GUIDE.md](UPSTREAM-MONITORING-GUIDE.md) | How to monitor OpenClaw upstream changes |
| [NAME-CUSTOMIZATION.md](NAME-CUSTOMIZATION.md) | Guide for replacing example names (Alice, Bob, Eve) with actual household names |
| [PLUGIN-RECOMMENDATIONS.md](PLUGIN-RECOMMENDATIONS.md) | Optional session-layer plugins (Gigabrain, LCM, OpenStinger) |

## Advanced / Optional

| File | Purpose |
|---|---|
| [../memory/OPENCLAW-FORK-CHANGES.md](../memory/OPENCLAW-FORK-CHANGES.md) | TypeScript gateway changes for end-to-end multi-user isolation (only needed if forking the OpenClaw gateway) |

## See Also

- [../README.md](../README.md) — Project overview and AI agent reading order
- [../ARCHITECTURE.md](../ARCHITECTURE.md) — Primary architecture document
- [../QUICKSTART.md](../QUICKSTART.md) — Condensed quickstart
- [../evergreens/EVERGREENS.md](../evergreens/EVERGREENS.md) — The 8-step cycle framework
