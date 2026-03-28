# HEARTBEAT.md Template

**Copy this to your workspace root and customize for your deployment.**
**If you used `deploy.sh`, this was already copied as `HEARTBEAT.md`.**

---

~~~markdown
# HEARTBEAT.md

## Memory Capture (CRITICAL - Every Heartbeat)

This step MUST run every heartbeat to capture active conversation context.

```bash
# cd to workspace root first (all paths are relative to workspace)
# Replace $WORKSPACE with your actual workspace path (e.g., ~/.openclaw/workspace)
cd $WORKSPACE
source .venv/bin/activate
source .memory_env

# Auto-detect current session user and save to Redis
python3 memory/scripts/save_current_session_memory.py
```

### What This Does

- Finds the most recent session JSONL file
- Extracts USER_ID from session metadata or message context
- Saves ALL conversation turns to Redis buffer (`mem:<user_id>`)
- Updates state file for turn tracking

**Expected output:**
```
✅ Saved 42 turns to Redis (mem:<user>)
   State updated to turn 42
```

### Fallback: Manual User ID

If auto-detection fails, specify user explicitly:
```bash
python3 memory/scripts/save_mem.py --user-id <user>
```

---

## Check for Evergreen Triggers

Evergreen programs can request an on-demand run by creating a `.run_requested` file in their directory (e.g., `touch evergreens/system-health/.run_requested`). This is an **optional on-demand trigger mechanism** — no action is needed during initial setup. These files are created at runtime when an evergreen wants to request an out-of-schedule run. See [docs/OPERATIONAL-GUIDE.md](docs/OPERATIONAL-GUIDE.md) for implementation details.

Check for these triggers during heartbeat:

```bash
ls evergreens/*/.run_requested 2>/dev/null || echo "No triggers"
```

If triggers found, process them:
```bash
python3 scripts/run-single-evergreen.py --evergreen <name>
```

---

## Check for Notifications

The `notifications/` directory is populated at runtime by scripts that need to alert the user (e.g., evergreen failures, security findings). It may not exist until the first notification is created. Each notification is a JSON file with `type`, `source`, `message`, and `timestamp` fields. See [docs/HEARTBEAT-MEMORY-INTEGRATION.md](docs/HEARTBEAT-MEMORY-INTEGRATION.md) for full heartbeat integration guidance.

```bash
ls notifications/*.json 2>/dev/null || echo "No notifications"
```

Process any pending notifications.

---

## Reply

If nothing needs attention:
```
HEARTBEAT_OK
```

If something needs attention, respond with details.
~~~

---

## Customization Notes

1. **Paths are workspace-relative** — commands assume `cd $WORKSPACE` at the top. If your workspace is at a non-standard location, adjust the `cd` command.
2. **Adjust memory scripts** if you use a different memory system
3. **Add custom checks** for your specific use case (emails, calendar, etc.)

## Scheduling

Heartbeat frequency is configured in your agent's settings:

```json
{
  "heartbeat": {
    "interval_minutes": 30
  }
}
```

**Recommended:** 30 minutes for active session capture without excessive token usage.

---

**For full documentation:** See [`docs/HEARTBEAT-MEMORY-INTEGRATION.md`](../docs/HEARTBEAT-MEMORY-INTEGRATION.md)
