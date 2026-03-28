# ⏰ Scheduling Guide

**Configure evergreen and memory scheduling for your timezone.**

---

## Default Schedule (Reference)

All times shown as **local time** — adjust the cron entries for your timezone.

> **Canonical source:** [`config/crontab.sample`](../config/crontab.sample) is the single source of truth for exact cron timing. The table below is a summary for reference.

| Time | Task | Duration | Component |
|------|------|----------|-----------|
| Every 5 min | Session capture (`cron_capture.py`, per user) | — | Memory |
| 2:30 AM | True Recall curation (<user1>) | ~5 min | Memory |
| 2:35 AM | True Recall curation (<user2>) | ~5 min | Memory |
| 3:00 AM | Jarvis backup (<user1>) | ~5 min | Memory |
| 3:05 AM | Jarvis backup (<user2>) | ~5 min | Memory |
| 3:30 AM | Full system backup | ~2 min | Backup |
| 4:00 AM | upstream-architecture | ~30 min | Evergreen |
| 4:30 AM | system-health | ~5 min | Evergreen |
| 5:00 AM | prompt-injection | ~10 min | Evergreen |
| 5:30 AM | household-memory | ~30 min | Evergreen |
| 6:00 AM | **Final check + notification** 📱 | ~1 min | Verification |

**Total maintenance window:** 2:30 AM - 6:00 AM (3.5 hours)  
**Actual work:** ~90 minutes (memory + 4 AI-orchestrated evergreens + final check)

### Weekly Schedule

| Time | Day | Task | Component |
|------|-----|------|-----------|
| 2:00 AM | Sunday | PARA promotion (gems → durable facts) | Memory |
| 6:30 AM | Sunday | Weekly deep-analysis cycle | Evergreen |

> **Notes:**
> - `cron_capture.py` vs heartbeat-driven `save_current_session_memory.py` — see [memory/README.md](../memory/README.md) for a comparison of both capture methods.
> - **Full system backup** (3:30 AM) is user-provided — see the placeholder in [`config/crontab.sample`](../config/crontab.sample).

**Critical ordering:** Memory cron jobs (2:30-3:00 AM) MUST run before evergreens. True Recall must run before Jarvis backup (which clears Redis). Jarvis clears only the specific user's key (`mem:{user_id}`) after that user's backup succeeds — so processing one user won't affect another user's buffer.

> **What happens if the order is wrong?** Jarvis clears the Redis buffer after backing up. If it runs before True Recall, the curated gem extraction gets an empty buffer and produces no gems for that day. Raw backups in Qdrant are still preserved, but the high-salience extraction is lost.

---

## Why This Schedule?

### Staggered Execution (30-minute intervals)

Evergreens run at separate times to:
- **Prevent resource contention** - Each gets full CPU/RAM attention
- **Isolate failures** - One crash doesn't block others
- **Enable debugging** - Clear logs for each evergreen
- **Reduce timeout risk** - No competition for resources

### AI Runner Script (Recommended)

The toolkit provides `evergreen-ai-runner.sh` which spawns a full AI agent session via `openclaw agent`. The agent reads context, runs real commands, analyses results, and writes substantive findings.

#### Model Override (Optional)

By default, the AI runner uses your system's default model. If your default model is lightweight (e.g., a local model) and you want evergreens to use a more capable model for technical accuracy, you can route them to a dedicated named agent:

```bash
# 1. Create a named agent with a specific model
openclaw agents add evergreen --model "provider/model" --workspace "/path/to/workspace"

# 2. Set EVERGREEN_AGENT in your crontab or environment
EVERGREEN_AGENT=evergreen

# 3. Or override per-evergreen inline in crontab
0 4 * * * EVERGREEN_AGENT=heavy-model $WORKSPACE/scripts/evergreen-ai-runner.sh upstream-architecture
```

If `EVERGREEN_AGENT` is unset, the system default model is used — no changes needed for single-model setups.

```bash
# ✅ CORRECT: Uses AI runner — full cognitive cycle
0 4 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh upstream-architecture
```

**What the AI runner does:**
- Acquires a `flock` lock (prevents concurrent runs of the same evergreen)
- Checks OpenClaw gateway health (warns but continues if down — auto-fallback available)
- Backs up STATE.md, AGENDA.md, and timing.json before each run
- Spawns a full AI agent turn via `openclaw agent --json`
- The agent reads STATE.md (and the daily briefing from earlier runs), runs investigative commands, writes AGENDA.md and STATE.md
- Validates output files after completion (timing.json, AGENDA.md, STATE.md)
- On failure or validation error: rolls back files from backup and sends a notification (if `EVERGREEN_NOTIFY_TARGET` is set)
- On success: appends a stub entry to the daily briefing file for later evergreens
- Cleans up old backups (>7 days) and daily briefings (>14 days)
- Logs everything to `logs/evergreen-{name}-{YYYYMMDD}.log`
- Returns exit code 0 (success) or 1 (failure) for cron

**Requirements:**
- OpenClaw installed and on PATH
- OpenClaw gateway running (falls back to embedded mode if not)
- No Python virtual environment needed (uses `openclaw agent` CLI directly)

---

## Timezone Handling

### Use Your System Timezone

Set cron times in your local timezone. Cron uses the system timezone by default:

```bash
# Check your system timezone
timedatectl

# Set timezone if needed
sudo timedatectl set-timezone America/New_York
```

### Adjust for Daylight Saving Time

If your timezone observes DST, remember to adjust:
- **Spring forward** (March): Maintenance runs 1 hour later relative to UTC
- **Fall back** (November): Maintenance runs 1 hour earlier relative to UTC

