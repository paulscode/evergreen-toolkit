# Workspace Memory System

A 7-layer memory architecture designed for multi-user households. Each layer has exactly one job.

## Layers

| # | Layer | Purpose | Technology | Persistence |
|---|-------|---------|------------|-------------|
| 1 | **Session** | In-session coherence + automatic recall | LCM (optional) + Gigabrain (optional) | Current session |
| 2 | **Fast Capture** | Real-time conversation capture | Redis buffer (`mem:<user_id>`) | 24-48h TTL |
| 3 | **Raw Archive** | Full transcript backup + daily files | Qdrant `<agent>-memories` + `memory/<user>/YYYY-MM-DD.md` | Permanent |
| 4 | **AI Curation** | High-salience gem extraction | True Recall → Qdrant `true_recall` | Permanent |
| 5 | **Durable Knowledge** | Structured facts — canonical source of truth | PARA (`memory/para/<user>/`) | Permanent |
| 6 | **Operational Rules** | Behavioral rules, autonomy guidelines | `AGENTS.md` (managed blocks) | Permanent |
| 7 | **Routing** | Tells the agent where to look | `MEMORY.md` (tiny index) | Permanent |

## Data Flow

```
Conversation → Redis capture → True Recall (gems) → PARA promotion (facts)
                             → Jarvis (raw backup) → Daily files
```

## Guardrails

- **PARA is durable truth.** Nothing overrides it.
- **LCM is NOT long-term truth.** Session-scoped only.
- **MEMORY.md is a router**, not a warehouse. Keep it tiny.
- **AGENTS.md is for rules**, not memory storage.
- **Daily notes are ephemeral.** Promote to PARA, then archive.
- **Use retrieval, not preload.** Query by need, don't load everything at session start.

## Key Ordering

1. True Recall (2:30 AM) runs BEFORE Jarvis (3:00 AM) — Jarvis clears Redis.
2. PARA promotion (weekly, Sunday 2:00 AM) runs independently.

## Multi-User

All layers support per-user isolation via `user_id`:
- Redis keys: `mem:<user_id>`
- Daily files: `memory/<user>/YYYY-MM-DD.md`
- PARA: `memory/para/<user>/`
- Qdrant metadata: `user_id` filter on all queries
- Curator prompts: `memory/curator_prompts/<user_id>.md`

See [memory/MULTI-USER-GUIDE.md](memory/MULTI-USER-GUIDE.md) for full details.

> **Implementation:** See [memory/README.md](memory/README.md) for scripts and [QUICKSTART.md](QUICKSTART.md) Step 6 for setup.

## Credits

- **True Recall / Jarvis Memory**: SpeedyFoxAI (GitLab: mdkrush)
- **PARA method**: Tiago Forte (adapted for multi-user AI agents)
- **Layer separation concepts**: Lucas Synnott / appliedleverage.io
