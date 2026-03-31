#!/usr/bin/env bash
#
# evergreen-ai-runner.sh — Run an AI-orchestrated evergreen cycle via openclaw agent.
#
# Usage: evergreen-ai-runner.sh <evergreen-name>
#
# This script spawns a full AI agent session to execute an evergreen cycle.
# The agent can read files, run commands, analyse results, and write findings —
# performing the cognitive work (research, analysis, planning) that scripted
# executors cannot do.
#
# Designed for cron: no interactive input, clear exit codes, full logging.
#
# Requirements:
#   - OpenClaw installed and on PATH (or set OPENCLAW_BIN)
#   - OpenClaw gateway running (auto-falls back to embedded mode if not)
#   - Evergreen directory exists at $WORKSPACE/evergreens/<name>/
#
# Environment variables (all optional):
#   OPENCLAW_WORKSPACE  — workspace path (default: parent of this script's dir)
#   OPENCLAW_BIN        — path to openclaw binary (default: found via PATH)
#   OPENCLAW_STATE_DIR  — OpenClaw state directory (default: ~/.openclaw)
#   EVERGREEN_TIMEOUT   — timeout in seconds (default: 1500)
#   EVERGREEN_AGENT     — named agent to use (default: none, uses system default)
#                         Set to route evergreens to a specific model via
#                         `openclaw agents add <name> --model <provider/model>`
#   EVERGREEN_NOTIFY_TARGET — messaging target for failure alerts (e.g. phone number,
#                             channel ID). If unset, failure notifications are skipped
#                             but still logged.
#

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────
EVERGREEN_NAME="${1:?Usage: $0 <evergreen-name>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENCLAW_WORKSPACE:-$(dirname "$SCRIPT_DIR")}"
OPENCLAW="${OPENCLAW_BIN:-openclaw}"
DATE=$(date +%Y%m%d)
LOG_DIR="$WORKSPACE/logs"
LOG_FILE="$LOG_DIR/evergreen-${EVERGREEN_NAME}-${DATE}.log"
LOCK_FILE="$WORKSPACE/.evergreen-${EVERGREEN_NAME}.lock"
TIMING_FILE="$WORKSPACE/evergreens/${EVERGREEN_NAME}/timing.json"
SESSION_ID="evergreen-${EVERGREEN_NAME}-${DATE}"
TIMEOUT_SECONDS="${EVERGREEN_TIMEOUT:-1500}"
EVERGREEN_AGENT="${EVERGREEN_AGENT:-}"
EVERGREEN_NOTIFY_TARGET="${EVERGREEN_NOTIFY_TARGET:-}"
BRIEFING_FILE="$WORKSPACE/evergreens/daily-briefing-${DATE}.md"
BACKUP_DIR="$WORKSPACE/evergreens/${EVERGREEN_NAME}/.backups"
EVERGREEN_DIR="$WORKSPACE/evergreens/${EVERGREEN_NAME}"

mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# ── Source environment ───────────────────────────────────────────────────
[[ -f "$WORKSPACE/.memory_env" ]] && source "$WORKSPACE/.memory_env"
PYTHON="${WORKSPACE}/.venv/bin/python3"

