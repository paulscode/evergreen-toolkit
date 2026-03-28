#!/usr/bin/env python3
"""
Create today's memory file if it doesn't exist
Usage: create_daily_memory.py [date] [--user-id USER]
"""

import sys
import os
from datetime import datetime, timezone

def get_local_date():
    """Get current date in local time"""
    from datetime import datetime, timezone
    import time
    
    # Use system local time
    now = datetime.now()
    return now.strftime('%Y-%m-%d')

def create_daily_memory(date_str=None, user_id=None):
    """Create memory file for the given date"""
    if date_str is None:
        date_str = get_local_date()
    
    workspace = os.getenv("OPENCLAW_WORKSPACE", os.path.join(os.path.expanduser("~"), ".openclaw", "workspace"))
    memory_dir = os.path.join(workspace, "memory")
    if user_id:
        memory_dir = os.path.join(memory_dir, user_id)
    filepath = os.path.join(memory_dir, f"{date_str}.md")
    
    # Ensure directory exists
    os.makedirs(memory_dir, exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(filepath):
        print(f"✅ Memory file already exists: {filepath}")
        return filepath
    
    # Create new daily memory file
    content = f"""# {date_str} — Daily Memory Log

## Session Start
- **Date:** {date_str}
- **Agent:** {os.getenv('AGENT_NAME', 'Assistant')}

## Activities

*(Log activities, decisions, and important context here)*

## Notes

---
*Stored for long-term memory retention*
"""
    
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Created memory file: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error creating memory file: {e}")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create daily memory file")
    parser.add_argument("date", nargs="?", help="Date in YYYY-MM-DD format")
    parser.add_argument("--user-id", help="User ID for per-user directory")
    args = parser.parse_args()
    create_daily_memory(args.date, user_id=args.user_id)
