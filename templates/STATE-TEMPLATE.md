# [Evergreen Name] - State

<!-- REQUIRED SECTIONS: Status, Cycle Timing, Current Focus, Completed Recently, Next Steps.
     These sections must be present in every STATE.md — the dashboard and validation scripts depend on them.
     
     OPTIONAL SECTIONS: Active Experiments, System Information, Key Learnings, Research Topics,
     Blocking Issues. Add domain-specific sections as needed for your evergreen type. -->

## Status
- Overall Health: 🟢 Healthy (or 🟡 Degraded / 🔴 Critical)
- Last Cycle: YYYY-MM-DD
- Next Cycle: YYYY-MM-DD

## Cycle Timing
- Started At: YYYY-MM-DDTHH:MM:SSZ
- Completed At: YYYY-MM-DDTHH:MM:SSZ
- Duration: ~X minutes

## Current Focus
[Brief description of current focus area - update each cycle]

## Active Experiments
| ID | Hypothesis | Started | Status | Notes |
|----|------------|---------|--------|-------|
| E001 | ... | YYYY-MM-DD | running | ... |

## System Information
[Relevant system info for this evergreen type - customize per evergreen]

## Key Learnings

<!-- Entries older than 14 days are automatically archived to
     LEARNINGS-ARCHIVE-YYYY-MM.md by the pre-session maintenance script.
     Only recent learnings appear here to keep context lean. -->

- YYYY-MM-DD: [Learning from this cycle]
- YYYY-MM-DD: [Previous learning]

## Research Topics
- [ ] [Topic to research]
- [x] [Completed topic] ✅

## Blocking Issues
[None currently, or list blockers]

## Completed Recently
**CRITICAL:** Maintain this section! The dashboard's "Recent Activity" reads from here.

**Rules:**
- Add each cycle's accomplishment: `- [YYYY-MM-DD] Brief description`
- Keep only 3-5 most recent items
- Remove oldest when exceeding 5 items
- The dashboard generator extracts lines matching the pattern: `^- \[YYYY-MM-DD\] ...`
- Date format MUST be `[YYYY-MM-DD]` (ISO 8601 in square brackets) — other formats will not be parsed

**Examples:**
- [YYYY-MM-DD] AI orchestration implemented for evergreen cycles
- [YYYY-MM-DD] Voice-call extension merged with upstream
- [YYYY-MM-DD] Security vulnerabilities V001-V005 addressed

## Next Steps
1. [ ] [Next task]
2. [ ] [Following task]
3. [ ] [Future task]

---
*Last updated: YYYY-MM-DD*
