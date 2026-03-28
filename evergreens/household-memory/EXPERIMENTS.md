<!-- EXAMPLE: Experiment proposals shown here illustrate the format.
     Replace with experiments relevant to your deployment.
     Dates from 2008-2009 are intentionally fake placeholders;
     they will be replaced with real dates on first cycle. -->

# Household Memory Architecture - Experiments

## Proposed Experiments

### E001: Session Continuity / Active Task Tracking

**Status:** 📋 Proposed (2008-12-27)
**Priority:** Medium
**Source:** <user1> (2008-12-27 conversation)

**Problem Statement:**
When chat sessions terminate unexpectedly, work in progress may be lost. Two scenarios occur:
1. Chat terminates, but agent continues in background → work completes, <user1> sees results after restart
2. Chat terminates, agent process halts → work is incomplete, no notification or recovery

**Proposed Solution:**
Maintain an "active work" document that:
- Contains brief summary of current work items
- Tracks progress state for each item (started, in-progress, blocked, completed)
- Is updated as the agent progresses through requests
- Is referenced on startup (new chat or heartbeat) to detect interrupted work
- Allows <user1> to decide whether to continue, abandon, or modify interrupted tasks

**Key Design Questions:**
1. **Document Location:** Where should this live? Options:
   - `memory/active-work.md` — simple, discoverable
   - `memory/{user_id}/active-work.md` — per-user tracking
   - `evergreens/household-memory/ACTIVE-WORK.md` — tied to memory evergreen

2. **Update Frequency:** When to update?
   - On every user message (verbose, but complete)
   - On task start/completion only (leaner, but may miss mid-task interruptions)
   - On significant state changes only (requires defining "significant")

3. **Startup Integration:** How to surface on startup?
   - Explicit check in agent startup sequence (e.g., AGENTS.md)
   - Reference in startup sequence for session-initiated startups
   - Both (different contexts)

4. **Granularity:** What level of detail?
   - High-level: "Working on X for <user1>"
   - Mid-level: "Working on X for <user1>; step 2 of 5 complete"
   - Detailed: "Working on X for <user1>; fetched data, now processing, next is formatting"

5. **Session Isolation:**
   - Single global document? (simpler, but concurrent sessions could conflict)
   - Per-session documents? (more complex, but handles concurrency)
   - Session ID in filename? (e.g., `active-work-session-123.md`)

**Potential Approaches:**

**Option A: Simple Active Work File**
```
memory/active-work.md
```
Updated on task start, progress milestones, and completion. Checked on every session start.

**Option B: Session-Aware Tracking**
```
memory/sessions/{session_id}/active-work.md
```
Each session has its own tracker. On startup, check for orphaned sessions and prompt for recovery.

**Option C: State Machine Approach**
```
memory/work-queue.json
```
Structured queue with states: pending, in_progress, blocked, completed. More machine-readable, enables automation.

**Option D: Hybrid**
Simple markdown for human-readability + JSON for programmatic state tracking.

**Tests Required:**
- [ ] Define: What constitutes "interrupted work"?
- [ ] Define: How to detect interruption vs normal completion?
- [ ] Test: Session crash during task → recovery prompt appears
- [ ] Test: Normal session end → no false recovery prompt
- [ ] Test: Multiple concurrent sessions → correct isolation

**Success Criteria:**
- <user1> is notified of interrupted work on next session start
- <user1> can choose to continue, abandon, or modify the work
- No significant overhead in normal operation
- Works across both chat-initiated and scheduled sessions

**Failure Detection:**
- False positives: Recovery prompts for completed work
- False negatives: Interrupted work not detected
- Performance impact: Noticeable slowdown from frequent updates

**Rollback Plan:**
Remove active work file and startup references. No permanent changes to existing systems.

**Dependencies:**
- Requires decision on document location/structure
- May require agent configuration changes (e.g., AGENTS.md)
- May need session ID tracking in OpenClaw

**Related:**
- Agent startup sequence configuration
- MEMORY.md architecture

**Next Steps:**
1. Discuss with <user1> to clarify requirements and preferences
2. Decide on document location and structure
3. Define update triggers and granularity
4. Prototype simple implementation
5. Test interruption scenarios

---

## Completed Experiments

(None yet)

---

## Abandoned Experiments

(None yet)

---

## Active Experiments

### E002: Theory of Mind Development

**Status:** 🎯 Core Mission (Ongoing)
**Priority:** **CRITICAL** — Primary differentiator for household AI
**Started:** 2009-01-01

**Problem:** Generic AI treats all users as one entity, causing confusion, attribution errors, and privacy violations.

**Solution:** Build the agent's theory of mind through 5 layers:
1. Memory Isolation ✅ (separate Redis/Qdrant/files per user)
2. User Detection (active development)
3. Personalized Curation (active development)
4. Knowledge Boundaries (future)
5. Relationship Graph (future)

**Tests:** Isolation, user detection, knowledge boundaries, relationship tracking, privacy audits

**Success:** Users report feeling "understood", zero privacy violations, accurate attribution

See household-memory/STATE.md for current cycle tasks.
