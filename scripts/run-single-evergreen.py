#!/usr/bin/env python3
"""
Run a single evergreen with full AI orchestration.

Called by cron with --evergreen argument. Executes the complete 8-step cycle
for one evergreen, waiting for AI research/analysis/planning to complete.

Note: This script does not use flock locking. If concurrent-run prevention is
needed, use scripts/evergreen-ai-runner.sh instead (which uses flock).

Usage: python3 scripts/run-single-evergreen.py --evergreen system-health
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"
LOGS_DIR = WORKSPACE / "logs"

# Import shared utility
sys.path.insert(0, str(Path(__file__).parent))
from evergreen_utils import discover_evergreens


# Expected runtime per evergreen (seconds) — defaults for known programs
EXPECTED_RUNTIME = {
    "upstream-architecture": 1800,  # 30 min (research-heavy)
    "system-health": 300,           # 5 min
    "prompt-injection": 600,        # 10 min
    "household-memory": 1800,       # 30 min (memory processing)
}

def log(message: str, level: str = "INFO"):
    """Print and log a message."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    log_file = LOGS_DIR / "evergreen-executor.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(log_line + "\n")


def update_timing(evergreen: str, status: str, started: str = None, completed: str = None):
    """Update the evergreen's timing.json file."""
    timing_file = EVERGREENS_DIR / evergreen / "timing.json"
    
    timing = {}
    if timing_file.exists():
        try:
            timing = json.loads(timing_file.read_text())
        except Exception:
            pass
    
    if started:
        timing["started_at"] = started
    if completed:
        timing["completed_at"] = completed
    timing["status"] = status
    
    if "started_at" in timing and "completed_at" in timing:
        try:
            start_dt = datetime.fromisoformat(timing["started_at"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(timing["completed_at"].replace("Z", "+00:00"))
            timing["duration_seconds"] = round((end_dt - start_dt).total_seconds(), 1)
        except Exception:
            pass
    
    timing_file.write_text(json.dumps(timing, indent=2))


def run_evergreen(evergreen: str, verbose: bool = False) -> bool:
    """
    Run a single evergreen through the AI executor.
    
    Returns True if successful, False otherwise.
    """
    executor = WORKSPACE / "scripts" / "evergreen_ai_executor.py"
    
    if not executor.exists():
        log(f"Executor not found: {executor}", "ERROR")
        return False
    
    valid_evergreens = discover_evergreens()
    if evergreen not in valid_evergreens:
        log(f"Invalid evergreen: {evergreen} (available: {', '.join(valid_evergreens)})", "ERROR")
        return False
    
    started_at = datetime.now(timezone.utc).isoformat()
    update_timing(evergreen, "in_progress", started=started_at)
    
    log(f"Starting {evergreen}...", "INFO")
    
    # Run the AI executor
    log_file = LOGS_DIR / f"evergreen-{evergreen}.log"
    timeout = EXPECTED_RUNTIME.get(evergreen, 600) * 2  # 2x expected time
    
    try:
        cmd = [
            sys.executable,
            str(executor),
            "--evergreen", evergreen,
            "--mode", "auto"
        ]
        
        # Run and wait for completion
        with open(log_file, "a") as log_fh:
            stdout_target = None if verbose else log_fh
            result = subprocess.run(
                cmd,
                stdout=stdout_target,
                stderr=subprocess.STDOUT,
                cwd=str(WORKSPACE),
                timeout=timeout
            )
        
        if result.returncode == 0:
            completed_at = datetime.now(timezone.utc).isoformat()
            update_timing(evergreen, "completed", completed=completed_at)
            log(f"✅ {evergreen} completed successfully", "SUCCESS")
            return True
        elif result.returncode == 2:
            # Exit code 2 = "awaiting_ai" — intermediate state, not a failure.
            # The executor returns this when cognitive steps need AI orchestration.
            completed_at = datetime.now(timezone.utc).isoformat()
            update_timing(evergreen, "partial", completed=completed_at)
            log(f"⏳ {evergreen} returned awaiting_ai (exit code 2) — partial completion", "INFO")
            return True
        else:
            completed_at = datetime.now(timezone.utc).isoformat()
            update_timing(evergreen, "failed", completed=completed_at)
            log(f"❌ {evergreen} failed with code {result.returncode}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        completed_at = datetime.now(timezone.utc).isoformat()
        update_timing(evergreen, "timeout", completed=completed_at)
        log(f"⚠️  {evergreen} timed out after {timeout}s", "WARNING")
        return False
        
    except Exception as e:
        completed_at = datetime.now(timezone.utc).isoformat()
        update_timing(evergreen, "error", completed=completed_at)
        log(f"❌ {evergreen} crashed: {e}", "ERROR")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run a single evergreen")
    parser.add_argument("--evergreen", "-e", required=False, 
                        help="Evergreen to run (upstream-architecture, system-health, prompt-injection, household-memory)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output (show executor stdout)")
    parser.add_argument("--list", action="store_true",
                        help="List all available evergreens and their status")
    parser.add_argument("--complete", action="store_true",
                        help="Run all evergreens sequentially")
    args = parser.parse_args()

    if args.list:
        print("Available evergreens:")
        for name in discover_evergreens():
            timing_file = EVERGREENS_DIR / name / "timing.json"
            status = "unknown"
            if timing_file.exists():
                try:
                    timing = json.loads(timing_file.read_text())
                    status = timing.get("status", "unknown")
                except Exception:
                    pass
            print(f"  {name:30s} [{status}]")
        sys.exit(0)

    if args.complete:
        log("Running all evergreens sequentially", "INFO")
        results = {}
        for name in discover_evergreens():
            results[name] = run_evergreen(name, verbose=args.verbose)
        failed = [n for n, ok in results.items() if not ok]
        if failed:
            log(f"Failed: {', '.join(failed)}", "ERROR")
            sys.exit(1)
        log("All evergreens completed successfully", "SUCCESS")
        sys.exit(0)

    if not args.evergreen:
        parser.error("--evergreen is required (or use --list / --complete)")

    success = run_evergreen(args.evergreen, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
