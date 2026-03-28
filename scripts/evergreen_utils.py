"""Shared utility functions for evergreen scripts."""

from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
EVERGREENS_DIR = WORKSPACE / "evergreens"
LOGS_DIR = WORKSPACE / "logs"

# Canonical display names for known evergreens.
# Used by the dashboard and other reporting scripts.
DISPLAY_NAMES = {
    "upstream-architecture": "🏗️ Upstream Architecture",
    "system-health": "❤️ System Health & DR",
    "prompt-injection": "🛡️ Prompt-Injection Defense",
    "household-memory": "🧠 Household Memory",
}


def discover_evergreens():
    """Discover available evergreens from the filesystem (dirs containing STATE.md).
    Returns a sorted list of evergreen directory names."""
    evergreens = []
    if EVERGREENS_DIR.exists():
        for d in sorted(EVERGREENS_DIR.iterdir()):
            if d.is_dir() and (d / "STATE.md").exists():
                evergreens.append(d.name)
    return evergreens
