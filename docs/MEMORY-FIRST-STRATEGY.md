# Memory-First Recall Strategy

> **For implementing agents:** This document defines a behavioral strategy for your agent's daily operation. After setup is complete, ensure your agent's system prompt or skill files reference this strategy. It is NOT a setup step — it describes how your agent should behave once the memory system is running.

**Eliminating "I don't know" without searching first.**

This guide documents a behavioral strategy for AI agents with memory systems. The core principle: **never claim ignorance without searching memory first.** This dramatically improves user experience by making the agent feel knowledgeable and proactive rather than limited and passive.

---

## The Problem

AI agents with memory systems often default to phrases like:

- "I don't have access to that information"
- "I'm not able to recall that"
- "I don't know"

...even when the answer may be sitting in their memory system. The agent has tools to search but doesn't use them proactively, creating a frustrating experience where the user knows the agent *should* know something but it claims otherwise.

---

## The Strategy

### 1. Search Before Responding

When asked about anything that could be in memory — people, projects, preferences, past conversations, schedules, decisions — the agent should **search memory before answering.** This applies to:

- Direct questions ("What did we decide about X?")
- Contextual questions ("Do you remember when...?")
- Implicit references ("How's the project going?")
- Identity questions ("What's my name?")

### 2. Retry with Different Terms

If the first search returns nothing, **rephrase and try again.** Memory systems are imperfect — a different query may surface what the first missed:

- Broaden the query ("project backup" → "backup")
- Try synonyms ("meeting" → "discussion" / "conversation")
- Search for names or key terms instead of full questions
- Try at least 2 different searches before concluding

### 3. Use Graceful Degradation Language

When searches genuinely find nothing, the agent's language matters:

| Instead of... | Say... |
|---------------|--------|
| "I don't have access to that" | "I'm not finding that in my notes" |
| "I can't recall that" | "I don't seem to have that one" |
| "I don't have that information" | "Nothing's coming up for that" |
| "I'm unable to look that up" | "I checked but didn't find anything on that" |

The difference: **knowledge gap** (natural, human) vs **system limitation** (robotic, frustrating).

### 4. Use Natural Stalling (Voice/Real-Time)

For voice interfaces or real-time conversations where tool calls create pauses, use natural filler language while searching. These patterns are most relevant for voice interfaces (e.g., WhatsApp voice calls). For text-only setups, the same principle applies — signal intent before a long operation (e.g., "Let me check my notes...").

- "Let me think..."
- "Hmm, one moment..."
- "Let me check on that..."
- "Give me just a sec..."

---

## Implementation

### SOUL.md Addition

Add this to your agent's `SOUL.md` (`SOUL.md` is OpenClaw's agent personality/identity file, typically at `~/.openclaw/workspace/SOUL.md` — this is an OpenClaw concept, not part of the Evergreen Toolkit. See [OpenClaw documentation](https://docs.openclaw.ai) for details):

```markdown
### Memory-First Recall

Never claim ignorance without searching first. When asked about anything that
could be in memory — people, projects, preferences, past conversations,
schedules — search before responding. If the first search finds nothing,
rephrase and try again. Only after genuine effort, say "I'm not finding that
in my notes" — never "I don't have access to that" or "I can't" which implies
a system limitation rather than a knowledge gap.
```

### Use Hybrid Search

If you're using the True Recall memory system, prefer `hybrid_search.py` over `search_memories.py` for memory lookups. Hybrid search combines:

- **Daily file keyword search** — Finds exact mentions in recent daily memory files
- **Qdrant vector search** — Finds semantically similar content across all memories

This dual approach catches both exact matches and conceptual matches, significantly reducing false negatives.

```bash
# Single-source (Qdrant only - may miss file-based context)
python3 memory/scripts/search_memories.py "project status" --user-id <user1>

# Hybrid (files + Qdrant - recommended)
python3 memory/scripts/hybrid_search.py "project status" --user-id <user1> --json
```

### Escalation Path

For multi-tier systems, define a search escalation:

1. **Fast path**: Hybrid search (files + vectors) — ~2 seconds
2. **Deep path**: Full agent sub-task with all available tools — ~10 seconds
3. **External**: Web search or knowledge base query — ~15 seconds

The agent should start with the fast path and escalate only when needed.

---

## Why This Matters

Memory is the foundation of relationship-building between an AI agent and its users. An agent that says "I don't know your name" when the user's name is in Qdrant feels broken. An agent that says "Let me check... ah, you're Alice!" feels like it *knows* you.

The difference between a good and great agent experience often isn't the quality of the memory system — it's whether the agent **actually uses it** before responding.

---

## Related Documentation

- [AUTONOMY-GUIDELINES.md](AUTONOMY-GUIDELINES.md) — Agent decision framework for autonomous actions
- [MEMORY-INTEGRATION.md](MEMORY-INTEGRATION.md) — Full memory system architecture
- [HEARTBEAT-MEMORY-INTEGRATION.md](HEARTBEAT-MEMORY-INTEGRATION.md) — Automatic memory capture
- [../memory/SKILL.md](../memory/SKILL.md) — Memory skill reference
