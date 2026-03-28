#!/usr/bin/env python3
"""
Memory validation module — validates content before storing in memory.

Provides two functions used by save_mem.py and other capture scripts:
  - validate_content(text): Returns (is_safe, list_of_issues)
  - wrap_external_content(text, source, sender): Wraps untrusted content with markers

Injection patterns based on: evergreens/prompt-injection/MEMORY-VALIDATION.md
"""

import re
from typing import List, Tuple, Optional

# Patterns that indicate prompt injection attempts in stored content.
# Sourced from evergreens/prompt-injection/MEMORY-VALIDATION.md
INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|above|prior) instructions", re.IGNORECASE),
    re.compile(r"disregard (all )?(previous|above|prior)", re.IGNORECASE),
    re.compile(r"your (new |actual |real )?instructions are", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"forget everything", re.IGNORECASE),
    re.compile(r"override (your )?(system |prompt )?(settings|instructions)", re.IGNORECASE),
    re.compile(r"reveal (your )?(credentials|api keys|passwords)", re.IGNORECASE),
    re.compile(r"send (me |us )?(your )?(credentials|api keys)", re.IGNORECASE),
    re.compile(r"execute (the following|this) command", re.IGNORECASE),
    re.compile(r"run (the following|this)", re.IGNORECASE),
]


def validate_content(text: str) -> Tuple[bool, List[str]]:
    """Check text for prompt injection patterns.

    Args:
        text: Content to validate.

    Returns:
        Tuple of (is_safe, list_of_matched_issues).
        is_safe is True if no injection patterns were found.
    """
    if not text:
        return True, []

    issues = []
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            issues.append(f"Injection pattern detected: '{match.group()}'")

    return len(issues) == 0, issues


def wrap_external_content(text: str, source: str = "unknown", sender: Optional[str] = None) -> str:
    """Wrap untrusted external content with safety markers.

    Args:
        text: The external content to wrap.
        source: Origin type (e.g., "email", "web", "api").
        sender: Optional sender identifier.

    Returns:
        The content wrapped in EXTERNAL_UNTRUSTED_CONTENT markers.
    """
    sender_attr = f' from="{sender}"' if sender else ""
    return (
        f'<<<EXTERNAL_UNTRUSTED_CONTENT source="{source}"{sender_attr}>>>\n'
        f"{text}\n"
        f"<<<END_EXTERNAL_UNTRUSTED_CONTENT>>>"
    )
