# Plugin Recommendations — Session Layer Enhancements

Optional OpenClaw plugins that enhance the memory system's session layer (Layer 1). These are **not required** for core operation — the memory system works fully without them.

## LCM (lossless-context-management) — Session Compaction & Recovery

**What it does:** Session compaction plus transcript recovery. Keeps long sessions coherent without losing context. If a session drops or the agent restarts mid-conversation, LCM restores the complete context.

**Why it matters:** Without LCM, a dropped session loses all in-flight context. The agent starts fresh with no memory of the interrupted conversation. LCM makes sessions resilient and prevents long sessions from degrading.

**Scope:** Session-only. LCM data does NOT persist as long-term memory. It is a session management mechanism, not a storage layer.

**Installation:**
```bash
# Check if available in the OpenClaw plugin registry
openclaw plugins list | grep -i lossless

# Install if available
openclaw plugins install lossless-context-management
```

**Configuration:**
```json
// Add to openclaw-plugins.json
{
  "lossless-context-management": {
    "enabled": true,
    "maxContextTokens": 32000,
    "compactionStrategy": "summarize"
  }
}
```

**Status:** Optional. Test on your live system before relying on it in production. Some OpenClaw versions may not support this plugin.

---

## Gigabrain — Automatic Context Recall

**What it does:** Automatically injects relevant past memories into active sessions. When a user mentions a topic, Gigabrain fetches related memories from Qdrant and includes them in the agent's context.

**Why it matters:** Without Gigabrain, the agent must be explicitly asked to search memory. With it, relevant context appears automatically — the agent "remembers" without being prompted.

**How it interacts with existing memory:**
- Gigabrain queries the same Qdrant collections (True Recall + Jarvis)
- It does NOT replace the memory system — it automates the *retrieval* step
- PARA facts should still be consulted for canonical truth (Gigabrain may surface outdated info)

**Installation:**
```bash
# Check availability
openclaw plugins list | grep -i gigabrain

# Install if available
openclaw plugins install gigabrain
```

**Configuration:**
```json
// Add to openclaw-plugins.json
{
  "gigabrain": {
    "enabled": true,
    "vaultMirror": true,
    "deduplication": true,
    "maxSlots": 20
  }
}
```

**Caution:** Gigabrain may inject memories from any user into any session unless filtered by `user_id`. Ensure your Qdrant queries include user_id filtering to maintain privacy boundaries.

**Status:** Optional. Useful for single-user setups. Multi-user setups should verify user_id filtering works correctly before enabling.

---

## OpenStinger — Cross-Session Knowledge Graph

**What it does:** Builds a knowledge graph across sessions — tracking entities, relationships, and how they evolve over time. Enables queries like "when did we last discuss X?" or "how has user's opinion on Y changed?"

**Why it matters:** Qdrant provides semantic search (find similar content), but not structural queries (find connections between entities). OpenStinger fills that gap.

**Current status:** Deferred. The PARA layer covers most of the same ground (structured facts, relationships, contradiction tracking). If PARA proves insufficient for cross-session entity tracking, OpenStinger can be evaluated.

**When to reconsider:**
- If users frequently ask "when did I first mention X?"
- If contradiction resolution needs entity-level history
- If the household-memory evergreen identifies cross-session patterns that PARA can't capture

**Alternative:** Enhanced Qdrant metadata (temporal filtering, `mentioned_entities`, `session_id`) covers most use cases without a separate graph database. These enhancements may be added in a future version.

---

## Plugin Compatibility Notes

- All plugins are version-dependent on OpenClaw. Check compatibility before installing.
- Plugins should be tested individually before enabling multiple simultaneously.
- The core memory system (layers 2-7) works fully without any plugins.
- Plugin configurations go in `openclaw-plugins.json` — see `config/openclaw-plugins.example.json` for the template.

## Credits

- **LCM / lossless-claw:** Referenced in the 5-Layer Memory Stack by Lucas Synnott (appliedleverage.io)
- **Gigabrain:** Referenced in the 5-Layer Memory Stack by Lucas Synnott (appliedleverage.io)
- **OpenStinger:** Referenced in the 5-Layer Memory Stack by Lucas Synnott (appliedleverage.io)
