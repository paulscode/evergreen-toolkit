#!/usr/bin/env python3
"""
Update the evergreens dashboard HTML from STATE.md and timing.json files.
"""
from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"

# Import shared utilities
from evergreen_utils import discover_evergreens as _discover_evergreens, DISPLAY_NAMES


def discover_evergreens():
    """Discover available evergreens with display titles.
    Returns list of (name, display_title) tuples."""
    return [
        (name, DISPLAY_NAMES.get(name, name.replace("-", " ").title()))
        for name in _discover_evergreens()
    ]


def read_state(evergreen: str) -> dict:
    """Parse STATE.md for key info."""
    state_file = EVERGREENS_DIR / evergreen / "STATE.md"
    if not state_file.exists():
        return {"exists": False}

    content = state_file.read_text()
    result = {"exists": True, "raw": content}

    lines = content.split("\n")
    in_status = False
    in_next_steps = False
    in_completed = False
    next_steps = []
    completed = []

    for line in lines:
        # Status section
        if line.startswith("## Status"):
            in_status = True
            continue
        if in_status and line.startswith("##"):
            in_status = False
        if in_status:
            if "Overall Health:" in line:
                result["health"] = line.split(":", 1)[-1].strip()
            if "Last Cycle:" in line:
                result["last_cycle"] = line.split(":", 1)[-1].strip()

        # Next Steps section
        if line.startswith("## Next Steps"):
            in_next_steps = True
            continue
        if in_next_steps and line.startswith("##"):
            in_next_steps = False
        if in_next_steps and line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "- [")):
            next_steps.append(line.strip())

        # Completed Recently section
        if line.startswith("## Completed Recently"):
            in_completed = True
            continue
        if in_completed and line.startswith("##"):
            in_completed = False
        if in_completed and line.strip().startswith("- ["):
            completed.append(line.strip())

    # Limit dashboard display to 5 next steps and 3 completed items
    result["next_steps"] = next_steps[:5]
    result["completed"] = completed[:3]
    return result

def read_timing(evergreen: str) -> dict:
    """Read timing.json for cycle timing info."""
    timing_file = EVERGREENS_DIR / evergreen / "timing.json"
    if not timing_file.exists():
        return {}
    try:
        return json.loads(timing_file.read_text())
    except json.JSONDecodeError:
        return {}

def format_duration(seconds: float | None) -> str:
    """Format duration in human-readable form."""
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"~{int(seconds)}s"
    minutes = int(seconds / 60)
    secs = int(seconds % 60)
    return f"~{minutes}m {secs}s" if secs else f"~{minutes}m"

def format_timestamp(iso_str: str | None) -> str:
    """Format ISO timestamp for display."""
    if not iso_str:
        return "never"
    try:
        # Handle various formats
        if "T" in iso_str:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        return iso_str.split("T")[0]
    except ValueError:
        return iso_str

def get_status_badge(health: str) -> str:
    """Get status badge HTML."""
    if "🟢" in health or "green" in health.lower() or "healthy" in health.lower():
        return '<span class="status-badge status-green">Healthy</span>'
    elif "🟡" in health or "yellow" in health.lower() or "assessing" in health.lower() or "initializing" in health.lower():
        return '<span class="status-badge status-yellow">Assessing</span>'
    elif "🔴" in health or "red" in health.lower():
        return '<span class="status-badge status-red">Issues</span>'
    return '<span class="status-badge status-yellow">Unknown</span>'

def parse_task(line: str) -> str:
    """Parse a task line and return HTML."""
    # Handle numbered lists with checkboxes
    match = re.match(r'^\d+\.\s*\[([ x])\]\s*(.+)$', line)
    if match:
        checked, text = match.groups()
        text = html.escape(text)
        cls = "task-done" if checked == "x" else "task-pending"
        return f'<li class="{cls}">{text}</li>'

    # Handle bullet lists with checkboxes
    match = re.match(r'^-\s*\[([ x])\]\s*(.+)$', line)
    if match:
        checked, text = match.groups()
        text = html.escape(text)
        cls = "task-done" if checked == "x" else "task-pending"
        return f'<li class="{cls}">{text}</li>'

    # Plain items
    text = re.sub(r'^(\d+\.\s*|\-\s*)', '', line)
    text = html.escape(text)
    return f'<li class="task-pending">{text}</li>'