log() {
    echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# ── Validation function ─────────────────────────────────────────────────
validate_output() {
    local errors=0

    # timing.json: must be valid JSON with required fields and recent timestamp
    if [[ -f "$EVERGREEN_DIR/timing.json" ]]; then
        if ! EVERGREEN_DIR="$EVERGREEN_DIR" "$PYTHON" -c "
import json, sys, os
from datetime import datetime, timezone, timedelta
evergreen_dir = os.environ['EVERGREEN_DIR']
d = json.load(open(os.path.join(evergreen_dir, 'timing.json')))
assert 'completed_at' in d, 'missing completed_at'
assert 'status' in d, 'missing status'
assert d['status'] in ('completed', 'partial'), f'status is {d[\"status\"]}, expected completed or partial'
try:
    ct = datetime.fromisoformat(d['completed_at'].replace('Z', '+00:00'))
    age = (datetime.now(timezone.utc) - ct).total_seconds()
    assert age < 1800, f'completed_at is {age:.0f}s ago (>30min)'
except (ValueError, TypeError):
    pass  # timestamp parse failure is not fatal
" 2>/dev/null; then
            log "VALIDATION FAIL: timing.json is invalid or has unexpected content"
            errors=$((errors + 1))
        fi
    else
        log "VALIDATION FAIL: timing.json does not exist"
        errors=$((errors + 1))
    fi

    # AGENDA.md: must exist, be non-empty, and contain today's date
    if [[ -s "$EVERGREEN_DIR/AGENDA.md" ]]; then
        if ! grep -q "$DATE\|$(date +%Y-%m-%d)" "$EVERGREEN_DIR/AGENDA.md" 2>/dev/null; then
            log "VALIDATION WARN: AGENDA.md does not contain today's date"
            # Warn only — agent may format dates differently
        fi
    else
        log "VALIDATION FAIL: AGENDA.md is missing or empty"
        errors=$((errors + 1))
    fi

    # STATE.md: must exist and be non-empty
    if [[ ! -s "$EVERGREEN_DIR/STATE.md" ]]; then
        log "VALIDATION FAIL: STATE.md is missing or empty"
        errors=$((errors + 1))
    fi

    return "$errors"
}

# ── Rollback function ──────────────────────────────────────────────────
rollback_from_backup() {
    log "Restoring from pre-run backup"
    for f in STATE.md AGENDA.md timing.json; do
        local backup="$BACKUP_DIR/${f}.pre-${DATE}"
        local dest="$EVERGREEN_DIR/$f"
        if [[ -f "$backup" ]]; then
            cp "$backup" "$dest"
            log "Restored $f from backup"
        fi
    done
    log "Backup restored. Originals preserved in $BACKUP_DIR"
}

# ── Notification function ──────────────────────────────────────────────
# Sends a failure alert via OpenClaw's messaging system.
# Requires EVERGREEN_NOTIFY_TARGET to be set (e.g. phone number, channel ID).
# The messaging channel (WhatsApp, Telegram, Slack, etc.) is configured in
# your openclaw.json — this script just provides the target and message.
send_failure_alert() {
    local reason="$1"
    local message="Evergreen Rollback: ${EVERGREEN_NAME}"
    message+=$'\n\n'
    message+="Date: $(date '+%Y-%m-%d %H:%M')"$'\n'
    message+="Reason: ${reason}"$'\n'
    message+="Action: Pre-run backup restored automatically."$'\n'
    message+="Log: logs/evergreen-${EVERGREEN_NAME}-${DATE}.log"$'\n'

    if [[ -z "$EVERGREEN_NOTIFY_TARGET" ]]; then
        log "WARN: EVERGREEN_NOTIFY_TARGET not set — rollback notification skipped (logged only)"
        return 0
    fi

    log "Sending rollback alert notification to $EVERGREEN_NOTIFY_TARGET"
    if command -v "$OPENCLAW" &>/dev/null; then
        "$OPENCLAW" message send \
            --target "$EVERGREEN_NOTIFY_TARGET" \
            --message "$message" \
            2>/dev/null || log "WARN: Failed to send rollback notification"
    fi
}

# ── Lock (flock — auto-releases on exit/crash) ─────────────────────────
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log "SKIP: $EVERGREEN_NAME already running (lock held)"
    exit 0
fi

# ── Pre-flight checks ──────────────────────────────────────────────────
log "Starting AI-orchestrated cycle: $EVERGREEN_NAME"

if ! command -v "$OPENCLAW" &>/dev/null; then
    log "FATAL: openclaw command not found in PATH (set OPENCLAW_BIN if installed elsewhere)"
    exit 1
fi

if [[ ! -d "$WORKSPACE/evergreens/$EVERGREEN_NAME" ]]; then
    log "FATAL: Evergreen directory not found: $WORKSPACE/evergreens/$EVERGREEN_NAME"
    exit 1
fi

if [[ ! -f "$WORKSPACE/evergreens/$EVERGREEN_NAME/STATE.md" ]]; then
    log "FATAL: STATE.md not found in $WORKSPACE/evergreens/$EVERGREEN_NAME (not a valid evergreen)"
    exit 1
fi

if ! "$OPENCLAW" health --timeout 5000 &>/dev/null; then
    log "WARN: Gateway health check failed — will attempt anyway (auto-fallback available)"
fi

# ── Pre-run backup ─────────────────────────────────────────────────────
for f in STATE.md AGENDA.md timing.json; do
    SRC="$EVERGREEN_DIR/$f"
    [[ -f "$SRC" ]] && cp "$SRC" "$BACKUP_DIR/${f}.pre-${DATE}"
done
log "Pre-run backup saved to $BACKUP_DIR"

# ── Pre-session state maintenance ──────────────────────────────────────
# Compact old Key Learnings and detect stale Next Steps items before the
# agent session starts. This keeps STATE.md lean and surfaces stuck work.
MAINTENANCE_SCRIPT="$SCRIPT_DIR/preflight-state-maintenance.py"
if [[ -f "$MAINTENANCE_SCRIPT" ]]; then
    MAINT_OUTPUT=$("$PYTHON" "$MAINTENANCE_SCRIPT" "$EVERGREEN_DIR" 2>&1) || true
    [[ -n "$MAINT_OUTPUT" ]] && log "State maintenance: $MAINT_OUTPUT"
fi

# ── Capture pre-run timing state ───────────────────────────────────────
TIMING_BEFORE=""
[[ -f "$TIMING_FILE" ]] && TIMING_BEFORE=$(cat "$TIMING_FILE")

# ── Build task prompt ──────────────────────────────────────────────────
read -r -d '' TASK_PROMPT <<PROMPT || true
You are running the '${EVERGREEN_NAME}' evergreen maintenance cycle autonomously.

Workspace: ${WORKSPACE}
Evergreen directory: ${WORKSPACE}/evergreens/${EVERGREEN_NAME}/

Cross-evergreen context:
Before beginning your cycle, check if a daily briefing file exists:
  ${BRIEFING_FILE}
If it exists, read it to understand what earlier evergreens discovered today.
Also check for a recent weekly synthesis file:
  ${WORKSPACE}/evergreens/weekly-synthesis-*.md
If one exists from the past 7 days, read it for cross-cutting themes and
patterns detected across all evergreens over the past week.
Factor any relevant cross-cutting findings into your analysis.
Do NOT write to the daily briefing file — the runner script handles that
automatically. If you notice cross-cutting patterns, document them in your
AGENDA.md under a "Cross-Evergreen Insights" heading.

Instructions:
1. Read your STATE.md to understand current context and recent history.
2. Read ${WORKSPACE}/ARCHITECTURE.md for the full cycle methodology.
3. If AGENDA.md exists, archive it to agenda-history/ with a date prefix (e.g. ${DATE}-AGENDA.md) before creating a new one.
4. Execute a thorough cycle for '${EVERGREEN_NAME}':
   - Run actual commands to gather real, current data. Do not guess or use stale information.
   - Analyse findings against previous state — identify changes, trends, and risks.
   - Create a concise AGENDA.md with this cycle's findings and 3-5 prioritised next tasks.
   - Update STATE.md with current status, findings summary, and 'Completed Recently' section.
5. Update timing.json with accurate timing:
   {
     "started_at": "<ISO timestamp when you began>",
     "completed_at": "<ISO timestamp when you finish>",
     "duration_seconds": <actual seconds>,
     "status": "completed"
   }
6. If your cycle produces quantitative measurements (sizes, counts, growth
   rates, etc.), append a data point to metrics.json in your evergreen
   directory. Schema:
   {
     "<metric_name>": [
       {"date": "YYYY-MM-DD", "value": <number>},
       ...
     ]
   }
   Keep at most 90 data points per metric (drop the oldest if over). Read
   existing metrics.json at the start of your cycle to compute trends and
   detect anomalies across previous data points.

Time management:
- You have approximately 25 minutes for this cycle.
- Prioritise completing all steps over perfecting any single step.
- If your research phase is taking longer than expected, move on to analysis
  with the data you have — partial coverage is better than no output.
- Always ensure you write AGENDA.md, update STATE.md, and update timing.json
  before finishing, even if your analysis is incomplete. Mark the cycle as
  "partial" in timing.json status if you could not complete all planned work.

Be thorough but focused. Prioritise actionable findings over exhaustive data dumps.
This is an autonomous run — no human is available for clarification.
PROMPT

# ── Reset session history ──────────────────────────────────────────────
# OpenClaw maps all --session-id values for a named agent to a single,
# persistent session key (agent:<name>:main).  Without a reset the conversation
# grows indefinitely and eventually the model treats new cycle prompts as
# continuations of old ones instead of executing fresh tool calls.
# Archive then clear the session store before each run so every cycle starts
# with a clean context window.
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
        [[ -f "$sf" ]] && mv "$sf" "$SESSION_ARCHIVE_DIR/$(basename "$sf").${DATE}" 2>/dev/null || true
    done
    # Reset session index so the gateway creates a fresh session
    [[ -f "$AGENT_SESSION_DIR/sessions.json" ]] && echo '{}' > "$AGENT_SESSION_DIR/sessions.json"
    log "Session store reset (archived previous session)"
fi

# ── Invoke openclaw agent ─────────────────────────────────────────────
if [[ -n "$EVERGREEN_AGENT" ]]; then
    log "Session: $SESSION_ID | Agent: $EVERGREEN_AGENT | Timeout: ${TIMEOUT_SECONDS}s"
else
    log "Session: $SESSION_ID | Agent: (default) | Timeout: ${TIMEOUT_SECONDS}s"
fi

# Build openclaw agent command
AGENT_CMD=("$OPENCLAW" agent)
[[ -n "$EVERGREEN_AGENT" ]] && AGENT_CMD+=(--agent "$EVERGREEN_AGENT")
AGENT_CMD+=(--message "$TASK_PROMPT" --session-id "$SESSION_ID" --timeout "$TIMEOUT_SECONDS" --json)

AGENT_EXIT=0
AGENT_STDERR_FILE=$(mktemp)
trap "rm -f '$AGENT_STDERR_FILE'" EXIT
AGENT_OUTPUT=$("${AGENT_CMD[@]}" 2>"$AGENT_STDERR_FILE") || AGENT_EXIT=$?

# Log stderr (config warnings, errors) separately
if [[ -s "$AGENT_STDERR_FILE" ]]; then
    log "Agent stderr:"
    cat "$AGENT_STDERR_FILE" >> "$LOG_FILE"
fi

# Log the full agent output
echo "$AGENT_OUTPUT" >> "$LOG_FILE"

# Extract key info from JSON output if available
if [[ -x "$PYTHON" ]]; then
    SUMMARY=$(echo "$AGENT_OUTPUT" | "$PYTHON" -c "
import sys, json
text = sys.stdin.read()
d = None
try:
    d = json.loads(text)
except json.JSONDecodeError:
    decoder = json.JSONDecoder()
    for i, c in enumerate(text):
        if c == '{':
            try:
                d, _ = decoder.raw_decode(text, i)
                break
            except json.JSONDecodeError:
                continue
if d:
    m = d.get('result', {}).get('meta', {}).get('agentMeta', {})
    model = m.get('model', 'unknown')
    provider = m.get('provider', 'unknown')
    dur = d.get('result', {}).get('meta', {}).get('durationMs', 0)
    stop = d.get('result', {}).get('meta', {}).get('stopReason', 'unknown')
    payloads = d.get('result', {}).get('payloads', [])
    text_len = sum(len(p.get('text', '')) for p in payloads)
    print(f'Model: {provider}/{model} | Duration: {dur/1000:.1f}s | Stop: {stop} | Response: {text_len} chars')
else:
    print('(could not parse JSON output)')
" 2>/dev/null) || SUMMARY="(no JSON summary)"
    log "Agent result: $SUMMARY"
fi

# ── Check for incomplete agent session ────────────────────────────────
if [[ -x "$PYTHON" ]]; then
    STOP_REASON=$(echo "$AGENT_OUTPUT" | "$PYTHON" -c "
import sys, json
text = sys.stdin.read()
d = None
try:
    d = json.loads(text)
except json.JSONDecodeError:
    decoder = json.JSONDecoder()
    for i, c in enumerate(text):
        if c == '{':
            try:
                d, _ = decoder.raw_decode(text, i)
                break
            except json.JSONDecodeError:
                continue
if d:
    print(d.get('result', {}).get('meta', {}).get('stopReason', 'unknown'))
else:
    print('unknown')
" 2>/dev/null) || STOP_REASON="unknown"

    if [[ "$STOP_REASON" == "toolUse" ]]; then
        log "WARN: Agent session ended mid-tool-call (stopReason=toolUse) — cycle likely incomplete"
    elif [[ "$STOP_REASON" == "error" ]]; then
        log "WARN: Agent session ended with model error (stopReason=error)"
    fi
fi

# ── Extract response preview for log ──────────────────────────────────
if [[ -x "$PYTHON" ]]; then
    SNIPPET=$(echo "$AGENT_OUTPUT" | "$PYTHON" -c "
import sys, json
text = sys.stdin.read()
d = None
try:
    d = json.loads(text)
except json.JSONDecodeError:
    decoder = json.JSONDecoder()
    for i, c in enumerate(text):
        if c == '{':
            try:
                d, _ = decoder.raw_decode(text, i)
                break
            except json.JSONDecodeError:
                continue
if d:
    payloads = d.get('result', {}).get('payloads', [])
    text = ' '.join(p.get('text', '') for p in payloads)
    preview = text[:300].replace('\n', ' ').strip()
    if len(text) > 300:
        preview += '...'
    print(preview if preview else '(no preview available)')
else:
    print('(no preview available)')
" 2>/dev/null) || SNIPPET=""
    [[ -n "$SNIPPET" && "$SNIPPET" != "(no preview available)" ]] && log "Preview: $SNIPPET"
fi

# ── Verify completion & validate output ────────────────────────────────
FAILED=0
FAIL_REASON=""

if [[ "$AGENT_EXIT" -ne 0 ]]; then
    log "FAIL: openclaw agent exited with code $AGENT_EXIT"
    FAILED=1
    FAIL_REASON="Agent exited with code $AGENT_EXIT"
fi

if [[ "$FAILED" -eq 0 ]]; then
    TIMING_AFTER=""
    [[ -f "$TIMING_FILE" ]] && TIMING_AFTER=$(cat "$TIMING_FILE")

    if [[ "$TIMING_BEFORE" == "$TIMING_AFTER" ]]; then
        log "WARN: timing.json unchanged — agent may not have completed the full cycle"
    fi

    if ! validate_output; then
        FAILED=1
        FAIL_REASON="Post-run validation failed"
    fi
fi

if [[ "$FAILED" -ne 0 ]]; then
    rollback_from_backup
    send_failure_alert "$FAIL_REASON"
    exit 1
fi

# ── Update dashboard ──────────────────────────────────────────────────
DASHBOARD_SCRIPT="$WORKSPACE/scripts/update_evergreen_dashboard.py"
if [[ -f "$DASHBOARD_SCRIPT" ]]; then
    log "Updating dashboard..."
    if "$PYTHON" "$DASHBOARD_SCRIPT" 2>>"$LOG_FILE"; then
        log "Dashboard updated successfully"
    else
        log "WARN: Dashboard update failed (non-fatal)"
    fi
else
    log "WARN: Dashboard script not found at $DASHBOARD_SCRIPT"
fi

# ── Fix raw file:// links in dashboard ────────────────────────────────
LINK_FIXER="$WORKSPACE/scripts/fix-markdown-links.js"
if [[ -f "$LINK_FIXER" ]] && command -v node &>/dev/null; then
    node "$LINK_FIXER" 2>>"$LOG_FILE" || log "WARN: Markdown link fixer failed (non-fatal)"
fi

# ── Append findings to daily briefing ──────────────────────────────────
# Extract key findings from AGENDA.md so later evergreens get substantive
# cross-cutting context, not just a completion stub.
AGENDA_FILE="$EVERGREEN_DIR/AGENDA.md"
BRIEFING_SUMMARY=""

if [[ -f "$AGENDA_FILE" ]]; then
    # Try "Cycle Summary" first (most concise), then "Research Findings"
    for SECTION in "Cycle Summary" "Research Findings"; do
        BRIEFING_SUMMARY=$(sed -n "/^## ${SECTION}/,/^## /{
            /^## ${SECTION}/d
            /^## /d
            /^---$/d
            p
        }" "$AGENDA_FILE" | sed '/^[[:space:]]*$/{ N; /^\n[[:space:]]*$/d; }' | head -20)
        [[ -n "$(echo "$BRIEFING_SUMMARY" | tr -d '[:space:]')" ]] && break
        BRIEFING_SUMMARY=""
    done
fi

{
    echo ""
    echo "## ${EVERGREEN_NAME} ($(date +%H:%M))"
    echo ""
    if [[ -n "$BRIEFING_SUMMARY" ]]; then
        echo "$BRIEFING_SUMMARY"
    else
        echo "_Completed. No structured summary found in AGENDA.md._"
    fi
    echo ""
    echo "_Full details: evergreens/${EVERGREEN_NAME}/AGENDA.md_"
    echo ""
} >> "$BRIEFING_FILE"
log "Appended findings to daily briefing: $BRIEFING_FILE"

# ── Cleanup old backups, briefings, and archived sessions ──────────────
find "$BACKUP_DIR" -name "*.pre-*" -mtime +7 -delete 2>/dev/null || true
find "$WORKSPACE/evergreens" -maxdepth 1 -name "daily-briefing-*.md" -mtime +14 -delete 2>/dev/null || true
[[ -d "$AGENT_SESSION_DIR/archive" ]] && find "$AGENT_SESSION_DIR/archive" -type f -mtime +14 -delete 2>/dev/null || true

log "SUCCESS: $EVERGREEN_NAME cycle completed"
exit 0
