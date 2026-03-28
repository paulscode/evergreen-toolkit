<!-- EXAMPLE: This file contains illustrative content showing the format for infrastructure
     optimization tracking. Replace entirely with your own infrastructure details,
     or clear and let the system-health evergreen populate it during cycles. -->

# Infrastructure Optimization Plan

## Remote GPU Evaluation

### Available Hardware
- **Host:** `<gpu-host>:<port>` <!-- CUSTOMIZE: your GPU host, or remove if not applicable -->
- **GPU:** <!-- CUSTOMIZE: your GPU specs (e.g. NVIDIA RTX 4090, 24GB vRAM) -->
- **Status:** ⬜ Not yet configured

### Available Models
<!-- CUSTOMIZE: List your locally-available Ollama models.
     Run `ollama list` to see what's installed. Example table: -->
| Model | Size | Use Case |
|-------|------|----------|
| `<model-name>` | — | Complex reasoning, analysis |
| `<model-name>` | — | Code generation, debugging |
| `<model-name>` | — | General purpose |
| `<model-name>` | — | Fast, simple tasks |

### Potential Use Cases for Your Agent

1. **Memory Curation (True Recall)**
   - Currently: `<your-cloud-model>` (cloud API)
   - Alternative: `deepseek-r1:32b` (local)
   - Benefit: Cost savings, privacy
   - Tradeoff: Slower, dependent on network

2. **Sub-Agent Tasks**
   - Currently: Cloud models
   - Alternative: `qwen2.5-coder:32b` for coding tasks
   - Benefit: No API costs
   - Tradeoff: Network latency

3. **Embedding Generation**
   - Currently: `snowflake-arctic-embed2` (local via Ollama)
   - Alternative: Local embedding model
   - Benefit: Privacy, no API costs
   - Tradeoff: Need to set up local embedding

### Cost/Privacy Analysis

| Factor | Cloud | Local GPU |
|--------|-------|-----------|
| Cost per 1M tokens | $0.10-$2.00 | $0 (hardware paid) |
| Latency | 1-3s | 5-15s (network + inference) |
| Privacy | Data sent to API | Fully local |
| Reliability | 99.9% uptime | Depends on network/host |
| Model variety | Unlimited | Limited to installed |

### Recommendation

**Short-term:** Continue using cloud for primary operations (reliability).

**Medium-term:** Route high-volume tasks to local GPU:
- True Recall curation (runs at 2:30 AM, latency doesn't matter)
- Batch embedding generation
- Sub-agent coding tasks

**Implementation:**
1. Add `OLLAMA_URL=http://remote-gpu-host:11435` to `.memory_env`  
   *(Port 11435 is used here to distinguish the remote GPU instance from local Ollama on the default port 11434)*
2. Update `curate_memories.py` to use local model
3. Add fallback to cloud if local fails

---

## Backup Strategy

> **Note:** The table below reflects the initial template state at project setup. All entries show ❌ because no backups are configured yet. After setting up backups (see `RECOVERY-RUNBOOK.md` for procedures), update this table to reflect actual status.

### Current State

| Data | Location | Backed Up? |
|------|----------|------------|
| OpenClaw config | `~/.openclaw/` | ❌ No |
| Workspace | `~/.openclaw/workspace/` | ❌ No |
| Qdrant data | `~/.openclaw/qdrant-storage/` | ❌ No |
| Credentials | `~/.openclaw/credentials/` | ❌ No |
| Redis data | `/var/lib/redis/` (system) | ❌ No |

### Critical Files to Backup

1. **Configuration**
   - `~/.openclaw/openclaw.json`
   - `~/.openclaw/agents/`
   - `~/.openclaw/identity/`

2. **Memory Data**
   - `memory/` (workspace-relative)
   - `~/.openclaw/qdrant-storage/`
   - Redis dump (if persistent)

3. **Credentials** (encrypted!)
   - `~/.openclaw/credentials/`
   - `~/.openclaw/workspace/<your-credential-file>`   <!-- CUSTOMIZE: your credential files -->
   - `~/.openclaw/workspace/<your-api-key-file>`       <!-- CUSTOMIZE: your API key files -->

4. **Custom Skills**
   - `~/.openclaw/workspace/skills/` (custom skills only)

### Backup Strategy Options

#### Option A: Local Backup (Simple)
```bash
# Daily backup to local directory
BACKUP_DIR="/backup/openclaw"
tar -czf $BACKUP_DIR/openclaw-$(date +%Y%m%d).tar.gz \
  --exclude='*.log' \
  --exclude='completions/*' \
  ~/.openclaw/

# Keep last 7 days
find $BACKUP_DIR -name "openclaw-*.tar.gz" -mtime +7 -delete
```

#### Option B: Cloud Backup (Offsite)
- Use `rclone` to sync to cloud storage (S3, B2, etc.)
- Encrypt before upload with `gpg`
- Schedule with cron

#### Option C: Git-based (For Workspace)
- Initialize git repo in the workspace
- Commit daily changes
- Push to private repository
- Exclude sensitive files with `.gitignore`

### Recommended Implementation

**Option 1: Local Backup**
- Daily tarball to `/backup/openclaw`
- 7-day retention
- Run at 4:00 AM (after memory jobs)

**Option 2: Cloud Backup**
- Set up `rclone` with Backblaze B2 or similar
- Encrypt with `gpg --symmetric`
- Upload after local backup

**Option 3: Git for Workspace**
- Initialize git repo
- Commit significant changes
- Push to private GitHub repo

---

## Health Check Script Design

### Purpose
Automated health monitoring and alerting.

### Checks

1. **Service Health**
   - OpenClaw gateway running?
   - Redis responding?
   - Qdrant responding?

2. **Resource Health**
   - Disk usage > 80%?
   - Memory usage > 90%?

3. **Data Health**
   - Memory jobs ran successfully?
   - Qdrant collections accessible?

### Implementation

```bash
#!/bin/bash
# scripts/health_check.sh

# Check OpenClaw
if ! pgrep -f "openclaw" > /dev/null; then
    echo "❌ OpenClaw not running"
    # Could send notification
fi

# Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis not responding"
fi

# Check Qdrant
if ! curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    echo "❌ Qdrant not responding"
fi

# Check disk
DISK_USAGE=$(df -h ~/.openclaw | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️ Disk usage: ${DISK_USAGE}%"
fi
```

### Integration with Scheduled Runs

Add health check to the cron schedule:
```markdown
## System Health Check

Run `scripts/health_check.sh` and report any issues.
```

---

## Implementation Checklist

- [ ] Set up local backup cron job
- [ ] Configure cloud backup (rclone + B2/S3)
- [ ] Create health check script
- [ ] Test restore procedure
- [ ] Document backup/restore process in RECOVERY-RUNBOOK.md

---

*Created: 2009-01-02*
*Reference: evergreens/system-health/STATE.md*