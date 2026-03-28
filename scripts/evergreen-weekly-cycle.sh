#!/usr/bin/env bash
#
# evergreen-weekly-cycle.sh — Run a weekly deep-analysis cycle across all evergreens.
#
# This is an opt-in weekly cycle that performs heavier, LLM-powered analysis
# that would be too expensive for daily runs:
#   - Semantic learning compaction (merge redundant Key Learnings)
#   - Agenda-history pattern mining (surface emerging themes)
#   - Cross-evergreen synthesis (real semantic analysis vs keyword overlap)
#   - PARA candidate extraction (identify durable facts for promotion)
#   - Next Steps triage (recommend keep/escalate/merge/drop)
#   - Metrics trend projection (compute projections from metrics.json)
#
# The daily cycles (evergreen-ai-runner.sh) continue to work without this.
# This script produces enrichment files that daily cycles read if available.
#
# Usage: evergreen-weekly-cycle.sh
#
# Schedule: Once per week (e.g., Sunday 6:30 AM, after daily cycles complete).
# Add to crontab only if you want the deeper analysis.
#
# Environment variables (all optional):
#   OPENCLAW_WORKSPACE  — workspace path (default: parent of this script's dir)
#   OPENCLAW_BIN        — path to openclaw binary (default: found via PATH)
#   OPENCLAW_STATE_DIR  — OpenClaw state directory (default: ~/.openclaw)
#   WEEKLY_TIMEOUT      — timeout in seconds (default: 5400 = 90 min)
#   EVERGREEN_AGENT     — named agent to use (default: none)
#

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$(dirname "$SCRIPT_DIR")}"
OPENCLAW="${OPENCLAW_BIN:-openclaw}"
DATE=$(date +%Y%m%d)
DATE_ISO=$(date +%Y-%m-%d)
LOG_DIR="$WORKSPACE/logs"
LOG_FILE="$LOG_DIR/evergreen-weekly-${DATE}.log"
LOCK_FILE="$WORKSPACE/.evergreen-weekly.lock"
SESSION_ID="evergreen-weekly-${DATE}"
TIMEOUT_SECONDS="${WEEKLY_TIMEOUT:-5400}"
EVERGREEN_AGENT="${EVERGREEN_AGENT:-}"
EVERGREENS_DIR="$WORKSPACE/evergreens"
SYNTHESIS_FILE="$EVERGREENS_DIR/weekly-synthesis-${DATE}.md"

mkdir -p "$LOG_DIR"

# ── Source environment ───────────────────────────────────────────────────
[[ -f "$WORKSPACE/.memory_env" ]] && source "$WORKSPACE/.memory_env"

log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# ── Lock ────────────────────────────────────────────────────────────────
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log "SKIP: weekly cycle already running (lock held)"
    exit 0
fi

# ── Pre-flight ──────────────────────────────────────────────────────────
log "Starting weekly deep-analysis cycle"

if ! command -v "$OPENCLAW" &>/dev/null; then
    log "FATAL: openclaw command not found in PATH (set OPENCLAW_BIN if installed elsewhere)"
    exit 1
fi

# ── Generate shell-side weekly synthesis first (P3 fallback) ────────────
# This provides the keyword-based synthesis even if the LLM cycle fails.
SYNTHESIS_SCRIPT="$SCRIPT_DIR/weekly-synthesis.py"
PYTHON="${WORKSPACE}/.venv/bin/python3"
[[ ! -x "$PYTHON" ]] && PYTHON="python3"  # fallback if no venv

if [[ -f "$SYNTHESIS_SCRIPT" ]]; then
    log "Running shell-side weekly synthesis..."
    "$PYTHON" "$SYNTHESIS_SCRIPT" --days 7 2>>"$LOG_FILE" || log "WARN: weekly-synthesis.py failed (non-fatal)"
fi

# ── Collect context for the LLM ────────────────────────────────────────
# Gather STATE.md files, recent agenda summaries, and metrics for the prompt.

EVERGREEN_NAMES=""
STATE_CONTEXT=""
METRICS_CONTEXT=""
HISTORY_CONTEXT=""

