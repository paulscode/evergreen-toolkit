<!-- EXAMPLE: Test commands shown here are illustrative.
     Customize for your actual service endpoints and configuration.
     Commands use placeholder values (marked with < >) that must be replaced
     with your deployment-specific values before running. See .memory_env
     and your local config for actual values. -->

# System Health & DR - Tests

## Smoke Tests (run every cycle)
| ID | Test | Command | Expected |
|----|------|---------|----------|
| S01 | Disk space > 20% free | `df -h / \| awk 'NR==2 {print $5}' \| sed 's/%//'` | < 80 |
| S02 | Memory not exhausted | `free \| awk '/Mem:/ {printf "%.0f", $3/$2 * 100}'` | < 90 |
| S03 | OpenClaw process running | `pgrep -f "openclaw" > /dev/null && echo OK \|\| echo "Not running"` | OK |
| S04 | WhatsApp gateway connected | Check heartbeat log or connection status | Connected |
| S05 | Workspace directory exists | `test -d ~/.openclaw/workspace && echo OK` | OK |
| S06 | Qdrant container running | `docker ps --filter name=qdrant --filter status=running -q \| wc -l` | 1 | <!-- CUSTOMIZE: your container name -->
| S07 | Redis reachable | `redis-cli ping` | PONG |

## Regression Tests (run after changes)
| ID | Test | Trigger | Command | Expected |
|----|------|---------|---------|----------|
| R01 | Config backup exists | After config change | `ls ~/.openclaw/*.json.bak 2>/dev/null \| wc -l` | ≥ 1 (after first backup) |
| R02 | Memory files intact | After backup/restore | Spot check memory files exist and readable | OK |
| R03 | Qdrant auto-restart enabled | After Docker change | `docker inspect qdrant --format '{{.HostConfig.RestartPolicy.Name}}'` | unless-stopped | <!-- CUSTOMIZE: your container name -->

## Integration Tests (run periodically)
| ID | Test | Frequency | Command | Expected |
|----|------|-----------|---------|----------|
| I01 | Full backup cycle | Weekly | Create backup → verify → test restore | Data preserved |
| I02 | Service restart | Monthly | Restart OpenClaw → verify all services reconnect | All green |

## Safety Tests (run on security changes)
| ID | Test | Trigger | Command | Expected |
|----|------|---------|---------|----------|
| F01 | Secrets not in backups | After backup creation | `grep -r "API_KEY\|PASSWORD" /backup/<agent>/ 2>/dev/null` | No matches |
| F02 | Backup permissions | After backup creation | `stat -c "%a" /backup/<agent>/*.tar.gz 2>/dev/null` | 600 or 400 |

---

## Current System State

```bash
# Run these to populate current state
df -h /                              # Disk usage
free -h                              # Memory usage
uptime                               # Load and uptime
systemctl --failed                   # Failed services
```

*Last updated: 2009-01-02*