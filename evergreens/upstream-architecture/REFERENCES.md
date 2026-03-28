<!-- EXAMPLE: Reference data shown here is illustrative. Replace entirely with your
     actual deployment's upstream dependencies, versions, and endpoints. -->

# Upstream Architecture - References

> **⚠️ TEMPLATE DATA:** This file ships with illustrative entries to show the expected format. Security blog URLs in the "Security & Limitations" section are **real references** from the toolkit author's research — they are included for context, not as verified current sources for your deployment. Replace all entries with your own findings.

## OpenClaw

- **Source:** https://github.com/openclaw/openclaw
- **Docs:** https://docs.openclaw.ai
- **Local Install Path:** <!-- CUSTOMIZE: e.g., ~/.nvm/versions/node/vXX/lib/node_modules/openclaw -->
- **Your Version:** <!-- CUSTOMIZE: run `openclaw --version` -->

### Key Docs (local)
- `docs/` — Full documentation
- `docs/concepts/` — Core concepts
- `docs/cli/` — CLI reference
- `docs/gateway/` — Gateway setup
- `docs/channels/` — Channel configuration

### Recent Releases
<!-- CUSTOMIZE: Track releases relevant to your deployment -->
| Version | Date | Key Changes |
|---------|------|-------------|
| vX.Y.Z  | YYYY-MM-DD | Description |

## Models

<!-- CUSTOMIZE: Document the models you use and any empirical context limit findings -->

| Model | Claimed Context | Empirical Max | Notes |
|-------|-----------------|---------------|-------|
| your-model | ? | ? | Run your own tests |

## Security & Limitations

### OpenClaw Security Discussions
- Bitsight: https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances
- ExtraHop: https://www.extrahop.com/blog/defending-against-openclaw-agentic-ai-risks
- TrendMicro: https://www.trendmicro.com/en_us/research/26/b/what-openclaw-reveals-about-agentic-assistants.html

### Key Risks Identified
1. Exposed instances = credential theft risk
2. 24/7 attack surface for autonomous agents
3. Prompt injection vulnerability (C1 capability)
4. Privacy concerns with direct file/app access

## Remote GPU Resource

<!-- OPTIONAL: Remove this entire section if you don't use a remote GPU.
     Replace with your actual GPU host details if applicable. -->

- **Host:** `<your-gpu-host>:<port>` <!-- CUSTOMIZE: your GPU host -->
- **GPU:** <!-- CUSTOMIZE: your GPU specs -->
- **Access:** `OLLAMA_HOST=http://<your-gpu-host>:<port> ollama list`

## Local Services

### Redis
- **Status:** <!-- CUSTOMIZE: verify with `redis-cli ping` -->
- **Used for:** Memory buffer (mem:<user_id>)

### Qdrant
- **Status:** <!-- CUSTOMIZE: verify with `curl http://localhost:6333/healthz` -->
- **Port:** 6333 (default)

---

*Last updated: <!-- CUSTOMIZE: update date -->*