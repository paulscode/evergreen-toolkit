# Upstream Monitoring Guide

**How the Evergreen Toolkit tracks and adopts improvements from upstream repositories.**

---

## Overview

The Evergreen Toolkit is built on the work of others. Two evergreens are specifically tasked with monitoring upstream repositories for improvements:

1. **Upstream Architecture Evergreen** - Monitors OpenClaw core, agent frameworks, and system dependencies
2. **Household Memory Evergreen** - Monitors the True Recall memory system and related memory architecture

---

## Why Monitor Upstream?

**Benefits:**
- **Security:** Stay informed about security patches and breaking changes
- **Innovation:** Adopt proven improvements without reinventing the wheel
- **Compatibility:** Avoid falling so far behind that upgrades become painful
- **Attribution:** Properly credit upstream authors whose work we build upon

**Risks of NOT monitoring:**
- Missing critical security fixes
- Incompatible upgrades that break your system
- Duplicating work that upstream already solved
- Losing attribution and community goodwill

---

## Monitored Repositories

### Upstream Architecture Evergreen Watches:

| Repository | URL | Frequency | What to Watch |
|-----------|-----|-----------|---------------|
| OpenClaw Core | https://github.com/openclaw/openclaw | Weekly | Releases, breaking changes, security advisories |
| Agent Claw | https://github.com/openclaw/agent-claw | Monthly | Agent framework updates (the CLI / agent-mode library that `openclaw agent` uses) |
| True Recall Base | https://gitlab.com/mdkrush/openclaw-true-recall-base | Bi-weekly | Memory curation improvements |

> **Note on frequency vs. daily schedule:** Evergreens run daily, but the AI agent should check each repository's "Last Checked" date in STATE.md and only perform research on repositories that are due for their scheduled check frequency. For example, a "Monthly" repository is only actively researched once per month — on other days the agent skips it.

### Household Memory Evergreen Watches:

| Repository | URL | Frequency | What to Watch |
|-----------|-----|-----------|---------------|
| True Recall Base | https://gitlab.com/mdkrush/openclaw-true-recall-base | Bi-weekly | Curation algorithms, category management, bug fixes |

---

## Monitoring Process

### Every Cycle (Automated)

1. **Check for new commits/releases**
   ```bash
   # GitHub releases
   curl -s https://api.github.com/repos/openclaw/openclaw/releases | jq '.[0:3]'
   
   # GitLab commits
   git ls-remote https://gitlab.com/mdkrush/openclaw-true-recall-base.git | head -10
   ```

   > **Rate limit note:** Unauthenticated GitHub API requests are limited to 60/hour per IP. If you monitor multiple repos, set `GITHUB_TOKEN` in your environment and pass it via `curl -H "Authorization: token $GITHUB_TOKEN"` to get 5,000 requests/hour.

2. **Review changelog/commits**
   - Look for keywords: "breaking", "security", "performance", "memory"
   - Check commit messages for relevant changes

3. **Update monitoring log** in STATE.md:
   ```markdown
   | Date Checked | Upstream Status | Notable Changes | Action Taken |
   |--------------|-----------------|-----------------|--------------|
   | 2009-01-03 | 🟢 Current | Bug fix in category suggestions | Reviewed, no action needed |
   ```

### When Notable Changes Found

1. **Document in AGENDA.md**
   ```markdown
   ## Upstream Evaluation: [Repository] - [Date]
   
   **Change:** [Brief description]
   
   **Impact:** [How this affects our system]
   
   **Test Plan:** [How to test before adopting]
   
   **Decision:** [Adopt / Defer / Reject]
   ```

2. **Test in isolation**
   - Create experiment branch
   - Test with subset of data
   - Verify no breaking changes

3. **Adopt (if beneficial)**
   - Merge changes
   - Update attribution
   - Document in "Key Learnings"

---

## Seeding New Installations

When setting up a new Evergreen Toolkit instance:

