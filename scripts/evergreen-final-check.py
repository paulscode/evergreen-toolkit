#!/usr/bin/env python3
"""
Evergreen Final Check - Run after all evergreens should be complete.

Checks if all evergreens ran successfully today and sends a status notification
via your configured messaging system (WhatsApp, Telegram, etc.).

Usage: python3 scripts/evergreen-final-check.py [--force] [--notify-target "+11234567890"]

Options:
  --force, -f         Send status even if everything is good (default: only on failure)
  --notify-target NUM  Phone number or channel ID for notification (default: from EVERGREEN_NOTIFY_TARGET env var)
  --phone-number NUM   Alias for --notify-target (backward compatibility)

For OpenClaw integration: Uses `openclaw message send` to deliver notifications.
Configure your notification channel in openclaw.json before running.
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"
LOGS_DIR = WORKSPACE / "logs"

# Default phone number — set via EVERGREEN_NOTIFY_TARGET env var or --phone-number flag
DEFAULT_PHONE_NUMBER = os.environ.get("EVERGREEN_NOTIFY_TARGET")

# Import shared utility
sys.path.insert(0, str(Path(__file__).parent))
from evergreen_utils import discover_evergreens

# When to run: After all evergreens should be complete (e.g., 6:00 AM local time)
# Schedule in cron: 0 6 * * *

def log(message: str, level: str = "INFO"):
    """Print and log a message."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    log_file = LOGS_DIR / "evergreen-final-check.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(log_line + "\n")


def get_timing(evergreen: str) -> dict:
    """Get timing data for an evergreen."""
    timing_file = EVERGREENS_DIR / evergreen / "timing.json"
    if timing_file.exists():
        try:
            return json.loads(timing_file.read_text())
        except Exception:
            return {}
    return {}


def is_today(timestamp: str) -> bool:
    """Check if an ISO timestamp is from today (local timezone)."""
    if not timestamp:
        return False
    
    try:
        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        
        # Convert to local timezone (system default)
        dt_local = dt.astimezone()
        
        # Check if it's today
        today_local = datetime.now().astimezone().date()
        return dt_local.date() == today_local
        
    except Exception:
        return False


def check_evergreens() -> dict:
    """
    Check status of all evergreens.
    
    Returns dict with:
    - all_good: bool
    - issues: list of issue descriptions
    - details: dict of per-evergreen status
    """
    issues = []
    details = {}
    
    for evergreen in discover_evergreens():
        timing = get_timing(evergreen)
        
        status = timing.get("status", "unknown")
        completed_at = timing.get("completed_at")
        started_at = timing.get("started_at")
        
        details[evergreen] = {
            "status": status,
            "completed_at": completed_at,
            "started_at": started_at,
            "ran_today": is_today(completed_at)
        }
        
        # Check if it ran today
        if not is_today(completed_at):
            issues.append(f"**{evergreen}**: Did not run today (last: {completed_at or 'never'})")
        elif status in ("completed", "partial"):
            pass  # Success — partial means ran but couldn't finish all planned work
        elif status == "failed":
            issues.append(f"**{evergreen}**: Failed during execution")
        elif status == "timeout":
            issues.append(f"**{evergreen}**: Timed out")
        elif status == "skipped":
            issues.append(f"**{evergreen}**: Skipped (scripted executor — use AI runner for full coverage)")
        elif status == "requires_ai":
            issues.append(f"**{evergreen}**: Requires AI runner (scripted executor cannot run this evergreen)")
        elif status == "error":
            issues.append(f"**{evergreen}**: Crashed with error")
        elif status == "in_progress":
            # Check how long it's been running
            if started_at:
                try:
                    start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds() / 60
                    if elapsed > 30:
                        issues.append(f"**{evergreen}**: Still running ({elapsed:.0f} min - possible stall)")
                except Exception:
                    pass
    
    return {
        "all_good": len(issues) == 0,
        "issues": issues,
        "details": details
    }


