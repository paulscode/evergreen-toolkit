#!/bin/bash
# Evergreen Final Check Wrapper Script for Cron
#
# This wrapper ensures cron can execute the final check reliably by:
# - Using absolute paths (cron doesn't inherit your interactive PATH)
# - Activating the virtual environment properly
# - Passing --force flag to always send status (success or failure)
# - Logging execution with timestamps

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$WORKSPACE/.venv/bin/python3"
LOGFILE="$WORKSPACE/logs/evergreen-final-check.log"

# Ensure log directory exists
mkdir -p "$WORKSPACE/logs"

# Source environment variables (memory config, notification targets, etc.)
[[ -f "$WORKSPACE/.memory_env" ]] && source "$WORKSPACE/.memory_env"

# Log start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting final check..." >> "$LOGFILE"

# Run the final check (with --force to always send status notification)
cd "$WORKSPACE"
"$VENV_PYTHON" "$WORKSPACE/scripts/evergreen-final-check.py" --force >> "$LOGFILE" 2>&1 || EXIT_CODE=$?
EXIT_CODE=${EXIT_CODE:-0}

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Final check completed" >> "$LOGFILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Final check failed with exit code $EXIT_CODE" >> "$LOGFILE"
fi

exit $EXIT_CODE
