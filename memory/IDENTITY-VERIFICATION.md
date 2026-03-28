<!-- STATUS: FUTURE WORK — This file will be populated by the prompt-injection evergreen
     during its first cycles. No action needed during initial setup. -->

# Identity Verification Protocol

> **Status: Future Work** — No action needed during initial setup. This file will be populated by the prompt-injection evergreen over successive cycles. The structure below outlines planned work; implementing agents should skip this file during onboarding.

## Purpose

Define procedures for verifying the identity of users and external contacts before acting on sensitive requests (e.g., financial transactions, credential sharing, data export).

## TODO

- [ ] Define verification challenge-response flow
- [ ] Integrate with user phone number / WhatsApp mapping
- [ ] Add escalation rules for unrecognized contacts
- [ ] Document bypass conditions for trusted channels

## References

- See `evergreens/prompt-injection/STATE.md` for vulnerability context
- See `memory/APPROVED-CONTACTS.json` for the trusted contacts list
