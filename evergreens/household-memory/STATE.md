<!-- EXAMPLE: This STATE.md contains sample data showing the expected format.
     Values are illustrative — your evergreen cycle will update this file
     with real data from your deployment.
     Date convention: All example dates use 2008-2009 era timestamps
     to make them obviously distinguishable from real data. -->

# Household Memory Architecture - State

## Status
- Overall Health: 🟢 Healthy
- Last Cycle: 2009-01-03
- Next Cycle: 2009-01-04

## Cycle Timing
- Started At: 2009-01-03T05:30:00Z
- Completed At: 2009-01-03T06:04:07Z
- Duration: ~34 min

## Current Focus

### 🧠 Core Mission: Theory of Mind Development

**Primary Goal:** Enable your AI agent to build and maintain accurate mental models of each household member.

**Why This Matters:** Theory of mind is not a feature to complete, but a capability to deepen over time. It enables:
- User-specific understanding (User A ≠ User B)
- Relationship tracking (e.g., "User B is User A's spouse")
- Privacy boundaries (personal memories stay private)
- Context-switching without leakage
- Personalized, relevant responses

**Success Metrics:**
- ✅ User-specific memory isolation
- ✅ User-specific curator prompts
- ✅ Relationship tracking in gems
- ⚠️ Knowledge boundary testing (ongoing)
- ⚠️ Context-switching accuracy (ongoing)
- ⚠️ Cross-user reference handling (ongoing)

## Current Implementation

### Memory Capture Pipeline

The memory capture pipeline has two parallel processing paths (True Recall for curated gems + Jarvis for raw backups) within the broader [7-layer architecture](../../MEMORY-SYSTEM.md):

| Layer | Status | Details |
|-------|--------|---------|
| Redis Buffer | ✅ Working | `mem:<user_id>` keys per household member |
| True Recall | 🆕 Ready | Curated gems, `true_recall` collection |
| Daily Files | ✅ Working | `memory/<user_id>/` directories |
| Qdrant (Jarvis) | ⏳ Not yet checked | Raw backups in `<agent>-memories` collection |

### Two-Tier Storage
| System | Schedule | Purpose | Collection |
|--------|----------|---------|------------|
| **True Recall** | 2:30 AM | AI-curated gems (decisions, insights, preferences) | `true_recall` |
| **Jarvis Memory** | 3:00 AM | Raw conversation backup (all turns) | `<agent>-memories` |

### User IDs
- `<user1>` — Household member #1 (e.g., WhatsApp, Webchat)
- `<user2>` — Household member #2 (e.g., WhatsApp)
- `<agent>` — System-level memories

### Scripts
- Save session: `memory/scripts/save_mem.py --user-id <USER_ID>`
- Curate gems: `memory/scripts/curate_memories.py --user-id <USER_ID>`
- Search memories: `memory/scripts/search_memories.py "query" --user-id <USER_ID>`

## Active Experiments

> See [EXPERIMENTS.md](EXPERIMENTS.md) for full hypothesis details, design questions, and rollback plans.

| ID | Hypothesis | Started | Status | Notes |
|----|------------|---------|--------|-------|
| E001 | Active work tracking enables session continuity | 2009-01-02 | proposed | See EXPERIMENTS.md for details |
| E002 | True Recall curated gems improve memory relevance | 2009-01-02 | implementing | Integrated via curate_memories.py |

## Key Learnings
- 2009-01-02: Example — All memory components verified operational (Redis, daily files, Qdrant)
- 2009-01-02: Example — True Recall integration designed with user-specific curator prompts

## Blocking Issues
None currently.

## Completed Recently
- [2009-01-02] Example — memory capture patterns documented
- [2009-01-02] Example — True Recall curator integrated

## Category Analysis

Per-cycle category analysis procedure: see [CATEGORY-ANALYSIS.md](CATEGORY-ANALYSIS.md).

## Upstream Monitoring (CRITICAL)

### Primary Upstream Repository
**SpeedyFoxAI's True Recall Base** — https://gitlab.com/mdkrush/openclaw-true-recall-base

This is the original implementation of the Jarvis Memory + True Recall system. Monitor actively for:
- Bug fixes and performance improvements
- New curation patterns or gem extraction techniques
- Enhanced category management
- Integration improvements with OpenClaw core

### Monitoring Schedule
**Every household-memory cycle:**
1. Check upstream repo for new commits/releases
2. Review changelog for breaking changes or improvements
3. Test promising improvements in isolated experiment
4. Document findings in agenda-history/ (archived automatically each cycle)
5. Adopt if beneficial (with attribution)

### Upstream Monitoring Log

| Date Checked | Upstream Status | Notable Changes | Action Taken |
|--------------|-----------------|-----------------|--------------|
| 2009-01-02 | 🟢 Current | None | No action needed |

**Attribution:** This memory system is based on SpeedyFoxAI's original True Recall work. See `memory/UPSTREAM-CREDITS.md` for full details.

---

## Research Topics
- [ ] Memory consolidation strategies
- [ ] Long-term memory retention policies
- [ ] Cross-user memory isolation verification
- [ ] **Monitor upstream True Recall base** — Watch gitlab.com/mdkrush/openclaw-true-recall-base for improvements to adopt

## Next Steps
1. [ ] Verify Redis buffer is working
2. [ ] Verify Qdrant collection exists and is searchable
3. [ ] Test True Recall curator end-to-end
4. [ ] Add True Recall cron jobs
5. [ ] Document current memory capture patterns

*Last updated: 2009-01-03*
6. [ ] Monitor memory growth and relevance