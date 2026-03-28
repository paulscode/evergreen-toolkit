# Agent Autonomy Guidelines

**When can the AI agent make changes without asking for permission?**

This document defines the autonomy framework for evergreen cycles. Agents are empowered to make reversible, low-risk changes automatically while escalating truly risky modifications for human review.

---

## Decision Framework

### 🎯 The 30-Second Rule

**If you can undo it in <30 seconds with one command, it's probably safe to auto-apply.**

Examples:
- `chmod 600 config.json` → Undo: `chmod 644 config.json` (5 seconds)
- `mkdir -p logs/` → Undo: `rmdir logs/` (2 seconds)
- `systemctl restart openclaw-gateway` → Undo: `systemctl restart openclaw-gateway` (same command)

Counter-examples:
- `chown <user2>:<user2> config.json` → Undo requires knowing original owner (uncertain)
- `apt install package` → Undo: `apt remove package` + config cleanup (minutes, may leave artifacts)
- `iptables -A INPUT ...` → Undo requires knowing exact rule syntax (error-prone)

---

## ✅ AUTO-APPLY List (No Permission Needed)

### File Operations

| Action | Example | Why Safe |
|--------|---------|----------|
| **File permissions** | `chmod 600 openclaw.json` | Reversible, no data loss |
| **Directory creation** | `mkdir -p logs/ backup/` | Easily removed if wrong |
| **Config formatting** | Fix indentation in JSON/YAML | No semantic change |
| **Timestamp updates** | `Last Cycle: 2009-01-03` | Documentation only |
| **Version numbers** | `Version: 2009.1.1` | Documentation only |

### Service Management

| Action | Example | Why Safe |
|--------|---------|----------|
| **Restart configured services** | `systemctl restart openclaw-gateway` | Service restarts on boot anyway |
| **Check service status** | `systemctl status redis` | Read-only operation |
| **Enable auto-start** | `systemctl enable openclaw-gateway` | Reversible with `disable` |

### Cleanup Operations

| Action | Example | Why Safe |
|--------|---------|----------|
| **Temp file cleanup** | `rm -rf /tmp/openclaw-*` | Temp files are ephemeral |
| **Old log rotation** | Delete logs >30 days | Already archived if needed |
| **Cache cleanup** | `rm -rf ~/.cache/pip/*` | Cache rebuilds automatically |
| **Minor disk cleanup** | See below | <1GB, non-critical paths |

### Documentation

| Action | Example | Why Safe |
|--------|---------|----------|
| **Typo fixes** | Grammar, spelling | No functional impact |
| **AGENDA.md updates** | Add findings, tasks | Working document |
| **"Completed Recently"** | Add item, maintain 3-5 | Auto-rolling window |

---

## 🔍 Minor Disk Cleanup - Detailed Guidelines

**AUTO-APPLY when ALL criteria met:**
- **Size:** <1GB total
- **Age:** Files older than 7 days
- **Location:** Non-critical paths only
- **Type:** Cache, temp, logs (not data, configs, or credentials)

### Safe Paths (`rm -rf <path>/*` contents, NOT the path itself)

> **Important:** Always use `<path>/*` (trailing `/*`) to clean a directory's *contents*. Never use `rm -rf <path>` without the trailing `/*` — that would delete the directory itself and may break services that expect it to exist.

| Path | Purpose | Safe? |
|------|---------|-------|
| `~/.cache/pip/` | Python package cache | ✅ Yes |
| `~/.cache/node-gyp/` | Node.js build cache | ✅ Yes |
| `~/tmp/` or `/tmp/workspace-*` | Workspace temp files | ✅ Yes |
| `logs/*.log.old` | Archived logs | ✅ Yes |
| `evergreens/*/agenda-history/*.md` | old agendas (>60 days) | ✅ Yes |
| `~/.local/share/Trash/` | Trash contents | ✅ Yes |
| `node_modules/.cache/` | Build cache | ✅ Yes |

### Unsafe Paths (REQUIRES ASK-FIRST)

| Path | Why Unsafe |
|------|------------|
| `~/Documents/` or `~/data/` | May contain user files |
| `.openclaw/workspace/` | Workspace root - could delete critical files |
| `evergreens/*/STATE.md` | Long-term state tracking |
| `memory/` directory | User memory files |
| `skills/` or `scripts/` | Code directories |
| `~/.ssh/` | SSH keys and config |
| `.config/` directories | Application configs |
| Any path with credentials | Could break authentication |

### Cleanup Command Pattern

```bash
# SAFE - clean contents of cache directory
find ~/.cache/pip -type f -mtime +7 -delete

# SAFE - clean old archived logs
find logs/ -name "*.log.old" -mtime +30 -delete

# SAFE - clean agenda history older than 60 days
find evergreens/*/agenda-history/ -name "*.md" -mtime +60 -delete

# UNSAFE - don't delete entire directories
# rm -rf ~/.cache/  ❌ (breaks apps)
# rm -rf logs/      ❌ (loses all logs)
```

**When in doubt:** Document in AGENDA.md, send a message: "Found 500MB old cache in ~/.cache/pip - OK to clean?"

