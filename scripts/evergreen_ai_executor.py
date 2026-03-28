#!/usr/bin/env python3
"""
AI-Orchestrated Evergreen Cycle Executor

This script is called by an AI agent during the heartbeat session to execute
one full 8-step evergreen cycle. The AI handles cognitive work (research,
analysis, writing), while this script handles mechanical operations.

Usage:
  python3 evergreen_ai_executor.py --evergreen system-health --mode full
  
  # Or step-by-step for AI orchestration:
  python3 evergreen_ai_executor.py --evergreen system-health --step research

The AI agent should:
1. Call this script with --mode full for complete automation
2. OR call step-by-step for fine-grained control
3. Read the output/context files to continue the cycle
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Ensure sibling modules (evergreen_utils) are importable
sys.path.insert(0, str(Path(__file__).parent))

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"
LOGS_DIR = WORKSPACE / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log(message: str, evergreen: Optional[str] = None):
    """Print and log a message."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    prefix = f"[{timestamp}]"
    if evergreen:
        prefix += f" [{evergreen}]"
    print(f"{prefix} {message}")
    
    # Write to log file
    evergreen_str = evergreen or "executor"
    log_file = LOGS_DIR / f"evergreen-ai-{evergreen_str}.log"
    with open(log_file, "a") as f:
        f.write(f"{prefix} {message}\n")


def get_agenda_file(evergreen: str) -> Path:
    """Get the AGENDA.md file path."""
    agenda_file = EVERGREENS_DIR / evergreen / "AGENDA.md"
    if not agenda_file.exists():
        # Create from template
        template_file = WORKSPACE / "config" / "agenda-template.md"
        if template_file.exists():
            import shutil
            shutil.copy(template_file, agenda_file)
        else:
            agenda_file.write_text(f"# {evergreen.replace('-', ' ').title()} - Agenda for {datetime.now().strftime('%Y-%m-%d')}\n\n## Tasks\n- [ ] TBD\n")
    return agenda_file


def get_state_file(evergreen: str) -> Path:
    """Get the STATE.md file path."""
    return EVERGREENS_DIR / evergreen / "STATE.md"


def read_context(evergreen: str) -> dict:
    """Read current context for an evergreen."""
    context = {
        "evergreen": evergreen,
        "agenda": None,
        "state": None,
        "last_cycle": None,
        "unfinished_tasks": []
    }
    
    agenda_file = get_agenda_file(evergreen)
    state_file = get_state_file(evergreen)
    
    if agenda_file.exists():
        context["agenda"] = agenda_file.read_text()
    
    if state_file.exists():
        content = state_file.read_text()
        context["state"] = content
        
        # Extract Next Steps
        in_steps = False
        for line in content.split("\n"):
            if line.startswith("## Next Steps"):
                in_steps = True
                continue
            if in_steps and line.startswith("##"):
                break
            if in_steps and ("[ ]" in line or "pending" in line.lower()):
                context["unfinished_tasks"].append(line.strip())
    
    # Get timing
    timing_file = EVERGREENS_DIR / evergreen / "timing.json"
    if timing_file.exists():
        try:
            context["last_cycle"] = json.loads(timing_file.read_text())
        except Exception:
            pass
    
    # Add autonomy guidelines
    context["autonomy"] = """
### 🎯 Your Autonomy

**AUTO-APPLY (No Permission Needed):**
- File permission fixes (`chmod 600`, `chmod 700`)
- Adding missing directories (`mkdir -p logs/`)
- Updating timestamps, versions in STATE.md
- Maintaining "Completed Recently" (3-5 items)
- Restarting configured services (`systemctl restart`)
- Clearing temp files (<1GB, non-critical)
- Fixing typos in documentation

**ASK FIRST (notify your household members):**
- Changing file ownership (`chown`)
- Modifying cron jobs
- Installing packages
- Network/firewall changes
- Exposing services beyond LAN
- External communications

**Rule:** If you can undo it in <30 seconds with one command, auto-apply.
When blocked: Document in AGENDA.md → Send notification → Continue with other tasks.
"""
    
    return context


