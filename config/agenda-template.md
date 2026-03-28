<!-- Reference template: This file shows the expected format for completed
     evergreen agenda files. It is NOT automatically processed by the executor
     (which uses its own inline template). Use this as a reference for
     understanding the agenda structure and required sections.
     Variables shown below indicate the expected data points:
     {{EVERGREEN_NAME}}  - Name of the evergreen program (e.g., system-health)
     {{DATE}}            - Today's date (YYYY-MM-DD)
     {{START_TIME}}      - Cycle start time (ISO 8601)
     {{COMPLETION_TIME}} - Cycle end time (ISO 8601, filled at end)
     {{DURATION}}        - Cycle duration (e.g., ~10 min, filled at end)
     {{USER_ID}}         - Agent user ID
     {{TASK_NAME}}       - First task from STATE.md Next Steps
     {{CYCLE_NUMBER}}    - Cycle count (if tracked)
-->

# {{EVERGREEN_NAME}} - Agenda for {{DATE}}

## Cycle Status

- **Started:** {{START_TIME}}
- **Status:** in_progress
- **User ID:** {{USER_ID}}

---

## Tasks for This Cycle

### 1. {{TASK_NAME}}

**Source:** STATE.md Next Steps

- [ ] Status: pending
- [ ] Findings: (to be filled)
- [ ] Actions: (to be filled)
- [ ] Recommendations: (to be filled)
- [ ] Reasoning: (to be filled)

---

## Research Findings

(to be filled during cycle)

- 
- 
- 

---

## Analysis & Synthesis

(to be filled during cycle)

### Key Insights

- 

### Identified Gaps

- 

---

## Blockers & Missing Information

(to be filled if encountered)

| Blocker | Impact | Resolution Needed |
|---------|--------|-------------------|
|         |        |                   |

---

## Housekeeping Notes

(to be filled during cycle)

- Archived: 
- Compacted: 
- Pruned: 

---

## Next Cycle Plan

(to be written at end of cycle)

1. 
2. 
3. 

---

## Notifications Sent

(log any messages sent to users)

| Time | Channel | Recipient | Reason |
|------|---------|-----------|--------|
|      |         |           |        |

---

## Cycle Summary

**Completed:** {{COMPLETION_TIME}}

**Duration:** {{DURATION}}

### Tasks Completed

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Test Results

- [ ] Smoke tests: PASS/FAIL
- [ ] Regression tests: PASS/FAIL
- [ ] Safety checks: PASS/FAIL

### Key Decisions Made

1. 
2. 
3. 

---

*Agenda generated from template. Update sections as you work through the 8-step evergreen cycle.*
