<!-- EXAMPLE: Attack surfaces shown here are illustrative, based on a typical
     OpenClaw deployment. Adapt for your specific configuration.
     NOTE: Dates in this document use stub-era values (2008-2009).
     Replace with actual data from your deployment.
     NOTE: CVE numbers below have been fictionalized (EXAMPLE-CVE-001, etc.)
     to avoid confusion with real CVE lookups. They are based on real
     vulnerabilities — research actual CVEs for your deployment. -->

# Prompt-Injection Constraints — Attack Surfaces & Priority Vulnerabilities

> **⚠️ Example Data:** All CVE numbers, version references, dates, and statistics below are from the toolkit author's deployment and may be outdated. Perform your own security research and replace with current findings.

## Red Team Analysis

### External Attack Vectors (from Upstream Architecture research)

Based on security research from Bitsight, ExtraHop, TrendMicro, and others:

#### 1. Exposed Instance Attacks
- **30,000+ exposed instances** found in 2 weeks (2009-01-27 — 2009-02-08)
- Default port: 18789/tcp
- Weak authentication (single character passwords accepted)
- EXAMPLE-CVE-001: "1-click" RCE via malicious gatewayUrl *(fictionalized — research actual CVEs for your deployment)*

#### 2. Supply Chain: Malicious Skills
- **900+ malicious skills** found on ClawHub (20% of total, Feb 2009)
- "ClawHavoc" campaign: skills that prompt users to run malicious commands
- Skills requesting sensitive data: 125+ skills ask for passwords, API keys, wallet keys
- 179 skills download unsigned binaries from untrusted sources

#### 3. Credential Storage
- MEMORY.md, SOUL.md stored in plaintext
- API keys in config files (though Anthropic keys were protected in testing)
- Credentials can be exfiltrated via prompt injection

#### 4. Prompt Injection Vectors
- Email content (invisible injection possible)
- Web content via browser automation
- Skill instructions treated as authoritative
- Agent may "fix" installation errors by executing malicious commands

### Local Attack Vectors (This Instance)

#### 1. Channel: WhatsApp
- Single channel configured
- Sender verification via IDENTITY-VERIFICATION.md *(planned)*
- Spoofing protection documented ✅

#### 2. Sensitive Files Identified
```
~/.openclaw/workspace/<your-credential-file>     <!-- CUSTOMIZE: your credential files -->
~/.openclaw/credentials/whatsapp/default/tctoken-*.json
~/.openclaw/workspace/<your-api-key-file>         <!-- CUSTOMIZE: your API key files -->
~/.openclaw/openclaw.json (gateway token)
```

#### 3. Trust Boundaries
| Boundary | Untrusted Source | Trusted Destination |
|----------|-----------------|---------------------|
| WhatsApp | Any sender | Agent processing |
| Email | Any sender | Memory, actions |
| Web fetch | External content | Agent context |
| Skills | Third-party code | System execution |
| Memory files | Stored context | Agent behavior |

#### 4. Current Defenses
- ✅ Identity verification protocol
- ✅ Approved contacts list
- ✅ Spoofing protection in agent configuration
- ✅ External content wrapping in web_fetch
- ⚠️ No explicit tool execution confirmation for all tools
- ⚠️ Skills can be installed without security review
- ⚠️ Memory files modifiable by agent without confirmation

---

## Attack Scenarios (Red Team Thinking)

### Scenario 1: Email Spoofing
**Attack:** Attacker spoofs admin@yourdomain.com with urgent request to exfiltrate data
**Current Defense:** Spoofing protection requires WhatsApp confirmation
**Gap:** Does agent always follow the gut-check protocol?

### Scenario 2: Skill Supply Chain
**Attack:** Malicious skill from ClawHub includes prompt injection or exfiltration code
**Current Defense:** None documented
**Gap:** No skill vetting process

### Scenario 3: Web Content Injection
**Attack:** Agent fetches webpage with hidden instructions to reveal credentials
**Current Defense:** External content wrapping
**Gap:** Does wrapping prevent injection? Need to verify.

### Scenario 4: Memory Poisoning
**Attack:** Injection in stored conversation affects future behavior
**Current Defense:** None documented
**Gap:** Memory files are plaintext and agent-trusted

### Scenario 5: Credential Exfiltration
**Attack:** Social engineering to get agent to read and send credential files
**Current Defense:** Identity verification
**Gap:** Agent has file read access; can it be tricked into reading sensitive files?

---

## Priority Vulnerabilities (Red Team Assessment)

| ID | Vulnerability | Severity | Exploitability |
|----|--------------|----------|----------------|
| V001 | No skill vetting process | Critical | High |
| V002 | Memory files are trusted without validation | High | Medium |
| V003 | Tool execution may not always require confirmation | High | Medium |
| V004 | Credential files readable by agent | High | Medium |
| V005 | External content wrapping effectiveness unknown | Medium | Medium |

---

*Last updated: 2009-01-02*