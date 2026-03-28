# Per-User Memory Directories

Each household user needs a directory under `memory/` for their daily markdown files.

## Setup

```bash
# Create directories for your users (e.g., alice, bob)
mkdir -p memory/<user1> memory/<user2>
```

## What Goes Here

- Daily memory files: `memory/<user>/2009-01-02.md`
- Created automatically by the memory pipeline (True Recall curation + Jarvis backup)
- Human-readable markdown format for review and editing

## Details

See [MULTI-USER-GUIDE.md](MULTI-USER-GUIDE.md) for full multi-user configuration.