for eg_dir in "$EVERGREENS_DIR"/*/; do
    [[ ! -f "$eg_dir/STATE.md" ]] && continue
    eg_name=$(basename "$eg_dir")
    EVERGREEN_NAMES="${EVERGREEN_NAMES:+$EVERGREEN_NAMES, }$eg_name"

    # Collect STATE.md paths
    STATE_CONTEXT="${STATE_CONTEXT}  - ${eg_dir}STATE.md\n"

    # Collect metrics.json paths if they exist
    if [[ -f "$eg_dir/metrics.json" ]]; then
        METRICS_CONTEXT="${METRICS_CONTEXT}  - ${eg_dir}metrics.json\n"
    fi

    # Collect recent agenda-history file paths (last 7 days)
    if [[ -d "$eg_dir/agenda-history" ]]; then
        recent=$(find "$eg_dir/agenda-history" -name "*.md" -mtime -7 2>/dev/null | sort | tail -5)
        if [[ -n "$recent" ]]; then
            HISTORY_CONTEXT="${HISTORY_CONTEXT}  $eg_name recent archives (read Cycle Summary sections):\n"
            while IFS= read -r f; do
                HISTORY_CONTEXT="${HISTORY_CONTEXT}    - $f\n"
            done <<< "$recent"
        fi
    fi
done

# Collect PARA paths if they exist
PARA_CONTEXT=""
PARA_DIR="${PARA_DIR:-$WORKSPACE/memory/para}"
if [[ -d "$PARA_DIR" ]]; then
    for user_dir in "$PARA_DIR"/*/; do
        [[ -f "$user_dir/items.json" ]] && PARA_CONTEXT="${PARA_CONTEXT}  - ${user_dir}items.json\n"
    done
fi

# ── Build task prompt ──────────────────────────────────────────────────
read -r -d '' TASK_PROMPT <<PROMPT || true
You are running the weekly deep-analysis cycle across all evergreens.

This is a once-per-week meta-cycle that reads across all evergreen programs
and performs heavier analysis than daily runs can afford.

Workspace: ${WORKSPACE}
Evergreens: ${EVERGREEN_NAMES}
Date: ${DATE_ISO}

## Inputs to read

STATE.md files (read all):
$(echo -e "$STATE_CONTEXT")
${HISTORY_CONTEXT:+Recent agenda-history (read Cycle Summary / Research Findings sections only):
$(echo -e "$HISTORY_CONTEXT")}
${METRICS_CONTEXT:+Metrics files (read all):
$(echo -e "$METRICS_CONTEXT")}
${PARA_CONTEXT:+PARA knowledge (read for deduplication in task 4):
$(echo -e "$PARA_CONTEXT")}
If a weekly synthesis already exists, read it:
  ${SYNTHESIS_FILE}

## Tasks

Perform each task below. Write all outputs to the weekly synthesis file:
  ${SYNTHESIS_FILE}

If the file already exists (from the shell-side generator), replace its content
with your richer analysis. Preserve the per-evergreen summary sections.

### 1. Semantic Learning Compaction

For each evergreen's STATE.md, read the Key Learnings section. If multiple
entries describe the same underlying issue or discovery, merge them into a
single consolidated insight. Write the merged version back to STATE.md,
preserving the most recent date. Move the original entries to the archive
file (LEARNINGS-ARCHIVE-YYYY-MM.md in the evergreen directory).

Example: Five entries about "duplicate voice-call registration" across
different dates → one entry: "Voice-call plugin has persistent duplicate
registration; root cause is plugins.allow unset. First observed YYYY-MM-DD."

Be conservative — only merge entries that are clearly about the same thing.

### 2. Agenda-History Pattern Mining

Read the Cycle Summary and Research Findings sections from each evergreen's
recent agenda-history files (listed above). Identify:
- Recurring themes the daily cycle may have missed
- Emerging patterns not yet in Next Steps
- Work that was started and quietly abandoned

Document findings in a "## Patterns Detected" section of the weekly synthesis.

### 3. Cross-Evergreen Semantic Synthesis

Read all evergreens' STATE.md files together and answer:
- Which findings from different evergreens describe the same underlying issue?
- Are any evergreen's Next Steps blocked by another evergreen's domain?
- What systemic risks emerge when you look across all domains together?

Write a "## Cross-Cutting Issues" section in the weekly synthesis.

### 4. PARA Candidate Extraction

From the week's findings, identify durable facts worth promoting to the
shared PARA knowledge base. A durable fact is something unlikely to change
soon (e.g., "backup grows ~300KB/day", "plugin X has known issue Y").

${PARA_CONTEXT:+Read existing PARA items.json files to avoid duplicates.}

Write candidates to a "## PARA Candidates" section in the weekly synthesis.
Format each as:
- **Fact:** [the durable fact]
- **Source:** [which evergreen(s) surfaced this]
- **Confidence:** high/medium

Do NOT write directly to PARA files — the household-memory evergreen reviews
and approves candidates.

### 5. Next Steps Triage

Read all evergreens' Next Steps sections. For each item, recommend one of:
- **Keep** — still relevant, actionable
- **Escalate** — stuck for multiple cycles, needs attention
- **Merge** — duplicates an item in another evergreen
- **Drop** — overtaken by events or no longer relevant

Write a "## Next Steps Triage" section in the weekly synthesis.