def get_system_status() -> dict:
    """Get current system status."""
    import subprocess

    status = {
        "ram": "Unknown",
        "disk": "Unknown",
        "cpu": "Unknown",
        "openclaw": "Unknown",
        "models": "Unknown",
    }

    try:
        # RAM
        result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    total = parts[1]
                    used = parts[2]
                    status["ram"] = f"{total} ({used} used)"
    except Exception:
        pass

    try:
        # Disk
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    total = parts[1]
                    used_pct = parts[4]
                    status["disk"] = f"{total} ({used_pct} used)"
    except Exception:
        pass

    try:
        # CPU
        result = subprocess.run(["nproc"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            status["cpu"] = f"{result.stdout.strip()} cores"
    except Exception:
        pass

    # OpenClaw version
    try:
        result = subprocess.run(["openclaw", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            status["openclaw"] = result.stdout.strip()
    except Exception:
        pass

    status["models"] = "Check openclaw --version for details"

    return status

def get_services_status() -> list:
    """Get status of key services."""
    import subprocess

    services = [
        ("Redis", "?", "Unknown"),
        ("Qdrant", "?", "Unknown"),
    ]

    # Check Redis
    try:
        result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and "PONG" in result.stdout:
            services[0] = ("Redis", "✓", "Running")
        else:
            services[0] = ("Redis", "✗", "Not responding")
    except Exception:
        services[0] = ("Redis", "?", "Unknown")

    # Check Qdrant
    collection_name = os.environ.get("QDRANT_COLLECTION")
    if not collection_name:
        collection_name = "(not configured)"
        services[1] = ("Qdrant", "?", "QDRANT_COLLECTION not set in .memory_env")
        return services
    try:
        import urllib.request
        qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        req = urllib.request.Request(f"{qdrant_url}/collections/{collection_name}")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("result", {}).get("status") == "green":
                count = data.get("result", {}).get("points_count", "?")
                services[1] = ("Qdrant", "✓", f"Running ({count} memories)")
    except Exception:
        services[1] = ("Qdrant", "✗", "Not responding")

    return services

def count_stats() -> dict:
    """Count evergreen stats."""
    evergreens = discover_evergreens()
    stats = {
        "active": len(evergreens),
        "cycles": 0,
        "tasks": 0,
        "experiments": 0,
        "blocking": 0,
    }

    for name, _ in evergreens:
        timing = read_timing(name)
        if timing.get("status") == "completed":
            stats["cycles"] += 1

        state = read_state(name)
        stats["tasks"] += len(state.get("next_steps", []))

        # Count experiments and blocking issues from STATE.md raw content
        state_file = EVERGREENS_DIR / name / "STATE.md"
        if state_file.exists():
            try:
                content = state_file.read_text()
                # Count experiment references (E001, E002, etc.)
                stats["experiments"] += len(re.findall(r'\bE\d{3}\b', content))
                # Count blocking issues
                if "## Blocking Issues" in content:
                    blocking_section = content.split("## Blocking Issues")[1].split("##")[0]
                    stats["blocking"] += len([l for l in blocking_section.strip().split("\n") if l.strip().startswith("- ")])
            except Exception:
                pass

    return stats

def get_agenda_info(evergreen: str) -> dict:
    """Check for agenda file and return info."""
    agenda_file = EVERGREENS_DIR / evergreen / "AGENDA.md"
    result = {"exists": False, "path": None, "date": None}

    if agenda_file.exists():
        result["exists"] = True
        result["path"] = str(agenda_file)
        try:
            # Try to extract date from agenda content
            content = agenda_file.read_text()
            match = re.search(r'Agenda for (\d{4}-\d{2}-\d{2})', content)
            if match:
                result["date"] = match.group(1)
            else:
                # Use file modification time
                mtime = agenda_file.stat().st_mtime
                result["date"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except Exception:
            result["date"] = "today"

    return result

def generate_dashboard():
    """Generate the dashboard HTML."""

    now = datetime.now(timezone.utc)
    # Convert to local time for display
    local_now = datetime.now()
    data_timestamp = local_now.strftime("%Y-%m-%d %I:%M %p")

    # Get system status
    sys_status = get_system_status()
    services = get_services_status()
    stats = count_stats()

    # Determine overall system health from service checks
    service_icons = [s[1] for s in services]
    if all(i == "✓" for i in service_icons):
        sys_health_badge = '<span class="status-badge status-green">Healthy</span>'
    elif any(i == "✗" for i in service_icons):
        sys_health_badge = '<span class="status-badge status-red">Degraded</span>'
    else:
        sys_health_badge = '<span class="status-badge status-yellow">Unknown</span>'

    # Collect evergreen data
    evergreen_cards = []
    recent_activity = []

    for name, title in discover_evergreens():
        state = read_state(name)
        timing = read_timing(name)
        agenda = get_agenda_info(name)

        health = state.get("health", "🟡 Unknown")
        last_cycle = format_timestamp(timing.get("completed_at"))
        duration = format_duration(timing.get("duration_seconds"))
        status = timing.get("status", "never_run")

        # Build next steps HTML
        next_steps_html = ""
        for step in state.get("next_steps", []):
            next_steps_html += parse_task(step) + "\n"

        # Build agenda link HTML
        agenda_html = ""
        if agenda["exists"]:
            agenda_html = f'''
            <div class="agenda-link">
                <a href="evergreens/{name}/AGENDA.md" class="agenda-btn">📋 Current Agenda</a>
                <span class="agenda-date">{agenda['date']}</span>
            </div>'''

        # Build completed HTML for recent activity
        for item in state.get("completed", []):
            # Extract date and text
            match = re.match(r'^-\s*\[([^\]]+)\]\s*(.+)$', item)
            if match:
                date, text = match.groups()
                recent_activity.append((date, text, name))

        card = f'''
        <div class="card">
            <div class="card-header">
                <h2>{title}</h2>
                {get_status_badge(health)}
            </div>
            <div class="cycle-info">
                <span class="cycle-badge cycle-blue">Cycle</span>
                Last: {last_cycle}
            </div>
            <div class="timing-info">
                Duration: <span class="timing-duration">{duration}</span>
                {" <em>(in progress)</em>" if status == "in_progress" else ""}
            </div>
            {agenda_html}
            <h3>Next Steps</h3>
            <ul class="task-list">
                {next_steps_html if next_steps_html else '<li class="task-pending">No pending tasks</li>'}
            </ul>
        </div>'''
        evergreen_cards.append(card)

    # Sort recent activity by date (newest first)
    recent_activity.sort(key=lambda x: x[0], reverse=True)
    recent_activity_html = ""
    for date, text, source in recent_activity[:5]:
        recent_activity_html += f'<li class="task-done">{html.escape(date)}: {html.escape(text)}</li>\n'

    # Build services HTML
    services_html = ""
    for name, icon, status in services:
        color = "#00ba7c" if icon == "✓" else ("#f4212e" if icon == "✗" else "#71767b")
        services_html += f'''
            <div class="metric">
                <span class="metric-label">{name}</span>
                <span class="metric-value" style="color: {color};">{icon} {status}</span>
            </div>'''

    # Full HTML
    html_output = f'''<!-- GENERATED FILE — Do not edit manually.
     Built by scripts/update_evergreen_dashboard.py from evergreens/STATE.md + timing.json -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evergreens Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #0f1419;
            color: #e7e9ea;
            line-height: 1.6;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #2f3336;
        }}
        h1 {{ font-size: 1.8em; color: #f7b267; }}
        .last-updated {{ color: #71767b; font-size: 0.9em; }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: #16181c;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2f3336;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .card h2 {{ font-size: 1.1em; color: #f7b267; }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .status-green {{ background: #00ba7c; color: white; }}
        .status-yellow {{ background: #f4af3d; color: black; }}
        .status-red {{ background: #f4212e; color: white; }}

        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #2f3336;
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #71767b; }}
        .metric-value {{ font-weight: 600; }}

        h3 {{
            font-size: 0.95em;
            color: #71767b;
            margin: 20px 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .agenda-link {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 12px 0;
            padding: 8px 12px;
            background: #1a2a3a;
            border-radius: 6px;
        }}
        .agenda-btn {{
            display: inline-block;
            padding: 4px 10px;
            background: #1f4a6a;
            color: #6bb3ff;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        .agenda-btn:hover {{
            background: #2a5a7a;
        }}
        .agenda-date {{
            color: #71767b;
            font-size: 0.8em;
        }}

        .task-list {{ list-style: none; }}
        .task-list li {{
            padding: 8px 12px;
            margin: 6px 0;
            background: #1d1f23;
            border-radius: 6px;
            font-size: 0.9em;
        }}
        .task-pending {{ border-left: 3px solid #f4af3d; }}
        .task-done {{ border-left: 3px solid #00ba7c; opacity: 0.7; }}

        .cycle-info {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85em;
            color: #71767b;
            margin-bottom: 10px;
        }}
        .cycle-badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .cycle-blue {{ background: #1f3a4a; color: #6bb3ff; }}

        .timing-info {{
            font-size: 0.8em;
            color: #71767b;
            margin-bottom: 10px;
        }}
        .timing-info em {{ color: #f4af3d; }}
        .timing-duration {{
            color: #00ba7c;
            font-weight: 600;
        }}

        section {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #2f3336;
        }}
        section h2 {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #f7b267;
        }}

        .investment-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        .investment-card {{
            background: #1a1a2e;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #9b59b6;
        }}
        .investment-card h4 {{ color: #9b59b6; margin-bottom: 8px; }}
        .investment-card p {{ font-size: 0.9em; color: #a0a0a0; }}
        .investment-card .price {{ font-size: 1.2em; color: #f7b267; margin-top: 8px; }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #2f3336;
            text-align: center;
            color: #71767b;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🌲 Evergreens Dashboard</h1>
        <div class="last-updated">Data updated: <span id="data-timestamp">{data_timestamp}</span></div>
    </header>

    <!-- System Overview -->
    <div class="grid">
        <div class="card">
            <div class="card-header">
                <h2>💻 System Status</h2>
                {sys_health_badge}
            </div>
            <div class="metric">
                <span class="metric-label">RAM</span>
                <span class="metric-value">{sys_status['ram']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Disk</span>
                <span class="metric-value">{sys_status['disk']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">CPU</span>
                <span class="metric-value">{sys_status['cpu']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">OpenClaw</span>
                <span class="metric-value">{sys_status['openclaw']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Models</span>
                <span class="metric-value">{sys_status['models']}</span>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h2>📊 Evergreen Summary</h2>
            </div>
            <div class="metric">
                <span class="metric-label">Active Programs</span>
                <span class="metric-value">{stats['active']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Cycles Completed</span>
                <span class="metric-value">{stats['cycles']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Open Tasks</span>
                <span class="metric-value">{stats['tasks']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Active Experiments</span>
                <span class="metric-value">{stats['experiments']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Blocking Issues</span>
                <span class="metric-value">{stats['blocking']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Schedule</span>
                <span class="metric-value">Daily (see crontab)</span>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h2>🔧 Services</h2>
            </div>
            {services_html}
        </div>
    </div>

    <!-- Evergreen Cards -->
    <div class="grid">
        {''.join(evergreen_cards)}
    </div>

    <!-- Investment Suggestions -->
    <section>
        <h2>💰 Investment Suggestions</h2>
        <p style="color: #71767b; margin-bottom: 15px;">Populated by the system-health evergreen. Edit this section in update_evergreen_dashboard.py or let your agent customize it.</p>
        <div class="investment-grid">
            <!-- Add cards here based on your system's actual needs, e.g.:
            <div class="investment-card">
                <h4>Upgrade Title</h4>
                <p>Why this matters for your setup.</p>
                <div class="price">Estimated cost</div>
            </div>
            -->
        </div>
    </section>

    <!-- Recent Activity -->
    <section>
        <h2>📋 Recent Activity</h2>
        <ul class="task-list">
            {recent_activity_html if recent_activity_html else '<li class="task-done">No recent activity recorded</li>'}
        </ul>
    </section>

    <footer>
        <p>Evergreens Dashboard • Generated from evergreens/STATE.md + timing.json</p>
        <p>Framework: <a href="evergreens/EVERGREENS.md" style="color: #f7b267;">EVERGREENS.md</a></p>
    </footer>
</body>
</html>'''

    return html_output

if __name__ == "__main__":
    html_output = generate_dashboard()
    output_file = EVERGREENS_DIR / "DASHBOARD.html"
    output_file.write_text(html_output)
    print(f"Dashboard updated: {output_file}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")