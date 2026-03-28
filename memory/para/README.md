# PARA — Durable Knowledge Store

**Canonical source of long-term facts about users, projects, and the household.**

PARA (Projects, Areas, Resources, Archives) is the structured durable knowledge layer. It is the highest-authority memory layer — nothing overrides facts stored here.

---

## Structure

Each user gets their own PARA directory. A `shared/` directory holds household-level facts.

```
memory/para/
├── <user1>/                  # Per-user durable knowledge
│   ├── projects/             # Active, time-bound goals
│   ├── areas/                # Ongoing responsibilities
│   ├── resources/            # Reusable reference material
│   ├── archives/             # Completed/outdated (preserved)
│   ├── summary.md            # Quick-read overview (keep under 2K tokens)
│   ├── items.json            # Atomic facts (rich schema)
│   └── review-queue.md       # Contradictions for conversational review
├── <user2>/                  # (same structure)
├── shared/                   # Household-level facts
│   ├── projects/
│   ├── areas/
│   ├── resources/
│   ├── archives/
│   ├── summary.md
│   └── items.json
└── <agent>/                  # Agent's own knowledge
    ├── areas/
    ├── resources/
    ├── summary.md
    └── items.json
```

---

## Rules

1. **Read `summary.md` first** — it's the cheap, fast overview.
2. **Read `items.json` for detail** — atomic facts with source tracking.
3. **Store facts as atomic entries** — one fact per item, not paragraphs.
4. **Supersede, don't delete** — mark old facts as superseded, preserving history.
5. **Never store secrets** in PARA (API keys, passwords, tokens).
6. **PARA is canonical** — if PARA and another source disagree, PARA wins.

---

## items.json Schema

Each entry in `items.json` uses the rich format:

```json
[
  {
    "id": "fact-001",
    "fact": "Uses Redis for caching (chose over Postgres for speed)",
    "category": "technical-decisions",
    "source": "true_recall:2009-01-02",
    "confidence": 0.85,
    "supersedes": null,
    "added": "2009-01-03",
    "last_verified": "2009-01-03",
    "tags": ["infrastructure", "decisions"]
  }
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (e.g., `fact-001`) |
| `fact` | string | yes | The atomic fact (1-2 sentences) |
| `category` | string | yes | Classification (see categories below) |
| `source` | string | yes | Where this came from (e.g., `true_recall:2009-01-02`, `migration:memory.md`) |
| `confidence` | float | yes | 0.0-1.0, from the source gem or migration |
| `supersedes` | string/null | yes | ID of the fact this replaces, or null |
| `added` | string | yes | ISO date when added to PARA |
| `last_verified` | string | yes | ISO date when last confirmed accurate |
| `tags` | array | yes | Searchable tags (1-5 items) |

### Categories

`preference`, `decision`, `technical`, `relationship`, `project`, `knowledge`, `insight`, `workflow`, `contact`, `health`, `financial`, `family`, `plan`, `architecture`

---

## summary.md Format

```markdown
# <User Name>

## Key Facts
- Brief bullet points of the most important things to know

## Relationships
- How this person relates to other household members

## Active Focus
- What they're currently working on or interested in

## Communication
- Preferred channels, styles, technical level
```

Keep `summary.md` concise — under 2K tokens. It's meant to be injected into agent context at session start.

---

## How PARA Gets Populated

1. **Initial seeding**: `seed_para.py` back-populates from existing True Recall gems
2. **Migration**: `migrate_memory_to_para.py` converts existing MEMORY.md content
3. **Weekly promotion**: `promote_to_para.py` promotes new gems → PARA (cron, Sunday 2:00 AM)
4. **Manual**: Agent or human can add facts directly during conversation

---

## Privacy

- Each user's PARA is isolated by default
- When talking to User A, the agent reads User A's PARA + `shared/`
- The agent may read another user's `summary.md` only (for relationship context)
- The agent does NOT read another user's full `items.json`
- PARA directories are gitignored (contain personal data)

---

## Setup

```bash
# Create directories for your users (replace with actual user IDs)
mkdir -p memory/para/<user1>/{projects,areas,resources,archives}
mkdir -p memory/para/<user2>/{projects,areas,resources,archives}
mkdir -p memory/para/shared/{projects,areas,resources,archives}
mkdir -p memory/para/<agent>/{areas,resources}

# If True Recall data already exists, seed PARA:
source .venv/bin/activate && source .memory_env
python3 memory/scripts/seed_para.py --user-id <user1>
python3 memory/scripts/seed_para.py --user-id <user2>

# If migrating from an existing rich MEMORY.md:
python3 memory/scripts/migrate_memory_to_para.py --memory-file /path/to/MEMORY.md
```

See [MULTI-USER-GUIDE.md](../MULTI-USER-GUIDE.md) for full multi-user PARA configuration.