### 6. Metrics Trend Projection

${METRICS_CONTEXT:+Read the metrics.json files listed above. For any metric with 3+ data
points, compute the trend and project forward (e.g., "at current growth rate,
backup reaches N GB in M weeks"). Write a "## Trend Projections" section.}
${METRICS_CONTEXT:-No metrics.json files found. Skip this task. When evergreens start
recording metrics, this task will produce trend projections.}

## Output format

Write everything to: ${SYNTHESIS_FILE}

Structure:
\`\`\`
# Weekly Deep Analysis — ${DATE_ISO}
## Cross-Cutting Issues
## Patterns Detected
## PARA Candidates
## Next Steps Triage
## Trend Projections
## Per-Evergreen Highlights
## Learning Compaction Summary
\`\`\`

## Time management

You have approximately 60 minutes. Prioritize tasks 1, 3, and 5 (highest
impact). Tasks 2, 4, and 6 are valuable but can be abbreviated if time
is short.
PROMPT

# ── Reset session history ──────────────────────────────────────────────
OPENCLAW_STATE="${OPENCLAW_STATE_DIR:-$HOME/.openclaw}"
if [[ -n "$EVERGREEN_AGENT" ]]; then
    AGENT_SESSION_DIR="$OPENCLAW_STATE/agents/${EVERGREEN_AGENT}/sessions"
else
    AGENT_SESSION_DIR="$OPENCLAW_STATE/agents/main/sessions"
fi
if [[ -d "$AGENT_SESSION_DIR" ]]; then
    SESSION_ARCHIVE_DIR="$AGENT_SESSION_DIR/archive"
    mkdir -p "$SESSION_ARCHIVE_DIR"
    for sf in "$AGENT_SESSION_DIR"/*.jsonl; do
        [[ -f "$sf" ]] && mv "$sf" "$SESSION_ARCHIVE_DIR/$(basename "$sf").weekly-${DATE}" 2>/dev/null || true
    done
    [[ -f "$AGENT_SESSION_DIR/sessions.json" ]] && echo '{}' > "$AGENT_SESSION_DIR/sessions.json"
    log "Session store reset for weekly cycle"
fi

# ── Backup STATE.md files before LLM modifies them ─────────────────────
BACKUP_SUFFIX="weekly-backup-${DATE}"
BACKED_UP_STATES=()
for eg_dir in "$EVERGREENS_DIR"/*/; do
    [[ ! -f "$eg_dir/STATE.md" ]] && continue
    cp "$eg_dir/STATE.md" "$eg_dir/STATE.md.${BACKUP_SUFFIX}"
    BACKED_UP_STATES+=("$eg_dir/STATE.md")
done
log "Backed up ${#BACKED_UP_STATES[@]} STATE.md files (suffix: .${BACKUP_SUFFIX})"

# ── Invoke openclaw agent ─────────────────────────────────────────────
if [[ -n "$EVERGREEN_AGENT" ]]; then
    log "Session: $SESSION_ID | Agent: $EVERGREEN_AGENT | Timeout: ${TIMEOUT_SECONDS}s"
else
    log "Session: $SESSION_ID | Agent: (default) | Timeout: ${TIMEOUT_SECONDS}s"
fi

AGENT_CMD=("$OPENCLAW" agent)
[[ -n "$EVERGREEN_AGENT" ]] && AGENT_CMD+=(--agent "$EVERGREEN_AGENT")
AGENT_CMD+=(--message "$TASK_PROMPT" --session-id "$SESSION_ID" --timeout "$TIMEOUT_SECONDS" --json)

AGENT_EXIT=0
AGENT_OUTPUT=$("${AGENT_CMD[@]}" 2>&1) || AGENT_EXIT=$?
echo "$AGENT_OUTPUT" >> "$LOG_FILE"

if [[ "$AGENT_EXIT" -ne 0 ]]; then
    log "WARN: Weekly cycle agent exited with code $AGENT_EXIT"
    log "Restoring STATE.md backups due to non-zero exit"
    for state_file in "${BACKED_UP_STATES[@]}"; do
        cp "${state_file}.${BACKUP_SUFFIX}" "$state_file"
    done
    log "STATE.md files restored from backups"
    log "The shell-side weekly synthesis (if generated) is still available as fallback"
else
    log "Weekly deep-analysis cycle completed"
fi

# ── Cleanup old weekly logs ────────────────────────────────────────────
find "$LOG_DIR" -name "evergreen-weekly-*.log" -mtime +30 -delete 2>/dev/null || true
find "$EVERGREENS_DIR" -maxdepth 1 -name "weekly-synthesis-*.md" -mtime +30 -delete 2>/dev/null || true

log "SUCCESS: Weekly cycle finished"
exit 0
