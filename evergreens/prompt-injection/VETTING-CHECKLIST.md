<!-- STATUS: STUB — This file will be populated by the prompt-injection evergreen
     during its first cycles. No action needed during initial setup. -->

# Skill Vetting Checklist

> **Status:** Stub — to be developed by the prompt-injection evergreen.

## Purpose

Checklist for evaluating new OpenClaw skills before installation, based on findings from the ClawHavoc campaign (900+ malicious skills on ClawHub).

## Pre-Installation Checks

- [ ] **Source code reviewed** — Check that the skill doesn't use `exec`, `eval`, `subprocess`, or `process` tools without clear justification. Look for obfuscated or minified code that hides behavior.
- [ ] **No credential requests** — Search source code for strings like "password", "api_key", "secret", "wallet", "token". Reject skills that prompt users for these.
- [ ] **No unsigned binary downloads** — Check for `curl | bash`, `wget`, or download URLs pointing to non-HTTPS or unknown domains.
- [ ] **No unjustified exec/process calls** — If the skill uses shell execution, verify each command is necessary and scoped. Reject open-ended command execution.
- [ ] **Author reputation verified** — Check ClawHub profile age, number of published skills, GitHub history. New accounts with a single skill are higher risk.
- [ ] **Minimal permissions** — The skill should only request tools it actually needs. A weather skill shouldn't need file system access.
- [ ] **No suspicious network calls** — Check for outbound HTTP requests to unknown endpoints. Legitimate skills should only call well-known APIs.

## Post-Installation Monitoring

- [ ] Monitor agent behavior for unexpected tool calls
- [ ] Review logs for credential access after skill activation
- [ ] Test with sandboxed data before production use

## References

- See `evergreens/prompt-injection/CONSTRAINTS.md` for attack surface analysis
- See `evergreens/prompt-injection/TOOL-AUDIT.md` for tool risk classification
