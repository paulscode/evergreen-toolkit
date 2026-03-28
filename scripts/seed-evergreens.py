#!/usr/bin/env python3
"""
Seed Evergreen STATE.md and AGENDA.md files with upstream monitoring tasks.

Run this after installing the Evergreen Toolkit to initialize the
upstream-architecture and household-memory evergreens with tasks to monitor
relevant upstream repositories.

Usage:
    python3 scripts/seed-evergreens.py
    python3 scripts/seed-evergreens.py --dry-run

What it does:
- Creates STATE.md if missing (from template)
- Adds upstream monitoring tasks to AGENDA.md
- Seeds research topics in STATE.md
- Does NOT overwrite existing files (safe to run multiple times)
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"

def log(message: str, level: str = "INFO"):
    """Print a message."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}")


def file_contains(filepath: Path, text: str) -> bool:
    """Check if file contains specific text."""
    if not filepath.exists():
        return False
    try:
        content = filepath.read_text()
        return text in content
    except Exception:
        return False


def append_if_missing(filepath: Path, section: str, before_marker: str = None):
    """Append section to file if not already present."""
    if filepath.exists():
        content = filepath.read_text()
        if section.strip() in content:
            log(f"Skipping {filepath.name} - section already present", "SKIP")
            return False
    
    if before_marker:
        # Insert before marker
        if filepath.exists():
            content = filepath.read_text()
            if before_marker in content:
                content = content.replace(before_marker, section + "\n" + before_marker)
                filepath.write_text(content)
                log(f"Added section to {filepath.name}", "SUCCESS")
                return True
            else:
                # Marker not found, append at end
                with open(filepath, "a") as f:
                    f.write("\n" + section + "\n")
                log(f"Appended section to {filepath.name}", "SUCCESS")
                return True
        else:
            # File doesn't exist
            filepath.write_text(section + "\n")
            log(f"Created {filepath.name}", "SUCCESS")
            return True
    else:
        # Append at end
        with open(filepath, "a") as f:
            f.write("\n" + section + "\n")
        log(f"Appended section to {filepath.name}", "SUCCESS")
        return True