def run_step(evergreen: str, step: str, params: Optional[dict] = None) -> dict:
    """Run one step of the 8-step cycle."""
    log(f"Running step: {step}", evergreen)
    
    # Mechanical steps - handled by script
    if step == "housekeep":
        from pathlib import Path
        import shutil
        
        agenda_file = EVERGREENS_DIR / evergreen / "AGENDA.md"
        history_dir = EVERGREENS_DIR / evergreen / "agenda-history"
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # Archive current agenda
        if agenda_file.exists():
            today = datetime.now().strftime("%Y-%m-%d")
            archive_name = f"{today}.md"
            counter = 1
            while (history_dir / archive_name).exists():
                archive_name = f"{today}-{counter}.md"
                counter += 1
            shutil.move(str(agenda_file), str(history_dir / archive_name))
            log(f"Archived agenda to {archive_name}", evergreen)
        
        from evergreen_utils import DISPLAY_NAMES as _canonical_names
        # NOTE: These display names are more descriptive than the canonical
        # DISPLAY_NAMES used in the dashboard. They're used in agenda headers.
        # The _canonical_names import is kept for potential future consistency checks.
        display_names = {
            "upstream-architecture": "Upstream Architecture & Constraints",
            "system-health": "System Health, Reliability & Disaster Recovery",
            "prompt-injection": "Prompt-Injection Defense & Safety Hardening",
            "household-memory": "Household Memory Architecture",
        }
        display = display_names.get(evergreen, evergreen.replace("-", " ").title())
        
        agenda_content = f"""# {display} - Agenda for {datetime.now().strftime('%Y-%m-%d')}

## Cycle Status
- Started: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
- Status: in_progress

## Tasks for This Cycle

### 1. [Your AI agent should define Task 1 based on research]
- Status: ⏳ pending
- Findings:
- Actions taken:
- Recommendations:
- Reasoning:

### 2. [Your AI agent should define Task 2]
- Status: ⏳ pending
- Findings:
- Actions taken:
- Recommendations:
- Reasoning:

### 3. [Your AI agent should define Task 3]
- Status: ⏳ pending
- Findings:
- Actions taken:
- Recommendations:
- Reasoning:

## Research Findings
- [AI: Fill in findings from research phase]

## Blockers & Missing Information
- None (or list any)

## Next Cycle Plan (Seeds Tomorrow's Agenda)
- [AI: Define based on this cycle's work]

## Notifications Sent
- None

---
Completed: TBD
Duration: TBD
"""
        agenda_file.write_text(agenda_content)
        log(f"Created new agenda template", evergreen)
        
        return {"status": "success", "agenda_file": str(agenda_file)}
    
    elif step == "timing_start":
        timing = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress"
        }
        timing_file = EVERGREENS_DIR / evergreen / "timing.json"
        timing_file.write_text(json.dumps(timing, indent=2))
        log(f"Cycle started", evergreen)
        return {"status": "success", "timing": timing}
    
    elif step == "timing_complete":
        timing_file = EVERGREENS_DIR / evergreen / "timing.json"
        if timing_file.exists():
            timing = json.loads(timing_file.read_text())
            started = datetime.fromisoformat(timing["started_at"].replace("Z", "+00:00"))
            duration = (datetime.now(timezone.utc) - started).total_seconds()
            timing.update({
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": round(duration, 1),
                "status": "completed"
            })
            timing_file.write_text(json.dumps(timing, indent=2))
            log(f"Cycle completed in {duration:.1f}s", evergreen)
            return {"status": "success", "duration": duration}
        return {"status": "error", "message": "No timing file found"}
    
    elif step == "dashboard_update":
        try:
            result = subprocess.run(
                [sys.executable, str(WORKSPACE / "scripts" / "update_evergreen_dashboard.py")],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(WORKSPACE)
            )
            if result.returncode == 0:
                log(f"Dashboard updated", evergreen)
            else:
                log(f"Dashboard update failed: {result.stderr}", evergreen)
        except Exception as e:
            log(f"Dashboard update error: {e}", evergreen)
        
        # Fix any raw file:// links to .md files
        try:
            result = subprocess.run(
                ["node", str(WORKSPACE / "scripts" / "fix-markdown-links.js")],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(WORKSPACE)
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if "Links fixed:" in output:
                    # Extract count
                    for line in output.split("\n"):
                        if "Links fixed:" in line:
                            count = line.split(":")[1].strip()
                            if count != "0":
                                log(f"Markdown link fixer: {count} link(s) updated", evergreen)
                            break
        except Exception as e:
            log(f"Markdown link fixer error: {e}", evergreen)
        
        return {"status": "success"}
    
    elif step == "delete_trigger":
        trigger_file = EVERGREENS_DIR / evergreen / ".run_requested"
        if trigger_file.exists():
            trigger_file.unlink()
            log(f"Trigger file deleted", evergreen)
        return {"status": "success"}
    
    # AI cognitive steps - return context for AI to process
    elif step == "research":
        context = read_context(evergreen)
        research_prompt = build_research_prompt(evergreen, context)
        log(f"Research context prepared - AI should execute research", evergreen)
        return {
            "status": "awaiting_ai",
            "step": "research",
            "context": context,
            "research_prompt": research_prompt,
            "next_step": "analyze"
        }
    
    elif step == "analyze":
        context = read_context(evergreen)
        analyze_prompt = build_analyze_prompt(evergreen, context)
        log(f"Analysis context prepared - AI should analyze findings", evergreen)
        return {
            "status": "awaiting_ai",
            "step": "analyze",
            "context": context,
            "analyze_prompt": analyze_prompt,
            "next_step": "plan"
        }
    
    elif step == "plan":
        context = read_context(evergreen)
        plan_prompt = build_plan_prompt(evergreen, context)
        log(f"Planning context prepared - AI should define tasks", evergreen)
        return {
            "status": "awaiting_ai",
            "step": "plan",
            "context": context,
            "plan_prompt": plan_prompt,
            "next_step": "update"
        }
    
    elif step == "update":
        context = read_context(evergreen)
        update_prompt = build_update_prompt(evergreen, context)
        log(f"Update context prepared - AI should finalize agenda", evergreen)
        return {
            "status": "awaiting_ai",
            "step": "update",
            "context": context,
            "update_prompt": update_prompt
        }
    
    else:
        log(f"Unknown step: {step}", evergreen)
        return {"status": "error", "message": f"Unknown step: {step}"}


def build_research_prompt(evergreen: str, context: dict) -> str:
    """Build research prompt for AI agent."""
    
    prompts = {
        "upstream-architecture": """## Research Tasks for Upstream Architecture

1. **Check OpenClaw Version Status**
   - Run `openclaw status` and extract version
   - Check git status: `git status --branch --porcelain`
   - Compare with upstream (how many commits behind?)
   - Check dependency status

2. **Review Constraint Documentation**
   - Local hardware specs (RAM, CPU, disk)
   - Remote GPU availability and models
   - Current model strategy vs alternatives

3. **Tool and Capability Audit**
   - List available tools
   - Check which are working/broken
   - Identify gaps

4. **Security Posture**
   - Check config file permissions
   - Review any security warnings
   - Credential file security

**Output Format:**
Write findings to the agenda's "Research Findings" section with:
- Bullet points for each finding
- Status indicators (✅/❌/⚠️)
- Specific data (versions, sizes, counts)
""",
        
        "system-health": """## Research Tasks for System Health

1. **Check System Resources**
   - Disk usage: `df -h /`
   - Memory usage: `free -h`
   - Load average: `uptime`

2. **Verify OpenClaw Gateway**
   - Run `openclaw status`
   - Check latency
   - Verify plugins operational

3. **Review Backup Status**
   - Check backup directory: `ls -lt ~/.backup/`
   - Verify latest backup size and date
   - Check backup rotation

4. **Check Service Status**
   - Cron jobs running: `systemctl status cron`
   - Any systemd services
   - Git workspace status

5. **Security Review**
   - File permissions on sensitive files
   - Config security warnings
   - Network exposure

**Output Format:**
Write findings to agenda with specific metrics and health indicators.
""",
        
        "prompt-injection": """## Research Tasks for Prompt-Injection Defense

1. **Review Vulnerability Tracking**
   - Read STATE.md for current vulnerability status (V001-V005)
   - Verify all mitigations still in place
   - Check for new vulnerabilities

2. **Skill Vetting Compliance**
   - Check if evergreens/prompt-injection/VETTING-CHECKLIST.md exists
   - Review recent skill installations
   - Verify checklist was used

3. **Memory Validation**
   - Verify memory/scripts/validate_memory.py exists and is called (stub — implementation is future work)
   - Check for any injection attempts in logs
   - Test validation patterns

4. **Tool Execution Audit**
   - Review TOOL-AUDIT.md
   - Check for any unauthorized tool usage
   - Verify confirmation prompts working

5. **Credential Security**
   - Check permissions on credential files
   - Verify no plaintext credentials in logs
   - Review access patterns

**Output Format:**
Security status summary with vulnerability-by-vulnerability checklist.
""",
        
        "household-memory": """## Research Tasks for Household Memory

1. **Review Memory Capture Pipeline**
   - Check Redis connectivity: `redis-cli ping`
   - Check user buffers: `redis-cli keys "mem:*"`
   - Verify save_mem.py working

2. **True Recall Curation**
   - Check if curation ran (logs/memory-curation.log)
   - Review what was extracted
   - Assess quality of curation

3. **Per-User Memory Isolation**
   - Verify separate memories per user
   - Check for any cross-contamination
   - Review privacy boundaries

4. **Theory-of-Mind Implementation**
   - Check USER.md and MEMORY.md
   - Verify relationship tracking
   - Review any gaps in user profiles

5. **Memory Architecture Improvements**
   - Any performance issues?
   - Storage growth trends
   - Needed optimizations

**Output Format:**
Memory system health report with per-user status and recommendations.
"""
    }
    
    specific_prompt = prompts.get(evergreen, f"Conduct research for {evergreen} evergreen and document findings.")
    return f"{context.get('autonomy', '')}\n\n---\n\n{specific_prompt}"


def build_analyze_prompt(evergreen: str, context: dict) -> str:
    """Build analysis prompt for AI agent."""
    return f"""## Analysis Tasks for {evergreen}

Based on your research findings above, analyze:

1. **What patterns do you see?**
   - Trends over time
   - Recurring issues
   - Improvements or degradations

2. **What are the risks?**
   - Security concerns
   - Performance issues
   - Technical debt

3. **What are the opportunities?**
   - Optimization potential
   - Quick wins
   - Strategic improvements

4. **What's the priority?**
   - Critical (act now)
   - High (this week)
   - Medium (this month)
   - Low (backlog)

Write your analysis to the agenda's "Analysis" section (add it if missing).
"""


def build_plan_prompt(evergreen: str, context: dict) -> str:
    """Build planning prompt for AI agent."""
    return f"""## Planning Tasks for {evergreen}

Based on your analysis, define 3-5 specific tasks for this cycle:

1. **Task should be specific and actionable**
   - Not "Check X" but "Check X and do Y if Z"
   - Include success criteria
   - Include priority

2. **Each task should have:**
   - Clear description
   - Expected outcome
   - Estimated effort (minutes)
   - Priority (Critical/High/Medium/Low)

3. **Seed tomorrow's agenda:**
   - What unfinished work should continue?
   - What new tasks emerged?

Update the agenda's "Tasks for This Cycle" section with your plan.
"""


def build_update_prompt(evergreen: str, context: dict) -> str:
    """Build update prompt for AI agent."""
    
    # Evergreen-specific instructions for Completed Recently section
    completed_instructions = {
        "upstream-architecture": """
4. **Update "Completed Recently" in STATE.md:**
   - Add today's date and key accomplishment
   - Examples: "[2009-01-03] AI orchestration implemented", "[2008-12-31] Voice-call extension merged"
   - Keep 3-5 recent items (remove oldest if more than 5)
   - Focus on: version updates, model strategy changes, tool additions, constraint discoveries
""",
        "system-health": """
4. **Update "Completed Recently" in STATE.md:**
   - Add today's date and key accomplishment
   - Examples: "[2009-01-03] Config security fixed", "[2008-12-28] Backup script deployed"
   - Keep 3-5 recent items (remove oldest if more than 5)
   - Focus on: health fixes, backup improvements, monitoring additions, recovery tests
""",
        "prompt-injection": """
4. **Update "Completed Recently" in STATE.md:**
   - Add today's date and key accomplishment
   - Examples: "[2008-12-28] Blue Team Cycle 2: Hardened all 5 vulnerabilities"
   - Keep 3-5 recent items (remove oldest if more than 5)
   - Focus on: vulnerability fixes, security audits, vetting completions, validation updates
""",
        "household-memory": """
4. **Update "Completed Recently" in STATE.md:**
   - Add today's date and key accomplishment
   - Examples: "[2008-12-28] True Recall curator fully operational"
   - Keep 3-5 recent items (remove oldest if more than 5)
   - Focus on: memory pipeline improvements, curation fixes, category updates, user-specific wins
"""
    }
    
    specific_instructions = f"""## Finalization Tasks for {evergreen}

Complete the cycle by:

1. **Update agenda with completed work:**
   - Mark tasks as done ✅ or pending ⏳
   - Fill in findings, actions, recommendations, reasoning for each task
   - Add completion timestamp

2. **Update STATE.md:**
   - Update "Overall Health" status (🟢/🟡/🔴)
   - Update "Last Cycle" timestamp to today
   - Update "Next Steps" with any carryover work (keep 3-5 items)

{completed_instructions.get(evergreen, "")}

3. **Document any blockers:**
   - What prevented completion?
   - What help/information is needed?

4. **Final status:**
   - Set status to "completed" in agenda
   - Write summary of cycle outcome
   - Note any notifications sent
"""
    return f"{context.get('autonomy', '')}\n\n---\n\n{specific_instructions}"


def run_full_cycle(evergreen: str) -> dict:
    """
    Run a complete 8-step evergreen cycle.
    
    This function orchestrates the full cycle, calling each step in order.
    For cognitive steps (research, analyze, plan, update), it returns control
    to the AI agent with context and prompts.
    
    NOTE: This function returns after the research step with status 
    "awaiting_ai", since the AI agent must execute the cognitive work.
    The intended usage is for an AI agent to call this script, receive
    the "awaiting_ai" response, then execute research/analysis/planning
    cognitively, and continue the cycle.
    
    For cron-based automation without AI orchestration, use the heartbeat
    system which injects system events to wake the OpenClaw agent.
    
    Returns a status dict with results.
    """
    log(f"{'='*60}")
    log(f"Starting AI-orchestrated evergreen cycle: {evergreen}")
    log(f"{'='*60}")
    
    results = {
        "evergreen": evergreen,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": {},
        "status": "in_progress"
    }
    
    # Step 1: Start timing
    results["steps"]["timing_start"] = run_step(evergreen, "timing_start")
    
    # Step 2: Housekeep (mechanical)
    results["steps"]["housekeep"] = run_step(evergreen, "housekeep")
    
    # Step 3: Research (AI cognitive - return to AI)
    results["steps"]["research"] = run_step(evergreen, "research")
    if results["steps"]["research"]["status"] == "awaiting_ai":
        log(f"🤖 RESEARCH: AI agent should now execute research")
        log(f"   Prompt saved in results - AI should call with completed findings")
        return results  # Return to AI for research execution
    
    # Continue only if AI already provided findings (orchestrated call)
    # Step 4: Analyze
    results["steps"]["analyze"] = run_step(evergreen, "analyze")
    if results["steps"]["analyze"].get("status") == "awaiting_ai":
        return results
    
    # Step 5: Plan
    results["steps"]["plan"] = run_step(evergreen, "plan")
    if results["steps"]["plan"].get("status") == "awaiting_ai":
        return results
    
    # Step 6: Update (mechanical)
    results["steps"]["update"] = run_step(evergreen, "update")
    
    # Step 7: Complete timing
    results["steps"]["timing_complete"] = run_step(evergreen, "timing_complete")
    
    # Step 8: Update dashboard (mechanical)
    results["steps"]["dashboard_update"] = run_step(evergreen, "dashboard_update")
    
    results["status"] = "completed"
    results["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    log(f"{'='*60}")
    log(f"✅ Evergreen cycle complete: {evergreen}")
    log(f"{'='*60}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="AI-orchestrated evergreen executor")
    parser.add_argument("--evergreen", "-e", required=True, help="Evergreen name")
    parser.add_argument("--mode", choices=["full", "step", "auto"], default="auto",
                       help="Full cycle (with AI pauses), step-by-step, or fully automated")
    parser.add_argument("--step", help="Specific step to run (for step mode)")
    parser.add_argument("--params", help="JSON parameters for step")
    args = parser.parse_args()
    
    if args.mode == "step":
        if not args.step:
            print("Error: --step required for step mode")
            sys.exit(1)
        
        params = json.loads(args.params) if args.params else {}
        result = run_step(args.evergreen, args.step, params)
        print(json.dumps(result, indent=2))
        
        if result.get("status") == "error":
            sys.exit(1)
    else:
        # Full cycle mode (orchestrated by AI)
        result = run_full_cycle(args.evergreen)
        print(json.dumps(result, indent=2))
        
        if result.get("status") == "error":
            sys.exit(1)
        elif result.get("status") in ("awaiting_ai", "in_progress"):
            sys.exit(2)  # Intermediate state — not an error, but not complete
    
    sys.exit(0)


if __name__ == "__main__":
    main()