def send_notification(message: str, phone_number: str):
    """
    Send notification via OpenClaw message tool.
    
    Uses `openclaw message send` which delivers via your configured channel
    (WhatsApp, Telegram, etc.). The channel must be authenticated in openclaw.json.
    """
    try:
        cmd = [
            "openclaw", "message", "send",
            "--target", phone_number,
            "--message", message
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE
        )
        
        if result.returncode == 0:
            # Extract message ID if present
            if "Message ID:" in result.stdout:
                msg_id = result.stdout.split("Message ID:")[-1].strip()
                log(f"Notification sent successfully (Message ID: {msg_id})", "SUCCESS")
            else:
                log("Notification sent successfully", "SUCCESS")
            return True
        else:
            log(f"Failed to send notification: {result.stderr}", "ERROR")
            return False
            
    except FileNotFoundError:
        log("openclaw command not found - is OpenClaw installed?", "ERROR")
        return False
    except Exception as e:
        log(f"Failed to send notification: {e}", "ERROR")
        return False


def build_message(result: dict, today: str) -> str:
    """Build the notification message."""
    if result["all_good"]:
        message = f"✅ **Evergreen Status - {today}**\n\n"
        message += "**All evergreens completed successfully!**\n\n"
    else:
        message = f"🚨 **Evergreen Alert - {today}**\n\n"
        message += "**Issues detected:**\n"
        for issue in result["issues"]:
            message += f"• {issue}\n"
        message += "\n"
    
    message += "**Status summary:**\n"
    for evergreen, details in result["details"].items():
        status_icon = "✅" if details["ran_today"] and details["status"] == "completed" else "❌"
        status_text = details["status"]
        
        # Add timing info if available
        timing_info = ""
        if details.get("started_at") and details.get("completed_at"):
            try:
                start = datetime.fromisoformat(details["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(details["completed_at"].replace("Z", "+00:00"))
                duration = int((end - start).total_seconds())
                if duration > 60:
                    timing_info = f" ({duration//60} min)"
                else:
                    timing_info = f" ({duration} sec)"
            except Exception:
                pass
        message += f"{status_icon} {evergreen}: {status_text}{timing_info}\n"
    
    if result["all_good"]:
        message += "\n🎉 Everything's running smoothly!"
    else:
        message += "\n**Next steps:**\n"
        message += "1. Check logs: `tail -100 logs/evergreen-*.log`\n"
        message += "2. Review timing: `cat evergreens/<name>/timing.json | jq`\n"
        message += "3. Re-run failed evergreen: `python3 scripts/run-single-evergreen.py --evergreen <name>`\n"
    
    message += "\n\n_Details in `logs/evergreen-final-check.log`_"
    
    return message


def main():
    parser = argparse.ArgumentParser(description="Evergreen Final Check")
    parser.add_argument("--force", "-f", action="store_true", 
                        help="Send status even if everything is good (default: only on failure)")
    parser.add_argument("--status", "-s", action="store_true",
                        help="Show status as JSON without sending notifications")
    parser.add_argument("--notify-target", "--phone-number", type=str, default=DEFAULT_PHONE_NUMBER,
                        help="Phone number or channel ID for notification (required for sending)")
    args = parser.parse_args()
    
    log("Running evergreen final check...", "INFO")
    
    result = check_evergreens()
    
    if args.status:
        print(json.dumps(result, indent=2))
        return 0 if result["all_good"] else 1
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Always send if force mode, otherwise only on failure
    should_send = args.force or not result["all_good"]
    
    if should_send:
        if not args.notify_target:
            log("No notification target configured. Use --notify-target or set EVERGREEN_NOTIFY_TARGET env var.", "WARNING")
            print("⚠️  Notification skipped — no notification target configured")
        else:
            if args.force and result["all_good"]:
                log("Force mode - sending success summary", "INFO")
            else:
                log(f"Sending alert: {len(result['issues'])} issue(s) detected", "WARNING")
            
            message = build_message(result, today)
            send_notification(message, args.notify_target)
    else:
        log("All evergreens healthy - no notification sent (use --force to always send)", "INFO")
    
    # Write status file for reference
    status_file = WORKSPACE / ".evergreen-final-check-status.json"
    status_file.write_text(json.dumps({
        "last_check": datetime.now(timezone.utc).isoformat(),
        "all_good": result["all_good"],
        "issue_count": len(result["issues"]),
        "notification_sent": should_send,
    }, indent=2))
    
    # Print summary
    if result["all_good"]:
        print("✅ All evergreens healthy")
        return 0
    else:
        print(f"❌ {len(result['issues'])} issue(s) detected")
        for issue in result["issues"]:
            print(f"  - {issue}")
        print(f"\nNotification {'sent' if should_send else 'not sent'} to {args.notify_target}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