def seed_upstream_architecture(dry_run: bool = False):
    """Seed upstream-architecture evergreen with monitoring tasks."""
    log("Seeding upstream-architecture...", "INFO")
    if dry_run:
        log("DRY RUN - would seed upstream-architecture AGENDA.md and STATE.md", "INFO")
        return
    
    agenda_file = EVERGREENS_DIR / "upstream-architecture" / "AGENDA.md"
    state_file = EVERGREENS_DIR / "upstream-architecture" / "STATE.md"
    
    # AGENDA.md - First cycle tasks
    agenda_tasks = """
## Tasks for This Cycle

### 1. Initialize Upstream Repository Watchlist

**Action Items:**
- [ ] Add https://github.com/openclaw/openclaw to watchlist (OpenClaw core)
- [ ] Add https://github.com/openclaw/agent-claw (Agent framework)
- [ ] Add https://gitlab.com/mdkrush/openclaw-true-recall-base (True Recall memory system)
- [ ] Check each repo for recent releases/commits
- [ ] Note any breaking changes in last 30 days

**Research:**
```bash
# Check OpenClaw releases
curl -s https://api.github.com/repos/openclaw/openclaw/releases | head -50

# Check True Recall Base commits
git ls-remote https://gitlab.com/mdkrush/openclaw-true-recall-base.git | head -10
```

**Deliverable:** Updated watchlist in STATE.md with recent activity summary.

---

### 2. Establish Monitoring Cadence

**Define:**
- How often to check each upstream (daily? weekly?)
- What constitutes a "notable" change (major version, breaking changes, security fixes)
- How to test upstream changes before adopting

**Document in AGENDA.md:**
```markdown
## Upstream Monitoring Schedule
- OpenClaw core: Check releases weekly (Wednesdays)
- True Recall Base: Check commits bi-weekly
- Breaking changes: Test in isolated branch before adopting
```

---

### 3. Document Current Versions

**Record:**
- Current OpenClaw version: `openclaw --version`
- Current True Recall commit hash (if installed)
- Any forks or modifications in use

**Add to STATE.md** under "System Information" section.

"""
    
    # STATE.md - Research topics
    state_research = """
## Upstream Repository Watchlist

### Primary Repositories

| Repository | URL | Monitoring Frequency | Last Checked | Status |
|-----------|-----|---------------------|--------------|--------|
| OpenClaw Core | https://github.com/openclaw/openclaw | Weekly | YYYY-MM-DD | 🟢 Current |
| Agent Claw | https://github.com/openclaw/agent-claw | Monthly | YYYY-MM-DD | 🟢 Current |
| True Recall Base | https://gitlab.com/mdkrush/openclaw-true-recall-base | Bi-weekly | YYYY-MM-DD | 🟢 Current |

### What to Monitor

**OpenClaw Core:**
- New releases (especially major versions)
- Breaking changes in configuration or API
- Security advisories
- Gateway or channel updates
- Extension/plugin architecture changes

**True Recall Base:**
- Curation algorithm improvements
- Category management enhancements
- Bug fixes for memory leaks or duplication
- Integration improvements with OpenClaw

### Attribution

This evergreen toolkit includes memory architecture based on SpeedyFoxAI's True Recall work.
Maintain attribution when adopting upstream improvements. See `memory/UPSTREAM-CREDITS.md`.

"""
    
    appended = False
    
    if agenda_file.exists():
        content = agenda_file.read_text()
        if "Initialize Upstream Repository Watchlist" not in content:
            # Find the "## Tasks for This Cycle" section and append after it
            if "## Tasks for This Cycle" in content:
                content = content.replace(
                    "## Tasks for This Cycle",
                    "## Tasks for This Cycle" + agenda_tasks
                )
                agenda_file.write_text(content)
                log("Added tasks to AGENDA.md", "SUCCESS")
                appended = True
            else:
                log("AGENDA.md exists but has unexpected format - manual review needed", "WARNING")
        else:
            log("AGENDA.md already has upstream tasks", "SKIP")
    else:
        # Create AGENDA.md from scratch
        agenda_file.write_text(f"""# Upstream Architecture - Agenda

**Cycle Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** In Progress

{agenda_tasks}
""")
        log("Created AGENDA.md with upstream tasks", "SUCCESS")
        appended = True
    
    # Always ensure STATE.md has the watchlist section
    if state_file.exists():
        if "Upstream Repository Watchlist" not in state_file.read_text():
            append_if_missing(state_file, state_research, "## Research Topics")
        else:
            log("STATE.md already has watchlist section", "SKIP")
    else:
        log("STATE.md doesn't exist yet - will be created on first run", "SKIP")
    
    return appended