```bash
cd evergreen-toolkit
source .venv/bin/activate

# Seed upstream monitoring tasks
python3 scripts/seed-evergreens.py
```

This script:
- Creates AGENDA.md with initial upstream research tasks
- Adds upstream repository watchlist to STATE.md
- Establishes monitoring cadence and criteria
- Does NOT overwrite existing files (safe to run multiple times)

---

## Attribution Guidelines

**When adopting upstream improvements:**

1. **Credit the author**
   ```markdown
   - [2009-01-03] Category management improvements adopted from SpeedyFoxAI's True Recall Base (commit abc123)
   ```

2. **Link to the source**
   Include the upstream URL in your documentation.

3. **Preserve licenses**
   Ensure upstream licenses are compatible with your use.

4. **Give back**
   If you improve something upstream, consider contributing back.

---

## What NOT to Blindly Adopt

**Red flags:**
- ❌ Breaking changes without clear migration path
- ❌ Features that don't apply to multi-user households
- ❌ Unstable/experimental features (unless you want to test)
- ❌ Changes with no attribution or unclear licensing

**Adoption Evaluation Criteria:**
When deciding whether to adopt an upstream change, consider:
1. **Security fixes** — Adopt immediately. These protect your deployment.
2. **Bug fixes** — Adopt if they affect components you use (memory scripts, curation, search).
3. **New features** — Evaluate whether the feature benefits your household setup. Test in isolation first.
4. **Breaking changes** — Only adopt if the benefit outweighs the effort. Document the migration path before applying.

**Instead:**
- Test in isolation first
- Read commit history and issues
- Ask in community channels if uncertain
- Document your evaluation process

---

## Tools & Scripts

### `scripts/seed-evergreens.py`

Seeds AGENDA.md and STATE.md with upstream monitoring tasks for new installations.

```bash
python3 scripts/seed-evergreens.py           # Run seeding
python3 scripts/seed-evergreens.py --dry-run # Preview what would be done
```

### Manual Research Commands

```bash
# Check GitHub releases
curl -s https://api.github.com/repos/openclaw/openclaw/releases | jq '.[0:3] | {tag_name, published_at, name}'

# Check GitLab commits
git ls-remote https://gitlab.com/mdkrush/openclaw-true-recall-base.git | head -20

# Clone and review (for deep dives)
git clone https://gitlab.com/mdkrush/openclaw-true-recall-base.git /tmp/upstream-review
cd /tmp/upstream-review
git log --oneline -20
```

---

## Example: First Cycle Workflow

**Upstream Architecture Evergreen - First Run:**

1. AGENDA.md has seeded task: "Initialize Upstream Repository Watchlist"
2. AI researcher:
   - Checks OpenClaw releases (found v2025.1.15)
   - Checks True Recall Base commits (found 3 commits this month)
   - Documents current versions in STATE.md
   - Creates watchlist table in STATE.md
3. Documents findings in AGENDA.md:
   ```markdown
   ## Research Findings
   - OpenClaw v2025.1.15 is current (we're on v2025.1.15) ✅
   - True Recall Base: 3 commits, all documentation updates 🟢
   - No breaking changes detected
   ```
4. Updates "Completed Recently" in STATE.md:
   ```markdown
   - [2009-01-03] Initialized upstream repository watchlist
   ```

**Result:** AI now knows what to monitor every cycle going forward.

---

## Best Practices

1. **Consistency beats intensity**
   - Better to check bi-weekly consistently than daily for a week then never
   - Cron schedules ensure this happens automatically

2. **Document everything**
   - Future-you (or another AI) will thank you
   - Makes it clear what was considered and why

3. **Test before adopting**
   - Upstream might have different assumptions than your setup
   - Isolated testing prevents production issues

4. **Maintain relationships**
   - Follow upstream authors on GitHub/GitLab
   - Report bugs you find
   - Contribute improvements when possible