**Recommendation:** Use cron in system timezone, not UTC, to avoid DST confusion.

> **Warning — Spring Forward Ordering Risk:** If True Recall runs at 2:30 AM and Jarvis at 3:00 AM, during the March spring-forward the 2:00–2:59 AM window is skipped entirely. Cron implementations vary: some skip the job, others run it at 3:00 AM — which means both scripts may fire at the same wall-clock time and race. To avoid this, either (a) schedule memory jobs outside the 2:00–3:00 AM window, or (b) add a `flock` guard so they cannot overlap. The `crontab.sample` template already spaces jobs safely, but verify if you customize the schedule.

---

## Crontab Configuration

### Full Schedule Template

See [`config/crontab.sample`](../config/crontab.sample) for the complete template.

**Key points:**
```bash
# Set PATH explicitly (cron has minimal PATH)
PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin
SHELL=/bin/bash

# Memory jobs (2:30-3:30 AM) - Use absolute paths
30 2 * * * cd $WORKSPACE && $WORKSPACE/.venv/bin/python3 memory/scripts/curate_memories.py --user-id <user1>

# Evergreen jobs (4:00-5:30 AM) - Use AI runner
0 4 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh upstream-architecture

# Final check (6:00 AM)
0 6 * * * $WORKSPACE/scripts/final-check-wrapper.sh
```

### Minimal Schedule (Testing)

If you want to test with minimal scheduling:

```bash
# Just one evergreen, no memory system (for testing)
0 4 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh system-health

# Final check after test
30 4 * * * $WORKSPACE/scripts/final-check-wrapper.sh
```

---

## Notification Configuration

> **Two notification paths exist:**
> 1. **Per-run alerts** (immediate): Set the `EVERGREEN_NOTIFY_TARGET` env var in your crontab. If the AI runner detects a failure or rollback, it sends a notification immediately via `openclaw message send`.
> 2. **End-of-cycle summary** (6:00 AM): `evergreen-final-check.py --phone-number "+11234567890"` sends a single summary after all evergreens should have completed — reporting which succeeded and which failed.

### OpenClaw Message Integration

The final check script sends notifications via OpenClaw's messaging system:

```bash
# Test notification manually
openclaw message send --target +11234567890 --message "Evergreen test"

# Configure your channel in openclaw.json
```

### Supported Channels

- **WhatsApp** - Via OpenClaw WhatsApp channel
- **Telegram** - Via Telegram bot
- **Discord** - Via Discord webhook
- **Slack** - Via Slack webhook

See [OpenClaw documentation](https://docs.openclaw.ai) for channel setup.

### Notification Content

**Success message:**
```
✅ Evergreen Status - 2009-01-03

All evergreens completed successfully!

Status summary:
✅ upstream-architecture: completed (30 min)
✅ system-health: completed (5 min)
✅ prompt-injection: completed (10 min)
✅ household-memory: completed (32 min)

🎉 Everything's running smoothly!
```

**Alert message:**
```
🚨 Evergreen Alert - 2009-01-03

Issues detected:
• system-health: Still running (45 min - possible stall)

Status summary:
✅ upstream-architecture: completed (28 min)
❌ system-health: in_progress
✅ prompt-injection: completed (9 min)
✅ household-memory: completed (31 min)

Next steps:
1. Check logs: tail -100 logs/evergreen-*.log
2. Review timing: cat evergreens/<name>/timing.json | jq
3. Re-run failed evergreen: ./scripts/evergreen-ai-runner.sh <name>
```

---

## Testing Your Schedule

### Manual Test (Before Relying on Cron)

```bash
# Test AI runner execution
./scripts/evergreen-ai-runner.sh system-health

# Check log (per-evergreen daily log)
tail logs/evergreen-system-health-$(date +%Y%m%d).log

# Test final check with notification
./scripts/final-check-wrapper.sh

# Verify notification received
```

### Cron Test (Verify Timing)

```bash
# Schedule a test run 5 minutes from now
# Current time: 2:00 PM, schedule for 2:05 PM
crontab -l > /tmp/test-cron
echo "5 14 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh system-health" >> /tmp/test-cron
crontab /tmp/test-cron

# Wait for execution, check logs
tail -f logs/evergreen-system-health-$(date +%Y%m%d).log

# Remove test entry after verification
crontab -l | grep -v "5 14" | crontab -
```

### Verify Cron Daemon

```bash
# Check cron daemon status
systemctl status cron    # Debian/Ubuntu
systemctl status crond   # RHEL/CentOS

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Verify your crontab is loaded
crontab -l
```

---

## Common Scheduling Issues

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions to scheduling, notification, and execution-time issues.

---

## Production Checklist

Before deploying to production:

- [ ] All paths in crontab are absolute (no `~` or relative paths)
- [ ] Scripts are executable (`chmod +x scripts/*.sh`)
- [ ] OpenClaw gateway running (`openclaw health`)
- [ ] Test notification channel is working
- [ ] Verified timezone is correct
- [ ] Ran manual test of each evergreen via AI runner
- [ ] Confirmed logs are being written
- [ ] Checked cron daemon is running
- [ ] Scheduled test run during business hours first

---

## Appendix: Crontab Quick Reference

```bash
# Minute Hour Day Month Weekday Command
#   0-59  0-23  1-31  1-12   0-7    command

# Examples:
0 4 * * *    # Every day at 4:00 AM
30 2 * * *   # Every day at 2:30 AM
0 4 * * 1    # Every Monday at 4:00 AM
0 4 1 * *    # First day of month at 4:00 AM

# Special schedules:
@daily       # Every day at midnight (0:00 AM)
@hourly      # Every hour at minute 0
@reboot      # On system boot
```
