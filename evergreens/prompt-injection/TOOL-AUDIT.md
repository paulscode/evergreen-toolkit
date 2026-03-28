<!-- EXAMPLE: Tool policies and audit findings shown here are illustrative.
     Audit your own deployment's tool configuration. -->

# Tool Execution Audit (V003)

## Executive Summary

OpenClaw has a robust tool policy system with multiple layers of control. The primary security mechanism is the **exec approvals** system combined with **tool profiles** and **allowlists**.

---

## Tool Policy Layers

### Layer 1: Global Tool Policy (`tools.allow` / `tools.deny`)

Tools can be globally enabled or disabled in `openclaw.json`:

```json5
{
  tools: {
    profile: "coding",      // Base profile
    allow: ["group:fs"],    // Additional tools
    deny: ["exec"]          // Block specific tools (deny wins)
  }
}
```

### Layer 2: Tool Profiles

Profiles set base allowlists:

| Profile | Tools Included |
|---------|---------------|
| `minimal` | `session_status` only |
| `coding` | `group:fs`, `group:runtime`, `group:sessions`, `group:memory`, `image` |
| `messaging` | `group:messaging`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status` |
| `full` | No restriction |

### Layer 3: Exec Approvals

For `exec` tool specifically, three security modes:

| Mode | Behavior |
|------|----------|
| `deny` | Block all host exec requests |
| `allowlist` | Allow only allowlisted commands |
| `full` | Allow everything (equivalent to elevated) |

Ask modes:

| Mode | Behavior |
|------|----------|
| `off` | Never prompt |
| `on-miss` | Prompt when allowlist doesn't match |
| `always` | Prompt on every command |

---

## Tool Risk Classification

### High-Risk Tools (Require Explicit Policy)

| Tool | Risk | Current Control |
|------|------|-----------------|
| `exec` | Arbitrary command execution | Allowlist + approvals |
| `process` | Background process management | Gated by exec policy |
| `gateway` | Restart/update OpenClaw | Requires elevated mode |
| `cron` | Schedule arbitrary tasks | Should require confirmation |
| `nodes` | Remote command execution | Node-level approvals |

### Medium-Risk Tools (External Communication)

| Tool | Risk | Current Control |
|------|------|-----------------|
| `browser` | Web automation, potential data exfil | None documented |
| `web_fetch` | Fetch external content | None documented |
| `web_search` | Search queries leak intent | None documented |
| `message` | Send messages externally | None documented |
| `tts` | Audio output | None documented |

### Lower-Risk Tools (Internal Operations)

| Tool | Risk | Current Control |
|------|------|-----------------|
| `read` | File read (potential credential access) | None documented |
| `write` | File write | None documented |
| `edit` | File edit | None documented |
| `memory_search` | Search stored memories | None documented |
| `memory_get` | Retrieve memory content | None documented |
| `sessions_spawn` | Create sub-agents | None documented |

### Safe Tools (No External Impact)

| Tool | Purpose |
|------|---------|
| `session_status` | Show usage stats |
| `sessions_list` | List sessions |
| `sessions_history` | View session history |

---

## Safe Bins (Auto-Allow Without Explicit Allowlist)

Default safe bins that can run in allowlist mode without explicit entries:
- `jq`, `cut`, `uniq`, `head`, `tail`, `tr`, `wc`

These are **stdin-default** filters that primarily read from stdin and cannot execute subcommands. (Note: `jq` can also read files directly, but is low-risk in this context.)

**NOT safe bins:**
- `grep`, `sort` (not in default list, need explicit allowlist)
- Interpreters: `python3`, `node`, `ruby`, `bash`, `sh`, `zsh`

---

## Current Configuration

### Default Policy (from docs)

```json5
{
  defaults: {
    security: "deny",        // Block all by default
    ask: "on-miss",          // Prompt when not in allowlist
    askFallback: "deny",     // Deny if UI unreachable
    autoAllowSkills: false   // Don't auto-allow skill CLIs
  }
}
```

### Recommendations

1. **Keep `security: "deny"` as default** - Explicit allowlist required
2. **Keep `ask: "on-miss"`** - Human approval for new commands
3. **Review `autoAllowSkills`** - Only enable if skills are vetted (see V001)
4. **Add explicit allowlist entries** for commonly-used tools
5. **Monitor exec approval logs** for suspicious patterns

---

## Credential Access via File Read

The `read` tool can access any file the agent has permission to read. This includes:

- `~/.openclaw/workspace/<your-credential-file>`   <!-- CUSTOMIZE: your credential files -->
- `~/.openclaw/workspace/<your-api-key-file>`       <!-- CUSTOMIZE: your API key files -->
- `~/.openclaw/credentials/whatsapp/default/tctoken-*.json`
- `~/.openclaw/openclaw.json` (gateway token)

**Current Protection:** None documented. The agent can read these files.

**Mitigation Options:**
1. Store credentials in environment variables instead of files
2. Use file permissions (chmod 600) + separate user
3. Add a `read.deny` pattern for sensitive paths
4. Encrypt credentials at rest

See V004 for detailed credential audit.

---

## Action Items

- [ ] Audit current `exec-approvals.json` configuration
- [ ] Review which tools are actually enabled for the `main` agent
- [ ] Consider adding `tools.deny` for high-risk tools not actively used
- [ ] Document which tools require user confirmation in your agent configuration (e.g., AGENTS.md or openclaw.json)
- [ ] Set up logging for tool usage (especially `exec`, `read`, `message`)

---

*Created: 2009-01-02*
*Reference: evergreens/prompt-injection/CONSTRAINTS.md V003*