---

## ⚠️ ASK-FIRST List (Requires User Review)

### File Ownership & Access

| Action | Why Risky |
|--------|-----------|
| `chown user:group file` | May break service permissions |
| `setfacl` or `chmod +s` | Security implications |
| Moving files out of workspace | Data loss risk |

### System Configuration

| Action | Why Risky |
|--------|-----------|
| Modifying cron jobs | Could break scheduled tasks |
| Installing packages (`apt`, `pip`, `npm`) | Dependency conflicts, security |
| Network/firewall changes | Could block legitimate traffic |
| Exposing services beyond LAN | Security exposure |
| Modifying `systemd` unit files | Service startup behavior |

### Data Operations

| Action | Why Risky |
|--------|-----------|
| Deleting data files (non-temp) | Permanent data loss |
| Moving/renaming critical configs | Service breakage |
| Database operations | Data integrity risk |

### External Actions

| Action | Why Risky |
|--------|-----------|
| Spending money (API costs, services) | Financial impact |
| Contacting third parties | Social/professional impact |
| Sending emails/DMs on behalf of user | Communication on user's behalf |
| Posting to social media | Public representation |

---

## 📋 Blocked Workflow

**When agent encounters something requiring review:**

1. **Document** in AGENDA.md:
   ```markdown
   ## Blockers & Missing Information
   - [2009-01-03 16:00] Found 2GB old cache in ~/.cache/pip - sent message for approval
   ```

2. **Send a message** (via your configured channel — WhatsApp, Telegram, etc.):
   ```
   Hi! I found 2GB of old pip cache files (>30 days). Safe to clean?
   Path: ~/.cache/pip/
   Age: 30+ days
   Size: ~2GB
   Risk: Low - cache rebuilds if needed
   
   Reply YES to clean, NO to keep, or ASK for more info.
   ```

3. **Continue with other tasks** while waiting

4. **Resume when approved**:
   - If YES: Clean, log in AGENDA.md "## Notifications Sent"
   - If NO: Document decision, move on
   - If no response: Don't retry unless critical

---

## 🎯 Examples in Practice

### Example 1: CRITICAL Security Fix (AUTO-APPLY)

**Found:** `openclaw.json` permissions are `664` (world-readable)

**Action:** `chmod 600 ~/.openclaw/openclaw.json`

**Why AUTO-APPLY:**
- Reversible in 5 seconds
- Security improvement
- No functional impact
- Clear best practice

**Log in AGENDA.md:**
```markdown
### 1. Fix config file permissions (CRITICAL)
- Status: ✅ completed
- Findings: Config file was 664 (readable by all users)
- Actions taken: chmod 600 openclaw.json
- Reasoning: Security hardening - config contains gateway token
```

---

### Example 2: Package Installation (ASK-FIRST)

**Found:** Missing `jq` tool needed for JSON processing

**DON'T:** `sudo apt install jq`

**DO:** Send a message:
```
Hi! I need `jq` for JSON processing in evergreen cycles. 
Install with: sudo apt install jq
Size: 1.2MB
Risk: Low - standard tool, no config changes

OK to proceed?
```

**If approved:**
```bash
sudo apt install jq -y
# Log in AGENDA.md
## Notifications Sent
- [2009-01-03 16:00] Message to <user2>: Install jq - APPROVED
```

---

### Example 3: Disk Cleanup (AUTO-APPLY vs ASK-FIRST)

**Scenario A - AUTO-APPLY:**
- Path: `~/.cache/pip/`
- Size: 500MB
- Age: 14+ days
- **Action:** Clean (meets all safe criteria)

**Scenario B - ASK-FIRST:**
- Path: `~/projects/old-backup/`
- Size: 2GB
- Age: Unknown
- **Action:** Message user first (unclear if user needs it)

---

## 🌲 Evergreen-Specific Examples

### System Health

**AUTO-APPLY:**
- `chmod 600 backup/config.json`
- `mkdir -p /backup/openclaw/`
- `systemctl restart openclaw-gateway`

**ASK-FIRST:**
- Modify backup rotation schedule in crontab
- Install monitoring tool (`apt install htop`)

---

### Prompt Injection Defence

**AUTO-APPLY:**
- Update `evergreens/prompt-injection/VETTING-CHECKLIST.md` with new skill names
- Fix typos in security documentation

**ASK-FIRST:**
- Modify firewall rules to block new attack vectors
- Install security scanner package

---

### Household Memory

**AUTO-APPLY:**
- `mkdir -p memory/<user>/emails/`
- Clean agenda history >60 days
- Update timestamp in STATE.md

**ASK-FIRST:**
- Change Redis configuration
- Delete any files in `memory/*/2009-01-02.md`

---

## Summary

**Be bold with reversible improvements. Be conservative with irreversible changes.**

**See also:** [MEMORY-FIRST-STRATEGY.md](MEMORY-FIRST-STRATEGY.md) — complementary agent behavior for always searching memory before responding.

When in doubt:
1. Document the issue
2. Send a message with clear context
3. Continue with other work
4. Resume when approved

This framework enables daily incremental improvements while protecting users from risky mistakes.
