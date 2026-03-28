# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in the Evergreen Toolkit, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainer or use GitHub's private vulnerability reporting feature
3. Include steps to reproduce, impact assessment, and any suggested fixes

## Security Architecture

The Evergreen Toolkit includes a dedicated **prompt-injection** evergreen that continuously audits and hardens the system's security posture. See:

- [`evergreens/prompt-injection/STATE.md`](evergreens/prompt-injection/STATE.md) — Current vulnerability status
- [`evergreens/prompt-injection/CREDENTIAL-AUDIT.md`](evergreens/prompt-injection/CREDENTIAL-AUDIT.md) — Credential management guidelines
- [`evergreens/prompt-injection/MEMORY-VALIDATION.md`](evergreens/prompt-injection/MEMORY-VALIDATION.md) — Memory injection detection patterns
- [`docs/AUTONOMY-GUIDELINES.md`](docs/AUTONOMY-GUIDELINES.md) — Agent autonomy rules and escalation

## Response Timeline

- **Acknowledgment:** Within 48 hours of report
- **Assessment:** Within 1 week
- **Fix or mitigation:** Varies by severity; critical issues are prioritized

## Ongoing Security Monitoring

The **prompt-injection** evergreen runs daily and continuously monitors for:
- New prompt injection patterns and memory validation bypasses
- Credential exposure in logs, configs, or conversation data
- Supply chain risks from third-party skills and dependencies
- External content injection attempts

Findings are tracked in `evergreens/prompt-injection/STATE.md` and escalated via the notification system if configured. Review the prompt-injection evergreen's AGENDA.md periodically for security findings.

## Key Security Practices

- **Credential isolation:** `.memory_env` and API keys are excluded from version control via `.gitignore`
- **Memory validation:** 11 injection patterns detected and blocked (see MEMORY-VALIDATION.md)
- **External content wrapping:** Untrusted content is wrapped in `<<<EXTERNAL_UNTRUSTED_CONTENT>>>` markers
- **User memory isolation:** Each household member has separate Redis keys and Qdrant filters
- **Skill vetting:** All third-party skills must pass the vetting checklist before installation