def seed_household_memory(dry_run: bool = False):
    """Seed household-memory evergreen with upstream monitoring tasks."""
    log("Seeding household-memory...", "INFO")
    if dry_run:
        log("DRY RUN - would seed household-memory AGENDA.md and STATE.md", "INFO")
        return
    
    agenda_file = EVERGREENS_DIR / "household-memory" / "AGENDA.md"
    state_file = EVERGREENS_DIR / "household-memory" / "STATE.md"
    
    # AGENDA.md - First cycle tasks
    agenda_tasks = """
## Tasks for This Cycle

### 1. Initialize Upstream Memory Research

**Primary Upstream:**
- https://gitlab.com/mdkrush/openclaw-true-recall-base (True Recall memory system)

**Action Items:**
- [ ] Review upstream repository structure
- [ ] Identify key components: curation, category management, gem extraction
- [ ] Check for recent improvements or bug fixes
- [ ] Document differences between our implementation and upstream

**Research Questions:**
- What curation strategies work best for multi-user households?
- How does upstream handle category suggestions and approval workflows?
- Are there memory consolidation or retention policies we should adopt?

---

### 2. Establish Memory Improvement Pipeline

**Define Process:**
1. **Monitor** upstream bi-weekly for improvements
2. **Evaluate** if improvement applies to our household
3. **Test** in isolated experiment (not production)
4. **Adopt** if beneficial (with attribution)
5. **Document** in STATE.md "Key Learnings"

**Document in AGENDA.md:**
```markdown
## Upstream Evaluation Criteria

When considering upstream improvements:
- ✅ Improves memory relevance or retrieval quality
- ✅ Enhances user isolation or privacy
- ✅ Simplifies configuration or maintenance
- ✅ Has clear attribution and licensing compatibility
- ❌ Breaking changes without migration path
- ❌ Features that don't apply to multi-user households
```

---

### 3. Document Current Memory Architecture

**Record:**
- Redis buffer key format: `mem:<user_id>`
- Qdrant collections: `true_recall`, `agent-memories` (or user-specific)
- True Recall curation schedule: 2:30 AM (adjust for your timezone)
- Jarvis backup schedule: 3:00 AM (adjust for your timezone)
- Category hierarchy per user

**Verify:**
- [ ] Redis buffer is capturing conversations
- [ ] True Recall curation is running successfully
- [ ] Jarvis backup is backing up and clearing Redis
- [ ] User isolation is working (no cross-user leakage)

---

### 4. Set Category Management Goals

**Initial Review:**
```bash
cat memory/<user_id>/categories.yaml
cat memory/<user_id>/suggested_categories.json
```

**Goals for This Month:**
- [ ] Review category suggestions from True Recall
- [ ] Approve/modify/reject pending suggestions
- [ ] Archive unused categories
- [ ] Add user-specific curator prompts if missing

**Success Metric:** Category hierarchy reflects actual conversation topics without bloat (< 10 top-level categories per user).

"""
    
    # STATE.md - Upstream monitoring section
    state_upstream = """
## Upstream Monitoring (CRITICAL)

### Primary Upstream Repository
**SpeedyFoxAI's True Recall Base** — https://gitlab.com/mdkrush/openclaw-true-recall-base

This is the original implementation of the Jarvis Memory + True Recall system. Monitor actively for:
- Bug fixes and performance improvements
- New curation patterns or gem extraction techniques
- Enhanced category management
- Integration improvements with OpenClaw core

### Monitoring Schedule
**Every household-memory cycle:**
1. Check upstream repo for new commits/releases
2. Review changelog for breaking changes or improvements
3. Test promising improvements in isolated experiment
4. Document findings in HISTORY.md
5. Adopt if beneficial (with attribution)

### Upstream Monitoring Log

| Date Checked | Upstream Status | Notable Changes | Action Taken |
|--------------|-----------------|-----------------|--------------|
| YYYY-MM-DD | 🟢 Current | None | No action needed |

**Attribution:** This memory system is based on SpeedyFoxAI's original True Recall work. See `memory/UPSTREAM-CREDITS.md` for full details.

"""
    
    appended = False
    
    if agenda_file.exists():
        content = agenda_file.read_text()
        if "Initialize Upstream Memory Research" not in content:
            if "## Tasks for This Cycle" in content:
                content = content.replace(
                    "## Tasks for This Cycle",
                    "## Tasks for This Cycle" + agenda_tasks
                )
                agenda_file.write_text(content)
                log("Added tasks to AGENDA.md", "SUCCESS")
                appended = True
            else:
                log("AGENDA.md exists but has unexpected format - manual review needed", "WARNING")
        else:
            log("AGENDA.md already has upstream memory tasks", "SKIP")
    else:
        # Create AGENDA.md from scratch
        agenda_file.write_text(f"""# Household Memory - Agenda

**Cycle Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** In Progress

{agenda_tasks}
""")
        log("Created AGENDA.md with upstream memory tasks", "SUCCESS")
        appended = True
    
    # Always ensure STATE.md has the upstream monitoring section
    if state_file.exists():
        if "Upstream Monitoring (CRITICAL)" not in state_file.read_text():
            append_if_missing(state_file, state_upstream, "## Upstream Monitoring")
        else:
            log("STATE.md already has upstream monitoring section", "SKIP")
    else:
        log("STATE.md doesn't exist yet - will be created on first run", "SKIP")
    
    return appended


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed evergreens with upstream monitoring tasks")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()
    
    log("=" * 60, "INFO")
    log("Evergreen Toolkit - Seed Upstream Monitoring Tasks", "INFO")
    log("=" * 60, "INFO")
    
    if args.dry_run:
        log("DRY RUN - No changes will be made", "WARNING")
    
    print("\n📊 Seeding upstream-architecture evergreen...")
    seed_upstream_architecture(dry_run=args.dry_run)
    
    print("\n🧠 Seeding household-memory evergreen...")
    seed_household_memory(dry_run=args.dry_run)
    
    print("\n" + "=" * 60)
    print("✅ Seeding complete!")
    print("\nNext steps:")
    print("1. Review AGENDA.md files for seeded tasks")
    print("2. Run first evergreen cycle to execute tasks")
    print("3. Tasks will populate STATE.md with upstream watchlist")
    print("=" * 60)


if __name__ == "__main__":
    main()
