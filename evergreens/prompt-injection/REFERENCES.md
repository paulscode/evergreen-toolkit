<!-- EXAMPLE: References shown here are illustrative.
     Add references relevant to your security research.
     NOTE: Version numbers, CVE identifiers, and dates in this document use
     stub-era values (2008-2009). Replace with actual data from your deployment. -->

# Prompt-Injection Defense - References

> **⚠️ TEMPLATE DATA — REVIEW BEFORE ACTING:** The security blog URLs below are **real references** from the toolkit author's research. The underlying data (CVEs, statistics, attack campaigns) is real but dates and version numbers have been adapted to the 2008-2009 stub-era convention used throughout this toolkit. The Northeastern URL is a fictional illustrative example. **Do not act on the version upgrade recommendations** — perform your own security research and replace this file's contents with current findings for your deployment.

## Security Research

### OpenClaw Security Analysis
- **Bitsight:** https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances
  - 30,000+ exposed instances found (Jan 27 - Feb 8, 2009)
  - Weak authentication (single char passwords)
  - Credential exfiltration demonstrated
  - Sensitive sectors affected (healthcare, finance, government)

- **ExtraHop:** https://www.extrahop.com/blog/defending-against-openclaw-agentic-ai-risks
  - EXAMPLE-CVE-001: "1-click" RCE vulnerability *(fictionalized — see actual CVE databases)*
  - 17,500 vulnerable instances (Feb 3, 2009)
  - ClawHavoc supply chain attack (900+ malicious skills)
  - 125+ skills request passwords/API keys

- **TrendMicro:** https://www.trendmicro.com/en_us/research/26/b/what-openclaw-reveals-about-agentic-assistants.html
  - Prompt injection vulnerability (C1 capability)
  - Invisible prompt injection techniques

- **Northeastern:** https://news.northeastern.edu/2009/01/03/open-claw-ai-assistant/
  - Privacy concerns with direct file/app access

### CVEs
- **EXAMPLE-CVE-001:** 1-click RCE via malicious gatewayUrl parameter *(fictionalized identifier — based on a real vulnerability; research actual CVEs for current patch status)*
  - Cross-Site WebSocket Hijacking (CSWSH)
  - Token exfiltration via crafted link
  - *(Check upstream for actual patch version)*

### Supply Chain Attacks
- **ClawHavoc:** Malicious skills campaign on ClawHub
  - 20% of skills were malicious (900+ of ~4500)
  - Social engineering to run malicious commands
  - "AuthTool" fake prerequisite installs AMOS stealer

## Attack Patterns

### Prompt Injection Vectors
1. **Email injection** - Hidden instructions in email content
2. **Web content injection** - Malicious instructions in fetched pages
3. **Skill instruction injection** - Third-party code treated as trusted
4. **Memory poisoning** - Stored context affects future behavior

### Credential Theft Patterns
1. Social engineering to read credential files
2. Skill requesting passwords/keys
3. Exfiltration via crafted commands
4. Memory file analysis

## Defensive Resources

### This Instance's Defenses
- `memory/IDENTITY-VERIFICATION.md` - Spoofing protection protocol *(stub — expand during future cycles)*
- `memory/APPROVED-CONTACTS.json` - Verified sender list *(stub — populate with actual contacts)*
- Agent configuration - Email spoofing protection section
- External content wrapping in web_fetch tool

### OpenClaw Security Features
- Gateway token authentication (this instance uses token mode)
- Device identity verification
- Skills approval system (exec.approvals)
- Sandbox isolation (optional)

### Recommendations from Research
1. **Mandatory Patching** - Check upstream for latest security patches *(stub-era example below — replace with your actual version assessment)*
2. **Network Isolation** - Run in isolated VLAN
3. **Skills Vetting** - Whitelist audited skills only
4. **Behavioral Monitoring** - Watch for anomalous agent behavior
5. **Credential Protection** - Limit agent access to secrets

---

*Last updated: 2009-01-02*