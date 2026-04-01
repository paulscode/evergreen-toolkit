#!/usr/bin/env python3
"""
Pre-flight check for Evergreen Toolkit.

Verifies all required dependencies, services, and configuration are in place
before running evergreen cycles.

Usage:
    python3 scripts/preflight-check.py
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

passed = 0
warned = 0
failed = 0


def check(name, ok, msg_ok="OK", msg_fail="Missing", warn_only=False):
    global passed, warned, failed
    if ok:
        passed += 1
        print(f"  {GREEN}✓{RESET} {name}: {msg_ok}")
    elif warn_only:
        warned += 1
        print(f"  {YELLOW}⚠{RESET} {name}: {msg_fail}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {name}: {msg_fail}")


def run_quiet(cmd):
    """Run a command and return (success, stdout).

    cmd must be a list of arguments (no shell interpretation).
    """
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, ""


def main():
    print(f"\n{'=' * 50}")
    print("  Evergreen Toolkit — Pre-flight Check")
    print(f"{'=' * 50}\n")

    # --- Python ---
    print("Python:")
    v = sys.version_info
    check("Python version", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}", f"{v.major}.{v.minor} (need 3.10+)")

    # Check key packages
    for pkg in ["qdrant_client", "redis", "requests", "yaml"]:
        try:
            __import__(pkg)
            check(f"  {pkg}", True)
        except ImportError:
            check(f"  {pkg}", False, msg_fail="Not installed — run: pip install -r requirements.txt")

    # --- System tools ---
    print("\nSystem tools:")
    for tool, required in [("redis-cli", True), ("curl", True), ("jq", True), ("flock", True), ("node", False), ("ollama", False), ("openclaw", False)]:
        found = shutil.which(tool) is not None
        if required:
            check(tool, found, msg_fail=f"Not found on PATH")
        else:
            check(tool, found, msg_fail=f"Not found (optional)", warn_only=True)

    # --- Services ---
    print("\nServices:")
    ok, _ = run_quiet(["redis-cli", "ping"])
    check("Redis responding", ok, "PONG", "Not responding — start with: redis-server --daemonize yes")

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    ok, _ = run_quiet(["curl", "-sf", f"{qdrant_url}/health"])
    check("Qdrant responding", ok, "Healthy", f"Not responding at {qdrant_url}")

    ok, out = run_quiet(["ollama", "list"])
    check("Ollama responding", ok, "Running", "Not responding — start with: ollama serve (needed for embeddings)", warn_only=True)

    if ok:
        ok2 = "snowflake-arctic-embed2" in out
        check("  Embedding model", ok2, "snowflake-arctic-embed2 found", "Missing — run: ollama pull snowflake-arctic-embed2 (required for memory embeddings)")

        # Check curation model (reads from .memory_env or defaults to qwen3:4b)
        curation_model = os.environ.get("CURATION_MODEL", "qwen3:4b")
        ok3 = curation_model in out
        check("  Curation model", ok3, f"{curation_model} found", f"Missing — run: ollama pull {curation_model} (required for True Recall gem extraction)")

    # --- Configuration ---
    print("\nConfiguration:")
    env_file = WORKSPACE / ".memory_env"
    check(".memory_env exists", env_file.exists(), str(env_file), "Missing — copy from config/memory_env.example")

    if env_file.exists():
        content = env_file.read_text()
        for var in ["QDRANT_COLLECTION", "DEFAULT_USER_ID", "AGENT_NAME"]:
            has_var = var in content and f"<" not in content.split(var + "=")[-1].split("\n")[0]
            check(f"  {var} configured", has_var, msg_fail=f"Still has placeholder value", warn_only=(var == "AGENT_NAME"))

    venv = WORKSPACE / ".venv"
    check("Virtual environment", venv.exists(), str(venv), "Missing — run: python3 -m venv .venv")

    # --- OpenClaw exec config ---
    print("\nOpenClaw exec config:")
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", Path.home() / ".openclaw"))
    oc_config = openclaw_home / "openclaw.json"
    check("openclaw.json exists", oc_config.exists(), str(oc_config), f"Not found at {oc_config}", warn_only=True)

    if oc_config.exists():
        try:
            oc_data = json.loads(oc_config.read_text())
            tools_exec = oc_data.get("tools", {}).get("exec", {})
            exec_security = tools_exec.get("security", "")
            exec_ask = tools_exec.get("ask", "")

            check(
                "tools.exec.security",
                exec_security == "full",
                "full",
                f'{"not set" if not exec_security else repr(exec_security)} — set to "full" in openclaw.json (required for autonomous shell commands)',
            )
            check(
                "tools.exec.ask",
                exec_ask == "off",
                "off",
                f'{"not set" if not exec_ask else repr(exec_ask)} — set to "off" in openclaw.json (required for unattended cron execution)',
            )
        except (json.JSONDecodeError, OSError) as exc:
            check("openclaw.json readable", False, msg_fail=f"Parse error: {exc}")

    # --- Workspace structure ---
    print("\nWorkspace structure:")
    for d in ["evergreens", "memory/scripts", "scripts", "config", "logs"]:
        p = WORKSPACE / d
        check(d, p.exists())

    for eg in ["upstream-architecture", "system-health", "prompt-injection", "household-memory"]:
        state = WORKSPACE / "evergreens" / eg / "STATE.md"
        check(f"  {eg}/STATE.md", state.exists())

    # --- Summary ---
    total = passed + warned + failed
    print(f"\n{'=' * 50}")
    print(f"  Results: {GREEN}{passed} passed{RESET}, {YELLOW}{warned} warnings{RESET}, {RED}{failed} failed{RESET} ({total} checks)")
    if failed == 0 and warned == 0:
        print(f"  {GREEN}All checks passed! Ready to run evergreens.{RESET}")
    elif failed == 0:
        print(f"  {YELLOW}Warnings present but not blocking. Review above.{RESET}")
    else:
        print(f"  {RED}Fix the failed checks above before running evergreens.{RESET}")
    print(f"{'=' * 50}\n")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
