<!-- EXAMPLE: This STATE.md contains sample data showing the expected format.
     Values are illustrative — your evergreen cycle will update this file
     with real data from your deployment.
     Date convention: All example dates use 2008-2009 era timestamps
     to make them obviously distinguishable from real data.
     Name convention: '<agent>' is a placeholder — replace with your agent's name
     (e.g., 'jarvis', 'friday'). See QUICKSTART.md Step 3. -->

# System Health, Reliability & Disaster Recovery - State

## Status
- Overall Health: 🟢 Healthy
- Last Cycle: 2009-01-03
- Next Cycle: 2009-01-04

## Cycle Timing
- Started At: 2009-01-03T04:30:00Z
- Completed At: 2009-01-03T04:35:00Z
- Duration: ~5 min

## Current Focus
Infrastructure optimization complete. Backup and health check scripts operational.

## System Information
<!-- Auto-discovered on first cycle — example values shown below -->

### Host
- **Hostname:** example-server
- **OS:** Ubuntu 24.04 LTS
- **Node:** v20.11.0
- **Uptime:** Running

### Resources
- **Disk:** 500 GB (42% used)
- **RAM:** 16 GB
- **CPU:** 4 cores

### OpenClaw
- **Version:** 1.2.0
- **Config:** ~/.openclaw/openclaw.json
- **Agent:** <agent> (your configured model)
- **Gateway:** Active

### Connected Services
| Service | Status | Notes |
|---------|--------|-------|
| OpenClaw Gateway | ✅ Active | |
| Redis | ✅ PONG | Fast buffer for memory |
| Qdrant | ✅ Green | Collections: `true_recall`, `<agent>-memories` |
| WhatsApp Gateway | ✅ Connected | (if configured) |
| Email (SMTP) | ✅ Configured | user@example.com |

## Backup & Recovery

### Backup Schedule
| Time | Job | Target |
|------|-----|--------|
| 3:30 AM | Full backup | `/backup/<agent>/` (7-day rotation) |
| 3:00 AM | Jarvis Memory | Qdrant `<agent>-memories` |
| 2:30 AM | True Recall | Qdrant `true_recall` |

### Backup Scripts
- **Health check:** `scripts/health_check.sh`
- **Recovery:** `evergreens/system-health/RECOVERY-RUNBOOK.md`

### Last Backup
- **Date:** 2009-01-02
- **Location:** `/backup/<agent>/`

## Health Checks

### Automated Monitoring
- [x] Health check script (`scripts/health_check.sh`)
- [x] Gateway process check
- [x] Redis connectivity
- [x] Qdrant health
- [x] Collection status
- [x] Disk usage monitoring
- [x] Memory usage monitoring
- [x] Backup freshness check

### Recovery Procedures
- **Runbook:** `evergreens/system-health/RECOVERY-RUNBOOK.md`
- **Covers:** Gateway restart, Redis recovery, Qdrant recovery, backup restore

## Active Experiments
None currently.

## Key Learnings
- 2009-01-02: Example — restore test passed, backup extracts cleanly
- 2009-01-01: Example — cron redirect fails silently if log file doesn't exist

## Research Topics
- [ ] Automated backup strategies
- [ ] Recovery runbooks
- [ ] Service monitoring setup (external)
- [ ] Alert escalation paths

## Blocking Issues
None currently.

## Completed Recently
- [2009-01-02] Example — health check script created with service monitoring

## Next Steps
1. [ ] Run initial system health check
2. [ ] Set up backup strategy for critical files
3. [ ] Create recovery runbooks
4. [ ] Test restore procedure
5. [ ] Set up external monitoring (optional)

*Last updated: 2009-01-03*