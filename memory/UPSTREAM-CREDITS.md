# 🙏 Upstream Credits & Attribution

## Primary Inspiration: SpeedyFoxAI's Jarvis Memory + True Recall

The **household-memory evergreen** and the two-layer capture-and-curate pipeline (True Recall + Jarvis Memory) in this toolkit are built upon the original work of **SpeedyFoxAI**. The toolkit extends this foundation into a 7-layer memory architecture — see [MEMORY-SYSTEM.md](../MEMORY-SYSTEM.md) for the full model.

### Original Project

- **Repository:** https://gitlab.com/mdkrush/openclaw-true-recall-base
- **Author:** SpeedyFoxAI (mdkrush)
- **License:** MIT (same as this toolkit)
- **Status:** Actively maintained - watch for upstream improvements

### Upstream Foundation

SpeedyFoxAI designed and implemented:

1. **Two-Layer Memory Architecture**
   - Redis buffer for fast capture (sub-second writes)
   - Qdrant vector store for semantic search
   - Daily markdown files for human-readable logs

2. **True Recall Gating System**
   - Real-time monitoring of conversation buffer
   - High-salience event extraction
   - Immediate promotion to long-term storage

3. **Curation Engine**
   - The "Curator" AI prompt for gem extraction
   - Decision/insight/preference pattern recognition
   - Confidence scoring and categorization

4. **Session Context Handling**
   - Automatic conversation capture
   - User ID detection and routing
   - Timestamp normalization

### Toolkit Adaptations

Adaptations for the Evergreen Toolkit:

- **Integrated into evergreen cycle** - Memory curation runs as part of household-memory evergreen (not standalone)
- **Added progressive summarization** - Compaction rules for document management
- **Enhanced error handling** - Fault-tolerant execution with logging
- **Added tests** - Smoke and regression tests for memory operations
- **Documentation improvements** - Architecture diagrams, implementation guides

### Why This Matters

SpeedyFoxAI's True Recall system solved the core challenge of AI memory: **balancing speed with durability**. His insight that "not all memories are created equal" led to the gating mechanism that captures critical moments immediately while batching routine conversational context.

This toolkit builds on that foundation, adding continuous improvement through the evergreen cycle.

---

## Layer Architecture Concepts: Lucas Synnott / Applied Leverage

The **7-layer memory architecture** incorporates concepts from the **5-Layer Memory Stack** by **Lucas Synnott** (appliedleverage.io).

### Original Project

- **Author:** Lucas Synnott
- **Website:** appliedleverage.io
- **Package:** openclaw-memory-stack-giveaway v0.2.0
- **License:** Not explicitly specified in package; used with attribution

### Concepts Adopted

1. **PARA as Durable Knowledge Layer**
   - Structured facts store (Projects, Areas, Resources, Archives)
   - Originally at `~/life/`; adapted to workspace-local `memory/para/<user>/`
   - Extended for multi-user support with per-user directories

2. **MEMORY.md Routing Index**
   - Compact file that tells the agent where to look for different types of information
   - The insight that a routing layer prevents agents from searching blindly
   - Adapted as Layer 7 of the architecture

3. **Session Recovery (LCM / lossless-claw)**
   - Plugin for lossless session recovery across reconnections
   - Documented as optional Layer 1 enhancement (not required for core operation)

4. **Automatic Context Recall (Gigabrain)**
   - Plugin that injects relevant past memories into active sessions
   - Documented as optional Layer 1 enhancement

5. **Daily Notes Lifecycle**
   - Concept of daily capture → promotion → archival
   - Adapted to work with True Recall curation pipeline

### Toolkit Adaptations

- **Multi-user extension** — PARA directories are per-user, not global
- **Rich items.json schema** — Structured facts with confidence, supersedes, tags (not in original)
- **Tiered contradiction resolution** — 3-tier automated system for fact conflicts
- **Integration with True Recall** — PARA promotion from curated gems (not in original)
- **Workspace-local** — PARA stored in toolkit workspace, not `~/life/`

---

## Ongoing Upstream Monitoring

For the full upstream monitoring process — which repositories to watch, how to evaluate changes, and the monitoring workflow — see [`docs/UPSTREAM-MONITORING-GUIDE.md`](../docs/UPSTREAM-MONITORING-GUIDE.md).

---

## Attribution Requirements

When using or modifying this toolkit:

1. **Keep this file** - Do not remove UPSTREAM-CREDITS.md
2. **Credit SpeedyFoxAI** - Mention in your own documentation (True Recall + Jarvis Memory)
3. **Credit Lucas Synnott** - Mention in your documentation (layer architecture concepts, PARA adaptation)
4. **Share improvements** - Contribute back to both this toolkit and upstream
5. **Respect licenses** - MIT license applies to all components

---

## Contact & Community

### SpeedyFoxAI's Work
- **GitLab:** https://gitlab.com/mdkrush
- **Discord:** Active in OpenClaw community (#skills channel)
- **Contributions:** Jarvis Memory, True Recall, conversation context handling

### This Toolkit
- **Repository:** https://github.com/paulscode/evergreen-toolkit
- **Discord:** https://discord.com/invite/clawd (#skills channel)

### OpenClaw Community
- **Discord:** https://discord.com/invite/clawd
- **GitHub:** https://github.com/openclaw
- **Docs:** https://docs.openclaw.ai

---

## Timeline

- **Original True Recall System:** Developed by SpeedyFoxAI
- **Evergreen Toolkit Integration:** Adapted for continuous improvement cycle
- **Ongoing:** Active monitoring and bidirectional improvement adoption

---

**We stand on the shoulders of giants. 🙏**

*This toolkit would not exist without SpeedyFoxAI's pioneering work on AI memory systems. Our contribution is making his architecture continuously self-improving through the evergreen cycle.*
