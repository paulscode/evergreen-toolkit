#!/usr/bin/env python3
"""
Evergreen Scripted Executor - Runs evergreen checks without AI orchestration.
For use in cron jobs where AI agent coordination is not available.

This performs mechanical health checks and updates files, but skips
cognitive research/analysis/planning that would require an AI agent.

Note: Currently implements checks for system-health and prompt-injection only.
upstream-architecture and household-memory require AI orchestration and will
be skipped with a warning if invoked in this mode.
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"
LOGS_DIR = WORKSPACE / "logs"

def log(message: str, evergreen: str = None):
    """Print and log a message."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    prefix = f"[{timestamp}]"
    if evergreen:
        prefix += f" [{evergreen}]"
    print(f"{prefix} {message}")
    
    log_file = LOGS_DIR / "evergreen-scripted.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"{prefix} {message}\n")


def run_scripted_check(evergreen: str) -> bool:
    """
    Run a scripted (non-AI) evergreen check.
    
    Returns True if successful, False otherwise.
    """
    log(f"Starting scripted check for {evergreen}", evergreen)
    
    timing_file = EVERGREENS_DIR / evergreen / "timing.json"
    agenda_file = EVERGREENS_DIR / evergreen / "AGENDA.md"
    state_file = EVERGREENS_DIR / evergreen / "STATE.md"
    
    # Check files exist
    if not timing_file.exists():
        log(f"ERROR: timing.json not found", evergreen)
        return False
    if not agenda_file.exists():
        log(f"ERROR: AGENDA.md not found", evergreen)
        return False
    
    started_at = datetime.now(timezone.utc).isoformat()
    
    try:
        # Update timing
        timing = json.loads(timing_file.read_text()) if timing_file.exists() else {}
        timing.update({
            "started_at": started_at,
            "status": "in_progress"
        })
        timing_file.write_text(json.dumps(timing, indent=2))
        
        # Run evergreen-specific scripted checks
        if evergreen == "system-health":
            run_system_health_checks(evergreen)
        elif evergreen == "prompt-injection":
            run_prompt_injection_checks(evergreen)
        else:
            log(f"⚠️  Skipping {evergreen} — requires AI orchestration (use evergreen-ai-runner.sh)", evergreen)
            # Mark as requires_ai rather than completed to avoid misleading final-check
            completed_at = datetime.now(timezone.utc).isoformat()
            timing.update({
                "completed_at": completed_at,
                "status": "requires_ai"
            })
            if "started_at" in timing and "completed_at" in timing:
                start_dt = datetime.fromisoformat(timing["started_at"].replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(timing["completed_at"].replace("Z", "+00:00"))
                timing["duration_seconds"] = round((end_dt - start_dt).total_seconds(), 1)
            timing_file.write_text(json.dumps(timing, indent=2))
            log(f"⚠️  Marked as requires_ai (use AI runner for full coverage)", evergreen)
            return True
        
        # Mark complete
        completed_at = datetime.now(timezone.utc).isoformat()
        timing.update({
            "completed_at": completed_at,
            "status": "completed"
        })
        if "started_at" in timing and "completed_at" in timing:
            start_dt = datetime.fromisoformat(timing["started_at"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(timing["completed_at"].replace("Z", "+00:00"))
            timing["duration_seconds"] = round((end_dt - start_dt).total_seconds(), 1)
        timing_file.write_text(json.dumps(timing, indent=2))
        
        log(f"✅ Scripted check completed successfully", evergreen)
        return True
        
    except Exception as e:
        log(f"❌ Scripted check failed: {e}", evergreen)
        timing = json.loads(timing_file.read_text()) if timing_file.exists() else {}
        timing.update({
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "error": str(e)
        })
        timing_file.write_text(json.dumps(timing, indent=2))
        return False


def run_system_health_checks(evergreen: str):
    """Run scripted system health checks."""
    import subprocess
    
    checks = {
        "disk": lambda: subprocess.run(["df", "-h", "/"], capture_output=True, text=True).returncode == 0,
        "memory": lambda: subprocess.run(["free", "-h"], capture_output=True, text=True).returncode == 0,
        "uptime": lambda: subprocess.run(["uptime"], capture_output=True, text=True).returncode == 0,
    }
    
    results = []
    for name, check in checks.items():
        try:
            passed = check()
            results.append(f"  - {name}: {'✅' if passed else '❌'}")
        except Exception as e:
            results.append(f"  - {name}: ❌ ({e})")
    
    # Update agenda with results
    agenda_file = EVERGREENS_DIR / evergreen / "AGENDA.md"
    content = agenda_file.read_text() if agenda_file.exists() else f"# {evergreen} - Agenda\n\n"
    
    # Add check results
    content += f"\n## Scripted Checks ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
    content += "\n".join(results)
    content += "\n"
    
    agenda_file.write_text(content)
    log(f"System health checks completed", evergreen)


def run_prompt_injection_checks(evergreen: str):
    """Run scripted prompt injection checks."""
    # Check for skill vetting checklist
    vetting_file = WORKSPACE / "evergreens" / "prompt-injection" / "VETTING-CHECKLIST.md"
    validation_script = WORKSPACE / "memory" / "scripts" / "validate_memory.py"
    
    checks = [
        ("Vetting checklist exists", vetting_file.exists()),
        ("Memory validation script exists", validation_script.exists()),  # Stub exists — full implementation is future work
    ]
    
    results = [f"  - {name}: {'✅' if passed else '❌'}" for name, passed in checks]
    
    # Update agenda
    agenda_file = EVERGREENS_DIR / evergreen / "AGENDA.md"
    content = agenda_file.read_text() if agenda_file.exists() else f"# {evergreen} - Agenda\n\n"
    
    content += f"\n## Security Checks ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
    content += "\n".join(results)
    content += "\n"
    
    agenda_file.write_text(content)
    log(f"Security checks completed", evergreen)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run scripted evergreen checks")
    parser.add_argument("--evergreen", "-e", required=True, help="Evergreen name")
    args = parser.parse_args()
    
    success = run_scripted_check(args.evergreen)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
