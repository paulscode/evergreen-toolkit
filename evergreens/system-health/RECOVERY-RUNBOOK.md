<!-- EXAMPLE: Recovery procedures shown here are illustrative.
     Customize service names, ports, and paths for your deployment. -->

# Recovery Runbook

## Service Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw Gateway                        │
│                    (Node.js Application)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Redis   │    │  Qdrant  │    │  Ollama  │
    │  :6379   │    │  :6333   │    │  :11434  │
    └──────────┘    └──────────┘    └──────────┘
```

### Required Services
| Service | Port | Purpose | Auto-Start |
|---------|------|---------|------------|
| Redis | 6379 | Memory buffer, caching | System service |
| Qdrant | 6333 | Vector database | Docker/manual |
| Ollama | 11434 | Local LLM inference | System service |

### Optional Services
| Service | Port | Purpose |
|---------|------|---------|
| *(Add deployment-specific services here, e.g., remote GPU host for Ollama)* | | |

---

## Recovery Procedures

### Gateway Not Running

**Symptoms:** No response to messages, health check fails

**Diagnosis:**
```bash
pgrep -f "openclaw gateway"
systemctl --user status openclaw
```

**Recovery:**
```bash
# Try graceful restart
openclaw gateway restart

# If that fails, kill and restart
pkill -f "openclaw gateway"
openclaw gateway start

# Check logs
tail -100 ~/.openclaw/logs/gateway.log
```

### Redis Not Responding

**Symptoms:** Memory save errors, session issues

**Diagnosis:**
```bash
redis-cli ping
systemctl status redis
```

**Recovery:**
```bash
# Start Redis
sudo systemctl start redis

# If data corruption suspected
redis-cli FLUSHALL  # WARNING: Destroys all data
```

### Qdrant Not Responding

**Symptoms:** Memory search errors, collection not found

**Diagnosis:**
```bash
curl http://localhost:6333/healthz
docker ps | grep qdrant
```

**Recovery:**
```bash
# If using Docker
docker start qdrant

# If running manually
cd ~/.openclaw && ./qdrant &

# Recreate collections if missing
# See: memory/scripts/curate_memories.py
# It will auto-create the collection on first run
```

### Memory Collections Missing

**Symptoms:** Health check shows "missing" collections

**Recovery:**
```bash
# Check Qdrant is running
curl http://localhost:6333/collections

# Re-run curator to create true_recall
source .venv/bin/activate
source .memory_env
python3 memory/scripts/curate_memories.py --user-id <user1>

# Re-run backup to create <agent>-memories
python3 memory/scripts/cron_backup.py --user-id <user1>
```

### Backup Restore

**Symptoms:** Data loss, need to recover from backup

**Recovery:**
```bash
# Find latest backup
ls -lt /backup/openclaw/openclaw-*.tar.gz | head -1

# Extract to temporary location
mkdir -p /tmp/openclaw-restore
tar -xzf /backup/openclaw/openclaw-20090103.tar.gz -C /tmp/openclaw-restore

# Restore specific files
cp -r /tmp/openclaw-restore/.openclaw/qdrant-storage ~/.openclaw/

# Or full restore (WARNING: Overwrites current)
# cp -r /tmp/openclaw-restore/.openclaw ~/.openclaw/
```

### Cron Jobs Not Running

**Symptoms:** No memory curation, no backups

**Diagnosis:**
```bash
crontab -l
grep CRON /var/log/syslog | tail -20
```

**Recovery:**
```bash
# Re-add cron jobs
crontab -l > /tmp/cron-backup.txt

# Add missing jobs (see config/crontab.sample for full list)
crontab -e
```

### Remote GPU Unreachable

<!-- OPTIONAL: Remove this section if you don't use a remote GPU. -->

**Symptoms:** Local model tasks fail, timeout errors

**Diagnosis:**
```bash
curl -s --connect-timeout 5 http://<your-gpu-host>:<port>/api/tags  # CUSTOMIZE: your GPU host
```

**Recovery:**
```bash
# If unreachable, fall back to cloud models
# Update .memory_env or environment variables
export OLLAMA_HOST=http://127.0.0.1:11434

# Or in scripts, check availability and fall back
if ! curl -s --connect-timeout 5 http://<your-gpu-host>:<port>/health > /dev/null; then  # CUSTOMIZE: your GPU host
    echo "Remote GPU unavailable, using cloud"
    # Fall back to cloud model
fi
```

---

## Health Check Locations

| Check | Command |
|-------|---------|
| Full health | `scripts/health_check.sh` |
| Gateway | `pgrep -f "openclaw gateway"` |
| Redis | `redis-cli ping` |
| Qdrant | `curl http://localhost:6333/healthz` |
| Collections | `curl http://localhost:6333/collections` |
| Disk | `df -h ~/.openclaw` |
| Memory | `free -h` |
| Backups | `ls -lt /backup/openclaw/` |

---

## Emergency Contacts

<!-- Populate with your household contacts during setup.
     These should match the entries in memory/APPROVED-CONTACTS.json. -->

- **<user1>:** +1XXXYYYZZZZ (WhatsApp)
- **<user2>:** +1XXXYYYZZZZ (WhatsApp)
- **System Location:** `~/.openclaw/`
- **Logs:** `~/.openclaw/logs/`
- **Config:** `~/.openclaw/openclaw.json`

---

*Created: 2009-01-02*
*Reference: evergreens/system-health/RECOVERY-RUNBOOK.md*