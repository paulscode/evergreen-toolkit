#!/usr/bin/env python3
"""
Automatically save current session memory with user detection.

This script:
1. Finds the most recent session JSONL file
2. Detects the user ID from phone numbers or metadata
3. Calls save_mem.py with the correct user

Usage: python3 save_current_session_memory.py [--verbose]

Configuration:
    Set USER_PHONE_MAP in this script or via environment:
      OPENCLAW_SESSIONS_DIR  - Path to session JSONL files
      OPENCLAW_WORKSPACE     - Workspace root path
      DEFAULT_USER_ID        - Fallback user ID when detection fails
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Config
SESSIONS_DIR = Path(os.getenv("OPENCLAW_SESSIONS_DIR", str(Path.home() / ".openclaw" / "agents" / "main" / "sessions")))
WORKSPACE = Path(os.getenv("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
SAVE_MEM_SCRIPT = Path(__file__).parent / "save_mem.py"
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "user1")

# ============================================================
# USER PHONE MAP - Customize for your household!
# Map phone numbers to user IDs for automatic detection.
# Include both with and without leading country code.
# ============================================================
USER_PHONE_MAP = {
    # "+11234567890": "alice",
    # "11234567890": "alice",
    # "+12345678901": "bob",
    # "12345678901": "bob",
}

# WhatsApp number patterns in messages
PHONE_PATTERNS = [
    r'\+?1?\s?[-.]?\s?\(?\d{3}\)?[-.]?\s?\d{3}[-.]?\s?\d{4}',
]


def get_latest_session():
    """Find the most recently modified session JSONL file."""
    if not SESSIONS_DIR.exists():
        return None

    files = list(SESSIONS_DIR.glob("*.jsonl"))
    if not files:
        return None

    return max(files, key=lambda p: p.stat().st_mtime)


def detect_user_from_session(session_file):
    """Detect user ID from session content by scanning for phone numbers."""
    try:
        with open(session_file, 'r') as f:
            # Read last few lines (most recent messages)
            lines = f.readlines()[-50:]

            for line in reversed(lines):
                try:
                    entry = json.loads(line.strip())

                    # Check for user field in entry
                    if entry.get('type') == 'message' and 'message' in entry:
                        msg = entry['message']

                        # Check for phone number in message metadata
                        if 'from' in msg:
                            from_field = str(msg.get('from', ''))
                            for phone, user_id in USER_PHONE_MAP.items():
                                if phone in from_field:
                                    return user_id

                        # Check content for phone numbers
                        content = ""
                        if isinstance(msg.get('content'), list):
                            for item in msg['content']:
                                if isinstance(item, dict) and 'text' in item:
                                    content += item['text']
                        elif isinstance(msg.get('content'), str):
                            content = msg['content']

                        # Search for phone numbers in content
                        for pattern in PHONE_PATTERNS:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                # Normalize number
                                clean = re.sub(r'[-.\s()]+', '', match).replace('+', '')
                                if clean in USER_PHONE_MAP:
                                    return USER_PHONE_MAP[clean]

                    # Check for channel metadata
                    if 'channel' in entry:
                        channel = entry.get('channel', '')
                        if 'whatsapp' in channel.lower():
                            # Check metadata for phone
                            meta = entry.get('metadata', {})
                            if isinstance(meta, dict):
                                from_num = meta.get('from', '')
                                for phone, user_id in USER_PHONE_MAP.items():
                                    if phone in str(from_num):
                                        return user_id

                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

    except Exception as e:
        print(f"Error reading session: {e}", file=sys.stderr)

    # Default user when detection fails
    return DEFAULT_USER_ID


def detect_user_from_channel():
    """Try to detect user from OpenClaw channel context.

    Override this function if your OpenClaw setup provides
    channel-level user identification.
    """
    return None


def main():
    verbose = "--verbose" in sys.argv

    # Verify save_mem.py exists
    if not SAVE_MEM_SCRIPT.exists():
        print(f"❌ save_mem.py not found at: {SAVE_MEM_SCRIPT}", file=sys.stderr)
        print("   Ensure this script is in the same directory as save_mem.py", file=sys.stderr)
        sys.exit(1)

    # Try channel detection first
    user_id = detect_user_from_channel()

    # Fall back to session analysis
    if not user_id:
        session_file = get_latest_session()
        if not session_file:
            print("❌ No session files found", file=sys.stderr)
            if verbose:
                print(f"   Searched: {SESSIONS_DIR}", file=sys.stderr)
            sys.exit(1)

        user_id = detect_user_from_session(session_file)
        if verbose:
            print(f"🔍 Detected user from session: {user_id}")
            print(f"   Session: {session_file.name}")

    # Call save_mem.py with detected user
    print(f"💾 Saving memory for user: {user_id}")

    env = os.environ.copy()
    env["USER_ID"] = user_id

    cmd = [sys.executable, str(SAVE_MEM_SCRIPT), "--user-id", user_id]
    result = subprocess.run(
        cmd,
        env=env,
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
