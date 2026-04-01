# 🔧 Troubleshooting Guide

**Common issues and solutions for Evergreen Toolkit.**

> **Note:** Throughout this guide, `$WORKSPACE` refers to your OpenClaw workspace directory (e.g. `~/.openclaw/workspace`).

**Contents:**
- [Cron & Scheduling Issues](#cron--scheduling-issues)
- [Notification Issues](#notification-issues)
- [Memory System — Ollama / Embedding Issues](#memory-system--ollama--embedding-issues)
- [Evergreen Execution Issues](#evergreen-execution-issues)
- [AI Runner Issues](#ai-runner-issues)

---

## Cron & Scheduling Issues

### Evergreens Don't Run at Scheduled Time

**Most Common Cause:** Using `source .venv/bin/activate` in crontab (doesn't work in cron's minimal environment).

**Symptoms:**
- No logs created at scheduled time
- Evergreens stay in "ready" state
- Manual execution works fine

**Solution:** Use the AI runner script (recommended) or wrapper scripts!

```bash
# ✅ BEST: Uses AI runner with flock locking and agent session
0 4 * * * $WORKSPACE/scripts/evergreen-ai-runner.sh upstream-architecture

# ❌ WRONG: Won't work (source fails in cron)
0 4 * * * cd $WORKSPACE && source .venv/bin/activate && python3 scripts/...
```

**Verify:**

```bash
# Check cron daemon status
systemctl status cron   # or crond on RHEL/CentOS

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Verify scripts are executable
ls -la scripts/*.sh

# Test AI runner manually
./scripts/evergreen-ai-runner.sh system-health
```

---

### Crontab Not Loading

**Symptoms:** `crontab -l` shows old entries or nothing

**Solutions:**

1. **Check crontab syntax:**
   ```bash
   # Validate crontab before installing
   crontab -l > /tmp/test-cron
   # Edit /tmp/test-cron
   crontab /tmp/test-cron  # Should succeed without errors
   ```

2. **Verify cron daemon:**
   ```bash
   # Start if not running
   sudo systemctl start cron
   sudo systemctl enable cron
   ```

3. **Check PATH in crontab:**
   ```bash
   # First line of crontab should set PATH
   crontab -l | head -5
   ```

---

## Notification Issues

### Status Messages Not Arriving

**Symptoms:** Evergreens run but you don't receive WhatsApp/Telegram messages

**Check:**

```bash
# Verify OpenClaw channels
openclaw channels list

# Test notification manually
openclaw message send --target +11234567890 --message "Evergreen test"

# Check final check log
tail -30 logs/evergreen-final-check.log
```

**Solutions:**

1. **Channel not configured:**
   ```bash
   # Check openclaw.json
   cat ~/.openclaw/openclaw.json | grep -A 5 '"channels"'
   
   # Configure your channel (WhatsApp, Telegram, etc.)
   # See: https://docs.openclaw.ai/gateway/configuration
   ```

2. **Wrong phone number:**
   ```bash
   # Edit final-check-wrapper.sh or pass correct number
   python3 scripts/evergreen-final-check.py --force --phone-number "+11234567890"
   ```

3. **OpenClaw not running:**
   ```bash
   # Check gateway status
   openclaw health
   
   # Restart if needed
   openclaw gateway restart
   ```

---

### Notification Contains Errors

**Symptoms:** Message shows "openclaw command not found" or similar

**Solutions:**

1. **Add OpenClaw to PATH in crontab:**
   ```bash
   # Add to top of crontab
   PATH=/home/youruser/.nvm/versions/node/vXX.X.X/bin:/usr/local/bin:/usr/bin:/bin
   # Replace vXX.X.X with your installed Node.js version (run: node --version)
   ```

2. **Use absolute path to openclaw:**
   ```bash
   # Find openclaw location
   which openclaw
   
   # Update evergreen-final-check.py if needed
   ```

---

## Memory System — Ollama / Embedding Issues

### Ollama Not Running

**Symptoms:** Memory curation fails, embedding errors in logs

**Check:**

```bash
# Is Ollama running?
curl -s http://localhost:11434/api/version

# If using remote Ollama, check OLLAMA_URL
echo $OLLAMA_URL
curl -s ${OLLAMA_URL:-http://localhost:11434}/api/version
```

**Solutions:**

1. **Start Ollama:**
   ```bash
   ollama serve &
   ```

2. **If using remote Ollama:** Ensure `OLLAMA_URL` is set in `.memory_env` and the remote host is reachable.

### Embedding Model Not Available

**Symptoms:** `model not found` errors during curation or search

**Check:**

```bash
# List available models
ollama list

# Check if embedding model is pulled
ollama list | grep snowflake-arctic-embed2
```

**Solution:**

```bash
# Pull the required embedding model
ollama pull snowflake-arctic-embed2
```

### Embedding Dimension Mismatch

**Symptoms:** Qdrant rejects vectors, "wrong vector size" errors

**Check:**

```bash
# Check collection vector size
curl -s http://localhost:6333/collections/${QDRANT_COLLECTION} | jq '.result.config.params.vectors.size'

# Compare with model output dimensions (snowflake-arctic-embed2 = 1024)
```

**Solution:** The Qdrant collection vector size must match the embedding model's output dimensions. If they differ, you need to recreate the collection with the correct size or switch to a model that matches. See `memory/settings.md` for recommended models and dimensions.

### Curation Produces No Gems

**Symptoms:** `curate_memories.py` runs but extracts zero gems

**Check:**

```bash
# Is there data in Redis to curate?
redis-cli LLEN mem:<user_id>

# Check curation model is available
ollama list | grep -i qwen
```

**Solutions:**

1. **Empty Redis buffer:** Memory capture may not be running. Check that the heartbeat or `save_mem.py` is writing to Redis.
2. **Model not pulled:** Run `ollama pull <model_name>` for your configured `CURATION_MODEL`.
3. **Confidence threshold too high:** Lower `MIN_CONFIDENCE` in `.memory_env` (default: 0.7).

---

## Evergreen Execution Issues

### Evergreen Won't Start

**Symptoms:** Manual execution fails or hangs

**Check:**

```bash
# Check timing.json for errors
cat evergreens/<name>/timing.json | jq .

# Check logs (AI runner)
tail -50 logs/evergreen-<name>-$(date +%Y%m%d).log

# Check logs (direct executor)
tail -50 logs/evergreen-executor.log

# Check logs (weekly cycle)
tail -50 logs/evergreen-weekly-$(date +%Y%m%d).log

# Manual test run (AI runner — recommended)
./scripts/evergreen-ai-runner.sh <name>

# Manual test run (direct executor)
python3 scripts/run-single-evergreen.py --evergreen <name>
```

**Solutions:**

1. **Python environment issue:**
   ```bash
   # Verify venv exists
   ls -la .venv/bin/python3
   
   # Recreate if needed
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Missing dependencies:**
   ```bash
   # Check requirements
   source .venv/bin/activate
   pip list | grep -E "qdrant|redis|requests"
   
   # Install missing
   pip install qdrant-client redis requests
   ```

3. **Script permissions:**
   ```bash
   chmod +x scripts/*.sh
   chmod +x scripts/*.py
   ```

---

### Evergreen Takes Too Long

**Symptoms:** Cycle runs >1 hour, blocks next evergreen

**Check:**

```bash
# Check STATE.md for current focus
cat evergreens/<name>/STATE.md | grep -A 10 "Current Focus"

# Check AGENDA.md for stuck tasks
cat evergreens/<name>/AGENDA.md | head -40

# Check timing
cat evergreens/<name>/timing.json | jq '{started: .started_at, completed: .completed_at, status: .status}'
```

**Solutions:**

1. **Compact STATE.md** - Archive old completed items
2. **Reduce scope** - Focus on 1-2 experiments per cycle
3. **Skip optional steps** - Temporarily disable extensive research
4. **Check for infinite loops** - Look for repeated tasks in agenda
5. **Increase interval** - Space evergreens further apart in crontab

---

### Evergreen Crashes Mid-Execution

**Symptoms:** Log shows partial completion, timing.json shows "in_progress"

The AI runner automatically backs up STATE.md, AGENDA.md, and timing.json before each run. If the agent fails or output validation fails, files are rolled back automatically.

**Check:**

```bash
# Check the runner log for rollback messages
grep -i "rollback\|validation\|backup\|restored" logs/evergreen-<name>-$(date +%Y%m%d).log

# Check if backup files exist
ls -la evergreens/<name>/.backups/

# Check crash point
tail -100 logs/evergreen-<name>-$(date +%Y%m%d).log | grep -A 5 "FAIL"

# Check if process is still running
ps aux | grep -i evergreen
```

**Solutions:**

1. **If rollback occurred automatically** (check logs for "Restored"):
   Files are already in a consistent state. Simply re-run:
   ```bash
   ./scripts/evergreen-ai-runner.sh <name>
   ```

2. **If manual recovery is needed** (rare — rollback handles most cases):
   ```bash
   # Restore from backup manually
   cp evergreens/<name>/.backups/timing.json.pre-$(date +%Y%m%d) evergreens/<name>/timing.json
   cp evergreens/<name>/.backups/STATE.md.pre-$(date +%Y%m%d) evergreens/<name>/STATE.md
   cp evergreens/<name>/.backups/AGENDA.md.pre-$(date +%Y%m%d) evergreens/<name>/AGENDA.md
   ```

3. **Reset timing.json** (if no backup exists):
   ```bash
   cat > evergreens/<name>/timing.json << 'EOF'
   {
     "_comment": "Reset manually — will be populated by the evergreen runner on next cycle.",
     "started_at": null,
     "completed_at": null,
     "duration_seconds": null,
     "status": "ready"
   }
   EOF
   ```

4. **Check system resources:**
   ```bash
   # Memory pressure?
   free -h
   
   # Disk space?
   df -h
   
   # CPU load?
   uptime
   ```

---

## AI Runner Issues

### Commands Require Approval / Agent Hangs Waiting for Input

**Symptoms:**
- AI runner hangs indefinitely during cron execution
- Manual `openclaw agent` sessions prompt for approval before every shell command
- Log shows no progress after agent session starts
- Evergreen times out without producing output

**Cause:** OpenClaw v2026.3.31+ enables **exec approvals** by default. Every shell command the agent tries to run requires interactive approval — which never comes during unattended cron execution.

**Solution:** Add the exec tool configuration to `~/.openclaw/openclaw.json`:

```json
{
  "tools": {
    "exec": {
      "security": "full",
      "ask": "off"
    }
  }
}
```

Then restart the OpenClaw gateway:

```bash
openclaw gateway restart
```

**Verify the fix:**

```bash
# Quick test — agent should execute this without prompting for approval
openclaw agent --message "Run: echo hello world" --json

# Or run the preflight check (v1.1.0+)
python3 scripts/preflight-check.py
```

> **Note:** The `approvals.exec.enabled` key in openclaw.json controls approval *routing* to notification channels — it does NOT control the approval gate itself. The `exec-approvals.json` file manages a per-command allowlist but requires `tools.exec.security: "allowlist"` to take effect. For fully autonomous operation, `tools.exec.security: "full"` with `tools.exec.ask: "off"` is the correct configuration.

> **Security alternative:** If unrestricted shell access is a concern, use `"security": "allowlist"` with `"ask": "on-miss"` and pre-populate `~/.openclaw/exec-approvals.json` with commands your evergreens need. This requires more setup but limits the agent to approved commands only.

---

### Gateway Health Check Fails

**Symptoms:** AI runner logs show "Gateway health check failed" warning

**Check:**

```bash
# Test gateway manually
openclaw health

# Check if gateway is running
curl -s http://127.0.0.1:18789/health
```

**Solutions:**

1. **Start gateway:**
   ```bash
   openclaw gateway start
   ```

2. **Check model availability:**
   ```bash
   openclaw models list
   ```

3. **Note:** The AI runner warns but doesn't abort if the gateway is down — `openclaw agent` can fall back to embedded mode.

---

### AI Runner Lock Contention

**Symptoms:** AI runner exits immediately with "Another instance is running"

**Check:**

```bash
# Check for stale lock files (in your workspace directory)
ls -la $WORKSPACE/.evergreen-*.lock

# Check if any evergreen process is actually running
ps aux | grep evergreen
```

**Solutions:**

1. **If no process is running, the lock is stale:**
   ```bash
   # flock auto-releases on process exit, but if the system crashed:
   rm $WORKSPACE/.evergreen-<name>.lock
   ```

2. **If a process is genuinely stuck:**
   ```bash
   # Find and kill it
   ps aux | grep "evergreen-ai-runner" | grep -v grep
   kill <PID>
   ```

---

### AI Runner Timeout

**Symptoms:** Agent session times out before completing the cycle

**Solutions:**

1. **Increase timeout:**
   ```bash
   EVERGREEN_TIMEOUT=2400 ./scripts/evergreen-ai-runner.sh upstream-architecture
   ```

2. **Check which step is slow:**
   ```bash
   # Review the log for the last run
   tail -100 logs/evergreen-<name>-$(date +%Y%m%d).log
   ```

---

### Evergreen Appears Hung or Stuck

**Symptoms:** An evergreen process is running (or its lock file exists) but producing no output for an extended period. The log file stops growing.

**Diagnosis:**

1. **Check if the process is still running:**
   ```bash
   ps aux | grep "evergreen\|openclaw agent" | grep -v grep
   ```

2. **Check if a lock file is stale:**
   ```bash
   # Lock files are at $WORKSPACE/.evergreen-<name>.lock
   ls -la ~/.openclaw/workspace/.evergreen-*.lock
   # If the file exists but no matching process is running, the lock is stale
   ```

3. **Check the log for the last activity:**
   ```bash
   tail -20 logs/evergreen-<name>-$(date +%Y%m%d).log
   ```

**Solutions:**

1. **Kill a stuck process:**
   ```bash
   # Find the PID
   ps aux | grep "evergreen-ai-runner.*<name>" | grep -v grep
   # Kill it
   kill <PID>
   ```

2. **Remove a stale lock file** (only if no matching process is running):
   ```bash
   rm ~/.openclaw/workspace/.evergreen-<name>.lock
   ```

3. **Re-run the evergreen:**
   ```bash
   ./scripts/evergreen-ai-runner.sh <name>
   ```

**Prevention:** The AI runner uses `flock` with a timeout, so lock contention normally resolves automatically. Stuck processes are most often caused by an unresponsive LLM API or network issues. Check your LLM provider's status page if this happens repeatedly.

---

### AI Runner Validation Failure / Automatic Rollback

**Symptoms:** Log shows "VALIDATION FAIL" or "Restoring from pre-run backup"

The AI runner validates output files after each agent run. Validation failures trigger automatic rollback and (optionally) a notification.

**Check:**

```bash
# Review validation messages
grep -i "validation\|rollback\|restored\|backup" logs/evergreen-<name>-$(date +%Y%m%d).log

# Check current state of output files
cat evergreens/<name>/timing.json | python3 -m json.tool
wc -l evergreens/<name>/AGENDA.md evergreens/<name>/STATE.md

# Check backup files
ls -la evergreens/<name>/.backups/
```

**Common causes:**

1. **Agent didn't update timing.json:** Re-run the evergreen. The task prompt instructs the agent to always update timing.json.

2. **Agent wrote empty AGENDA.md or STATE.md:** This usually indicates the agent encountered an error during research. Check the full log for clues.

3. **timing.json has wrong status:** The validator accepts `completed` or `partial`. If the agent writes another status, validation fails.

**Solutions:**

1. **Re-run** — most validation failures are transient:
   ```bash
   ./scripts/evergreen-ai-runner.sh <name>
   ```

2. **If notification didn't arrive** — check that `EVERGREEN_NOTIFY_TARGET` is set and your messaging channel is configured in `openclaw.json`:
   ```bash
   openclaw channels list
   openclaw message send --target <your-target> --message "test"
   ```

---

### AI Runner Produces Low-Quality Output

**Symptoms:** AGENDA.md has placeholder content instead of real data

**Solutions:**

1. **Verify the agent has tool access:**
   ```bash
   openclaw agent --message "Run: echo hello world" --json
   ```

2. **Check model configuration:**
   ```bash
   openclaw models list
   # Ensure a capable model is set (not a tiny local model)
   ```

3. **Test with a simpler evergreen first:**
   ```bash
   ./scripts/evergreen-ai-runner.sh system-health
   # system-health is the fastest/simplest
   ```

---

### AI Runner Returns Summary Instead of Executing Cycle

**Symptoms:**
- All evergreens report "Did not run today" in the final check
- Logs show the agent responded with a text summary of *yesterday's* results instead of running tools
- `timing.json` is unchanged (stale timestamp from the previous day)
- Log contains `WARN: timing.json unchanged` and `VALIDATION FAIL`

**Cause:** OpenClaw maps all `--session-id` values for a named agent to a single persistent session key (`agent:<name>:main`). Without a session reset, the conversation history accumulates across days. Eventually the model sees so much context from prior successful runs that it treats new cycle prompts as continuations — replying with a summary rather than executing fresh tool calls.

This typically manifests after 5–7 days of continuous operation (500+ messages, 60k+ input tokens).

**Solution:** The runner script (`evergreen-ai-runner.sh`) includes a session reset step that archives and clears the session store before each run. If you're running an older version of the script without this step, update it from the latest toolkit.

To manually clear an accumulated session:

```bash
# Find the agent session directory
# (replace 'evergreen' with your EVERGREEN_AGENT name, or 'main' if unset)
AGENT_SESSION_DIR="$HOME/.openclaw/agents/evergreen/sessions"

# Archive and reset
mkdir -p "$AGENT_SESSION_DIR/archive"
mv "$AGENT_SESSION_DIR"/*.jsonl "$AGENT_SESSION_DIR/archive/" 2>/dev/null
echo '{}' > "$AGENT_SESSION_DIR/sessions.json"
```

**Prevention:** Keep `evergreen-ai-runner.sh` up to date. The session reset runs automatically before each agent invocation.

---

## Memory System Issues

### True Recall Not Curating

**Symptoms:** Qdrant `true_recall` collection stays empty

**Check:**

```bash
# Check Redis buffer
redis-cli KEYS "mem:*"

# Check Qdrant collection
curl http://localhost:6333/collections/true_recall

# Check curation log
tail -30 logs/true-recall.log
```

**Solutions:**

1. **Verify .memory_env:**
   ```bash
   cat .memory_env
   # Should have REDIS_HOST, QDRANT_URL, etc.
   ```

2. **Check Redis connectivity:**
   ```bash
   redis-cli ping  # Should return PONG
   ```

3. **Check Qdrant:**
   ```bash
   curl http://localhost:6333/  # Should return JSON
   ```

---

### Jarvis Backup Not Clearing Redis

**Symptoms:** `mem:user_id` keeps growing

**Check:**

```bash
# Check backup log
tail -30 logs/memory-backup.log

# Check Qdrant collection
curl http://localhost:6333/collections/<agent>-memories/points/scroll
```

**Solutions:**

1. **Verify backup script ran:**
   ```bash
   python3 memory/scripts/cron_backup.py --user-id <user-id>
   ```

2. **Check for errors:**
   ```bash
   # Manual run with verbose output
   source .venv/bin/activate
   source .memory_env
   python3 memory/scripts/cron_backup.py --user-id <user-id> --verbose
   ```

---

## Dashboard Issues

### Dashboard Not Updating

**Symptoms:** Evergreens complete but `evergreens/DASHBOARD.html` doesn't change

**Check:**

```bash
# Check if update script exists
ls -la scripts/update_evergreen_dashboard.py

# Run manually
python3 scripts/update_evergreen_dashboard.py

# Check for errors in the per-evergreen logs
tail -20 logs/evergreen-*-$(date +%Y%m%d).log | grep -i dashboard
```

**Solutions:**

1. **Manual regeneration:**
   ```bash
   python3 scripts/update_evergreen_dashboard.py
   ```

2. **Check script permissions:**
   ```bash
   chmod +x scripts/update_evergreen_dashboard.py
   ```

3. **Verify HTML write permissions:**
   ```bash
   ls -la evergreens/DASHBOARD.html
   chmod 644 evergreens/DASHBOARD.html
   ```

4. **Verify the runner calls it:**
   The dashboard is updated automatically by `evergreen-ai-runner.sh` after each
   successful cycle. Check the runner script for the "Update dashboard" section.
   If the step is missing, add it after the post-run validation block.

---

## Diagnostic Commands

### Quick Health Check

```bash
# All-in-one diagnostic
echo "=== Evergreen Health Check ==="
echo ""
echo "1. Cron daemon:"
systemctl status cron | grep -E "Active|Loaded"
echo ""
echo "2. Crontab entries:"
crontab -l | grep evergreen | head -10
echo ""
echo "3. Recent executions:"
tail -20 logs/evergreen-executor.log | grep -E "Starting|completed|ERROR"
echo ""
echo "4. Evergreen status:"
for dir in evergreens/*/; do
  name=$(basename $dir)
  status=$(cat $dir/timing.json | jq -r '.status')
  echo "  $name: $status"
done
echo ""
echo "5. Notification channel:"
openclaw channels list | grep -E "linked|enabled"
```

### Log Analysis

```bash
# Find errors in last 24 hours
grep -r "ERROR\|FAILED" logs/evergreen*.log | tail -20

# Check execution times
grep "Starting" logs/evergreen-executor.log | tail -10

# Find crashes
grep -B 5 "exit code" logs/evergreen*.log
```

---

## Getting Help

### Before Asking for Help

Gather this information:

1. **System info:**
   ```bash
   python3 --version
   openclaw --version
   timedatectl
   ```

2. **Cron status:**
   ```bash
   crontab -l
   systemctl status cron
   ```

3. **Recent logs:**
   ```bash
   tail -50 logs/evergreen-executor.log
   tail -50 logs/evergreen-final-check.log
   ```

4. **Evergreen state:**
   ```bash
   for dir in evergreens/*/; do
     echo "=== $(basename $dir) ==="
     cat $dir/timing.json | jq '{status: .status, started: .started_at}'
   done
   ```

### Where to Ask

- **OpenClaw Discord:** https://discord.com/invite/clawd
- **GitHub Issues:** https://github.com/paulscode/evergreen-toolkit/issues
- **ClawHub:** https://clawhub.com

---

## Memory System Performance

### Qdrant Collection Growing Large

**Symptoms:** Slow semantic search, high disk usage from Qdrant storage.

**Solutions:**
- Check collection size: `curl -s http://localhost:6333/collections/<agent>-memories | python3 -m json.tool | grep points_count`
- Archive old memories: Export vectors older than N months using Qdrant's scroll API, then delete them from the active collection
- Optimize vector indexing: Qdrant automatically builds HNSW indexes; ensure `on_disk` is enabled for large collections
- Consider separate collections per year if memory exceeds 100K points

### Redis Memory Pressure

**Symptoms:** Redis `OOM` errors, `save_mem.py` failures, slow heartbeat captures.

**Solutions:**
- Check memory: `redis-cli INFO memory | grep used_memory_human`
- The memory buffer should be small (cleared nightly by Jarvis backup at 3:00 AM)
- If Redis is accumulating data, verify `cron_backup.py` is running and clearing keys
- Set `maxmemory` in Redis config if other services share the instance
- Reduce `REDIS_TTL_HOURS` in `.memory_env` (default: 24)

### Slow Embedding Generation

**Symptoms:** `curate_memories.py` or `cron_backup.py` takes a long time, Ollama at 100% CPU.

**Solutions:**
- Check Ollama model size: `ollama list` — smaller embedding models are faster
- Ensure Ollama isn't swapping: if `snowflake-arctic-embed2` is too heavy, try a lighter model
- Batch size: most memory scripts process one user at a time; space cron jobs 5 minutes apart to avoid overlap
- GPU acceleration: if available, ensure Ollama is using GPU (`ollama ps` shows VRAM usage)

---

## PARA Promotion Issues

### Facts Not Appearing in PARA

**Symptom:** Weekly cycle runs but `memory/para/<user>/items.json` doesn't grow.

**Possible causes:**
1. **`seed_para.py` not run** — New installations must seed the PARA structure first:
   ```bash
   python3 scripts/seed-evergreens.py  # creates PARA directories and initial files
   ```
2. **No promotion candidates** — The weekly synthesis writes candidates to `## PARA Candidates` in the synthesis file, but the household-memory evergreen must review and approve them on a subsequent cycle.
3. **Missing curator prompt** — Check that `memory/curator_prompts/<user>.md` exists for each user.

### Contradictions in PARA

**Symptom:** `review-queue.md` grows but contradictions aren't resolved.

**Fix:** The household-memory evergreen reviews `review-queue.md` during its daily cycle. If it's not clearing, check:
- Household-memory evergreen is running (`timing.json` shows recent cycles)
- The curation prompt includes contradiction resolution guidance

---

## Weekly Synthesis Issues

### Weekly Cycle Produces Empty Synthesis

**Symptom:** `evergreens/weekly-synthesis-YYYYMMDD.md` exists but has minimal content.

**Possible causes:**
1. **No agenda-history files** — The weekly cycle reads recent agenda-history; if daily cycles haven't archived any, there's nothing to analyze. Verify: `find evergreens/*/agenda-history -name "*.md" -mtime -7`
2. **LLM timeout** — Check `logs/evergreen-weekly-*.log` for timeout errors. Increase `WEEKLY_TIMEOUT` in environment if needed (default: 5400 seconds).
3. **Shell-side fallback only** — If the LLM step fails, the shell-side `weekly-synthesis.py` produces a keyword-based summary as fallback. Check the log for `WARN: weekly-synthesis.py failed`.

### Weekly Cycle STATE.md Corruption

If the weekly cycle is interrupted mid-write, STATE.md files may be left in a partial state. The weekly cycle now creates backups before modifying STATE.md files — check for `STATE.md.weekly-backup-YYYYMMDD` files in each evergreen directory and restore if needed.

---

## Prevention Checklist

To avoid common issues:

- [ ] Use AI runner (`evergreen-ai-runner.sh`) or wrapper scripts, never `source` in crontab
- [ ] OpenClaw gateway running (`openclaw health`)
- [ ] All paths are absolute (no `~` or relative paths)
- [ ] Scripts are executable (`chmod +x scripts/*.sh`)
- [ ] Notification channel tested and working
- [ ] Cron daemon running and enabled
- [ ] Timezone set correctly on system
- [ ] Logs directory exists and writable
- [ ] Virtual environment activated for manual tests
- [ ] .memory_env file configured correctly
- [ ] Evergreen STATE.md files have reasonable scope

---

## Log Management

Evergreen logs accumulate in `logs/` over time. Each AI runner run creates a daily log file (e.g., `evergreen-system-health-20260307.log`).

**Automatic cleanup:** The sample crontab (`config/crontab.sample`) includes a weekly job that deletes log files older than 30 days:

```bash
0 0 * * 0 find $WORKSPACE/logs/ -name "*.log" -mtime +30 -delete
```

**Manual cleanup:**

```bash
# Check total log size
du -sh logs/

# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete

# Keep only the last 7 days
find logs/ -name "*.log" -mtime +7 -delete
```

---

## Migrating or Renaming an Agent

If you need to switch your agent's name (e.g., from "Eve" to "Friday"):

1. **Update `.memory_env`:** Change `AGENT_NAME` and `QDRANT_COLLECTION` to the new name
2. **Rename Qdrant collections:** Use the Qdrant API to create new collections and migrate vectors, or start fresh with `init_memory_collections.py`
3. **Re-run name customization:** Follow [NAME-CUSTOMIZATION.md](NAME-CUSTOMIZATION.md) with the new agent name
4. **Update crontab:** If your cront entries reference the old agent name, update them
5. **Verify:** Run `python3 scripts/validate-customization.py` to ensure no old references remain

> **Note:** Starting fresh (new collections) is simpler than migrating. Old memories in Qdrant are preserved in the original collection and can still be searched if needed.
